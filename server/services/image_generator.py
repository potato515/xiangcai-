# -*- coding: utf-8 -*-
"""图片生成服务：为选中段落生成3张备选图片，用户选择最终图片"""
import os
import json
import time
import traceback
from datetime import datetime
from typing import List, Optional, Tuple

from services.ai_doubao import DoubaoAIService
from services.article_generator import load_articles, save_articles, load_config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(BASE_DIR, "data", "images")


class ImageGenerator:
    """图片生成器"""

    def __init__(self):
        self.config = load_config()

    def reload_config(self):
        self.config = load_config()

    def build_image_prompt(self, chapter_content, chapter_title=""):
        """
        构建图片生成提示词
        基础提示词 + 段落内容摘要
        """
        base_prompt = self.config.get("image_prompt", "")

        # 提取段落前100字作为内容摘要
        content_summary = chapter_content[:100] if chapter_content else ""

        if chapter_title:
            prompt = f"{base_prompt}\n\n场景：{chapter_title}\n\n内容描述：{content_summary}"
        else:
            prompt = f"{base_prompt}\n\n内容描述：{content_summary}"

        return prompt

    def generate_for_chapter(self, article_id, chapter_num, account_id, count=3):
        """
        为指定段落生成备选图片
        Args:
            article_id: 文章ID
            chapter_num: 段落序号（如 "01", "03"）
            account_id: 豆包账号ID
            count: 备选图片数量（默认3）
        Returns:
            (success, image_paths, message)
        """
        try:
            self.reload_config()

            # 获取文章
            articles = load_articles()
            article = None
            for a in articles:
                if a["id"] == article_id:
                    article = a
                    break

            if not article:
                return False, [], "文章不存在"

            # 获取段落内容
            chapters = article.get("chapters", [])
            chapter = None
            for c in chapters:
                if c["num"] == chapter_num:
                    chapter = c
                    break

            if not chapter:
                return False, [], f"段落 {chapter_num} 不存在"

            # 构建图片提示词
            prompt = self.build_image_prompt(
                chapter_content=chapter.get("content", ""),
                chapter_title=chapter.get("title", "")
            )

            # 使用豆包生图
            doubao = DoubaoAIService(account_id, headless=False)

            if not doubao.initialize_browser():
                return False, [], "浏览器初始化失败"

            try:
                # 登录检查
                if not doubao.login():
                    return False, [], "豆包账号未登录，请先在浏览器中登录"

                # 批量生成备选图片
                success, image_paths, msg = doubao.generate_images_batch(
                    prompt=prompt,
                    count=count,
                    timeout=300
                )

                if not success:
                    return False, [], f"图片生成失败: {msg}"

                # 保存到文章数据
                if "images" not in article:
                    article["images"] = {}

                article["images"][chapter_num] = image_paths
                article["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 更新文章
                for i, a in enumerate(articles):
                    if a["id"] == article_id:
                        articles[i] = article
                        break
                save_articles(articles)

                return True, image_paths, "图片生成成功"

            finally:
                doubao.close_browser()

        except Exception as e:
            traceback.print_exc()
            return False, [], f"生成异常: {str(e)}"

    def generate_for_chapters(self, article_id, chapter_nums: List[str], account_id, count=3):
        """
        批量为多个段落生成备选图片
        Args:
            article_id: 文章ID
            chapter_nums: 段落序号列表（如 ["01", "03", "05"]）
            account_id: 豆包账号ID
            count: 每个段落的备选图片数量（默认3）
        Returns:
            生成结果字典 {chapter_num: (success, image_paths, message)}
        """
        results = {}

        for chapter_num in chapter_nums:
            print(f"\n{'='*50}")
            print(f"开始为段落 {chapter_num} 生成图片")
            print(f"{'='*50}")

            success, image_paths, msg = self.generate_for_chapter(
                article_id=article_id,
                chapter_num=chapter_num,
                account_id=account_id,
                count=count
            )

            results[chapter_num] = {
                "success": success,
                "image_paths": image_paths,
                "message": msg
            }

            # 每个段落生成后短暂等待
            time.sleep(3)

        return results

    def select_image(self, article_id, chapter_num, image_path):
        """
        选择某段落的最终图片
        Args:
            article_id: 文章ID
            chapter_num: 段落序号
            image_path: 选中的图片路径
        Returns:
            bool
        """
        articles = load_articles()
        for a in articles:
            if a["id"] == article_id:
                if "selected_images" not in a:
                    a["selected_images"] = {}
                a["selected_images"][chapter_num] = image_path
                a["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_articles(articles)
                return True
        return False

    def get_article_images(self, article_id):
        """获取文章的所有图片信息"""
        articles = load_articles()
        for a in articles:
            if a["id"] == article_id:
                return {
                    "images": a.get("images", {}),
                    "selected_images": a.get("selected_images", {})
                }
        return None


# 全局单例
image_generator = ImageGenerator()
