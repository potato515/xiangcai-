"""AI生成配置API：文章类型、提示词、AI账号配置、生成设置"""
import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "data", "ai_config.json")

DEFAULT_CONFIG = {
    "article_types": [],
    "default_article_prompt": "",
    "image_prompt": "",
    "ai_accounts": {
        "zhipu": [],
        "yuanbao": [],
        "doubao": []
    },
    "settings": {
        "default_chapter_count": 10,
        "default_image_count": 3,
        "default_ai_platform": "zhipu",
        "default_article_type": "free"
    }
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # 合并默认配置（确保新增字段存在）
                for key in DEFAULT_CONFIG:
                    if key not in config:
                        config[key] = DEFAULT_CONFIG[key]
                return config
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ==================== 文章类型管理 ====================

class ArticleType(BaseModel):
    id: Optional[int] = None
    name: str
    prompt: str = ""


@router.get("/article-types")
async def get_article_types():
    config = load_config()
    return {"list": config["article_types"], "total": len(config["article_types"])}


@router.post("/article-types")
async def create_article_type(req: ArticleType):
    config = load_config()
    new_id = max([t["id"] for t in config["article_types"]], default=0) + 1
    article_type = {
        "id": new_id,
        "name": req.name,
        "prompt": req.prompt,
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    config["article_types"].append(article_type)
    save_config(config)
    return article_type


@router.put("/article-types/{type_id}")
async def update_article_type(type_id: int, req: ArticleType):
    config = load_config()
    for t in config["article_types"]:
        if t["id"] == type_id:
            t["name"] = req.name
            t["prompt"] = req.prompt
            t["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_config(config)
            return t
    raise HTTPException(status_code=404, detail="文章类型不存在")


@router.delete("/article-types/{type_id}")
async def delete_article_type(type_id: int):
    config = load_config()
    config["article_types"] = [t for t in config["article_types"] if t["id"] != type_id]
    save_config(config)
    return {"status": "ok"}


# ==================== 提示词管理 ====================

class PromptUpdate(BaseModel):
    default_article_prompt: Optional[str] = None
    image_prompt: Optional[str] = None


@router.get("/prompts")
async def get_prompts():
    config = load_config()
    return {
        "default_article_prompt": config["default_article_prompt"],
        "image_prompt": config["image_prompt"]
    }


@router.post("/prompts")
async def update_prompts(req: PromptUpdate):
    config = load_config()
    if req.default_article_prompt is not None:
        config["default_article_prompt"] = req.default_article_prompt
    if req.image_prompt is not None:
        config["image_prompt"] = req.image_prompt
    save_config(config)
    return {"status": "ok"}


# ==================== AI账号配置 ====================

class AIAccount(BaseModel):
    id: Optional[int] = None
    name: str
    account_id: str
    model: Optional[str] = ""
    remark: Optional[str] = ""
    password: Optional[str] = None  # 可选，只有修改密码时才传入


@router.get("/accounts/{platform}")
async def get_ai_accounts(platform: str):
    if platform not in ["zhipu", "yuanbao", "doubao"]:
        raise HTTPException(status_code=400, detail="不支持的平台")
    config = load_config()
    # 返回账号列表时不包含密码明文
    accounts = []
    for a in config["ai_accounts"][platform]:
        acc = {k: v for k, v in a.items() if k != "password"}
        acc["has_password"] = bool(a.get("password"))
        accounts.append(acc)
    return {"list": accounts, "total": len(accounts)}


@router.post("/accounts/{platform}")
async def create_ai_account(platform: str, req: AIAccount):
    if platform not in ["zhipu", "yuanbao", "doubao"]:
        raise HTTPException(status_code=400, detail="不支持的平台")
    config = load_config()
    new_id = max([a["id"] for a in config["ai_accounts"][platform]], default=0) + 1
    account = {
        "id": new_id,
        "name": req.name,
        "account_id": req.account_id,
        "model": req.model or "",
        "remark": req.remark or "",
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # 保存密码（如果有）
    if req.password:
        account["password"] = req.password
    config["ai_accounts"][platform].append(account)
    save_config(config)
    # 返回时不包含密码
    result = {k: v for k, v in account.items() if k != "password"}
    result["has_password"] = bool(account.get("password"))
    return result


@router.put("/accounts/{platform}/{account_id}")
async def update_ai_account(platform: str, account_id: int, req: AIAccount):
    if platform not in ["zhipu", "yuanbao", "doubao"]:
        raise HTTPException(status_code=400, detail="不支持的平台")
    config = load_config()
    for a in config["ai_accounts"][platform]:
        if a["id"] == account_id:
            a["name"] = req.name
            a["account_id"] = req.account_id
            a["model"] = req.model or ""
            a["remark"] = req.remark or ""
            # 只有传入密码时才更新密码
            if req.password is not None:
                a["password"] = req.password
            a["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_config(config)
            # 返回时不包含密码
            result = {k: v for k, v in a.items() if k != "password"}
            result["has_password"] = bool(a.get("password"))
            return result
    raise HTTPException(status_code=404, detail="账号不存在")


@router.delete("/accounts/{platform}/{account_id}")
async def delete_ai_account(platform: str, account_id: int):
    if platform not in ["zhipu", "yuanbao", "doubao"]:
        raise HTTPException(status_code=400, detail="不支持的平台")
    config = load_config()
    config["ai_accounts"][platform] = [a for a in config["ai_accounts"][platform] if a["id"] != account_id]
    save_config(config)
    return {"status": "ok"}


# ==================== 生成设置 ====================

class SettingsUpdate(BaseModel):
    default_image_count: Optional[int] = None
    default_ai_platform: Optional[str] = None
    default_article_type: Optional[str] = None


@router.get("/settings")
async def get_settings():
    config = load_config()
    return config["settings"]


@router.post("/settings")
async def update_settings(req: SettingsUpdate):
    config = load_config()
    if req.default_chapter_count is not None:
        config["settings"]["default_chapter_count"] = req.default_chapter_count
    if req.default_image_count is not None:
        config["settings"]["default_image_count"] = req.default_image_count
    if req.default_ai_platform is not None:
        config["settings"]["default_ai_platform"] = req.default_ai_platform
    if req.default_article_type is not None:
        config["settings"]["default_article_type"] = req.default_article_type
    save_config(config)
    return {"status": "ok"}


# ==================== 完整配置 ====================

@router.get("/all")
async def get_all_config():
    return load_config()
