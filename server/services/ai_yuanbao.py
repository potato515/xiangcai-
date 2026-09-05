# -*- coding: utf-8 -*-
"""腾讯元宝AI写文章服务（从原 baijiahao 项目提取并适配）
网页版：https://yuanbao.tencent.com
"""
import os
import time
import traceback
from services.browser_base import BrowserBase


class YuanbaoAIService(BrowserBase):
    """腾讯元宝AI写文章服务"""

    def __init__(self, account_id, headless=False, model="DeepSeek"):
        super().__init__("yuanbao", account_id, headless)
        self.base_page_url = "https://yuanbao.tencent.com"
        self.model = model  # DeepSeek / Hunyuan

    def login(self):
        """登录检查 + 自动填充账号密码"""
        try:
            self.safe_goto(self.base_page_url)
            time.sleep(5)

            # 检测登录按钮
            login_btn = self.page.locator('.agent-dialogue__tool__login, button:has-text("登录"), a:has-text("登录")')
            if login_btn.count() > 0:
                self.print_info("检测到未登录，尝试自动登录...")

                # 点击登录按钮
                try:
                    login_btn.first.click()
                    time.sleep(3)
                except Exception as e:
                    self.print_warning(f"点击登录按钮失败: {e}")

                # 尝试自动填充账号密码（腾讯元宝支持QQ/微信/手机号登录）
                auto_filled = False

                # 尝试手机号+密码登录
                try:
                    # 切换到密码登录（如果有）
                    pwd_tab = self.page.locator('text=密码登录, text=手机号登录')
                    if pwd_tab.count() > 0:
                        pwd_tab.first.click()
                        time.sleep(1)

                    auto_filled = self.auto_fill_login(
                        username_selector='input[placeholder*="手机号"], input[placeholder*="QQ"], input[type="text"], input[name*="account"], input[name*="username"]',
                        password_selector='input[type="password"]',
                        submit_selector='button[type="submit"], button:has-text("登录"), button:has-text("确认")'
                    )
                except Exception as e:
                    self.print_warning(f"自动填充失败: {e}")

                if not auto_filled:
                    self.print_warning("自动登录失败，请在浏览器中手动登录")
                    # 等待用户手动登录（最多等待60秒）
                    wait_time = 0
                    while wait_time < 60:
                        time.sleep(5)
                        wait_time += 5
                        login_btn = self.page.locator('.agent-dialogue__tool__login')
                        if login_btn.count() == 0 or not login_btn.is_visible():
                            self.print_success("手动登录成功")
                            return True
                    return False

                # 等待登录完成
                time.sleep(5)
                login_btn = self.page.locator('.agent-dialogue__tool__login')
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

    def generate_article(self, title, prompt, apply_prompt="", timeout=600):
        """
        生成文章
        Args:
            title: 文章标题
            prompt: 文章生成提示词
            apply_prompt: 附加要求
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

            # 打开元宝AI
            self.safe_goto(self.base_page_url)
            time.sleep(5)

            # 选择模型
            try:
                current_model_button = self.page.locator('.ybc-model-select-button')
                if current_model_button.count() > 0:
                    current_model = current_model_button.inner_text()
                    if current_model != self.model:
                        current_model_button.click()
                        time.sleep(1)
                        self.page.locator(f'text="{self.model}"').click()
                        time.sleep(2)
                        self.print_info(f"已切换模型: {self.model}")
            except Exception as e:
                self.print_warning(f"模型切换失败（不影响生成）: {e}")

            # 填入提示词
            if not self.safe_fill('.ql-editor', instruct, timeout=15000):
                return False, "", "找不到输入框"

            time.sleep(1)

            # 点击发送
            if not self.safe_click('#yuanbao-send-btn', timeout=10000):
                return False, "", "找不到发送按钮"

            # 等待生成完成
            finished = False
            wait_time = 0
            while not finished:
                time.sleep(3)
                wait_time += 3

                # 检测发送按钮是否重新出现（出现表示生成完成）
                send_btn = self.page.locator('.style__send-btn___RwTm5')
                if send_btn.count() == 0 or not send_btn.is_visible():
                    self.print_success("文章生成完成")
                    finished = True
                elif wait_time > timeout:
                    self.print_error(f"生成文章超时（{timeout}秒）")
                    try:
                        send_btn.click()
                    except:
                        pass
                    return False, "", "生成超时"

            # 获取生成内容
            time.sleep(2)
            # 元宝的回复内容选择器
            answer_elements = self.page.locator('.markdown-body').last
            if answer_elements.count() > 0:
                content = answer_elements.inner_text()
            else:
                # 备选选择器
                answer_elements = self.page.locator('[class*="message-content"]').last
                if answer_elements.count() > 0:
                    content = answer_elements.inner_text()
                else:
                    return False, "", "无法获取生成内容"

            if len(content) < 100:
                self.print_warning(f"文章内容较短（{len(content)}字），可能不完整")

            self.print_success(f"文章生成成功，共 {len(content)} 字")
            return True, content, ""

        except Exception as e:
            self.print_error(f"生成文章发生异常: {str(e)}")
            traceback.print_exc()
            return False, "", f"生成异常: {str(e)}"
