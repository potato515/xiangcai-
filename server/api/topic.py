"""话题管理API"""
import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()
DATA_FILE = "data/topics.json"

def load_topics():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_topics(topics):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)

class TopicCreate(BaseModel):
    name: str
    description: Optional[str] = ""

@router.get("/list")
async def topic_list():
    topics = load_topics()
    return {"list": topics, "total": len(topics)}

@router.post("/create")
async def topic_create(req: TopicCreate):
    topics = load_topics()
    new_id = max([t["id"] for t in topics], default=0) + 1
    topic = {
        "id": new_id,
        "name": req.name,
        "description": req.description,
        "enabled": 1,
        "article_count": 0,
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    topics.append(topic)
    save_topics(topics)
    return topic

@router.post("/update/{topic_id}")
async def topic_update(topic_id: int, req: TopicCreate):
    topics = load_topics()
    for t in topics:
        if t["id"] == topic_id:
            t["name"] = req.name
            t["description"] = req.description
            save_topics(topics)
            return t
    raise HTTPException(status_code=404, detail="话题不存在")

@router.delete("/{topic_id}")
async def topic_delete(topic_id: int):
    topics = load_topics()
    topics = [t for t in topics if t["id"] != topic_id]
    save_topics(topics)
    return {"status": "ok"}

@router.post("/toggle/{topic_id}")
async def topic_toggle(topic_id: int):
    topics = load_topics()
    for t in topics:
        if t["id"] == topic_id:
            t["enabled"] = 0 if t["enabled"] else 1
            save_topics(topics)
            return {"status": "ok", "enabled": t["enabled"]}
    raise HTTPException(status_code=404, detail="话题不存在")
