"""
仓库根目录入口文件 —— 委托给 backend.start 方法执行，以保留现有功能行为。
"""
from backend.main import start
import os


if __name__ == "__main__":
    # 为开发环境保留现有的 DEV_RELOAD 功能行为
    reload_flag = os.getenv("DEV_RELOAD", "false").lower() == "true"
    start(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8000")), reload=reload_flag)
