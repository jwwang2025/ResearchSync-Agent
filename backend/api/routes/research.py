"""
Research API Routes

研究任务相关的 RESTful API 路由，带有任务持久化支持（SQLite）和与 WebSocket 的集成点。
"""

import os
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import uuid
import json
import sqlite3
from datetime import datetime
from pathlib import Path

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

# RQ 支持
import redis
from rq import Queue

router = APIRouter()

# 数据库文件位置
DB_PATH = Path(__file__).parents[2] / "data" / "tasks.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_db():
    """初始化 SQLite 数据库和表（如果不存在）。"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        data TEXT,
        updated_at TEXT
    )
    """)
    conn.commit()
    conn.close()


def load_all_tasks() -> Dict[str, Dict[str, Any]]:
    """从数据库加载所有任务到内存字典（datetime 字段为 ISO 字符串）。"""
    tasks: Dict[str, Dict[str, Any]] = {}
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute("SELECT id, data FROM tasks")
    for row in cur.fetchall():
        tid, data = row
        try:
            tasks[tid] = json.loads(data)
        except json.JSONDecodeError:
            tasks[tid] = {"task_id": tid, "status": "unknown", "request": {}}
    conn.close()
    return tasks


def persist_task(task_id: str):
    """将指定任务写入数据库（插入或替换）。"""
    task = tasks_store.get(task_id)
    if not task:
        return
    conn = sqlite3.connect(str(DB_PATH))
    # 使用 _serialize_task 保证可序列化后直接写入 JSON
    serializable = _serialize_task(task)
    data_blob = json.dumps(serializable, ensure_ascii=False, default=repr)

    conn.execute(
        "REPLACE INTO tasks (id, data, updated_at) VALUES (?, ?, ?)",
        (task_id, data_blob, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def _serialize_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """将不可序列化字段（如 datetime）转换为可序列化形式。"""
    def _make_serializable(obj):
        # 基本数据类型
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: _make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [_make_serializable(v) for v in obj]
        # 对于其他所有对象类型（包括复杂的运行时对象，如 ResearchWorkflow），
        # 返回一个稳定的字符串表示形式，以避免 JSON 序列化错误。
        try:
            return repr(obj)
        except Exception:
            return str(obj)

    out = {}
    for k, v in task.items():
        out[k] = _make_serializable(v)
    return out


# 初始化 DB 并加载现有任务
init_db()
tasks_store: Dict[str, Dict[str, Any]] = load_all_tasks()


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
    # 持久化新建任务
    persist_task(task_id)

    # 如果配置了 Redis，则入队到 Redis，由 worker 进程执行
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        conn = redis.from_url(redis_url)
        q = Queue("research", connection=conn)
        # 导入延迟任务函数路径
        from ...tasks.jobs import run_research_job
        job = q.enqueue(run_research_job, task_id, request.dict())
        # 记录 job id
        tasks_store[task_id]["job_id"] = job.get_id()
        persist_task(task_id)
        return ResearchResponse(
            task_id=task_id,
            status=ResearchStatus.PENDING,
            message="研究任务已入队，使用 RQ worker 处理"
        )
    # 持久化新建任务
    persist_task(task_id)

    # 创建工作流（延迟到 WebSocket 连接时创建，避免阻塞）
    # 这里只返回任务 ID，实际执行在 WebSocket 中
    return ResearchResponse(
        task_id=task_id,
        status=ResearchStatus.PENDING,
        message="研究任务已创建，请通过 WebSocket 连接获取实时更新"
    )


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

