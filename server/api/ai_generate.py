"""AI生成API：文章生成、图片生成、段落管理"""
import os
import re
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from services.article_generator import article_generator, load_articles, save_articles
from services.image_generator import image_generator

router = APIRouter()


# ==================== 文章生成 ====================

class GenerateArticleReq(BaseModel):
    title: str
    platform: str  # zhipu/yuanbao/doubao
    account_id: str
    article_type_id: Optional[int] = None
    article_type: Optional[str] = "free"  # free/paid
    apply_prompt: Optional[str] = ""


@router.post("/generate/article")
async def generate_article(req: GenerateArticleReq, background_tasks: BackgroundTasks):
    """
    生成文章（异步执行，立即返回任务ID）
    由于浏览器自动化需要较长时间，使用后台任务执行
    """
    # 创建任务记录
    task_id = int(datetime.now().timestamp())
    task_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", f"task_{task_id}.json")

    task = {
        "task_id": task_id,
        "type": "generate_article",
        "status": "running",
        "title": req.title,
        "platform": req.platform,
        "account_id": req.account_id,
        "article_type_id": req.article_type_id,
        "article_type": req.article_type,
        "apply_prompt": req.apply_prompt,
        "article_id": None,
        "message": "",
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    os.makedirs(os.path.dirname(task_file), exist_ok=True)
    with open(task_file, "w", encoding="utf-8") as f:
        json.dump(task, f, ensure_ascii=False, indent=2)

    # 后台执行生成任务
    def run_task():
        try:
            success, article_id, msg = article_generator.generate(
                title=req.title,
                platform=req.platform,
                account_id=req.account_id,
                article_type_id=req.article_type_id,
                article_type=req.article_type,
                apply_prompt=req.apply_prompt
            )

            task["status"] = "success" if success else "failed"
            task["article_id"] = article_id
            task["message"] = msg
            task["finish_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(task, f, ensure_ascii=False, indent=2)

        except Exception as e:
            task["status"] = "failed"
            task["message"] = str(e)
            task["finish_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(task, f, ensure_ascii=False, indent=2)

    background_tasks.add_task(run_task)

    return {"task_id": task_id, "status": "running", "message": "文章生成任务已启动"}


@router.get("/generate/status/{task_id}")
async def get_generate_status(task_id: int):
    """获取生成任务状态"""
    task_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", f"task_{task_id}.json")
    if not os.path.exists(task_file):
        raise HTTPException(status_code=404, detail="任务不存在")
    with open(task_file, "r", encoding="utf-8") as f:
        return json.load(f)


# ==================== 文章管理 ====================

@router.get("/articles")
async def list_articles(page: int = 1, pageSize: int = 15, keyword: str = ""):
    """获取文章列表"""
    articles = load_articles()
    if keyword:
        articles = [a for a in articles if keyword in a.get("title", "")]
    total = len(articles)
    start = (page - 1) * pageSize
    data = articles[start:start + pageSize]
    return {"list": data, "total": total, "page": page, "pageSize": pageSize}


@router.get("/articles/{article_id}")
async def get_article(article_id: int):
    """获取文章详情"""
    article = article_generator.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


@router.delete("/articles/{article_id}")
async def delete_article(article_id: int):
    """删除文章"""
    articles = load_articles()
    articles = [a for a in articles if a["id"] != article_id]
    save_articles(articles)
    return {"status": "ok"}


# ==================== 图片生成 ====================

class GenerateImagesReq(BaseModel):
    article_id: int
    chapter_nums: List[str]  # 如 ["01", "03", "05"]
    account_id: str
    count: Optional[int] = 3  # 每个段落的备选图片数量


@router.post("/generate/images")
async def generate_images(req: GenerateImagesReq, background_tasks: BackgroundTasks):
    """
    批量为选中段落生成备选图片（异步执行）
    """
    task_id = int(datetime.now().timestamp())
    task_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", f"task_{task_id}.json")

    task = {
        "task_id": task_id,
        "type": "generate_images",
        "status": "running",
        "article_id": req.article_id,
        "chapter_nums": req.chapter_nums,
        "account_id": req.account_id,
        "count": req.count,
        "results": {},
        "message": "",
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    os.makedirs(os.path.dirname(task_file), exist_ok=True)
    with open(task_file, "w", encoding="utf-8") as f:
        json.dump(task, f, ensure_ascii=False, indent=2)

    def run_task():
        try:
            results = image_generator.generate_for_chapters(
                article_id=req.article_id,
                chapter_nums=req.chapter_nums,
                account_id=req.account_id,
                count=req.count
            )

            task["status"] = "success"
            task["results"] = results
            task["message"] = "图片生成完成"
            task["finish_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(task, f, ensure_ascii=False, indent=2)

        except Exception as e:
            task["status"] = "failed"
            task["message"] = str(e)
            task["finish_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(task, f, ensure_ascii=False, indent=2)

    background_tasks.add_task(run_task)

    return {"task_id": task_id, "status": "running", "message": "图片生成任务已启动"}


class SelectImageReq(BaseModel):
    article_id: int
    chapter_num: str
    image_path: str


@router.post("/images/select")
async def select_image(req: SelectImageReq):
    """选择某段落的最终图片"""
    success = image_generator.select_image(
        article_id=req.article_id,
        chapter_num=req.chapter_num,
        image_path=req.image_path
    )
    if not success:
        raise HTTPException(status_code=404, detail="文章不存在")
    return {"status": "ok"}


@router.get("/images/{article_id}")
async def get_article_images(article_id: int):
    """获取文章的所有图片信息"""
    images = image_generator.get_article_images(article_id)
    if not images:
        raise HTTPException(status_code=404, detail="文章不存在")
    return images


# ==================== 排版与导出 ====================

@router.get("/format/{article_id}")
async def format_article(article_id: int):
    """获取排版后的文章HTML（预览用）"""
    from services.article_formatter import article_formatter

    article = article_generator.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    html_content = article_formatter.format_article(article)
    return {
        "article_id": article_id,
        "title": article.get("title", ""),
        "html": html_content
    }


@router.post("/export/{article_id}")
async def export_article(article_id: int):
    """导出文章为Word文件"""
    from services.article_formatter import article_formatter

    article = article_generator.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 生成输出文件路径
    exports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "exports")
    os.makedirs(exports_dir, exist_ok=True)

    safe_title = re.sub(r'[\\/:*?"<>|]', '_', article.get("title", "article"))[:50]
    filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    output_path = os.path.join(exports_dir, filename)

    try:
        article_formatter.export_to_word(article, output_path)
        return {
            "status": "ok",
            "filename": filename,
            "download_url": f"/exports/{filename}",
            "file_path": output_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/format-settings")
async def get_format_settings():
    """获取排版设置"""
    from services.article_formatter import load_format_settings
    return load_format_settings()


@router.post("/format-settings")
async def save_format_settings_endpoint(settings: dict):
    """保存排版设置"""
    from services.article_formatter import save_format_settings
    save_format_settings(settings)
    return {"status": "ok"}
