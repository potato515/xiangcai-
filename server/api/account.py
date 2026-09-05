"""账号管理API：5个平台账号的CRUD、登录状态、浏览器状态"""
import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

DATA_FILE = "data/accounts.json"

PLATFORMS = ["baijiahao", "doubao", "yangdu", "zhipu", "yuanbao"]

def load_accounts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {p: [] for p in PLATFORMS}

def save_accounts(accounts):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)

class AccountCreate(BaseModel):
    platform: str
    username: str
    password: Optional[str] = ""
    cookie: Optional[str] = ""
    remark: Optional[str] = ""
    account_type: Optional[str] = ""

@router.get("/{platform}/list")
async def account_list(platform: str):
    if platform not in PLATFORMS:
        raise HTTPException(status_code=400, detail="不支持的平台")
    accounts = load_accounts()
    return {"list": accounts.get(platform, []), "total": len(accounts.get(platform, []))}

@router.post("/{platform}/create")
async def account_create(platform: str, req: AccountCreate):
    if platform not in PLATFORMS:
        raise HTTPException(status_code=400, detail="不支持的平台")
    accounts = load_accounts()
    new_id = max([a["id"] for a in accounts[platform]], default=0) + 1
    account = {
        "id": new_id,
        "username": req.username,
        "password": req.password,
        "cookie": req.cookie,
        "remark": req.remark,
        "account_type": req.account_type,
        "login_status": 0,
        "browser_state": 0,
        "enabled": 1,
        "today_count": 0,
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    accounts[platform].append(account)
    save_accounts(accounts)
    return account

@router.post("/{platform}/update/{account_id}")
async def account_update(platform: str, account_id: int, req: AccountCreate):
    accounts = load_accounts()
    for a in accounts[platform]:
        if a["id"] == account_id:
            a.update(req.dict(exclude_unset=True))
            a["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_accounts(accounts)
            return a
    raise HTTPException(status_code=404, detail="账号不存在")

@router.delete("/{platform}/{account_id}")
async def account_delete(platform: str, account_id: int):
    accounts = load_accounts()
    accounts[platform] = [a for a in accounts[platform] if a["id"] != account_id]
    save_accounts(accounts)
    return {"status": "ok"}

@router.post("/{platform}/login/{account_id}")
async def account_login(platform: str, account_id: int):
    """触发账号登录（实际应启动浏览器自动化）"""
    accounts = load_accounts()
    for a in accounts[platform]:
        if a["id"] == account_id:
            a["browser_state"] = 2
            save_accounts(accounts)
            return {"status": "ok", "message": "登录指令已发送"}
    raise HTTPException(status_code=404, detail="账号不存在")

@router.post("/{platform}/toggle/{account_id}")
async def account_toggle(platform: str, account_id: int):
    accounts = load_accounts()
    for a in accounts[platform]:
        if a["id"] == account_id:
            a["enabled"] = 0 if a["enabled"] else 1
            save_accounts(accounts)
            return {"status": "ok", "enabled": a["enabled"]}
    raise HTTPException(status_code=404, detail="账号不存在")
