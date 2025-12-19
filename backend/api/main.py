"""
FastAPI Application Entry Point

FastAPI 应用主入口，提供 RESTful API 和 WebSocket 支持。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .routes import research, tasks, websocket, config

# 创建 FastAPI 应用
app = FastAPI(
    title="ResearchSync-Agent API",
    description="基于 LangGraph 的多智能体研究系统 API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

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

