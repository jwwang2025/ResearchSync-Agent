"""
用于任务队列工作进程（RQ）的后台任务函数。

这些函数旨在由 RQ 工作进程加入任务队列执行。
它们操作与 API 共用的 SQLite 数据库，以持久化存储任务状态。
"""
from typing import Dict, Any
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import os

# 导入应用工作流创建器
from backend.api.routes.research import create_workflow, DB_PATH, _serialize_task
from backend.api.routes.research import tasks_store as api_tasks_store
import redis


def run_research_job(task_id: str, request_data: Dict[str, Any]) -> int:
    """
    执行研究任务的 RQ 工作进程入口函数。

    直接更新 SQLite 数据库中的任务状态。
    成功时返回 0，失败时返回非 0 值。
    """
    # Ensure DB path is reachable
    db_path = Path(DB_PATH)
    conn = sqlite3.connect(str(db_path))
    try:
        # Update task to running
        _update_task_in_db(conn, task_id, {"status": "running", "updated_at": datetime.now().isoformat()})

        # Create workflow
        llm_provider = request_data.get("llm_provider")
        llm_model = request_data.get("llm_model")
        workflow, cfg = create_workflow(llm_provider=llm_provider, llm_model=llm_model)

        # Run the workflow directly (remove dependency on CLI runner)
        current_state = None
        try:
            stream_iter = workflow.stream_interactive(
                request_data.get("query", ""),
                request_data.get("max_iterations", 5),
                auto_approve=request_data.get("auto_approve", False),
                human_approval_callback=None,
                output_format=request_data.get("output_format", "markdown")
            )
            for state_update in stream_iter:
                for node_name, state in state_update.items():
                    if isinstance(state, tuple):
                        if len(state) >= 1:
                            current_state = state[0] if isinstance(state[0], dict) else state
                        else:
                            continue
                    else:
                        current_state = state
                    # Persist progress periodically
                    _update_task_in_db(conn, task_id, {"status": "researching", "updated_at": datetime.now().isoformat(), "progress": json.dumps({"last_state": current_state}, ensure_ascii=False)})
        except Exception as e:
            _update_task_in_db(conn, task_id, {"status": "failed", "error": str(e), "updated_at": datetime.now().isoformat()})
            return 2

        # On success, mark completed
        _update_task_in_db(conn, task_id, {"status": "completed", "updated_at": datetime.now().isoformat()})
        return 0
    finally:
        conn.close()


def _update_task_in_db(conn: sqlite3.Connection, task_id: str, partial: Dict[str, Any]) -> None:
    """辅助函数：更新数据库中的任务 JSON 数据块。"""
    cur = conn.execute("SELECT data FROM tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    if row:
        try:
            data = json.loads(row[0])
        except Exception:
            data = {}
    else:
        data = {"task_id": task_id}

    # Merge partial
    for k, v in partial.items():
        data[k] = v

    conn.execute(
        "REPLACE INTO tasks (id, data, updated_at) VALUES (?, ?, ?)",
        (task_id, json.dumps(data, ensure_ascii=False, default=repr), datetime.now().isoformat()),
    )
    conn.commit()
    # 尝试发布到 Redis 频道，供 API 转发到 WebSocket 使用
    try:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            r = redis.from_url(redis_url)
            channel = f"tasks:updates:{task_id}"
            message = {"task_id": task_id, "payload": partial, "updated_at": datetime.now().isoformat()}
            r.publish(channel, json.dumps(message, ensure_ascii=False, default=repr))
    except Exception:
        # 发布失败不影响主流程
        pass


