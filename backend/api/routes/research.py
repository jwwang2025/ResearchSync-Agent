"""
Research API Routes

研究任务相关的 RESTful API 路由。
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import uuid
from datetime import datetime

from ..models.research import (
    ResearchRequest,
    ResearchResponse,
    ResearchStatus,
    TaskInfo
)
from ...utils.config import load_config_from_env
from ...llm.factory import LLMFactory
from ...agents.coordinator import Coordinator
from ...agents.planner import Planner
from ...agents.researcher import Researcher
from ...agents.rapporteur import Rapporteur
from ...workflow.graph import ResearchWorkflow

router = APIRouter()

# 临时任务存储（生产环境应使用数据库或 Redis）
tasks_store: Dict[str, Dict[str, Any]] = {}


def create_workflow(llm_provider: str = None, llm_model: str = None):
    """
    创建工作流实例。

    Args:
        llm_provider: LLM 提供商
        llm_model: LLM 模型名称

    Returns:
        (ResearchWorkflow, Config) 元组
    """
    # 加载配置
    cfg = load_config_from_env()

    # 覆盖配置
    if llm_provider:
        import os
        os.environ['LLM_PROVIDER'] = llm_provider
        cfg = load_config_from_env()

    if llm_model:
        cfg.llm.model = llm_model

    # 创建 LLM
    llm = LLMFactory.create_llm(
        provider=cfg.llm.provider,
        api_key=cfg.llm.api_key,
        model=cfg.llm.model,
        base_url=cfg.llm.base_url
    )

    # 创建智能体
    coordinator = Coordinator(llm)
    planner = Planner(llm)
    researcher = Researcher(
        llm=llm,
        tavily_api_key=cfg.search.tavily_api_key,
        mcp_server_url=cfg.search.mcp_server_url,
        mcp_api_key=cfg.search.mcp_api_key
    )
    rapporteur = Rapporteur(llm)

    # 创建工作流
    workflow = ResearchWorkflow(coordinator, planner, researcher, rapporteur)

    return workflow, cfg


@router.post("/research/start", response_model=ResearchResponse)
async def start_research(request: ResearchRequest):
    """
    启动新的研究任务。

    返回任务 ID，客户端应使用此 ID 建立 WebSocket 连接以接收实时更新。
    """
    # 生成任务 ID
    task_id = str(uuid.uuid4())

    # 创建任务记录
    tasks_store[task_id] = {
        "task_id": task_id,
        "query": request.query,
        "status": ResearchStatus.PENDING,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "request": request.dict(),
        "workflow": None,
        "config": None
    }

    try:
        # 创建工作流（延迟到 WebSocket 连接时创建，避免阻塞）
        # 这里只返回任务 ID，实际执行在 WebSocket 中
        return ResearchResponse(
            task_id=task_id,
            status=ResearchStatus.PENDING,
            message="研究任务已创建，请通过 WebSocket 连接获取实时更新"
        )
    except Exception as e:
        # 清理任务记录
        del tasks_store[task_id]
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/research/{task_id}", response_model=TaskInfo)
async def get_task_status(task_id: str):
    """
    获取任务状态。
    """
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks_store[task_id]
    return TaskInfo(
        task_id=task["task_id"],
        query=task["query"],
        status=task["status"],
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        progress=task.get("progress")
    )


@router.delete("/research/{task_id}")
async def cancel_task(task_id: str):
    """
    取消研究任务。
    """
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks_store[task_id]
    task["status"] = ResearchStatus.CANCELLED
    task["updated_at"] = datetime.now()

    return {"message": "任务已取消"}


@router.get("/research/history")
async def get_task_history(limit: int = 20, offset: int = 0):
    """
    获取任务历史列表。
    """
    tasks_list = list(tasks_store.values())
    tasks_list.sort(key=lambda x: x["created_at"], reverse=True)

    return {
        "total": len(tasks_list),
        "tasks": [
            TaskInfo(
                task_id=t["task_id"],
                query=t["query"],
                status=t["status"],
                created_at=t["created_at"],
                updated_at=t["updated_at"],
                progress=t.get("progress")
            )
            for t in tasks_list[offset:offset + limit]
        ]
    }

