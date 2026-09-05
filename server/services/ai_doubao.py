# -*- coding: utf-8 -*-
"""豆包AI服务（写文章 + 生图）（从原 baijiahao 项目提取并适配）
网页版：https://www.doubao.com/chat
"""
import os
import json
import time
import traceback
import re
from services.browser_base import BrowserBase


class DoubaoAIService(BrowserBase):
    """豆包AI服务（写文章 + 生图）"""

    def __init__(self, account_id, headless=False):
        super().__init__("doubao", account_id, headless)
        self.base_page_url = "https://www.doubao.com/chat"
        self.images_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "images")

    def login(self):
        """登录检查 + 自动填充账号密码"""
        try:
            self.safe_goto(self.base_page_url)
            time.sleep(5)

            # 检测登录按钮
            login_btn = self.page.locator('[data-testid="to_login_button"]')
            if login_btn.count() > 0 and login_btn.is_visible():
                self.print_info("检测到未登录，尝试自动登录...")

                # 点击登录按钮
                try:
                    login_btn.click()
                    time.sleep(3)
                except Exception as e:
                    self.print_warning(f"点击登录按钮失败: {e}")

                # 尝试自动填充账号密码（豆包登录页可能有多种表单结构）
                auto_filled = False

                # 尝试方式1：手机号+密码登录
                try:
                    # 切换到密码登录（如果有）
                    pwd_tab = self.page.locator('text=密码登录')
                    if pwd_tab.count() > 0:
                        pwd_tab.first.click()
                        time.sleep(1)

                    auto_filled = self.auto_fill_login(
                        username_selector='input[placeholder*="手机号"], input[placeholder*="邮箱"], input[type="text"]',
                        password_selector='input[type="password"]',
                        submit_selector='button[type="submit"], button:has-text("登录")'
                    )
                except Exception as e:
                    self.print_warning(f"自动填充方式1失败: {e}")

                if not auto_filled:
                    self.print_warning("自动登录失败，请在浏览器中手动登录")
                    # 等待用户手动登录（最多等待60秒）
                    wait_time = 0
                    while wait_time < 60:
                        time.sleep(5)
                        wait_time += 5
                        login_btn = self.page.locator('[data-testid="to_login_button"]')
                        if login_btn.count() == 0 or not login_btn.is_visible():
                            self.print_success("手动登录成功")
                            return True
                    return False

                # 等待登录完成
                time.sleep(5)
                login_btn = self.page.locator('[data-testid="to_login_button"]')
                if login_btn.count() > 0 and login_btn.is_visible():
                    self.print_warning("自动登录可能失败，请在浏览器中手动登录")
                    return False

                self.print_success("自动登录成功")
                return True
            else:
                self.print_success("已登录")
                return True
        except Exception as e:
            self.print_error(f"登录检查发生异常: {str(e)}")
            traceback.print_exc()
            return False

    def _ai_chat(self, prompt, action="text", timeout=300):
        """
        通用对话方法
        Args:
            prompt: 提示词
            action: text=文本对话, image=图像生成
            timeout: 超时时间
        Returns:
            (success, result)
        """
        try:
            # 如果是图像生成，先切换到图像生成技能
            if action == "image":
                try:
                    # 检查是否已经在图像生成模式
                    if self.page.locator('[data-testid="skill_input_exit_button"]').count() == 0:
                        # 点击图像生成
                        img_btn = self.page.locator('xpath=//div[text()="图像生成"]')
                        if img_btn.count() > 0:
                            img_btn.click()
                        else:
                            # 点击技能菜单
                            self.page.click('text="技能"')
                            time.sleep(0.5)
                            img_btn = self.page.locator(".semi-popover").get_by_text('图像生成')
                            if img_btn.count() > 0:
                                img_btn.click()
                        time.sleep(0.5)
                except Exception as e:
                    self.print_warning(f"切换图像生成模式失败: {e}")

            # 填入提示词
            if not self.safe_fill('[data-testid="chat_input_input"]', prompt, timeout=15000):
                return False, "找不到输入框"

            time.sleep(0.5)

            # 点击发送
            if not self.safe_click('[data-testid="chat_input_send_button"]', timeout=10000):
                return False, "找不到发送按钮"

            time.sleep(5)

            # 等待生成完成
            waiting = 0
            while True:
                time.sleep(2)
                waiting += 2

                # 检测"停止生成"按钮是否消失
                stop_btn = self.page.locator('[data-testid="chat_input_local_break_button"]')
                if stop_btn.count() == 0 or not stop_btn.is_visible():
                    break

                if waiting > timeout:
                    self.print_error(f"生成超时（{timeout}秒）")
                    try:
                        stop_btn.click()
                    except:
                        pass
                    return False, "生成超时"

            # 滚动到底部
            try:
                bottom_btn = self.page.locator("#to-bottom-button")
                if bottom_btn.count() > 0 and bottom_btn.get_attribute("data-visible") == 'true':
                    bottom_btn.click()
                time.sleep(2)
            except:
                pass

            # 获取结果
            if action == "text":
                # 文本对话，获取文字内容
                result_el = self.page.locator('[data-testid="message_text_content"]').last
                if result_el.count() > 0:
                    content = result_el.inner_text()
                    return True, content
                else:
                    return False, "无法获取生成内容"

            elif action == "image":
                # 图像生成，获取图片并下载
                message_content = self.page.locator('[data-testid="message_content"]').last
                images = message_content.locator('[data-testid="mdbox_image"]')

                if images.count() == 0:
                    return False, "生成图片数量为0"

                urls = []
                for i in range(images.count()):
                    try:
                        img = images.nth(i)
                        img.click()
                        time.sleep(2)

                        # 下载图片
                        with self.page.expect_download() as download_info:
                            self.page.locator('[data-testid="edit_image_download_button"]').click()

                        download = download_info.value
                        download_path = download.path()
                        file_ext = os.path.splitext(download.suggested_filename)[1]

                        # 保存到本地
                        os.makedirs(self.images_dir, exist_ok=True)
                        new_filename = f"img_{int(time.time())}_{i}{file_ext}"
                        new_filepath = os.path.join(self.images_dir, new_filename)
                        download.save_as(new_filepath)

                        # 清理临时文件
                        try:
                            os.remove(download_path)
                        except:
                            pass

                        # 关闭图片预览
                        self.page.locator('[data-testid="edit_image_close_button"]').click()
                        time.sleep(1)

                        urls.append(new_filepath)
                        self.print_success(f"图片已保存: {new_filename}")

                    except Exception as e:
                        self.print_error(f"下载第{i}张图片失败: {e}")
                        try:
                            self.page.locator('[data-testid="edit_image_close_button"]').click()
                        except:
                            pass

                return True, urls

        except Exception as e:
            self.print_error(f"对话发生异常: {str(e)}")
            traceback.print_exc()
            return False, f"异常: {str(e)}"

    def generate_article(self, title, prompt, apply_prompt="", timeout=600):
        """
        生成文章
        Args:
            title: 文章标题
            prompt: 文章生成提示词
            apply_prompt: 附加要求
            timeout: 超时时间
        Returns:
            (success, content, message)
        """
        try:
            # 拼接提示词
            instruct = f"{prompt}\n\n{title}"
            if apply_prompt:
                instruct += f"\n\n附加要求：\n{apply_prompt}"

            self.print_info(f"开始生成文章: {title}")

            # 打开豆包
            self.safe_goto(self.base_page_url)
            time.sleep(5)

            # 使用文本对话模式
            success, result = self._ai_chat(instruct, action="text", timeout=timeout)

            if not success:
                return False, "", result

            content = result
            if len(content) < 100:
                self.print_warning(f"文章内容较短（{len(content)}字），可能不完整")

            self.print_success(f"文章生成成功，共 {len(content)} 字")
            return True, content, ""

        except Exception as e:
            self.print_error(f"生成文章发生异常: {str(e)}")
            traceback.print_exc()
            return False, "", f"生成异常: {str(e)}"

    def generate_image(self, prompt, timeout=300):
        """
        生成单张图片（实际豆包一次生成多张，返回所有图片路径）
        Args:
            prompt: 图片生成提示词
            timeout: 超时时间
        Returns:
            (success, image_paths, message)
        """
        try:
            self.print_info(f"开始生成图片: {prompt[:50]}...")

            # 打开豆包
            self.safe_goto(self.base_page_url)
            time.sleep(5)

            # 使用图像生成模式
            success, result = self._ai_chat(prompt, action="image", timeout=timeout)

            if not success:
                return False, [], result

            return True, result, ""

        except Exception as e:
            self.print_error(f"生成图片发生异常: {str(e)}")
            traceback.print_exc()
            return False, [], f"生成异常: {str(e)}"

    def generate_images_batch(self, prompt, count=3, timeout=300):
        """
        批量生成备选图片（调用多次生图，收集所有结果）
        Args:
            prompt: 图片生成提示词
            count: 需要的备选图片数量
            timeout: 单次超时时间
        Returns:
            (success, image_paths, message)
        """
        all_images = []
        attempts = 0
        max_attempts = count + 2  # 多尝试几次，确保凑够数量

        while len(all_images) < count and attempts < max_attempts:
            attempts += 1
            self.print_info(f"第{attempts}次尝试生成图片（已获取{len(all_images)}/{count}）")

            success, images, msg = self.generate_image(prompt, timeout=timeout)

            if success and images:
                all_images.extend(images)
            else:
                self.print_warning(f"第{attempts}次生成失败: {msg}")

            # 每次生成后短暂等待
            time.sleep(2)

        if len(all_images) == 0:
            return False, [], "所有生图尝试均失败"

        # 只返回需要的数量
        result_images = all_images[:count]
        self.print_success(f"批量生图完成，共获取 {len(result_images)} 张备选图片")
        return True, result_images, ""

    def rewrite_titles(self, original_titles, rewrite_instruction="", timeout=300):
        """
        调用豆包AI批量重写标题
        Args:
            original_titles: 原始标题列表
            rewrite_instruction: 重写指令（用户自定义）
            timeout: 超时时间
        Returns:
            (success, new_titles, message)
        """
        try:
            if not original_titles:
                return False, [], "原始标题列表为空"

            # 默认重写指令
            default_instruction = """学习上述标题内容，总结出标题的爆点，然后给出爆点结论，为什么会成为爆款标题。根据以上总结的内容，充分发挥你的想象力和创造力，套用以上爆款模板，重新仿写5个统一类型和特征的爆款标题，要求与原标题意思相近。
请直接输出5个新标题，每行一个，不要编号，不要其他解释。"""

            instruction = rewrite_instruction if rewrite_instruction else default_instruction

            # 拼接提示词
            titles_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(original_titles)])
            prompt = f"以下是原始爆款标题：\n{titles_text}\n\n{instruction}"

            self.print_info(f"开始批量重写标题，共 {len(original_titles)} 个原始标题")

            # 打开豆包
            self.safe_goto(self.base_page_url)
            time.sleep(5)

            # 使用文本对话模式
            success, result = self._ai_chat(prompt, action="text", timeout=timeout)

            if not success:
                return False, [], result

            # 解析返回的新标题
            new_titles = []
            lines = result.strip().split('\n')
            for line in lines:
                line = line.strip()
                # 去除编号（如 "1."、"1、"、"1)"等）
                line = re.sub(r'^[\d]+[\.\、\)\:]\s*', '', line)
                # 去除引号
                line = line.strip('"\'""''')
                if line and len(line) > 5:
                    new_titles.append(line)

            # 去重
            new_titles = list(dict.fromkeys(new_titles))

            self.print_success(f"标题重写完成，共生成 {len(new_titles)} 个新标题")
            return True, new_titles, ""

        except Exception as e:
            self.print_error(f"标题重写发生异常: {str(e)}")
            traceback.print_exc()
            return False, [], f"重写异常: {str(e)}"
