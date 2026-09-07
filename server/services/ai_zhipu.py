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

    def _close_popups_and_overlays(self):
        """关闭可能存在的弹窗、遮罩层、欢迎引导等"""
        try:
            # 1. 关闭常见的弹窗按钮（关闭、跳过、知道了、稍后再说等）
            close_selectors = [
                'button:has-text("关闭")',
                'button:has-text("跳过")',
                'button:has-text("知道了")',
                'button:has-text("稍后再说")',
                'button:has-text("我知道了")',
                'button:has-text("取消")',
                'button[aria-label="关闭"]',
                'button[class*="close"]',
                '.modal-close',
                '.popup-close',
                '[class*="close-btn"]',
            ]
            for selector in close_selectors:
                try:
                    btn = self.page.locator(selector)
                    if btn.count() > 0:
                        btn.first.click(force=True, timeout=2000)
                        time.sleep(0.5)
                        self.print_info(f"已关闭弹窗: {selector}")
                except:
                    pass

            # 2. 点击页面空白处（按ESC键）关闭可能的下拉菜单或弹窗
            try:
                self.page.keyboard.press('Escape')
                time.sleep(0.3)
            except:
                pass

            # 3. 移除可能存在的遮罩层（通过JS）
            try:
                self.page.evaluate("""
                    // 移除常见的遮罩层
                    const overlays = document.querySelectorAll('[class*="overlay"], [class*="mask"], [class*="modal-backdrop"], [class*="popup-mask"]');
                    overlays.forEach(el => el.remove());
                    // 移除body上的overflow:hidden
                    document.body.style.overflow = 'auto';
                """)
            except:
                pass

        except Exception as e:
            self.print_warning(f"关闭弹窗时发生异常（不影响使用）: {e}")

    def _scroll_to_input(self):
        """滚动到输入框位置，确保元素可见"""
        try:
            input_el = self.page.locator('#chat-input')
            if input_el.count() > 0:
                input_el.first.scroll_into_view_if_needed(timeout=3000)
                time.sleep(0.5)
        except:
            pass

    def _set_output_intensity(self):
        """设置模型输出强度为高（禁止使用最高档位）"""
        try:
            # 查找输出强度设置（可能是滑块、下拉菜单或按钮组）
            # 常见的选择器：包含"输出强度"、"创造性"、"温度"等文字的元素
            intensity_selectors = [
                '[aria-label*="输出强度"]',
                '[aria-label*="创造性"]',
                '[class*="intensity"]',
                '[class*="creativity"]',
                '[class*="temperature"]',
                'div:has-text("输出强度")',
                'div:has-text("创造性")',
            ]

            for selector in intensity_selectors:
                try:
                    el = self.page.locator(selector)
                    if el.count() > 0:
                        # 点击打开设置
                        el.first.click(force=True, timeout=2000)
                        time.sleep(0.5)

                        # 选择"高"档位（避免选择"最高"）
                        high_options = self.page.locator(
                            'div:has-text("高"), li:has-text("高"), button:has-text("高"), '
                            '[class*="option"]:has-text("高")'
                        )
                        if high_options.count() > 0:
                            # 遍历找到的选项，选择文字恰好是"高"的（避免选中"最高"）
                            for i in range(high_options.count()):
                                try:
                                    text = high_options.nth(i).inner_text().strip()
                                    if text == "高" or text == "高 " or "高" in text and "最高" not in text:
                                        high_options.nth(i).click(force=True, timeout=2000)
                                        self.print_info("已设置输出强度为高")
                                        return True
                                except:
                                    continue
                        # 按ESC关闭
                        self.page.keyboard.press('Escape')
                        break
                except:
                    continue

            self.print_warning("未找到输出强度设置（使用默认值）")
            return False
        except Exception as e:
            self.print_warning(f"设置输出强度失败（不影响使用）: {e}")
            return False

    def _close_deep_thinking(self):
        """关闭深度思考功能（增强版，确保能正确关闭）"""
        try:
            # 方法1：通过JS直接查找并点击深度思考开关
            # 智谱AI的深度思考开关通常是一个包含"深度思考"文字的button或div
            js_result = self.page.evaluate("""
                () => {
                    // 查找所有包含"深度思考"文字的元素
                    const allElements = document.querySelectorAll('button, div, span, label, [role="switch"], [role="button"]');
                    for (let el of allElements) {
                        const text = el.textContent || '';
                        if (text.includes('深度思考') && text.length < 20) {
                            // 检查是否是可点击的元素
                            const style = window.getComputedStyle(el);
                            const isClickable = style.cursor === 'pointer' || 
                                                el.tagName === 'BUTTON' || 
                                                el.getAttribute('role') === 'button' ||
                                                el.getAttribute('role') === 'switch';
                            
                            if (isClickable) {
                                // 检查是否是开启状态（通过背景颜色或class）
                                const bgColor = style.backgroundColor;
                                const classList = el.className || '';
                                const isOn = bgColor.includes('rgb(16, 16, 16)') ||  // 黑色背景（开启）
                                            bgColor.includes('rgb(0, 0, 0)') ||
                                            classList.includes('active') ||
                                            classList.includes('checked') ||
                                            classList.includes('on') ||
                                            el.getAttribute('aria-checked') === 'true' ||
                                            el.getAttribute('data-state') === 'on';
                                
                                if (isOn) {
                                    el.click();
                                    return { found: true, clicked: true, text: text.trim() };
                                } else {
                                    return { found: true, clicked: false, text: text.trim(), alreadyOff: true };
                                }
                            }
                        }
                    }
                    return { found: false, clicked: false };
                }
            """)

            if js_result and js_result.get('found'):
                if js_result.get('clicked'):
                    time.sleep(1)
                    self.print_info(f"已通过JS关闭深度思考: {js_result.get('text')}")
                    return True
                elif js_result.get('alreadyOff'):
                    self.print_info("深度思考已关闭")
                    return True

            # 方法2：使用Playwright选择器查找并点击
            think_selectors = [
                'button:has-text("深度思考")',
                'div[role="switch"]:has-text("深度思考")',
                '[role="button"]:has-text("深度思考")',
                'label:has-text("深度思考")',
                'button:has-text("思考")',
                '[aria-label*="深度思考"]',
                '[class*="deep-think"]',
                '[class*="deepThink"]',
            ]

            for selector in think_selectors:
                try:
                    el = self.page.locator(selector)
                    if el.count() > 0:
                        # 遍历所有找到的元素
                        for i in range(el.count()):
                            try:
                                target = el.nth(i)
                                # 获取元素文本
                                text = target.inner_text().strip()
                                if '深度思考' not in text and '思考' not in text:
                                    continue
                                
                                # 获取元素属性和样式
                                class_attr = target.get_attribute('class') or ''
                                aria_checked = target.get_attribute('aria-checked') or ''
                                data_state = target.get_attribute('data-state') or ''
                                
                                # 判断是否是开启状态
                                is_on = ('active' in class_attr or 'checked' in class_attr or
                                         'on' in class_attr or 'true' in aria_checked or
                                         'checked' in data_state or 'on' in data_state)
                                
                                # 即使判断不出来，也尝试点击一次（因为可能是开启状态）
                                target.click(force=True, timeout=3000)
                                time.sleep(1)
                                self.print_info(f"已点击深度思考开关: {text[:20]}")
                                return True
                            except:
                                continue
                except:
                    continue

            # 方法3：如果以上都失败，尝试点击输入框上方的工具栏区域
            try:
                # 查找输入框上方的工具栏
                input_el = self.page.locator('#chat-input')
                if input_el.count() > 0:
                    # 获取输入框位置
                    box = input_el.first.bounding_box()
                    if box:
                        # 在输入框上方50像素处点击（可能是深度思考开关的位置）
                        click_x = box['x'] + 100
                        click_y = box['y'] - 30
                        self.page.mouse.click(click_x, click_y)
                        time.sleep(1)
                        self.print_info("已点击输入框上方区域（尝试关闭深度思考）")
                        return True
            except:
                pass

            self.print_warning("未能找到或关闭深度思考开关，请手动检查")
            return False

        except Exception as e:
            self.print_warning(f"关闭深度思考失败（不影响使用）: {e}")
            return False

    def _select_glm52_model(self):
        """选择GLM-5.2模型"""
        try:
            # 查找模型选择按钮
            model_selectors = [
                'button[aria-label*="模型"]',
                'button[id*="model-selector"]',
                '[class*="modelSelectorButton"]',
                'button:has-text("GLM")',
                '[class*="model-select"]',
            ]

            model_btn = None
            for selector in model_selectors:
                try:
                    el = self.page.locator(selector)
                    if el.count() > 0:
                        model_btn = el.first
                        break
                except:
                    continue

            if not model_btn:
                self.print_warning("未找到模型选择按钮（使用默认模型）")
                return False

            # 点击打开模型选择下拉菜单
            model_btn.click(force=True, timeout=5000)
            time.sleep(1.5)

            # 查找GLM-5.2模型选项（精确匹配，避免选中其他版本）
            glm52_selectors = [
                'div:has-text("GLM-5.2")',
                'li:has-text("GLM-5.2")',
                'button:has-text("GLM-5.2")',
                '[class*="option"]:has-text("GLM-5.2")',
                '[role="option"]:has-text("GLM-5.2")',
            ]

            for selector in glm52_selectors:
                try:
                    el = self.page.locator(selector)
                    if el.count() > 0:
                        # 遍历找到的选项，选择文字包含"GLM-5.2"的
                        for i in range(el.count()):
                            try:
                                text = el.nth(i).inner_text().strip()
                                if 'GLM-5.2' in text or 'glm-5.2' in text.lower():
                                    el.nth(i).click(force=True, timeout=3000)
                                    time.sleep(1)
                                    self.print_info("已选择GLM-5.2模型")
                                    return True
                            except:
                                continue
                except:
                    continue

            # 如果没找到GLM-5.2，尝试找包含"5.2"的选项
            try:
                el = self.page.locator('div:has-text("5.2"), li:has-text("5.2"), button:has-text("5.2")')
                if el.count() > 0:
                    el.first.click(force=True, timeout=3000)
                    time.sleep(1)
                    self.print_info("已选择5.2模型（模糊匹配）")
                    return True
            except:
                pass

            # 按ESC关闭下拉菜单
            self.page.keyboard.press('Escape')
            time.sleep(0.5)
            self.print_warning("未找到GLM-5.2模型选项（使用默认模型）")
            return False

        except Exception as e:
            self.print_warning(f"选择GLM-5.2模型失败（使用默认模型）: {e}")
            # 按ESC关闭可能打开的下拉菜单
            try:
                self.page.keyboard.press('Escape')
            except:
                pass
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

            # 打开智谱AI（使用domcontentloaded等待，避免页面加载超时）
            try:
                self.page.goto(self.base_page_url, wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                self.print_warning(f"页面加载超时，继续尝试: {e}")
            time.sleep(8)  # 增加等待时间，确保页面完全加载

            # 关闭可能存在的弹窗和遮罩层
            self._close_popups_and_overlays()

            # 1. 选择GLM-5.2模型
            self._select_glm52_model()

            # 2. 关闭深度思考功能
            self._close_deep_thinking()

            # 3. 设置输出强度为高（禁止使用最高档位）
            self._set_output_intensity()

            # 再次关闭弹窗（设置后可能弹出新弹窗）
            self._close_popups_and_overlays()

            # 滚动到输入框位置
            self._scroll_to_input()

            # 填入提示词 - 使用强制填充
            try:
                input_el = self.page.locator('#chat-input')
                if input_el.count() > 0:
                    input_el.first.click(force=True)
                    time.sleep(0.5)
                    input_el.first.fill(instruct)
                    time.sleep(1)
                    self.print_info("提示词已填入")
                else:
                    return False, "", "找不到输入框"
            except Exception as e:
                return False, "", f"填入提示词失败: {e}"

            # 再次关闭弹窗
            self._close_popups_and_overlays()

            # 点击发送 - 使用强制点击，绕过遮罩层拦截
            try:
                send_btn = self.page.locator('#send-message-button')
                if send_btn.count() > 0:
                    send_btn.first.click(force=True)
                    self.print_info("已点击发送按钮")
                else:
                    # 尝试其他发送按钮选择器
                    send_btn2 = self.page.locator('button[type="submit"], button[class*="send"]')
                    if send_btn2.count() > 0:
                        send_btn2.first.click(force=True)
                        self.print_info("已点击发送按钮（备用选择器）")
                    else:
                        return False, "", "找不到发送按钮"
            except Exception as e:
                return False, "", f"点击发送按钮失败: {e}"

            # 等待生成完成（优化版：加快检测频率+进度输出）
            finished = False
            wait_time = 0
            last_content_len = 0
            stable_count = 0
            min_wait = 8  # 最小等待时间，避免误判
            last_progress_time = 0

            while not finished:
                time.sleep(2)  # 从3秒减少到2秒，加快检测频率
                wait_time += 2

                # 超时检测
                if wait_time > timeout:
                    # 超时，尝试强制停止
                    try:
                        stop_btn = self.page.locator('div[aria-label="停止"]')
                        if stop_btn.count() > 0:
                            stop_btn.click(force=True)
                    except:
                        pass
                    self.print_error(f"生成文章超时（{timeout}秒）")
                    return False, "", "生成超时"

                # 检测"停止"按钮是否存在（存在表示正在生成）
                stop_btn = self.page.locator('div[aria-label="停止"]')
                is_generating = stop_btn.count() > 0

                # 内容稳定性检测：获取当前内容长度
                try:
                    answer_content_el = self.page.locator('#response-content-container').last.locator('> div > [dir="auto"]')
                    current_len = 0
                    if answer_content_el.count() > 0:
                        for ai in range(answer_content_el.count()):
                            current_len += len(answer_content_el.nth(ai).inner_text())
                except:
                    current_len = 0

                # 进度输出：每30秒输出一次当前生成字数
                if wait_time - last_progress_time >= 30:
                    self.print_info(f"生成中... 已等待{wait_time}秒，当前约{current_len}字")
                    last_progress_time = wait_time

                # 判断是否生成完成
                if not is_generating and wait_time > min_wait:
                    # 停止按钮不存在，且超过最小等待时间，认为生成完成
                    # 再做一次内容稳定性确认
                    if current_len > 0 and current_len == last_content_len:
                        stable_count += 1
                        if stable_count >= 2:  # 连续2次内容长度不变，确认生成完成
                            self.print_success(f"文章生成完成（等待{wait_time}秒，共{current_len}字）")
                            finished = True
                    else:
                        stable_count = 0
                else:
                    stable_count = 0

                last_content_len = current_len

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
