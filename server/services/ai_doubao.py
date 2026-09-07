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

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


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

    def _crop_image(self, image_path, target_ratio=1.5):
        """
        自动裁剪图片为合适的比例（默认3:2，适合文章配图）
        Args:
            image_path: 原始图片路径
            target_ratio: 目标宽高比（默认1.5，即3:2）
        Returns:
            裁剪后的图片路径，失败返回None
        """
        if not PIL_AVAILABLE:
            self.print_warning("Pillow库未安装，跳过图片裁剪")
            return None

        try:
            img = Image.open(image_path)
            width, height = img.size
            current_ratio = width / height

            # 如果当前比例已经接近目标比例（误差在5%以内），不需要裁剪
            if abs(current_ratio - target_ratio) / target_ratio < 0.05:
                self.print_info(f"图片比例 {current_ratio:.2f} 已接近目标比例 {target_ratio}，无需裁剪")
                return image_path

            # 计算裁剪区域
            if current_ratio > target_ratio:
                # 图片太宽，裁剪左右
                new_width = int(height * target_ratio)
                left = (width - new_width) // 2
                right = left + new_width
                top = 0
                bottom = height
            else:
                # 图片太高，裁剪上下
                new_height = int(width / target_ratio)
                top = (height - new_height) // 2
                bottom = top + new_height
                left = 0
                right = width

            # 执行裁剪
            cropped_img = img.crop((left, top, right, bottom))

            # 保存裁剪后的图片（覆盖原图）
            cropped_img.save(image_path, quality=95)

            self.print_info(f"图片已从 {width}x{height} 裁剪为 {right-left}x{bottom-top}（比例 {target_ratio}）")
            return image_path

        except Exception as e:
            self.print_error(f"图片裁剪失败: {e}")
            return None

    def _ai_chat(self, prompt, action="text", timeout=300, expected_group_count=0):
        """
        通用对话方法
        Args:
            prompt: 提示词
            action: text=文本对话, image=图像生成
            timeout: 超时时间
            expected_group_count: 期望的分组数量（用于内容完整性检测，0表示不检测）
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

            # 填入提示词（使用多个备选选择器，提高兼容性）
            input_selectors = [
                '[data-testid="chat_input_input"]',
                'textarea',
                '[contenteditable="true"]',
                '[class*="input"] textarea',
                '[class*="editor"] [contenteditable="true"]',
            ]
            input_filled = False
            for selector in input_selectors:
                try:
                    elem = self.page.locator(selector).first
                    if elem.count() > 0 and elem.is_visible():
                        elem.click()
                        time.sleep(0.3)
                        elem.fill(prompt)
                        input_filled = True
                        self.print_info(f"使用选择器 [{selector}] 填充成功")
                        break
                except:
                    continue
            if not input_filled:
                return False, "找不到输入框"

            time.sleep(0.5)

            # 点击发送（使用多个备选选择器）
            send_selectors = [
                '[data-testid="chat_input_send_button"]',
                'button:has-text("发送")',
                '[class*="send"] button',
                'button[aria-label*="发送"]',
            ]
            send_clicked = False
            for selector in send_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.count() > 0 and btn.is_visible():
                        btn.click()
                        send_clicked = True
                        self.print_info(f"使用选择器 [{selector}] 点击发送成功")
                        break
                except:
                    continue
            if not send_clicked:
                return False, "找不到发送按钮"

            time.sleep(10)  # 先等待10秒，确保AI开始生成

            # 等待生成完成
            waiting = 10
            last_message_count = 0
            stable_count = 0
            # 根据标题数量动态调整最小等待时间：每个标题至少需要15秒生成时间
            # 例如：3个标题至少等待45秒，10个标题至少等待150秒
            min_wait_time = max(30, expected_group_count * 15) if expected_group_count > 0 else 30
            self.print_info(f"期望生成 {expected_group_count} 个分组，最小等待时间 {min_wait_time} 秒")

            while True:
                time.sleep(3)
                waiting += 3

                # 方式1：检测"停止生成"按钮是否消失（使用更多备选选择器）
                stop_selectors = [
                    '[data-testid="chat_input_local_break_button"]',
                    'button:has-text("停止")',
                    '[class*="stop"] button',
                    'button[aria-label*="停止"]',
                    '[class*="break"] button',
                    '[class*="loading"] button',
                    'button[class*="stop"]',
                    'div[class*="stop"] button',
                ]
                stop_found = False
                for selector in stop_selectors:
                    try:
                        btn = self.page.locator(selector).first
                        if btn.count() > 0 and btn.is_visible():
                            stop_found = True
                            stop_btn = btn
                            break
                    except:
                        continue

                # 方式2：检测消息数量是否稳定（连续5次数量不变认为生成完成）
                try:
                    messages = self.page.locator('[class*="message"], [class*="chat-item"], [data-testid*="message"], [class*="answer"], [class*="reply"]')
                    current_count = messages.count()
                    if current_count == last_message_count and current_count > 0:
                        stable_count += 1
                    else:
                        stable_count = 0
                    last_message_count = current_count
                except:
                    pass

                # 方式3：检测内容完整性（是否包含所有期望的分组）
                content_complete = False
                if expected_group_count > 0 and waiting > min_wait_time:
                    try:
                        # 快速检测页面文本中包含的分组数量
                        page_text = self.page.evaluate("document.body.innerText")
                        group_count = page_text.count('=== 标题')
                        if group_count >= expected_group_count:
                            content_complete = True
                            self.print_info(f"内容完整性检测：已生成 {group_count}/{expected_group_count} 个分组")
                    except:
                        pass

                # 判断生成完成的条件：
                # 1. 已超过最小等待时间
                # 2. 停止按钮消失 或 消息数量稳定（连续5次） 或 内容完整
                if waiting >= min_wait_time and (not stop_found or stable_count >= 5 or content_complete):
                    self.print_info(f"生成完成检测：stop_found={stop_found}, stable_count={stable_count}, content_complete={content_complete}, 等待{waiting}秒")
                    break

                # 超时保护
                if waiting > timeout:
                    self.print_error(f"生成超时（{timeout}秒），停止等待")
                    try:
                        if stop_found:
                            stop_btn.click()
                    except:
                        pass
                    break

            time.sleep(5)  # 额外等待5秒，确保内容完全渲染

            # 滚动到底部
            try:
                bottom_btn = self.page.locator("#to-bottom-button")
                if bottom_btn.count() > 0 and bottom_btn.get_attribute("data-visible") == 'true':
                    bottom_btn.click()
                time.sleep(2)
            except:
                pass

            # 【重要】展开豆包AI折叠的内容卡片
            # 豆包AI生成长内容时会折叠成卡片，需要点击展开才能获取完整内容
            try:
                # 尝试点击折叠的内容卡片（多个备选选择器）
                expand_selectors = [
                    '[class*="note-card"]',
                    '[class*="article-card"]',
                    '[class*="doc-card"]',
                    '[class*="content-card"]',
                    '[class*="fold-card"]',
                    'div[class*="card"]:has([class*="title"])',
                ]
                expanded = False
                for selector in expand_selectors:
                    try:
                        cards = self.page.locator(selector)
                        if cards.count() > 0:
                            # 点击最后一个卡片（最新生成的内容）
                            cards.last.click()
                            time.sleep(2)
                            expanded = True
                            self.print_info("已尝试展开折叠的内容卡片")
                            break
                    except:
                        continue
                if not expanded:
                    # 备选方案：尝试点击包含"展开"文字的按钮
                    try:
                        expand_btn = self.page.locator('button:has-text("展开"), div:has-text("展开")')
                        if expand_btn.count() > 0:
                            expand_btn.last.click()
                            time.sleep(2)
                            self.print_info("已点击展开按钮")
                    except:
                        pass
            except Exception as e:
                self.print_info(f"展开折叠卡片时出错（不影响后续获取）: {e}")

            # 再次滚动到底部，确保展开后的内容完全显示
            try:
                bottom_btn = self.page.locator("#to-bottom-button")
                if bottom_btn.count() > 0 and bottom_btn.get_attribute("data-visible") == 'true':
                    bottom_btn.click()
                time.sleep(2)
            except:
                pass

            # 【重要】检测是否有云文档卡片，如果有则打开云文档并从中获取内容
            # 豆包AI生成长内容时会自动创建云文档，内容在云文档中而不是聊天页面
            doc_content = None
            try:
                # 检测云文档卡片（多个备选选择器）
                doc_card_selectors = [
                    '[class*="note-card"]',
                    '[class*="article-card"]',
                    '[class*="doc-card"]',
                    '[class*="content-card"]',
                    '[class*="fold-card"]',
                    'div[class*="card"]:has([class*="title"])',
                ]
                doc_card = None
                for selector in doc_card_selectors:
                    try:
                        cards = self.page.locator(selector)
                        if cards.count() > 0:
                            # 检查卡片是否包含"文档"或"正在生成"文字
                            last_card = cards.last
                            card_text = last_card.inner_text()
                            if '文档' in card_text or '正在生成' in card_text or '云盘' in card_text:
                                doc_card = last_card
                                self.print_info(f"检测到云文档卡片: {card_text[:50]}")
                                break
                    except:
                        continue

                if doc_card:
                    # 记录当前页面数量
                    page_count_before = len(self.page.context.pages)
                    # 点击云文档卡片，打开云文档
                    doc_card.click()
                    time.sleep(3)

                    # 等待新标签页打开
                    page_count_after = len(self.page.context.pages)
                    if page_count_after > page_count_before:
                        # 切换到新打开的云文档标签页
                        doc_page = self.page.context.pages[-1]
                        self.print_info("已切换到云文档标签页")

                        # 等待云文档内容加载完成（最多等待30秒）
                        doc_waiting = 0
                        while doc_waiting < 30:
                            time.sleep(2)
                            doc_waiting += 2
                            try:
                                # 检测云文档内容是否已加载
                                doc_text = doc_page.evaluate("document.body.innerText")
                                if doc_text and ('=== 标题' in doc_text or '【原始标题】' in doc_text or '仿写标题' in doc_text or len(doc_text) > 200):
                                    self.print_info(f"云文档内容已加载，长度{len(doc_text)}")
                                    break
                            except:
                                pass

                        # 获取云文档内容
                        try:
                            doc_content = doc_page.evaluate("document.body.innerText")
                            self.print_info(f"从云文档获取内容成功，长度{len(doc_content) if doc_content else 0}")
                        except Exception as e:
                            self.print_warning(f"从云文档获取内容失败: {e}")

                        # 关闭云文档标签页，回到聊天页面
                        try:
                            doc_page.close()
                            self.print_info("已关闭云文档标签页，回到聊天页面")
                        except:
                            pass
                        time.sleep(1)
                    else:
                        self.print_info("点击云文档卡片后未打开新标签页，尝试在当前页面获取内容")
            except Exception as e:
                self.print_info(f"云文档检测和获取时出错（不影响后续获取）: {e}")

            # 获取结果
            if action == "text":
                # 如果从云文档获取到了内容，优先使用云文档内容
                if doc_content and len(doc_content) > 100:
                    content = doc_content
                    self.print_info(f"使用云文档内容，长度{len(content)}")
                else:
                    content = None

                # 文本对话，获取文字内容（使用多个备选选择器）
                content_selectors = [
                    '[data-testid="message_text_content"]',
                    '[class*="message-content"] [class*="text"]',
                    '[class*="markdown-body"]',
                    '[class*="answer"] [class*="content"]',
                    '[data-testid*="message"] [class*="content"]',
                    '[class*="chat"] [class*="message"] [class*="text"]',
                    '[class*="markdown"]',
                    '[class*="prose"]',
                ]
                content = None
                for selector in content_selectors:
                    try:
                        result_el = self.page.locator(selector).last
                        if result_el.count() > 0:
                            text = result_el.inner_text()
                            if text and len(text.strip()) > 10:
                                content = text
                                self.print_info(f"使用选择器 [{selector}] 获取内容成功，长度{len(text)}")
                                break
                    except:
                        continue

                # 方案2：查找包含分组标记"=== 标题"或"【原始标题】"的文本元素
                if not content:
                    try:
                        # 获取所有可能的消息元素
                        all_elements = self.page.locator('div[class*="message"], div[class*="chat"], div[class*="answer"], div[class*="reply"]').all()
                        for elem in all_elements:
                            try:
                                text = elem.inner_text()
                                if text and ('=== 标题' in text or '【原始标题】' in text or '【爆点分析】' in text):
                                    content = text
                                    self.print_info(f"通过分组标记查找获取内容成功，长度{len(text)}")
                                    break
                            except:
                                continue
                    except Exception as e:
                        self.print_warning(f"分组标记查找失败: {e}")

                # 方案3：获取页面上所有文本块，找到包含分组标记的最长文本
                if not content:
                    try:
                        all_texts = self.page.locator('div, p, span, article').all_inner_texts()
                        if all_texts:
                            # 筛选包含分组标记的文本
                            group_texts = [t for t in all_texts if t and ('=== 标题' in t or '【原始标题】' in t or '仿写标题' in t)]
                            if group_texts:
                                content = max(group_texts, key=len)
                                self.print_info(f"通过分组标记筛选获取内容成功，长度{len(content)}")
                            else:
                                # 兜底：找到最长的文本（通常是AI的回复）
                                long_texts = [t for t in all_texts if t and len(t) > 50]
                                if long_texts:
                                    content = max(long_texts, key=len)
                                    self.print_info(f"通过最长文本兜底获取内容成功，长度{len(content)}")
                    except Exception as e:
                        self.print_warning(f"文本块筛选失败: {e}")

                # 方案4：最终兜底 - 获取整个页面的文本内容
                if not content:
                    try:
                        page_text = self.page.evaluate("document.body.innerText")
                        if page_text and len(page_text) > 50:
                            # 尝试提取包含分组标记的部分
                            import re as _re
                            # 查找从"=== 标题"开始的内容
                            match = _re.search(r'(={2,}\s*标题\s*[\d一二三四五六七八九十]+\s*={2,}.*)', page_text, _re.DOTALL)
                            if match:
                                content = match.group(1)
                                self.print_info(f"通过页面文本提取分组内容成功，长度{len(content)}")
                            else:
                                content = page_text[-3000:]  # 取最后3000字符
                                self.print_info(f"通过页面文本兜底获取内容成功，长度{len(content)}")
                    except Exception as e:
                        self.print_warning(f"页面文本兜底失败: {e}")

                # 调试：打印获取到的内容前500字符
                if content:
                    self.print_info(f"获取到的内容前500字符: {content[:500]}")
                    return True, content
                else:
                    return False, "无法获取生成内容"

            elif action == "image":
                # 图像生成，获取图片并下载
                # 使用多个备选选择器，提高兼容性
                message_selectors = [
                    '[data-testid="message_content"]',
                    '[class*="message-content"]',
                    '[class*="message_content"]',
                    '[data-testid*="message"]',
                    '[class*="chat-item"]',
                    '[class*="answer"]',
                    '[class*="reply"]',
                    '[class*="assistant-message"]',
                ]

                images = None
                for msg_selector in message_selectors:
                    try:
                        message_content = self.page.locator(msg_selector).last
                        if message_content.count() > 0:
                            # 使用多个备选图片选择器
                            img_selectors = [
                                '[data-testid="mdbox_image"]',
                                '[data-testid*="image"]',
                                'img[class*="image"]',
                                'img[class*="mdbox"]',
                                '[class*="image-container"] img',
                                '[class*="image-wrapper"] img',
                                'div[class*="image"] img',
                                'img',
                            ]
                            for img_selector in img_selectors:
                                try:
                                    imgs = message_content.locator(img_selector)
                                    if imgs.count() > 0:
                                        # 过滤掉小图片（比如头像、图标）
                                        valid_images = []
                                        for i in range(imgs.count()):
                                            try:
                                                img = imgs.nth(i)
                                                box = img.bounding_box()
                                                if box and box['width'] > 100 and box['height'] > 100:
                                                    valid_images.append(img)
                                            except:
                                                continue
                                        if len(valid_images) > 0:
                                            images = valid_images
                                            self.print_info(f"使用消息选择器 [{msg_selector}] 和图片选择器 [{img_selector}]，找到 {len(images)} 张图片")
                                            break
                                except:
                                    continue
                            if images:
                                break
                    except:
                        continue

                if not images or len(images) == 0:
                    # 兜底：在整个页面查找大图片
                    try:
                        all_images = self.page.locator('img')
                        valid_images = []
                        for i in range(all_images.count()):
                            try:
                                img = all_images.nth(i)
                                box = img.bounding_box()
                                if box and box['width'] > 200 and box['height'] > 200:
                                    valid_images.append(img)
                            except:
                                continue
                        if len(valid_images) > 0:
                            images = valid_images[-4:]  # 取最后4张（最新生成的）
                            self.print_info(f"兜底方案：在整个页面找到 {len(images)} 张大图片")
                    except Exception as e:
                        self.print_error(f"兜底查找图片失败: {e}")

                if not images or len(images) == 0:
                    return False, "生成图片数量为0"

                urls = []
                for i, img in enumerate(images):
                    try:
                        # 点击图片打开预览
                        img.click()
                        time.sleep(2)

                        # 下载图片 - 使用多个备选下载按钮选择器
                        download_selectors = [
                            '[data-testid="edit_image_download_button"]',
                            '[data-testid*="download"]',
                            'button:has-text("下载")',
                            '[class*="download"] button',
                            'button[aria-label*="下载"]',
                            'a[download]',
                        ]

                        download_success = False
                        for dl_selector in download_selectors:
                            try:
                                dl_btn = self.page.locator(dl_selector).first
                                if dl_btn.count() > 0 and dl_btn.is_visible():
                                    with self.page.expect_download(timeout=30000) as download_info:
                                        dl_btn.click()
                                    download = download_info.value
                                    download_path = download.path()
                                    file_ext = os.path.splitext(download.suggested_filename)[1] or '.png'

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

                                    # 自动裁剪图片
                                    try:
                                        cropped_path = self._crop_image(new_filepath)
                                        if cropped_path:
                                            new_filepath = cropped_path
                                            self.print_info(f"图片已自动裁剪: {os.path.basename(cropped_path)}")
                                    except Exception as crop_e:
                                        self.print_warning(f"图片裁剪失败，使用原图: {crop_e}")

                                    urls.append(new_filepath)
                                    self.print_success(f"图片已保存: {os.path.basename(new_filepath)}")
                                    download_success = True
                                    break
                            except Exception as dl_e:
                                self.print_warning(f"使用选择器 [{dl_selector}] 下载失败: {dl_e}")
                                continue

                        if not download_success:
                            # 兜底：直接获取图片src并下载
                            try:
                                img_src = img.get_attribute('src')
                                if img_src and img_src.startswith('http'):
                                    import requests
                                    resp = requests.get(img_src, timeout=30)
                                    if resp.status_code == 200:
                                        os.makedirs(self.images_dir, exist_ok=True)
                                        new_filename = f"img_{int(time.time())}_{i}.png"
                                        new_filepath = os.path.join(self.images_dir, new_filename)
                                        with open(new_filepath, 'wb') as f:
                                            f.write(resp.content)

                                        # 自动裁剪图片
                                        try:
                                            cropped_path = self._crop_image(new_filepath)
                                            if cropped_path:
                                                new_filepath = cropped_path
                                        except:
                                            pass

                                        urls.append(new_filepath)
                                        self.print_success(f"图片已通过src下载: {new_filename}")
                                        download_success = True
                            except Exception as src_e:
                                self.print_error(f"通过src下载图片失败: {src_e}")

                        # 关闭图片预览 - 使用多个备选关闭按钮选择器
                        close_selectors = [
                            '[data-testid="edit_image_close_button"]',
                            '[data-testid*="close"]',
                            'button:has-text("关闭")',
                            '[class*="close"] button',
                            'button[aria-label*="关闭"]',
                            '.modal-close',
                        ]
                        for close_selector in close_selectors:
                            try:
                                close_btn = self.page.locator(close_selector).first
                                if close_btn.count() > 0 and close_btn.is_visible():
                                    close_btn.click()
                                    break
                            except:
                                continue
                        time.sleep(1)

                        if not download_success:
                            self.print_error(f"下载第{i}张图片失败：所有下载方式均失败")

                    except Exception as e:
                        self.print_error(f"下载第{i}张图片失败: {e}")
                        try:
                            # 尝试关闭图片预览
                            for close_selector in ['[data-testid="edit_image_close_button"]', 'button:has-text("关闭")']:
                                try:
                                    self.page.locator(close_selector).first.click()
                                    break
                                except:
                                    continue
                        except:
                            pass

                if len(urls) == 0:
                    return False, "所有图片下载均失败"

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
        调用豆包AI批量重写标题（按样本分组输出 + 爆点分析）
        Args:
            original_titles: 原始标题列表
            rewrite_instruction: 重写指令（用户自定义）
            timeout: 超时时间
        Returns:
            (success, result_data, message)
            result_data = {
                "groups": [
                    {
                        "original_title": "原始标题",
                        "analysis": "爆点分析",
                        "new_titles": ["仿写标题1", "仿写标题2", ...]
                    },
                    ...
                ],
                "all_new_titles": ["所有仿写标题汇总"]
            }
        """
        try:
            if not original_titles:
                return False, None, "原始标题列表为空"

            # 默认重写指令（按样本分组输出 + 爆点分析 + 《》标识 + 中文顿号编号）
            default_instruction = """参考提供的原始爆款标题样本，完成以下任务：

【任务一：爆点分析】
针对每一条原始标题样本，分析其爆点特征，输出爆点总结结论，说明该标题具备爆款吸引力的底层原因。

【任务二：标题仿写】
针对每一条原始标题样本，分别仿写5条风格、叙事特征、冲突悬念与原标题保持一致的新爆款标题。

【输出格式要求】
严格按以下格式输出，按样本分组：

=== 标题 1 ===
【原始标题】：xxx
【爆点分析】：xxx
【仿写标题】：
1、《xxx》
2、《xxx》
3、《xxx》
4、《xxx》
5、《xxx》

=== 标题 2 ===
【原始标题】：xxx
【爆点分析】：xxx
【仿写标题】：
1、《xxx》
2、《xxx》
3、《xxx》
4、《xxx》
5、《xxx》

（以此类推，每个原始标题一个分组）

【重要要求】
1. 仿写标题必须与原标题风格、叙事特征、冲突悬念保持一致
2. 仿写标题意思相近，但不能完全相同
3. 每个分组必须恰好5条仿写标题
4. 所有仿写标题必须用《》符号包裹（例如：《妻子深夜和三名陌生男子进公寓》），用于区分AI生成标题与原始采集标题
5. 仿写标题编号必须使用中文顿号格式（1、2、3、4、5、），不要使用英文点号（1.2.3.）
6. 【重要】请直接在聊天页面输出全部内容，不要使用云文档、帮我写、文档生成或其他任何文档功能！所有内容必须直接显示在聊天对话框中，不要创建外部文档链接。
7. 严格按照上述格式输出，不要添加其他无关内容"""

            instruction = rewrite_instruction if rewrite_instruction else default_instruction

            # 拼接提示词
            titles_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(original_titles)])
            prompt = f"以下是原始爆款标题样本：\n{titles_text}\n\n{instruction}"

            self.print_info(f"开始批量重写标题，共 {len(original_titles)} 个原始标题")

            # 打开豆包
            self.safe_goto(self.base_page_url)
            time.sleep(5)

            # 使用文本对话模式，传入期望的分组数量用于内容完整性检测
            success, result = self._ai_chat(prompt, action="text", timeout=timeout, expected_group_count=len(original_titles))

            if not success:
                return False, None, result

            # 解析分组格式的返回结果
            result_data = self._parse_rewrite_result(result, original_titles)

            self.print_success(f"标题重写完成，共生成 {len(result_data['all_new_titles'])} 个新标题")
            return True, result_data, ""

        except Exception as e:
            self.print_error(f"标题重写发生异常: {str(e)}")
            traceback.print_exc()
            return False, None, f"重写异常: {str(e)}"

    def _parse_rewrite_result(self, result_text, original_titles):
        """
        解析重写结果的分组格式
        Returns:
            {
                "groups": [...],
                "all_new_titles": [...]
            }
        """
        groups = []
        all_new_titles = []

        # 【重要】先去除提示词部分，找到AI真正回复的起始位置
        # 提示词中包含"【任务一】"、"【任务二】"、"【输出格式要求】"、"【重要要求】"等标记
        # AI的真正回复在这些标记之后
        import re as _re

        # 找到最后一个"【重要要求】"或"严格按照上述格式输出"的位置
        # AI的回复通常在这些内容之后
        prompt_end_markers = [
            '严格按照上述格式输出',
            '【重要要求】',
            '【输出格式要求】',
            '【任务二：标题仿写】',
            '【任务一：爆点分析】',
        ]
        clean_text = result_text
        for marker in prompt_end_markers:
            marker_pos = result_text.rfind(marker)
            if marker_pos > 0:
                # 找到标记后的换行位置，从那里开始是AI的回复
                after_marker = result_text[marker_pos + len(marker):]
                newline_pos = after_marker.find('\n')
                if newline_pos > 0:
                    clean_text = after_marker[newline_pos + 1:]
                    self.print_info(f"已去除提示词部分（标记：{marker}），剩余内容长度{len(clean_text)}")
                    break

        # 按分组分割（=== 标题 N ===）
        # 匹配分组标记：=== 标题 1 === 或 ===标题1=== 等变体
        group_pattern = _re.compile(r'={2,}\s*标题\s*[\d一二三四五六七八九十]+\s*={2,}')
        parts = group_pattern.split(clean_text)

        # 第一个部分是分组前的内容（可能是引言，忽略）
        # 后续每个部分是一个分组的内容
        group_contents = parts[1:] if len(parts) > 1 else [clean_text]

        for idx, content in enumerate(group_contents):
            original_title = original_titles[idx] if idx < len(original_titles) else f"标题{idx+1}"
            analysis = ""
            new_titles = []

            # 提取【原始标题】
            orig_match = _re.search(r'【原始标题】[：:]\s*(.+?)(?:\n|$)', content)
            if orig_match:
                original_title = orig_match.group(1).strip()

            # 提取【爆点分析】
            analysis_match = _re.search(r'【爆点分析】[：:]\s*(.+?)(?=\n【|\Z)', content, _re.DOTALL)
            if analysis_match:
                analysis = analysis_match.group(1).strip()
                # 清理多余的换行
                analysis = _re.sub(r'\n+', ' ', analysis).strip()

            # 提取【仿写标题】部分
            imitate_match = _re.search(r'【仿写标题】[：:]\s*(.+?)(?=\n=|\Z)', content, _re.DOTALL)
            imitate_text = imitate_match.group(1) if imitate_match else content

            # 【优先】使用正则表达式直接提取《》符号中的标题内容（容错性最高）
            # 即使AI输出格式有变化（编号不对、有多余空格等），也能正确提取
            title_matches = _re.findall(r'《(.+?)》', imitate_text)
            if title_matches:
                for title in title_matches:
                    title = title.strip()
                    if title and len(title) > 5:
                        new_titles.append(f'《{title}》')

            # 【兜底】如果没有通过《》提取到标题，按行提取带编号的行
            if not new_titles:
                for line in imitate_text.split('\n'):
                    line = line.strip()
                    # 去除编号（如 "1."、"1、"、"1)"等）
                    line = _re.sub(r'^[\d]+[\.\、\)\:]\s*', '', line)
                    # 去除引号
                    line = line.strip('"\'""''')
                    if line and len(line) > 5:
                        new_titles.append(line)

            # 【最终兜底】如果还是没有提取到，从整个内容中提取带编号的行
            if not new_titles:
                for line in content.split('\n'):
                    line = line.strip()
                    if _re.match(r'^[\d]+[\.\、\)]', line):
                        line = _re.sub(r'^[\d]+[\.\、\)\:]\s*', '', line)
                        line = line.strip('"\'""''')
                        if line and len(line) > 5 and '原始标题' not in line and '爆点分析' not in line:
                            new_titles.append(line)

            # 【重要】确保所有仿写标题都包含《》符号（兜底处理）
            # 如果AI没有添加《》符号，自动添加
            formatted_titles = []
            for title in new_titles:
                title = title.strip()
                # 检查是否已经包含《》符号
                if not title.startswith('《') or not title.endswith('》'):
                    # 去除可能已有的部分符号
                    title = title.strip('《》')
                    title = f'《{title}》'
                formatted_titles.append(title)
            new_titles = formatted_titles

            # 去重
            new_titles = list(dict.fromkeys(new_titles))

            # 【重要】过滤掉空分组（没有仿写标题的分组，通常是提示词中的示例被误解析）
            # 只有当仿写标题数量 > 0 时，才保留这个分组
            if len(new_titles) > 0:
                all_new_titles.extend(new_titles)
                groups.append({
                    "original_title": original_title,
                    "analysis": analysis,
                    "new_titles": new_titles
                })
            else:
                self.print_info(f"过滤掉空分组（第{idx+1}组，无仿写标题）")

        # 【重要】确保分组数量不超过用户选择的原始标题数量
        # 如果解析出的分组数量超过原始标题数量，只保留前面的部分
        if len(groups) > len(original_titles):
            self.print_info(f"解析出 {len(groups)} 个分组，超过原始标题数量 {len(original_titles)}，只保留前 {len(original_titles)} 个")
            groups = groups[:len(original_titles)]
            # 重新汇总所有新标题
            all_new_titles = []
            for g in groups:
                all_new_titles.extend(g["new_titles"])

        # 全局去重
        all_new_titles = list(dict.fromkeys(all_new_titles))

        return {
            "groups": groups,
            "all_new_titles": all_new_titles
        }
