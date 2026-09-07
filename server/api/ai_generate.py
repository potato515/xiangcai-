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
def generate_article(req: GenerateArticleReq, background_tasks: BackgroundTasks):
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


@router.put("/articles/{article_id}")
async def update_article(article_id: int, req: dict):
    """更新文章（标题、内容、话题、付费类型等）"""
    articles = load_articles()
    found = False
    for article in articles:
        if article["id"] == article_id:
            # 先确定文章类型（优先使用请求中的，其次使用文章原有的）
            current_article_type = req.get("article_type", article.get("article_type", "free"))

            if "title" in req:
                article["title"] = req["title"]

            # 如果请求中包含自定义章节，直接使用，不重新拆分
            if "chapters" in req and req["chapters"]:
                article["chapters"] = req["chapters"]
                if "content" in req:
                    article["content"] = req["content"]
            elif "content" in req:
                article["content"] = req["content"]
                from services.article_generator import split_chapters
                article["chapters"] = split_chapters(req["content"], current_article_type)
            if "topic_type" in req:
                article["topic_type"] = req["topic_type"]
            if "article_type" in req:
                article["article_type"] = req["article_type"]
                # 如果文章类型改变了，且没有提供自定义章节，也需要重新拆分章节
                if "content" not in req and "chapters" not in req and article.get("content"):
                    from services.article_generator import split_chapters
                    article["chapters"] = split_chapters(article["content"], req["article_type"])
            # 保存选中的图片
            if "selected_images" in req:
                article["selected_images"] = req["selected_images"]

            # 保存图片候选（如果有的话）
            if "images" in req:
                article["images"] = req["images"]

            article["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="文章不存在")
    save_articles(articles)
    return {"status": "ok", "message": "文章更新成功"}


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
def generate_images(req: GenerateImagesReq, background_tasks: BackgroundTasks):
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


class RegenerateAllImagesReq(BaseModel):
    article_id: int
    count: Optional[int] = 3  # 每个段落的备选图片数量


@router.post("/generate/images/regenerate-all")
def regenerate_all_images(req: RegenerateAllImagesReq, background_tasks: BackgroundTasks):
    """
    单篇文章全部图片重生成（自动使用默认豆包账号，为所有章节重新生成图片）
    不影响文章内容及其他功能，支持随时重试
    """
    from services.article_generator import load_articles, load_config

    # 1. 获取文章
    articles = load_articles()
    article = next((a for a in articles if a["id"] == req.article_id), None)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 2. 获取所有章节号
    chapters = article.get("chapters", [])
    if not chapters:
        raise HTTPException(status_code=400, detail="文章没有章节，无法生成图片")
    chapter_nums = [c.get("num", "") for c in chapters if c.get("num")]
    if not chapter_nums:
        raise HTTPException(status_code=400, detail="无法获取章节号")

    # 3. 从AI配置中获取默认豆包账号
    config = load_config()
    doubao_accounts = config.get("ai_accounts", {}).get("doubao", [])
    if not doubao_accounts:
        raise HTTPException(status_code=400, detail="请先在AI配置中添加豆包账号")

    # 优先使用批量生成配置中指定的账号，否则使用第一个豆包账号
    batch_config = config.get("settings", {}).get("batch_generate", {})
    account_id = batch_config.get("image_account_id", "")
    if not account_id:
        account_id = doubao_accounts[0].get("account_id", "")
    if not account_id:
        raise HTTPException(status_code=400, detail="豆包账号配置无效")

    # 4. 清空之前的图片数据（不影响文章内容）
    if "images" in article:
        article["images"] = {}
    if "selected_images" in article:
        article["selected_images"] = {}
    article["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i, a in enumerate(articles):
        if a["id"] == req.article_id:
            articles[i] = article
            break
    from services.article_generator import save_articles
    save_articles(articles)

    # 5. 启动异步图片生成任务
    task_id = int(datetime.now().timestamp())
    task_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", f"task_{task_id}.json")

    task = {
        "task_id": task_id,
        "type": "regenerate_all_images",
        "status": "running",
        "article_id": req.article_id,
        "chapter_nums": chapter_nums,
        "account_id": account_id,
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
                chapter_nums=chapter_nums,
                account_id=account_id,
                count=req.count
            )

            task["status"] = "success"
            task["results"] = results
            task["message"] = f"图片重生成完成，共 {len(chapter_nums)} 个章节"
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

    return {
        "task_id": task_id,
        "status": "running",
        "message": f"图片重生成任务已启动，共 {len(chapter_nums)} 个章节",
        "chapter_count": len(chapter_nums)
    }


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


# ==================== 文章生成队列（待生成列表） ====================

class AddToQueueReq(BaseModel):
    title: str
    article_type_id: Optional[int] = None
    article_type: Optional[str] = "free"
    apply_prompt: Optional[str] = ""
    platform: Optional[str] = "doubao"
    account_id: Optional[str] = ""


class BatchAddToQueueReq(BaseModel):
    items: List[dict]  # [{title, article_type_id, article_type, apply_prompt}]
    platform: Optional[str] = "doubao"
    account_id: Optional[str] = ""


class UpdateQueueItemReq(BaseModel):
    title: Optional[str] = None
    article_type_id: Optional[int] = None
    article_type: Optional[str] = None
    apply_prompt: Optional[str] = None


class BatchUpdateQueueReq(BaseModel):
    ids: List[int]
    article_type_id: Optional[int] = None
    article_type: Optional[str] = None


@router.get("/queue")
async def get_generate_queue():
    """获取文章生成队列（待生成列表）"""
    from services.batch_task_engine import batch_engine
    return {"list": batch_engine.load_generate_queue(), "total": len(batch_engine.load_generate_queue())}


@router.post("/queue/add")
async def add_to_queue(req: AddToQueueReq):
    """添加文章到生成队列"""
    from services.batch_task_engine import batch_engine
    item = batch_engine.add_to_queue(
        title=req.title,
        article_type_id=req.article_type_id,
        article_type=req.article_type,
        apply_prompt=req.apply_prompt,
        platform=req.platform,
        account_id=req.account_id
    )
    return {"status": "ok", "item": item}


@router.post("/queue/batch-add")
async def batch_add_to_queue(req: BatchAddToQueueReq):
    """批量添加文章到生成队列"""
    from services.batch_task_engine import batch_engine
    added = []
    for item_data in req.items:
        item = batch_engine.add_to_queue(
            title=item_data.get("title", ""),
            article_type_id=item_data.get("article_type_id"),
            article_type=item_data.get("article_type", "free"),
            apply_prompt=item_data.get("apply_prompt", ""),
            platform=req.platform,
            account_id=req.account_id
        )
        added.append(item)
    return {"status": "ok", "added_count": len(added), "items": added}


@router.put("/queue/{item_id}")
async def update_queue_item(item_id: int, req: UpdateQueueItemReq):
    """更新队列项"""
    from services.batch_task_engine import batch_engine
    update_data = {k: v for k, v in req.dict().items() if v is not None}
    batch_engine.update_queue_item(item_id, **update_data)
    return {"status": "ok"}


@router.post("/queue/batch-update")
async def batch_update_queue(req: BatchUpdateQueueReq):
    """批量更新队列项（文章类型等）"""
    from services.batch_task_engine import batch_engine
    update_data = {}
    if req.article_type_id is not None:
        update_data["article_type_id"] = req.article_type_id
    if req.article_type is not None:
        update_data["article_type"] = req.article_type
    for item_id in req.ids:
        batch_engine.update_queue_item(item_id, **update_data)
    return {"status": "ok", "updated_count": len(req.ids)}


@router.delete("/queue/{item_id}")
async def remove_from_queue(item_id: int):
    """从队列中移除"""
    from services.batch_task_engine import batch_engine
    batch_engine.remove_from_queue(item_id)
    return {"status": "ok"}


@router.post("/queue/batch-delete")
async def batch_delete_queue(req: dict):
    """批量从队列中移除"""
    from services.batch_task_engine import batch_engine
    ids = req.get("ids", [])
    for item_id in ids:
        batch_engine.remove_from_queue(item_id)
    return {"status": "ok", "deleted_count": len(ids)}


@router.post("/queue/clear")
async def clear_queue():
    """清空队列"""
    from services.batch_task_engine import batch_engine
    batch_engine.clear_queue()
    return {"status": "ok"}


@router.post("/queue/reset/{item_id}")
async def reset_queue_item(item_id: int):
    """重置单个队列项状态（从running/failed重置为pending，允许重新生成）"""
    from services.batch_task_engine import batch_engine
    success = batch_engine.reset_queue_item(item_id)
    if success:
        return {"status": "ok", "message": "任务状态已重置，可以重新生成"}
    else:
        raise HTTPException(status_code=404, detail="未找到该任务")


@router.post("/queue/reset-all-stuck")
async def reset_all_stuck_items():
    """重置所有卡住的队列项（running状态）"""
    from services.batch_task_engine import batch_engine
    reset_count = batch_engine.reset_all_stuck_items()
    return {"status": "ok", "reset_count": reset_count, "message": f"已重置 {reset_count} 个卡住的任务"}


# ==================== 批量生成任务 ====================

class CreateBatchTaskReq(BaseModel):
    item_ids: List[int]
    platform: str
    account_id: str
    generate_images: Optional[bool] = True


@router.post("/batch/create")
async def create_batch_task(req: CreateBatchTaskReq):
    """创建批量生成任务"""
    from services.batch_task_engine import batch_engine
    task = batch_engine.create_batch_task(
        item_ids=req.item_ids,
        platform=req.platform,
        account_id=req.account_id,
        generate_images=req.generate_images
    )
    if not task:
        raise HTTPException(status_code=400, detail="创建批量任务失败，队列中没有找到指定项")
    return {"status": "ok", "batch_id": task["batch_id"], "task": task}


@router.post("/batch/start/{batch_id}")
async def start_batch_task(batch_id: int):
    """启动批量生成任务"""
    from services.batch_task_engine import batch_engine
    if batch_engine.is_running:
        raise HTTPException(status_code=400, detail="已有批量任务正在运行，请等待完成或停止后再启动")
    success = batch_engine.start_batch_task(batch_id)
    if not success:
        raise HTTPException(status_code=400, detail="启动批量任务失败")
    return {"status": "ok", "message": "批量任务已启动"}


@router.post("/batch/stop")
async def stop_batch_task():
    """停止批量生成任务"""
    from services.batch_task_engine import batch_engine
    batch_engine.stop_batch_task()
    return {"status": "ok", "message": "批量任务停止信号已发送"}


@router.get("/batch/status/{batch_id}")
async def get_batch_task_status(batch_id: int):
    """获取批量任务状态"""
    from services.batch_task_engine import batch_engine
    task = batch_engine.get_batch_task(batch_id)
    if not task:
        raise HTTPException(status_code=404, detail="批量任务不存在")
    engine_status = batch_engine.get_status()
    return {
        "task": task,
        "engine": engine_status
    }


@router.get("/batch/list")
async def list_batch_tasks():
    """获取批量任务列表"""
    from services.batch_task_engine import batch_engine
    tasks = batch_engine.load_batch_tasks()
    return {"list": tasks, "total": len(tasks)}


@router.get("/batch/engine-status")
async def get_batch_engine_status():
    """获取批量任务引擎状态"""
    from services.batch_task_engine import batch_engine
    return batch_engine.get_status()
