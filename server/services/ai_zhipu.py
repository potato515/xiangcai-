# -*- coding: utf-8 -*-
"""智谱AI写文章服务（从原 baijiahao 项目提取并适配）
网页版：https://chat.z.ai
"""
import os
import time
import traceback
from services.browser_base import BrowserBase


class ZhipuAIService(BrowserBase):
    """智谱AI写文章服务"""

    def __init__(self, account_id, headless=False):
        super().__init__("zhipu", account_id, headless)
        self.base_page_url = "https://chat.z.ai"

    def login(self):
        """登录检查 + 自动填充账号密码"""
        try:
            self.safe_goto(self.base_page_url)
            time.sleep(5)

            # 检测登录按钮（智谱AI的登录按钮可能在右上角）
            login_btn = self.page.locator('button:has-text("登录"), a:has-text("登录"), [class*="login"]')
            if login_btn.count() > 0:
                self.print_info("检测到未登录，尝试自动登录...")

                # 点击登录按钮
                try:
                    login_btn.first.click()
                    time.sleep(3)
                except Exception as e:
                    self.print_warning(f"点击登录按钮失败: {e}")

                # 尝试自动填充账号密码
                auto_filled = self.auto_fill_login(
                    username_selector='input[placeholder*="手机号"], input[placeholder*="邮箱"], input[type="text"], input[name*="account"], input[name*="username"]',
                    password_selector='input[type="password"]',
                    submit_selector='button[type="submit"], button:has-text("登录"), button:has-text("确认")'
                )

                if not auto_filled:
                    self.print_warning("自动登录失败，请在浏览器中手动登录")
                    # 智谱支持免登录体验，即使未登录也可以使用基础功能
                    time.sleep(3)
                    return True

                # 等待登录完成
                time.sleep(5)
                self.print_success("自动登录完成")
                return True
            else:
                self.print_success("已登录")
                return True
        except Exception as e:
            self.print_error(f"登录检查发生异常: {str(e)}")
            traceback.print_exc()
            return False

    def generate_article(self, title, prompt, apply_prompt="", timeout=600):
        """
        生成文章
        Args:
            title: 文章标题
            prompt: 文章生成提示词（根据文章类型配置）
            apply_prompt: 附加要求（可选）
            timeout: 超时时间（秒）
        Returns:
            (success, content, message)
        """
        try:
            # 拼接提示词
            instruct = f"{prompt}\n\n{title}"
            if apply_prompt:
                instruct += f"\n\n附加要求：\n{apply_prompt}"

            self.print_info(f"开始生成文章: {title}")

            # 打开智谱AI
            self.safe_goto(self.base_page_url)
            time.sleep(5)

            # 填入提示词
            if not self.safe_fill("#chat-input", instruct, timeout=15000):
                return False, "", "找不到输入框"

            time.sleep(0.8)

            # 点击发送
            if not self.safe_click("#send-message-button", timeout=10000):
                return False, "", "找不到发送按钮"

            # 等待生成完成
            finished = False
            wait_time = 0
            while not finished:
                time.sleep(5)
                wait_time += 5

                # 检测"停止"按钮是否存在（存在表示正在生成）
                stop_btn = self.page.locator('div[aria-label="停止"]')
                if stop_btn.count() == 1:
                    if wait_time > timeout:
                        # 超时，强制停止
                        try:
                            stop_btn.click()
                        except:
                            pass
                        self.print_error(f"生成文章超时（{timeout}秒）")
                        return False, "", "生成超时"
                else:
                    # 生成结束
                    self.print_success("文章生成完成")
                    finished = True

            # 获取生成内容
            answer_content_el = self.page.locator('#response-content-container').last.locator('> div > [dir="auto"]')
            answer_content = []
            if answer_content_el.count() > 0:
                for ai in range(answer_content_el.count()):
                    answer_content.append(answer_content_el.nth(ai).inner_text())

            if len(answer_content) == 0:
                return False, "", "生成失败，无文章内容"

            content = '\n'.join(answer_content)

            # 检查文章完整性（原项目要求包含"创作声明"，这里放宽，只检查内容长度）
            if len(content) < 500:
                self.print_warning(f"文章内容较短（{len(content)}字），可能不完整")

            self.print_success(f"文章生成成功，共 {len(content)} 字")
            return True, content, ""

        except Exception as e:
            self.print_error(f"生成文章发生异常: {str(e)}")
            traceback.print_exc()
            return False, "", f"生成异常: {str(e)}"
