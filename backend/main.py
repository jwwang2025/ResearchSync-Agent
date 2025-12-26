"""
后端启动脚本 —— 后端 FastAPI 应用的程序化入口文件。
"""
from typing import Optional
import os

# 导入 FastAPI 应用实例
from backend.api.main import app

import uvicorn


def start(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """
    以程序化方式启动 FastAPI 应用。

    参数:
        host: 绑定的主机地址（默认值 0.0.0.0）
        port: 绑定的端口号（默认值 8000）
        reload: 是否启用自动重载（仅用于开发环境）
    """
    uvicorn.run(app, host=host, port=port, reload=reload)


if __name__ == "__main__":
    # 读取 DEV_RELOAD 环境变量，提升开发便利性
    reload_flag = os.getenv("DEV_RELOAD", "false").lower() == "true"
    start(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8000")), reload=reload_flag)


