# -*- coding: utf-8 -*-
"""浏览器自动化基类（从原 baijiahao 项目提取并简化）
同步调用模式：启动浏览器→执行操作→关闭浏览器
"""
import os
import json
import time
import traceback
from datetime import datetime
from playwright.sync_api import sync_playwright, ViewportSize


class BrowserBase:
    """浏览器自动化基类"""

    def __init__(self, platform_name, account_id, headless=False):
        self.platform_name = platform_name
        self.account_id = account_id
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.base_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "browser_profiles")
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ai_config.json")
        self.account_config = self._load_account_config()

    def _load_account_config(self):
        """加载账号配置（账号密码等）"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                accounts = config.get("ai_accounts", {}).get(self.platform_name, [])
                for acc in accounts:
                    if str(acc.get("account_id")) == str(self.account_id):
                        return acc
        except Exception as e:
            self.print_warning(f"加载账号配置失败: {e}")
        return {}

    def get_username(self):
        """获取账号用户名"""
        return self.account_config.get("account_id", "") or self.account_config.get("username", "")

    def get_password(self):
        """获取账号密码"""
        return self.account_config.get("password", "")

    def auto_fill_login(self, username_selector, password_selector, submit_selector=None, timeout=15000):
        """
        通用自动填充登录表单
        Args:
            username_selector: 用户名输入框选择器
            password_selector: 密码输入框选择器
            submit_selector: 提交按钮选择器（可选）
            timeout: 超时时间
        Returns:
            True表示已填充并提交，False表示未配置账号密码
        """
        username = self.get_username()
        password = self.get_password()

        if not username or not password:
            self.print_warning("未配置账号密码，需要手动登录")
            return False

        try:
            # 填充用户名
            if username_selector:
                self.page.wait_for_selector(username_selector, timeout=timeout)
                self.page.fill(username_selector, username)
                self.print_info(f"已自动填充用户名: {username}")

            time.sleep(0.5)

            # 填充密码
            if password_selector:
                self.page.wait_for_selector(password_selector, timeout=timeout)
                self.page.fill(password_selector, password)
                self.print_info("已自动填充密码")

            time.sleep(0.5)

            # 点击提交
            if submit_selector:
                try:
                    self.page.wait_for_selector(submit_selector, timeout=5000)
                    self.page.click(submit_selector)
                    self.print_info("已点击登录按钮")
                except:
                    pass

            return True
        except Exception as e:
            self.print_error(f"自动填充登录失败: {e}")
            return False

    def initialize_browser(self):
        """初始化Playwright浏览器"""
        try:
            self.playwright = sync_playwright().start()
            viewport = ViewportSize(width=1440, height=768)

            user_data_dir = os.path.join(self.base_data_dir, f"account_{self.platform_name}_{self.account_id}")
            if not os.path.exists(user_data_dir):
                os.makedirs(user_data_dir, exist_ok=True)

            self.browser = self.playwright.chromium.launch_persistent_context(
                headless=self.headless,
                viewport=viewport,
                user_data_dir=user_data_dir,
                accept_downloads=True,
                downloads_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "download"),
                bypass_csp=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-site-isolation-trials",
                    "--disable-features=IsolateOrigins,site-per-process",
                ],
            )

            self.page = self.browser.new_page()
            self.print_info("浏览器初始化完成")
            return True
        except Exception as e:
            self.print_error(f"浏览器初始化失败: {str(e)}")
            traceback.print_exc()
            return False

    def close_browser(self):
        """关闭浏览器"""
        try:
            if hasattr(self, 'page') and self.page and not self.page.is_closed():
                try:
                    self.page.close()
                except:
                    pass
            time.sleep(1)

            if hasattr(self, 'browser') and self.browser:
                try:
                    self.browser.close()
                except Exception as e:
                    if "Connection closed" not in str(e) and "already closed" not in str(e):
                        self.print_error(f"关闭浏览器时发生错误: {e}")
                finally:
                    self.browser = None

            time.sleep(0.5)

            if hasattr(self, 'playwright') and self.playwright:
                try:
                    self.playwright.stop()
                except Exception as e:
                    self.print_error(f"关闭playwright时出错: {e}")
                finally:
                    self.playwright = None

            self.print_info("浏览器关闭完成")
        except Exception as e:
            self.print_error(f"浏览器关闭过程中发生异常: {e}")
            for attr in ['page', 'context', 'browser', 'playwright']:
                if hasattr(self, attr):
                    try:
                        setattr(self, attr, None)
                    except:
                        pass

    def print_info(self, *values):
        print(datetime.now(), f'[{self.platform_name}]', self.account_id, *values)

    def print_warning(self, *values):
        print(datetime.now(), '\033[38;5;208m', f'[{self.platform_name}]', self.account_id, *values, '\033[0m')

    def print_error(self, *values):
        print(datetime.now(), f'\033[31m', f'[{self.platform_name}]', self.account_id, *values, '\033[0m')

    def print_success(self, *values):
        print(datetime.now(), '\033[92m', f'[{self.platform_name}]', self.account_id, *values, '\033[0m')

    def login(self):
        """登录检查，子类需重写"""
        raise NotImplementedError("子类必须实现login方法")

    def safe_goto(self, url, timeout=30000):
        """安全的页面跳转"""
        try:
            self.page.goto(url, timeout=timeout)
            self.page.wait_for_load_state('domcontentloaded', timeout=timeout)
            return True
        except Exception as e:
            self.print_error(f"页面跳转失败: {url}, {e}")
            return False

    def safe_click(self, selector, timeout=10000):
        """安全的点击操作"""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            self.page.click(selector)
            return True
        except Exception as e:
            self.print_error(f"点击失败: {selector}, {e}")
            return False

    def safe_fill(self, selector, text, timeout=10000):
        """安全的填充操作"""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            self.page.fill(selector, text)
            return True
        except Exception as e:
            self.print_error(f"填充失败: {selector}, {e}")
            return False
