"""日志监控API：查询运行日志、实时日志流"""
from fastapi import APIRouter, Query
from typing import Optional
from utils.logger import get_recent_logs

router = APIRouter()

@router.get("/list")
async def log_list(
    level: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500)
):
    """获取最近的日志"""
    logs = get_recent_logs(level=level, limit=limit)
    return {"list": logs, "total": len(logs)}

@router.get("/levels")
async def log_levels():
    """获取日志级别统计"""
    logs = get_recent_logs(limit=500)
    stats = {"INFO": 0, "WARNING": 0, "ERROR": 0, "DEBUG": 0, "CRITICAL": 0}
    for log in logs:
        lvl = log.get("level", "INFO")
        stats[lvl] = stats.get(lvl, 0) + 1
    return stats

@router.get("/search")
async def log_search(
    keyword: str,
    level: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500)
):
    """搜索日志"""
    logs = get_recent_logs(level=level, limit=limit)
    filtered = [l for l in logs if keyword.lower() in l.get("message", "").lower()]
    return {"list": filtered, "total": len(filtered)}
