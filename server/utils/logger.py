"""日志工具：统一日志配置，支持文件+控制台输出，供前端日志面板查询"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from collections import deque

# 内存日志缓冲区（供前端实时查询）
log_buffer = deque(maxlen=500)

class BufferHandler(logging.Handler):
    """将日志写入内存缓冲区"""
    def emit(self, record):
        try:
            msg = self.format(record)
            log_buffer.append({
                "time": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
                "level": record.levelname,
                "logger": record.name,
                "message": msg.split(" - ", 1)[-1] if " - " in msg else msg
            })
        except Exception:
            pass

def setup_logger(level=logging.INFO):
    """配置全局日志"""
    os.makedirs("data/logs", exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    # 文件（按大小轮转，最多5个文件，每个10MB）
    file_handler = RotatingFileHandler(
        "data/logs/xiangcai.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # 内存缓冲区
    buffer_handler = BufferHandler()
    buffer_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(console)
    root.addHandler(file_handler)
    root.addHandler(buffer_handler)

def get_logger(name):
    return logging.getLogger(name)

def get_recent_logs(level=None, limit=100):
    """获取最近的日志（供前端查询）"""
    logs = list(log_buffer)
    if level:
        logs = [l for l in logs if l["level"] == level.upper()]
    return logs[-limit:]
