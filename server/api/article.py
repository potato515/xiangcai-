"""文章管理API：列表、详情、创建、更新、删除、批量操作、导出"""
import os
import json
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()

DATA_FILE = "data/articles.json"

def load_articles():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_articles(articles):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

class ArticleCreate(BaseModel):
    title: str
    topic_type: Optional[str] = "默认"
    ai_type: Optional[str] = "yangdu_new"
    article_type: Optional[str] = "free"
    limit_prompt: Optional[str] = ""

class BatchOperation(BaseModel):
    ids: List[int]
    action: str  # delete / regenerate / export

@router.get("/list")
async def article_list(
    page: int = 1,
    pageSize: int = 15,
    status: Optional[int] = None,
    topic: Optional[str] = None,
    keyword: Optional[str] = None
):
    articles = load_articles()
    filtered = articles
    if status is not None:
        filtered = [a for a in filtered if a.get("generate_status") == status]
    if topic:
        filtered = [a for a in filtered if a.get("topic_type") == topic]
    if keyword:
        filtered = [a for a in filtered if keyword in a.get("title", "")]
    total = len(filtered)
    start = (page - 1) * pageSize
    data = filtered[start:start + pageSize]
    return {"list": data, "total": total, "page": page, "pageSize": pageSize}

@router.get("/detail/{article_id}")
async def article_detail(article_id: int):
    articles = load_articles()
    for a in articles:
        if a["id"] == article_id:
            return a
    raise HTTPException(status_code=404, detail="文章不存在")

@router.post("/create")
async def article_create(req: ArticleCreate):
    articles = load_articles()
    new_id = max([a["id"] for a in articles], default=0) + 1
    article = {
        "id": new_id,
        "title": req.title,
        "topic_type": req.topic_type,
        "ai_type": req.ai_type,
        "article_type": req.article_type,
        "limit_prompt": req.limit_prompt,
        "generate_status": 11,
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": "",
        "images": []
    }
    articles.insert(0, article)
    save_articles(articles)
    return article

@router.post("/regenerate/{article_id}")
async def article_regenerate(article_id: int):
    articles = load_articles()
    for a in articles:
        if a["id"] == article_id:
            a["generate_status"] = 21
            a["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_articles(articles)
            return {"status": "ok", "message": "已提交重新生成"}
    raise HTTPException(status_code=404, detail="文章不存在")

@router.post("/batch")
async def article_batch(req: BatchOperation):
    articles = load_articles()
    count = 0
    if req.action == "delete":
        articles = [a for a in articles if a["id"] not in req.ids]
        count = len(req.ids)
    elif req.action == "regenerate":
        for a in articles:
            if a["id"] in req.ids:
                a["generate_status"] = 21
                count += 1
    elif req.action == "export":
        count = len(req.ids)
    save_articles(articles)
    return {"status": "ok", "count": count, "action": req.action}

@router.delete("/{article_id}")
async def article_delete(article_id: int):
    articles = load_articles()
    articles = [a for a in articles if a["id"] != article_id]
    save_articles(articles)
    return {"status": "ok"}

@router.get("/export/{article_id}")
async def article_export(article_id: int):
    """导出文章为Word"""
    from utils.export_helper import export_article_to_word
    filepath = export_article_to_word(article_id)
    return {"status": "ok", "filepath": filepath}

@router.get("/topics")
async def article_topics():
    articles = load_articles()
    topics = list(set([a.get("topic_type", "默认") for a in articles]))
    return {"topics": topics}
