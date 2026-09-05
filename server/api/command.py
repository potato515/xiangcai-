"""指令队列API：列表、状态、清空、WebSocket实时推送"""
import os
import json
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()
DATA_FILE = "data/commands.json"

# WebSocket 连接管理
active_connections: List[WebSocket] = []

def load_commands():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_commands(commands):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(commands, f, ensure_ascii=False, indent=2)

async def broadcast(message: dict):
    """向所有WebSocket连接广播消息"""
    for ws in active_connections:
        try:
            await ws.send_json(message)
        except Exception:
            pass

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@router.get("/list")
async def command_list(status: Optional[int] = None, platform: Optional[str] = None):
    commands = load_commands()
    filtered = commands
    if status is not None:
        filtered = [c for c in filtered if c.get("status") == status]
    if platform:
        filtered = [c for c in filtered if c.get("platform") == platform]
    return {"list": filtered, "total": len(filtered)}

@router.get("/stats")
async def command_stats():
    commands = load_commands()
    return {
        "pending": len([c for c in commands if c.get("status") == 0]),
        "running": len([c for c in commands if c.get("status") == 1]),
        "completed": len([c for c in commands if c.get("status") == 2]),
        "failed": len([c for c in commands if c.get("status") == 3])
    }

@router.post("/retry/{command_id}")
async def command_retry(command_id: int):
    commands = load_commands()
    for c in commands:
        if c["id"] == command_id:
            c["status"] = 0
            c["result"] = ""
            save_commands(commands)
            await broadcast({"type": "command_update", "id": command_id, "status": 0})
            return {"status": "ok"}
    raise HTTPException(status_code=404, detail="指令不存在")

@router.post("/clear")
async def command_clear(clear_all: bool = False):
    """清空已完成和失败的指令"""
    commands = load_commands()
    if clear_all:
        commands = []
    else:
        commands = [c for c in commands if c.get("status") in (0, 1)]
    save_commands(commands)
    return {"status": "ok", "remaining": len(commands)}

@router.delete("/{command_id}")
async def command_delete(command_id: int):
    commands = load_commands()
    commands = [c for c in commands if c["id"] != command_id]
    save_commands(commands)
    return {"status": "ok"}
