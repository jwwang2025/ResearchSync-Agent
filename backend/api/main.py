"""
FastAPI Application Entry Point

FastAPI 应用主入口，提供 RESTful API 和 WebSocket 支持。
"""
import os
import asyncio
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# 使用 redis.asyncio 作为异步客户端
import redis.asyncio as aioredis

from .routes import research, tasks, websocket, config

# 创建 FastAPI 应用 
app = FastAPI(
    title="ResearchSync-Agent API",
    description="基于 LangGraph 的多智能体研究系统 API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)


# Redis pub/sub: 在应用启动时订阅 worker 发布的任务更新并转发到 WebSocket manager
@app.on_event("startup")
async def startup_redis_pubsub():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return

    app.state._redis = aioredis.from_url(redis_url)
    pubsub = app.state._redis.pubsub()

    async def _listener():
        await pubsub.psubscribe("tasks:updates:*")
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                try:
                    # message example: {'type': 'pmessage', 'pattern': b'tasks:updates:*', 'channel': b'tasks:updates:<id>', 'data': b'...'}
                    channel = message.get("channel")
                    data = message.get("data")
                    if isinstance(channel, (bytes, bytearray)):
                        channel = channel.decode()
                    if isinstance(data, (bytes, bytearray)):
                        data = data.decode()
                    payload = json.loads(data) if data else {}
                    # extract task_id from channel name
                    parts = channel.split(":")
                    task_id = parts[-1] if parts else None
                    if task_id:
                        # 延迟导入 manager，避免循环依赖
                        from .routes.websocket import manager
                        # 转发到 WebSocket 连接
                        await manager.send_message(task_id, {"type": "redis_update", "task_id": task_id, "payload": payload})
                except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError):
                    # 忽略可预见的解析/类型错误，继续循环
                    continue
            await asyncio.sleep(0.01)
        # 清理订阅
        await pubsub.punsubscribe("tasks:updates:*")

    app.state._redis_listener_task = asyncio.create_task(_listener())


@app.on_event("shutdown")
async def shutdown_redis_pubsub():
    # 关闭订阅和连接
    task = getattr(app.state, "_redis_listener_task", None)
    if task:
        task.cancel()
        await asyncio.sleep(0)  # allow cancellation

    conn = getattr(app.state, "_redis", None)
    if conn:
        await conn.close()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(research.router, prefix="/api/v1", tags=["research"])
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
app.include_router(config.router, prefix="/api/v1", tags=["config"])


@app.get("/")
async def root():
    """根路径，返回 API 信息"""
    return {
        "name": "ResearchSync-Agent API",
        "version": "0.1.0",
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": type(exc).__name__}
    )


if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

