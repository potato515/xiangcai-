"""系统设置API：排版、导出、生成设置的存取"""
import os
import json
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()
SETTINGS_FILE = "data/settings.json"

DEFAULT_SETTINGS = {
    "formatting": {
        "introColor": "#165dff",
        "introItalic": True,
        "introBlod": False,
        "dialogueNewParagraph": True,
        "dialogueBlod": "colonAndContent",
        "declareBefore": False,
        "declareItalic": True,
        "declareBlod": False,
        "paragraphIndent": True,
        "freeAticleTopic": False,
        "filterContainText": ["关注我", "点赞", "收藏"],
        "filterStartText": ["#", "##"],
        "removeText": ["未完待续"],
        "checkedChapters": ["01", "03", "05", "07", "09"]
    },
    "export": {
        "isAutoFormatAndExport": False,
        "isExportSpecifiedDirectory": True,
        "exportSpecifiedDirectory": "D:\\Articles\\Export"
    },
    "generate": {
        "ai": "yangdu_new",
        "imageMode": "one-image",
        "articleInterval": 30,
        "imageInterval": 20,
        "maxArticlePerDay": 10,
        "maxImagePerDay": 10,
        "browserIdleTimeout": 15,
        "spiderMinCount": 50,
        "spiderMaxCount": 100,
        "newLimit": 1000,
        "oldLimit": 5000
    }
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_SETTINGS

def save_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

@router.get("/all")
async def get_all_settings():
    return load_settings()

@router.get("/{category}")
async def get_settings(category: str):
    settings = load_settings()
    return settings.get(category, {})

@router.post("/{category}")
async def save_settings_category(category: str, data: Dict[str, Any]):
    settings = load_settings()
    settings[category] = data
    save_settings(settings)
    return {"status": "ok", "category": category}

@router.post("/formatting/save")
async def save_formatting(data: Dict[str, Any]):
    settings = load_settings()
    settings["formatting"] = data
    save_settings(settings)
    return {"status": "ok"}

@router.post("/export/save")
async def save_export(data: Dict[str, Any]):
    settings = load_settings()
    settings["export"] = data
    save_settings(settings)
    return {"status": "ok"}

@router.post("/generate/save")
async def save_generate(data: Dict[str, Any]):
    settings = load_settings()
    settings["generate"] = data
    save_settings(settings)
    return {"status": "ok"}
