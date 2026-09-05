"""爬虫服务：管理标题采集爬虫的运行状态、统计、日志
使用 uiautomator2 + MuMu 模拟器真实采集百度App信息流标题
"""
import threading
import time
import os
import json
import subprocess
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 数据文件路径
DATA_FILE = os.path.join(BASE_DIR, 'data', 'titles.json')
# 采集脚本路径
COLLECTOR_SCRIPT = os.path.join(BASE_DIR, 'services', 'baidu_collector.py')
# Python 3.10 路径（安装了 uiautomator2）
PYTHON310 = r"C:\Users\11425\AppData\Local\Programs\Python\Python310\python.exe"


class SpiderService:
    def __init__(self):
        self.running = False
        self.today_count = 0
        self.total_count = 0
        self._thread = None
        self._stop_event = threading.Event()
        self.logs = []
        self.last_result = None  # 最后一次采集结果
        self._was_running = False  # 上一次的运行状态，用于检测状态变化
        self._load_stats()

    def _load_stats(self):
        """从数据文件加载统计"""
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.total_count = len(data)
        except Exception as e:
            logger.error(f"加载统计失败: {e}")

    def _add_log(self, level, message):
        """添加日志"""
        log_entry = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
        if level == 'info':
            logger.info(message)
        elif level == 'error':
            logger.error(message)
        elif level == 'warning':
            logger.warning(message)

    def start(self):
        if self.running:
            self._add_log('warning', '爬虫已在运行中')
            return False
        # 检查 Python 3.10 是否存在
        if not os.path.exists(PYTHON310):
            self._add_log('error', f'Python 3.10 不存在: {PYTHON310}')
            return False
        # 检查采集脚本是否存在
        if not os.path.exists(COLLECTOR_SCRIPT):
            self._add_log('error', f'采集脚本不存在: {COLLECTOR_SCRIPT}')
            return False

        self.running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._add_log('info', '爬虫服务已启动，开始采集百度信息流标题')
        return True

    def stop(self):
        if not self.running:
            return
        self.running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
        self._add_log('info', '爬虫服务已停止')

    def _run(self):
        """爬虫主循环：调用真实采集脚本"""
        start_count = self.today_count
        result_status = 'success'
        result_message = ''
        try:
            self._add_log('info', f'正在调用采集脚本: {COLLECTOR_SCRIPT}')
            self._add_log('info', f'使用 Python: {PYTHON310}')
            self._add_log('info', '请确保 MuMu 模拟器已启动，百度App已登录')

            # 确保数据目录存在
            os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

            # 调用采集脚本
            cmd = [
                PYTHON310,
                COLLECTOR_SCRIPT,
                '--output', DATA_FILE,
                '--swipes', '50'
            ]

            self._add_log('info', f'执行命令: {" ".join(cmd)}')

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )

            # 实时读取输出
            for line in process.stdout:
                if self._stop_event.is_set():
                    process.terminate()
                    self._add_log('warning', '用户中止采集')
                    result_status = 'stopped'
                    result_message = '用户手动停止'
                    break
                line = line.strip()
                if line:
                    # 解析采集脚本的输出
                    if '[+]' in line and '采集完成' in line:
                        self._add_log('info', line)
                    elif '[+]' in line and '条' in line:
                        self._add_log('info', line)
                        self.today_count += 1
                    elif '[x]' in line or '失败' in line or '错误' in line:
                        self._add_log('error', line)
                    elif '[!]' in line:
                        self._add_log('warning', line)
                    elif '[-]' in line:
                        # 滑动进度，不记录到日志，只更新状态
                        pass
                    else:
                        self._add_log('info', line)

            process.wait(timeout=10)
            self._load_stats()
            new_count = self.today_count - start_count
            if result_status != 'stopped':
                result_status = 'success'
                result_message = f'采集完成，本次新增 {new_count} 条，总计 {self.total_count} 条'
            self._add_log('info', f'采集结束，今日采集 {self.today_count} 条，总计 {self.total_count} 条')

        except subprocess.TimeoutExpired:
            self._add_log('error', '采集脚本超时')
            result_status = 'error'
            result_message = '采集脚本超时'
        except Exception as e:
            self._add_log('error', f'爬虫运行异常: {e}')
            import traceback
            traceback.print_exc()
            result_status = 'error'
            result_message = f'采集异常: {str(e)}'
        finally:
            self.running = False
            # 记录最后一次采集结果
            self.last_result = {
                'status': result_status,
                'message': result_message,
                'new_count': self.today_count - start_count,
                'total_count': self.total_count,
                'finish_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    def get_status(self):
        """获取爬虫状态"""
        return {
            'running': self.running,
            'today_count': self.today_count,
            'total_count': self.total_count,
            'last_result': self.last_result,
            'logs': self.logs[-20:]  # 最近20条日志
        }

    def reset_today(self):
        self.today_count = 0
        self._add_log('info', '今日采集计数已重置')

    def get_logs(self, limit=50):
        """获取采集日志"""
        return self.logs[-limit:]


# 全局单例
spider_service = SpiderService()
