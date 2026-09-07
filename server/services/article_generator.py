# -*- coding: utf-8 -*-
"""文章生成服务：调用AI平台生成文章，10段落拆分，存储管理"""
import os
import json
import re
import time
import traceback
from datetime import datetime
from typing import Optional, Tuple, List

from services.browser_base import BrowserBase
from services.ai_zhipu import ZhipuAIService
from services.ai_yuanbao import YuanbaoAIService
from services.ai_doubao import DoubaoAIService

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_FILE = os.path.join(BASE_DIR, "data", "articles.json")
CONFIG_FILE = os.path.join(BASE_DIR, "data", "ai_config.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}


def load_articles():
    if os.path.exists(ARTICLES_FILE):
        try:
            with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []


def save_articles(articles):
    os.makedirs(os.path.dirname(ARTICLES_FILE), exist_ok=True)
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


def split_chapters(content, article_type="free"):
    """
    将文章内容拆分为章节段落
    完全基于AI返回的内容，不强制固定章节数量
    优先识别 01、02... 或 一、二、三... 等格式的章节序号
    如果没有序号，则按自然段落拆分

    Args:
        content: 文章内容
        article_type: 文章类型（free/paid），付费文章只在05、06章节添加（付费内容）提示
    """
    if not content:
        return []

    lines = [line.strip() for line in content.split('\n') if line.strip()]
    if not lines:
        return []

    # 跳过文章标题行（第一行如果包含书名号或长度>50，认为是文章标题）
    start_idx = 0
    if lines and (('《' in lines[0] and '》' in lines[0]) or len(lines[0]) > 50):
        start_idx = 1

    # 严格的章节识别模式：只匹配明确的章节序号
    # 模式1：01、02、1、2 等数字开头，后跟分隔符（空格、点、顿号、冒号等）
    chapter_pattern_num = re.compile(
        r'^(\d{1,2})'  # 1-2位数字
        r'[\s\.\、\:\：\)\）]'  # 必须有分隔符
        r'\s*(.*)'  # 章节标题（可能为空）
    )
    # 模式2：一、二、三... 中文数字开头，后跟分隔符
    chapter_pattern_cn = re.compile(
        r'^([一二三四五六七八九十百]+)'  # 中文数字
        r'[\s\.\、\:\：\)\）]'  # 必须有分隔符
        r'\s*(.*)'  # 章节标题
    )
    # 模式3：第X章/节/部分/篇
    chapter_pattern_di = re.compile(
        r'^第[一二三四五六七八九十百\d]+[章节部分篇]'
        r'[\s\:\：]?\s*(.*)'
    )
    # 模式4：**01** 或 **引言** 等Markdown加粗格式的章节标题
    chapter_pattern_md = re.compile(
        r'^\*+\s*(\d{1,2}|引言|引子|楔子|尾声|后记)\s*\*+\s*(.*)'
    )

    def is_chapter_title(line):
        """判断是否是章节标题行"""
        if len(line) > 80:
            return None

        # 模式0：单独的数字行（如"01"、"02"、"1"、"2"等）
        if re.match(r'^\d{1,2}$', line):
            num = int(line)
            if 1 <= num <= 99:
                return (f'{num:02d}', '')

        # 模式0.5：单独的引言/引子/楔子/尾声/后记行
        if line in ['引言', '引子', '楔子', '尾声', '后记', '前言', '序']:
            if line in ['引言', '引子', '楔子', '前言', '序']:
                return ('00', line)
            else:
                return ('99', line)

        # 检查Markdown加粗格式
        match = chapter_pattern_md.match(line)
        if match:
            num_str = match.group(1)
            title = match.group(2).strip()
            if num_str in ['引言', '引子', '楔子', '前言', '序']:
                return ('00', title if title else num_str)
            elif num_str in ['尾声', '后记']:
                return ('99', title if title else num_str)
            else:
                try:
                    num = int(num_str)
                    return (f'{num:02d}', title)
                except:
                    return None
        # 检查数字序号
        match = chapter_pattern_num.match(line)
        if match:
            num = int(match.group(1))
            if 1 <= num <= 99:
                title = match.group(2).strip()
                return (f'{num:02d}', title)
        # 检查中文数字序号
        match = chapter_pattern_cn.match(line)
        if match:
            cn_num = match.group(1)
            cn_map = {'一':1, '二':2, '三':3, '四':4, '五':5, '六':6, '七':7, '八':8, '九':9, '十':10}
            if cn_num in cn_map:
                num = cn_map[cn_num]
                title = match.group(2).strip()
                return (f'{num:02d}', title)
        # 检查第X章/节格式
        match = chapter_pattern_di.match(line)
        if match:
            title = match.group(1).strip()
            return (None, title)  # 序号无法确定，用自动编号
        return None

    chapters = []
    current_chapter = None
    intro_collected = False

    for i in range(start_idx, len(lines)):
        line = lines[i]
        chapter_info = is_chapter_title(line)

        if chapter_info:
            # 保存当前章节
            if current_chapter is not None:
                chapters.append(current_chapter)

            num, title = chapter_info
            if num is None:
                num = f'{len(chapters)+1:02d}'

            # 小标题判断：只有简短的标题（<15字）才认为是真正的小标题
            # 长标题（如"01 沈玉芬，我媳妇穿那件..."）实际上是章节序号+正文第一行
            # 这种情况标题留空，把长内容当作正文内容的第一行
            display_title = ''
            first_content_line = ''
            if title:
                title = title.strip()
                if len(title) < 15:
                    # 短标题，认为是真正的小标题
                    display_title = title
                else:
                    # 长标题，认为是正文内容的第一行，不是小标题
                    first_content_line = title

            # 处理付费内容提示：付费文章只在05、06章节添加（付费内容）提示
            if article_type == 'paid' and num in ['05', '06']:
                if '付费内容' not in display_title:
                    if display_title:
                        display_title = f'{display_title}（付费内容）'
                    else:
                        display_title = '（付费内容）'

            current_chapter = {
                'num': num,
                'title': display_title,
                'content': first_content_line  # 如果有长标题，作为正文第一行
            }
            intro_collected = True
        elif current_chapter is not None:
            # 添加到当前章节内容
            if current_chapter['content']:
                current_chapter['content'] += '\n' + line
            else:
                current_chapter['content'] = line
        elif not intro_collected:
            # 还没有识别到任何章节，把内容作为引言
            current_chapter = {
                'num': '00',
                'title': '引言',
                'content': line
            }
            intro_collected = True

    # 保存最后一个章节
    if current_chapter is not None:
        chapters.append(current_chapter)

    # 如果识别到章节，直接返回
    if len(chapters) > 1:
        return chapters

    # 没有识别到章节序号，按自然段落拆分（每个非空行作为一个段落）
    chapters = []
    for i, line in enumerate(lines[start_idx:]):
        chapters.append({
            'num': f'{i+1:02d}',
            'title': line[:30] if len(line) > 30 else line,
            'content': line
        })

    return chapters


class ArticleGenerator:
    """文章生成器"""

    def __init__(self):
        self.config = load_config()

    def reload_config(self):
        self.config = load_config()

    def get_ai_service(self, platform, account_id):
        """获取对应平台的AI服务实例"""
        if platform == "zhipu":
            return ZhipuAIService(account_id, headless=False)
        elif platform == "yuanbao":
            # 查找账号配置的模型
            model = "DeepSeek"
            for acc in self.config.get("ai_accounts", {}).get("yuanbao", []):
                if str(acc.get("account_id")) == str(account_id):
                    model = acc.get("model", "DeepSeek")
                    break
            return YuanbaoAIService(account_id, headless=False, model=model)
        elif platform == "doubao":
            return DoubaoAIService(account_id, headless=False)
        else:
            raise ValueError(f"不支持的平台: {platform}")

    def get_prompt(self, article_type_id=None):
        """
        获取文章生成提示词
        如果指定了文章类型，使用该类型的提示词
        否则使用默认提示词
        """
        if article_type_id:
            for t in self.config.get("article_types", []):
                if t["id"] == article_type_id:
                    return t.get("prompt", "")
        return self.config.get("default_article_prompt", "")

    def render_prompt_template(self, prompt, title, article_type="free"):
        """
        渲染提示词模板，替换其中的变量
        支持的变量：
        - {{title}} / {{ title }} / {{ Title }} / {{ TITLE }}: 文章标题
        - {{article_type}} / {{ article_type }}: 文章类型（free/paid）
        - {{type}} / {{ type }}: 文章类型中文（免费/付费）
        - {title} / $title: 文章标题（兼容写法）
        """
        import re
        if not prompt:
            return prompt

        rendered = prompt
        type_cn = "付费" if article_type == "paid" else "免费"

        # 使用正则表达式替换，支持任意空格和大小写
        # {{title}} / {{ title }} / {{ Title }} / {{ TITLE }} 等
        rendered = re.sub(r'\{\{\s*title\s*\}\}', title, rendered, flags=re.IGNORECASE)
        rendered = re.sub(r'\{\{\s*article_type\s*\}\}', article_type, rendered, flags=re.IGNORECASE)
        rendered = re.sub(r'\{\{\s*type\s*\}\}', type_cn, rendered, flags=re.IGNORECASE)

        # 兼容写法
        rendered = rendered.replace("{title}", title)
        rendered = rendered.replace("$title", title)

        return rendered

    def generate(self, title, platform, account_id, article_type_id=None,
                 article_type="free", apply_prompt=""):
        """
        生成文章
        Args:
            title: 文章标题
            platform: AI平台 (zhipu/yuanbao/doubao)
            account_id: 账号ID
            article_type_id: 文章类型ID（用于获取提示词）
            article_type: 付费类型 (free/paid)
            apply_prompt: 附加要求
        Returns:
            (success, article_id, message)
        """
        try:
            self.reload_config()

            # 获取提示词
            prompt = self.get_prompt(article_type_id)
            if not prompt:
                return False, None, "未配置文章生成提示词，请先在AI配置中添加"

            # 渲染提示词模板，替换 {{title}} 等变量
            prompt = self.render_prompt_template(prompt, title, article_type)
            print(f"[ArticleGenerator] 提示词模板已渲染，标题: {title[:30]}...")

            # 获取AI服务
            ai_service = self.get_ai_service(platform, account_id)

            # 初始化浏览器
            if not ai_service.initialize_browser():
                return False, None, "浏览器初始化失败"

            try:
                # 登录检查
                if not ai_service.login():
                    return False, None, "账号未登录，请先在浏览器中登录"

                # 生成文章
                success, content, msg = ai_service.generate_article(
                    title=title,
                    prompt=prompt,
                    apply_prompt=apply_prompt,
                    timeout=600
                )

                if not success:
                    return False, None, f"文章生成失败: {msg}"

                # 拆分章节（完全基于AI返回内容，不强制固定数量，传入文章类型处理付费提示）
                chapters = split_chapters(content, article_type)

                # 保存文章
                articles = load_articles()
                new_id = max([a["id"] for a in articles], default=0) + 1

                article = {
                    "id": new_id,
                    "title": title,
                    "platform": platform,
                    "account_id": account_id,
                    "article_type_id": article_type_id,
                    "article_type": article_type,  # free/paid
                    "content": content,
                    "chapters": chapters,
                    "images": {},  # {chapter_num: [image_paths]}
                    "selected_images": {},  # {chapter_num: selected_image_path}
                    "generate_status": 3,  # 生成成功
                    "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                articles.insert(0, article)
                save_articles(articles)

                return True, new_id, "文章生成成功"

            finally:
                ai_service.close_browser()

        except Exception as e:
            traceback.print_exc()
            return False, None, f"生成异常: {str(e)}"

    def get_article(self, article_id):
        """获取文章详情"""
        articles = load_articles()
        for a in articles:
            if a["id"] == article_id:
                return a
        return None

    def update_article(self, article_id, **kwargs):
        """更新文章"""
        articles = load_articles()
        for a in articles:
            if a["id"] == article_id:
                a.update(kwargs)
                a["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_articles(articles)
                return True
        return False

    def select_image(self, article_id, chapter_num, image_path):
        """选择某段落的最终图片"""
        article = self.get_article(article_id)
        if not article:
            return False

        if "selected_images" not in article:
            article["selected_images"] = {}

        article["selected_images"][chapter_num] = image_path
        self.update_article(article_id, selected_images=article["selected_images"])
        return True


# 全局单例
article_generator = ArticleGenerator()
