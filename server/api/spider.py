"""标题采集API：爬虫控制、标题列表、标记使用、导出Excel"""
import os
import json
import csv
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()

# 使用绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "titles.json")

def load_titles():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_titles(titles):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(titles, f, ensure_ascii=False, indent=2)

class BatchMark(BaseModel):
    ids: List[int]
    used: bool = True

class BatchDelete(BaseModel):
    ids: List[int]

@router.get("/list")
async def title_list(
    page: int = 1,
    pageSize: int = 20,
    min_read: Optional[int] = None,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    used: Optional[int] = None
):
    titles = load_titles()
    filtered = titles
    if min_read is not None:
        filtered = [t for t in filtered if t.get("read_count", 0) >= min_read]
    if category:
        filtered = [t for t in filtered if t.get("category") == category]
    if keyword:
        filtered = [t for t in filtered if keyword in t.get("title", "")]
    if used is not None:
        filtered = [t for t in filtered if t.get("used", 0) == used]
    total = len(filtered)
    start = (page - 1) * pageSize
    data = filtered[start:start + pageSize]
    return {"list": data, "total": total, "page": page, "pageSize": pageSize}

@router.post("/start")
async def spider_start():
    from services.spider_service import spider_service
    spider_service.start()
    return {"status": "ok", "running": True}

@router.post("/stop")
async def spider_stop():
    from services.spider_service import spider_service
    spider_service.stop()
    return {"status": "ok", "running": False}

@router.get("/status")
async def spider_status():
    from services.spider_service import spider_service
    # 使用服务的get_status方法，包含last_result
    status = spider_service.get_status()
    # 补充标题统计
    titles = load_titles()
    status["total_count"] = len(titles)
    status["used_count"] = len([t for t in titles if t.get("used")])
    return status

@router.post("/mark/{title_id}")
async def title_mark_used(title_id: int):
    titles = load_titles()
    for t in titles:
        if t["id"] == title_id:
            t["used"] = 0 if t.get("used") else 1
            save_titles(titles)
            return {"status": "ok", "used": t["used"]}
    raise HTTPException(status_code=404, detail="标题不存在")

@router.post("/batch-mark")
async def title_batch_mark(req: BatchMark):
    titles = load_titles()
    count = 0
    for t in titles:
        if t["id"] in req.ids:
            t["used"] = 1 if req.used else 0
            count += 1
    save_titles(titles)
    return {"status": "ok", "count": count}

@router.get("/export")
async def title_export(format: str = "csv"):
    """导出标题为CSV/Excel"""
    titles = load_titles()
    os.makedirs("data/exports", exist_ok=True)
    filepath = f"data/exports/titles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "标题", "阅读量", "正在看人数", "是否已用", "采集时间"])
        for t in titles:
            writer.writerow([
                t["id"], t.get("title", ""), t.get("read_count", 0),
                t.get("watching_count", 0),
                "是" if t.get("used") else "否",
                t.get("create_time", "")
            ])
    return FileResponse(filepath, filename=os.path.basename(filepath))

@router.delete("/{title_id}")
async def title_delete(title_id: int):
    titles = load_titles()
    titles = [t for t in titles if t["id"] != title_id]
    save_titles(titles)
    return {"status": "ok"}

@router.post("/batch-delete")
async def title_batch_delete(req: BatchDelete):
    titles = load_titles()
    before = len(titles)
    titles = [t for t in titles if t["id"] not in req.ids]
    save_titles(titles)
    return {"status": "ok", "deleted": before - len(titles)}


# ==================== 标题重写（豆包AI） ====================

class RewriteTitlesReq(BaseModel):
    title_ids: List[int]  # 要重写的标题ID列表
    rewrite_instruction: Optional[str] = ""  # 自定义重写指令
    doubao_account_id: Optional[str] = ""  # 豆包账号ID


@router.post("/rewrite")
def rewrite_titles(req: RewriteTitlesReq):
    """
    调用豆包AI批量重写标题
    使用浏览器自动化控制豆包网页版，根据指令生成新标题
    """
    from services.ai_doubao import DoubaoAIService

    # 获取原始标题
    titles = load_titles()
    original_titles = [t["title"] for t in titles if t["id"] in req.title_ids]

    if not original_titles:
        raise HTTPException(status_code=400, detail="未找到指定的标题")

    # 获取豆包账号ID
    account_id = req.doubao_account_id
    if not account_id:
        # 如果没有指定账号，尝试使用第一个豆包账号
        try:
            config_file = os.path.join(BASE_DIR, "data", "ai_config.json")
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                doubao_accounts = config.get("ai_accounts", {}).get("doubao", [])
                if doubao_accounts:
                    account_id = doubao_accounts[0].get("account_id", "")
        except:
            pass

    if not account_id:
        raise HTTPException(status_code=400, detail="请先在AI配置中添加豆包账号")

    # 启动豆包AI服务并重写标题
    try:
        doubao = DoubaoAIService(account_id, headless=False)

        if not doubao.initialize_browser():
            raise HTTPException(status_code=500, detail="浏览器初始化失败")

        try:
            # 登录检查（会自动填充账号密码）
            if not doubao.login():
                raise HTTPException(status_code=401, detail="豆包登录失败，请在浏览器中手动登录后重试")

            # 重写标题
            success, result_data, msg = doubao.rewrite_titles(
                original_titles=original_titles,
                rewrite_instruction=req.rewrite_instruction,
                timeout=300
            )

            if not success:
                raise HTTPException(status_code=500, detail=f"标题重写失败: {msg}")

            return {
                "status": "ok",
                "original_count": len(original_titles),
                "group_count": len(result_data.get("groups", [])),
                "new_count": len(result_data.get("all_new_titles", [])),
                "groups": result_data.get("groups", []),
                "all_new_titles": result_data.get("all_new_titles", [])
            }

        finally:
            doubao.close_browser()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标题重写异常: {str(e)}")
