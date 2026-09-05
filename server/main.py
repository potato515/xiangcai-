"""
香菜工作台 - FastAPI 后端入口
整合多平台内容自动化发布系统的 API 服务
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 确保 server 目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import setup_logger, get_logger
from api import article, account, topic, spider, command, settings, logs, auth, ai_config, ai_generate

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化，关闭时清理"""
    logger.info("=" * 60)
    logger.info("香菜工作台后端服务启动中...")
    logger.info("=" * 60)
    yield
    logger.info("香菜工作台后端服务已关闭")

app = FastAPI(
    title="香菜工作台 API",
    description="多平台内容自动化发布系统后端接口",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件目录
os.makedirs("data/exports", exist_ok=True)
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/images", exist_ok=True)
app.mount("/exports", StaticFiles(directory="data/exports"), name="exports")
app.mount("/images", StaticFiles(directory="data/images"), name="images")

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(article.router, prefix="/api/article", tags=["文章管理"])
app.include_router(account.router, prefix="/api/account", tags=["账号管理"])
app.include_router(topic.router, prefix="/api/topic", tags=["话题管理"])
app.include_router(spider.router, prefix="/api/spider", tags=["标题采集"])
app.include_router(command.router, prefix="/api/command", tags=["指令队列"])
app.include_router(settings.router, prefix="/api/settings", tags=["系统设置"])
app.include_router(logs.router, prefix="/api/logs", tags=["日志监控"])
app.include_router(ai_config.router, prefix="/api/ai-config", tags=["AI配置"])
app.include_router(ai_generate.router, prefix="/api/ai-generate", tags=["AI生成"])

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "香菜工作台", "version": "1.0.0"}

@app.get("/api/global/status")
async def global_status():
    """全局状态"""
    from services.spider_service import spider_service
    from services.command_service import command_service
    return {
        "spider_running": spider_service.running,
        "spider_today_count": spider_service.today_count,
        "command_pending": command_service.pending_count,
        "command_running": command_service.running_count,
        "browser_count": 0
    }

if __name__ == "__main__":
    import uvicorn
    setup_logger()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8090,
        reload=True,
        log_level="info"
    )
