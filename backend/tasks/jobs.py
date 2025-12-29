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
import time

# 导入应用工作流创建器
# 延迟导入 `backend.api.routes.research` 中的符号以避免与 API 模块发生循环导入。
# 只有在实际执行任务时再导入需要的名称。
import importlib


def run_research_job(task_id: str, request_data: Dict[str, Any]) -> int:
    """
    执行研究任务的 RQ 工作进程入口函数。

    直接更新 SQLite 数据库中的任务状态。
    成功时返回 0，失败时返回非 0 值。
    """
    # 延迟导入以避免循环依赖（research.py 可能会导入本模块）
    from backend.api.routes.research import create_workflow, DB_PATH, _serialize_task
    from backend.api.routes.research import tasks_store as api_tasks_store

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
        # Graph config must match stream_interactive's config
        graph_config = {"configurable": {"thread_id": "1"}}

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
                    # 如果进入人工审批步骤且未开启自动批准，则在 DB 中轮询等待审批结果
                    try:
                        if isinstance(current_state, dict):
                            step = current_state.get('current_step', '')
                        else:
                            step = ''
                    except Exception:
                        step = ''

                    if step == 'awaiting_approval' and not request_data.get('auto_approve', False):
                        # 将任务标记为等待审批
                        _update_task_in_db(conn, task_id, {"status": "awaiting_approval", "updated_at": datetime.now().isoformat()})
                        # 等待审批标志（轮询 DB 中的 plan_approved 字段）
                        approval_timeout = int(request_data.get("approval_timeout", 300))
                        poll_interval = 1.0
                        waited = 0.0
                        approved = False
                        while waited < approval_timeout:
                            # 读取任务记录
                            cur = conn.execute("SELECT data FROM tasks WHERE id = ?", (task_id,))
                            row = cur.fetchone()
                            if row:
                                try:
                                    task_data = json.loads(row[0])
                                    if task_data.get('plan_approved', False):
                                        approved = True
                                        # 将可能的 user_feedback 合并到 current_state
                                        if task_data.get('user_feedback') is not None:
                                            current_state['user_feedback'] = task_data.get('user_feedback')
                                        break
                                except Exception:
                                    pass
                            time.sleep(poll_interval)
                            waited += poll_interval

                        if not approved:
                            # 审批超时或被拒绝，标记失败并返回
                            _update_task_in_db(conn, task_id, {"status": "failed", "updated_at": datetime.now().isoformat(), "error": "approval_timeout_or_rejected"})
                            return 3
                        # 审批通过：将结果写回工作流状态以继续执行
                        try:
                            current_state['plan_approved'] = True
                            # 尝试使用 graph_config 更新图的状态（若可用）
                            try:
                                snapshot = workflow.graph.get_state(graph_config)
                                snapshot_state = snapshot.values if hasattr(snapshot, "values") else snapshot
                            except Exception:
                                snapshot_state = {}
                            if isinstance(snapshot_state, dict):
                                snapshot_state.update(current_state)
                                try:
                                    workflow.graph.update_state(graph_config, snapshot_state)
                                except Exception:
                                    pass
                        except Exception:
                            pass
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
            try:
                redis = importlib.import_module("redis")
                r = redis.from_url(redis_url)
            except Exception:
                r = None
            channel = f"tasks:updates:{task_id}"
            message = {"task_id": task_id, "payload": partial, "updated_at": datetime.now().isoformat()}
            if r:
                r.publish(channel, json.dumps(message, ensure_ascii=False, default=repr))
    except Exception:
        # 发布失败不影响主流程
        pass


