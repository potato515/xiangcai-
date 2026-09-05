# -*- coding: utf-8 -*-
"""文章排版服务（从原 baijiahao 项目提取并适配）
将文章内容+用户选择的图片排版为HTML，支持导出Word
"""
import os
import re
import json
import base64
from typing import Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(BASE_DIR, "data", "settings.json")

# 默认排版设置
DEFAULT_FORMAT_SETTINGS = {
    "filterContainText": ["广告", "推广", "下载", "关注", "点赞", "收藏"],
    "filterStartText": ["#", "##", "###", "---", "***"],
    "removeText": [],
    "dialogueNewParagraph": True,
    "dialogueBlod": "colonAndContent",
    "declareBefore": False,
    "declareItalic": True,
    "declareBlod": False,
    "introColor": "#888888",
    "introItalic": True,
    "introBlod": False,
    "paragraphIndent": True,
    "freeAticleTopic": "",
    "titleFontSize": 18,
    "contentFontSize": 14,
    "lineHeight": 1.8
}


def load_format_settings():
    """加载排版设置"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
                format_settings = settings.get("format", {})
                # 合并默认设置
                merged = DEFAULT_FORMAT_SETTINGS.copy()
                merged.update(format_settings)
                return merged
        except:
            pass
    return DEFAULT_FORMAT_SETTINGS.copy()


def save_format_settings(settings):
    """保存排版设置"""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    all_settings = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                all_settings = json.load(f)
        except:
            pass
    all_settings["format"] = settings
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_settings, f, ensure_ascii=False, indent=2)


def image_to_base64_url(image_path):
    """将图片转换为base64 URL"""
    if not image_path or not os.path.exists(image_path):
        return ""
    try:
        with open(image_path, "rb") as f:
            img_data = f.read()
        ext = os.path.splitext(image_path)[1].lower().replace(".", "")
        if ext == "jpg":
            ext = "jpeg"
        base64_data = base64.b64encode(img_data).decode("utf-8")
        return f"data:image/{ext};base64,{base64_data}"
    except Exception as e:
        print(f"图片转base64失败: {e}")
        return ""


class ArticleFormatter:
    """文章排版器"""

    def __init__(self):
        self.settings = load_format_settings()

    def reload_settings(self):
        """重新加载设置"""
        self.settings = load_format_settings()

    def format_article(self, article: Dict) -> str:
        """
        将文章排版为HTML

        Args:
            article: 文章数据字典，包含 title, chapters, selected_images 等

        Returns:
            排版后的HTML字符串
        """
        self.reload_settings()
        settings = self.settings

        title = article.get("title", "")
        chapters = article.get("chapters", [])
        selected_images = article.get("selected_images", {})
        article_type = article.get("article_type", "free")

        if not chapters:
            # 如果没有章节，直接使用content
            content = article.get("content", "")
            chapters = [{"num": "01", "title": "", "content": content}]

        # 第一步：基础排版处理
        processed_lines = []
        is_declare = False
        declare_lines = []

        for chapter in chapters:
            chapter_num = chapter.get("num", "")
            chapter_title = chapter.get("title", "")
            chapter_content = chapter.get("content", "")

            # 章节标题行
            if chapter_title:
                header_line = f"{chapter_num} {chapter_title}"
            else:
                header_line = chapter_num

            processed_lines.append(header_line)

            # 检查该章节是否有选中的图片
            if chapter_num in selected_images and selected_images[chapter_num]:
                processed_lines.append("__IMAGE_PLACEHOLDER__:" + selected_images[chapter_num])

            # 处理章节内容
            content_lines = chapter_content.split("\n")
            for line in content_lines:
                line = self._process_line(line, settings)

                if not line:
                    continue

                # 提取创作声明
                if line.startswith("创作声明"):
                    is_declare = True
                    if line == "创作声明":
                        line += "："
                if is_declare:
                    declare_lines.append(line)
                    continue

                # 过滤包含特定文本的段落
                if any(item in line for item in settings.get("filterContainText", [])):
                    continue

                # 过滤以特定文本开头的段落
                if any(line.startswith(item) for item in settings.get("filterStartText", [])):
                    continue

                # 拆分段落（句号、问号、感叹号后换行）
                if "创作声明" not in line:
                    line = re.sub(
                        r'([！？。])(?!(?:\n|[""''【】]|$))(?=(?:[^""''【】]*[""''【】][^""''【】]*[""''【】])*[^""''【】]*$)',
                        r'\1\n',
                        line
                    )

                # 对话换行
                if settings.get("dialogueNewParagraph"):
                    line = self._process_dialogue_newline(line)

                if line:
                    for sub_line in line.split("\n"):
                        if sub_line.strip():
                            processed_lines.append(sub_line)

        # 创作声明位置
        declare = re.sub(r'\n', '', ''.join(declare_lines))
        if declare:
            if settings.get("declareBefore"):
                processed_lines.insert(0, declare)
            else:
                processed_lines.append(declare)

        # 第二步：生成HTML
        html_lines = []
        is_intro = True  # 第一段作为引言
        image_index = 0

        html_lines.append(
            f'<div class="article-content" style="font-family: \'Microsoft YaHei\', sans-serif; '
            f'font-size: {settings.get("contentFontSize", 14)}px; '
            f'line-height: {settings.get("lineHeight", 1.8)};">'
        )

        # 文章标题
        html_lines.append(
            f'<h1 style="text-align: center; font-size: {settings.get("titleFontSize", 18)}px; '
            f'font-weight: bold; margin-bottom: 20px;">{title}</h1>'
        )

        for line in processed_lines:
            if not line.strip():
                continue

            # 图片占位符
            if line.startswith("__IMAGE_PLACEHOLDER__:"):
                image_path = line.replace("__IMAGE_PLACEHOLDER__:", "")
                base64_url = image_to_base64_url(image_path)
                if base64_url:
                    html_lines.append(
                        f'<p style="text-align: center; margin: 15px 0;">'
                        f'<img src="{base64_url}" style="max-width: 100%; border-radius: 4px;"/>'
                        f'</p>'
                    )
                continue

            processed_line = line

            # 移除特定文本
            for item in settings.get("removeText", []):
                escaped_item = re.escape(item)
                processed_line = re.sub(rf"\s*{escaped_item}\s*", "", processed_line)

            if not processed_line:
                continue

            # 创作声明样式
            if processed_line.startswith("创作声明"):
                if settings.get("declareItalic"):
                    processed_line = f"<em>{processed_line}</em>"
                if settings.get("declareBlod"):
                    processed_line = f"<strong>{processed_line}</strong>"
                html_lines.append(f'<p style="color: #999; font-size: 12px;">{processed_line}</p>')
                continue

            # 章节序号加粗
            chapter_number_regex = re.compile(r'^[01][0-9](?:\s|$)')

            if is_intro and not chapter_number_regex.match(processed_line):
                # 引言样式
                intro_style = f"color: {settings.get('introColor', '#888888')};"
                if settings.get("introItalic"):
                    processed_line = f"<em>{processed_line}</em>"
                if settings.get("introBlod"):
                    processed_line = f"<strong>{processed_line}</strong>"
                html_lines.append(f'<p style="{intro_style}">{processed_line}</p>')
                is_intro = False
            else:
                is_intro = False

                # 章节序号加粗
                processed_line = re.sub(
                    r'(\b(0[1-9]|10)\b\.?)',
                    r'<strong>\1</strong>',
                    processed_line
                )

                # 对话加粗
                if settings.get("dialogueBlod") == "colonAndContent":
                    processed_line = re.sub(
                        r'(：)"([^"]+)"',
                        r'<strong>\1</strong>"<strong>\2</strong>',
                        processed_line
                    )

                # 小标题加粗（序号后的标题）
                processed_line = re.sub(
                    r'(<strong>(\b(0[1-9]|10)\b\.?)</strong>)[\s]*(.+?)(?=[。？！\n]|$)',
                    r'\1<strong>\4</strong>',
                    processed_line
                )

                # 段落缩进
                indent = ' style="text-indent: 2em;"' if settings.get("paragraphIndent") else ''
                html_lines.append(f'<p{indent}>{processed_line}</p>')

        html_lines.append('</div>')

        # 免费文章结尾话题
        if article_type == "free" and settings.get("freeAticleTopic"):
            html_lines.append(f'<p style="color: #999; font-size: 12px; text-align: center;">{settings["freeAticleTopic"]}</p>')

        return ''.join(html_lines)

    def _process_line(self, line: str, settings: Dict) -> str:
        """基础文本处理"""
        line = re.sub(r'(\r*\n)+', '', line)
        line = re.sub(r'\s*[#\-*]+\s*', '', line)
        line = re.sub(r'？！', '？', line)
        line = re.sub(r'"([^"]*)"', r'"\1"', line)
        line = re.sub(r'，"', '"', line)
        line = re.sub(r'，"', '："', line)
        line = re.sub(r'^\s+|\s+$', '', line)
        line = re.sub(r'<[^>]+>', '', line)
        return line

    def _process_dialogue_newline(self, line: str) -> str:
        """对话换行处理"""
        def replace_callback(match):
            inner_text = match.group(1)
            new_content = re.sub(r'([！？。])(?!$)', r'\1"\n"', inner_text)
            return f'"{new_content}"'

        line = re.sub(r"「([^」]*)」", replace_callback, line)
        return line

    def export_to_word(self, article: Dict, output_path: str) -> str:
        """
        导出文章为Word

        Args:
            article: 文章数据
            output_path: 输出文件路径

        Returns:
            输出文件路径
        """
        from utils.html_to_word_tool import HTMLToWordConverter

        # 先排版为HTML
        html_content = self.format_article(article)

        # 转换为Word
        converter = HTMLToWordConverter()
        converter.convert(html_content, output_path)

        return output_path


# 全局单例
article_formatter = ArticleFormatter()
