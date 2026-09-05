"""指令服务：管理多平台AI生成指令队列、执行、状态"""
import threading
import time
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

class CommandService:
    def __init__(self):
        self.running = False
        self.pending_count = 0
        self.running_count = 0
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        if self.running:
            return
        self.running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("指令队列服务已启动")

    def stop(self):
        self.running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("指令队列服务已停止")

    def _run(self):
        """指令执行主循环"""
        while not self._stop_event.is_set():
            try:
                # 检查待执行指令
                # 实际应从数据库加载并执行
                time.sleep(2)
            except Exception as e:
                logger.error(f"指令服务异常: {e}")
                time.sleep(5)

    def add_command(self, command_type: str, platform: str, article_id: int = None):
        """添加新指令到队列"""
        logger.info(f"新指令: type={command_type}, platform={platform}, article_id={article_id}")
        self.pending_count += 1
        return True

    def get_stats(self):
        return {
            "running": self.running,
            "pending": self.pending_count,
            "running_count": self.running_count
        }

# 全局单例
command_service = CommandService()
