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


def split_chapters(content):
    """
    将文章内容拆分为章节段落
    完全基于AI返回的内容，不强制固定章节数量
    优先识别 01、02... 或 一、二、三... 等格式的章节序号
    如果没有序号，则按自然段落拆分
    """
    if not content:
        return []

    lines = [line.strip() for line in content.split('\n') if line.strip()]

    # 尝试识别章节序号（支持多种格式：01、一、第1章、第一节等）
    chapters = []
    current_chapter = None
    chapter_pattern = re.compile(
        r'^(?:(?:0?[1-9]\d?)|(?:[一二三四五六七八九十百]+))'  # 数字或中文数字
        r'[\s\.\、\:\：\)\）]?\s*'  # 分隔符
        r'(.*)'  # 章节标题
    )
    # 更宽松的章节识别：以"第X章/节/部分"开头
    chapter_pattern2 = re.compile(r'^第[一二三四五六七八九十百\d]+[章节部分篇][\s\:\：]?\s*(.*)')

    for line in lines:
        match = chapter_pattern.match(line) or chapter_pattern2.match(line)
        if match and len(line) < 80:  # 章节标题通常较短
            if current_chapter is not None:
                chapters.append(current_chapter)
            title = match.group(1).strip()
            current_chapter = {
                'num': f'{len(chapters)+1:02d}',
                'title': title if title else f'第{len(chapters)+1}节',
                'content': line
            }
        elif current_chapter is not None:
            current_chapter['content'] += '\n' + line
        else:
            # 还没有识别到章节，把内容作为引言
            if chapters or current_chapter is None:
                current_chapter = {
                    'num': '00',
                    'title': '引言',
                    'content': line
                }

    if current_chapter is not None:
        chapters.append(current_chapter)

    # 如果识别到章节，直接返回（不限制数量）
    if len(chapters) > 1:
        return chapters

    # 没有识别到章节序号，按自然段落拆分（每个非空行作为一个段落）
    chapters = []
    for i, line in enumerate(lines):
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

                # 拆分章节（完全基于AI返回内容，不强制固定数量）
                chapters = split_chapters(content)

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
