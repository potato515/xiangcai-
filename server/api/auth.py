"""认证API：登录、登出、当前用户、角色管理"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# 模拟用户数据（实际应接数据库）
USERS = {
    "admin": {"password": "admin123", "role": "admin", "name": "管理员"},
    "editor": {"password": "editor123", "role": "editor", "name": "编辑员"}
}

SESSIONS = {}

class LoginRequest(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    username: str
    name: str
    role: str
    permissions: list

@router.post("/login")
async def login(req: LoginRequest):
    user = USERS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = f"token_{req.username}_{len(SESSIONS)+1}"
    SESSIONS[token] = {"username": req.username, "role": user["role"]}
    return {
        "token": token,
        "user": {
            "username": req.username,
            "name": user["name"],
            "role": user["role"],
            "permissions": get_permissions(user["role"])
        }
    }

@router.post("/logout")
async def logout(token: str = ""):
    SESSIONS.pop(token, None)
    return {"status": "ok"}

@router.get("/me")
async def get_current_user(token: str = ""):
    session = SESSIONS.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="未登录")
    user = USERS[session["username"]]
    return {
        "username": session["username"],
        "name": user["name"],
        "role": user["role"],
        "permissions": get_permissions(user["role"])
    }

def get_permissions(role: str) -> list:
    if role == "admin":
        return ["article:view", "article:edit", "article:delete", "account:view", "account:edit",
                "spider:view", "spider:control", "command:view", "command:control", "settings:edit", "logs:view"]
    return ["article:view", "spider:view", "command:view", "logs:view"]
