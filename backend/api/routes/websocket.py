"""
WebSocket Routes

WebSocket 路由，用于实时通信和流式输出。
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Any
import json
import asyncio
from datetime import datetime
import os

from ..models.research import ResearchStatus, PlanApprovalRequest
from .research import tasks_store, create_workflow, persist_task

router = APIRouter()


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        """接受 WebSocket 连接"""
        # 若环境变量 WS_ALLOWED_ORIGINS 已配置，则对 Origin 请求头进行白名单校验；未配置则允许所有来源。
        origin = None
        for (k, v) in websocket.scope.get("headers", []):
            if k.lower() == b"origin":
                origin = v.decode("utf-8", errors="ignore")
                break

        allowed_env = os.getenv("WS_ALLOWED_ORIGINS")
        if allowed_env:
            allowed = [o.strip() for o in allowed_env.split(",") if o.strip()]
            if origin is None or origin not in allowed:
                # 以 1008 状态码（策略违规）拒绝未知来源的连接
                await websocket.close(code=1008, reason="Origin not allowed")
                # 抛出连接断开异常，终止后续的处理逻辑
                raise WebSocketDisconnect()

        await websocket.accept()
        self.active_connections[task_id] = websocket

    def disconnect(self, task_id: str):
        """断开连接"""
        if task_id in self.active_connections:
            del self.active_connections[task_id]

    async def send_message(self, task_id: str, message: Dict[str, Any]):
        """发送消息到指定任务"""
        if task_id in self.active_connections:
            try:
                await self.active_connections[task_id].send_json(message)
            except Exception as e:
                print(f"发送消息失败: {e}")
                self.disconnect(task_id)

    async def broadcast(self, message: Dict[str, Any]):
        """广播消息到所有连接"""
        for task_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"广播消息失败: {e}")
                self.disconnect(task_id)


manager = ConnectionManager()
# 任务的活跃审批事件（任务ID -> 异步IO事件对象）
active_approval_events: Dict[str, asyncio.Event] = {}


async def run_research_workflow(task_id: str, request_data: Dict[str, Any]):
    """
    运行研究工作流（异步）。

    Args:
        task_id: 任务 ID
        request_data: 研究请求数据
    """
    try:
        # 更新任务状态
        task = tasks_store[task_id]
        task["status"] = ResearchStatus.PLANNING
        task["updated_at"] = datetime.now()
        # 持久化任务状态
        persist_task(task_id)

        # 发送状态更新
        await manager.send_message(task_id, {
            "type": "status_update",
            "task_id": task_id,
            "step": "planning",
            "message": "正在创建研究计划..."
        })

        # 创建工作流
        workflow, cfg = create_workflow(
            llm_provider=request_data.get("llm_provider"),
            llm_model=request_data.get("llm_model")
        )

        # 保存工作流和配置（用于后续审批）
        task["workflow"] = workflow
        task["config"] = cfg
        # Graph 使用固定的执行配置（与 ResearchWorkflow.stream_interactive 一致）
        graph_config = {"configurable": {"thread_id": "1"}}
        task["graph_config"] = graph_config
        persist_task(task_id)

        # 运行工作流（流式）
        max_iterations = request_data.get("max_iterations", 5)
        auto_approve = request_data.get("auto_approve", False)

        # 使用同步流式执行（在实际实现中可能需要改为异步）
        # 这里简化处理，实际应该使用异步任务队列
        stream_iter = workflow.stream_interactive(
            query=request_data["query"],
            max_iterations=max_iterations,
            auto_approve=auto_approve,
            human_approval_callback=None,  # WebSocket 处理审批
            output_format=request_data.get("output_format", "markdown")
        )

        current_state = None
        approval_pending = False

        for state_update in stream_iter:
            # 检查是否发生了中断
            if "__interrupt__" in state_update:
                print(f"[run_research_workflow] Detected interrupt in workflow")
                # 获取当前状态快照来检查是否需要审批
                gcfg = task.get("graph_config", {"configurable": {"thread_id": "1"}})
                snapshot = workflow.graph.get_state(gcfg)
                current_state = snapshot.values if hasattr(snapshot, "values") else snapshot

                if isinstance(current_state, dict) and current_state.get('research_plan') and not auto_approve:
                    # 发送计划审批请求给前端
                    approval_pending = True
                    task["status"] = ResearchStatus.AWAITING_APPROVAL
                task["updated_at"] = datetime.now()
                persist_task(task_id)

                await manager.send_message(task_id, {
                    "type": "plan_ready",
                    "task_id": task_id,
                    "plan": current_state.get('research_plan'),
                    "message": "研究计划已生成，等待审批"
                })

                # 等待审批（通过 WebSocket 消息）
                evt = asyncio.Event()
                active_approval_events[task_id] = evt
                persist_task(task_id)
                try:
                    timeout = request_data.get("approval_timeout", 300)
                    await asyncio.wait_for(evt.wait(), timeout=timeout)
                except asyncio.TimeoutError:
                    task["status"] = ResearchStatus.FAILED
                    task["updated_at"] = datetime.now()
                    persist_task(task_id)
                    await manager.send_message(task_id, {
                        "type": "error",
                        "task_id": task_id,
                        "message": "审批超时，研究终止"
                    })
                    active_approval_events.pop(task_id, None)
                    return
                finally:
                    active_approval_events.pop(task_id, None)

                    # 从中断点继续执行工作流
                    print(f"[run_research_workflow] Continuing workflow from interrupt point")
                    for continue_output in workflow.graph.stream(None, config=gcfg):
                        # 处理继续执行的输出
                        for continue_node_name, continue_state in continue_output.items():
                            if isinstance(continue_state, tuple):
                                if len(continue_state) >= 1:
                                    continue_current_state = continue_state[0] if isinstance(continue_state[0], dict) else continue_state
                                else:
                                    continue
                            else:
                                continue_current_state = continue_state

                            if not isinstance(continue_current_state, dict):
                                continue

                            continue_step = continue_current_state.get('current_step', 'unknown')

                            # 发送继续执行的进度更新
                            if continue_step == 'researching':
                                task["status"] = ResearchStatus.RESEARCHING
                                task["updated_at"] = datetime.now()
                                persist_task(task_id)

                                await manager.send_message(task_id, {
                                    "type": "progress",
                                    "task_id": task_id,
                                    "step": continue_step,
                                    "iteration": continue_current_state.get('iteration_count', 0),
                                    "max_iterations": continue_current_state.get('max_iterations', max_iterations),
                                    "current_task": continue_current_state.get('current_task', {}).get('description', ''),
                                    "data": continue_current_state
                                })

                            elif continue_step == 'generating_report':
                                task["status"] = ResearchStatus.GENERATING_REPORT
                                task["updated_at"] = datetime.now()
                                persist_task(task_id)

                                await manager.send_message(task_id, {
                                    "type": "status_update",
                                    "task_id": task_id,
                                    "step": continue_step,
                                    "message": "正在生成最终报告..."
                                })

                    # 检查最终状态
                    final_snapshot = workflow.graph.get_state(gcfg)
                    final_state = final_snapshot.values if hasattr(final_snapshot, "values") else final_snapshot

                    if isinstance(final_state, dict) and final_state.get('final_report'):
                        task["status"] = ResearchStatus.COMPLETED
                        task["updated_at"] = datetime.now()
                        persist_task(task_id)

                        cfg_obj = task.get('config')
                        out_dir = "./outputs"
                        if cfg_obj:
                            out_dir = getattr(cfg_obj.workflow, "output_dir", out_dir)

                        os.makedirs(out_dir, exist_ok=True)
                        fmt = final_state.get('output_format', request_data.get("output_format", "markdown"))
                        ext = "html" if fmt == "html" else "md"
                        fname = f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
                        fpath = os.path.join(out_dir, fname)
                        with open(fpath, "w", encoding="utf-8") as f:
                            f.write(final_state['final_report'])
                        task['output_path'] = fpath
                        persist_task(task_id)
                        print(f"[run_research_workflow] Saved report to {fpath}")

                        await manager.send_message(task_id, {
                            "type": "report_ready",
                            "task_id": task_id,
                            "report": final_state['final_report'],
                            "format": request_data.get("output_format", "markdown")
                        })
                    else:
                        task["status"] = ResearchStatus.FAILED
                        task["updated_at"] = datetime.now()
                        persist_task(task_id)

                        debug_info = repr(final_state)
                        await manager.send_message(task_id, {
                            "type": "error",
                            "task_id": task_id,
                            "message": "研究未成功完成",
                            "debug": debug_info
                        })
                        print(f"[run_research_workflow] Task {task_id} finished without final_report after continue. state={debug_info}")

                    return  # 成功完成，退出函数


            # 处理正常的节点输出
            for node_name, state in state_update.items():
                if isinstance(state, tuple):
                    if len(state) >= 1:
                        current_state = state[0] if isinstance(state[0], dict) else state
                    else:
                        continue
                else:
                    current_state = state

                if not isinstance(current_state, dict):
                    continue

                step = current_state.get('current_step', 'unknown')

                # 处理正常的节点输出（非中断情况）
                # 发送进度更新
                if step == 'researching':
                    task["status"] = ResearchStatus.RESEARCHING
                    task["updated_at"] = datetime.now()
                    persist_task(task_id)

                    await manager.send_message(task_id, {
                        "type": "progress",
                        "task_id": task_id,
                        "step": step,
                        "iteration": current_state.get('iteration_count', 0),
                        "max_iterations": current_state.get('max_iterations', max_iterations),
                        "current_task": current_state.get('current_task', {}).get('description', ''),
                        "data": current_state
                    })

                elif step == 'generating_report':
                    task["status"] = ResearchStatus.GENERATING_REPORT
                    task["updated_at"] = datetime.now()
                    persist_task(task_id)

                    await manager.send_message(task_id, {
                        "type": "status_update",
                        "task_id": task_id,
                        "step": step,
                        "message": "正在生成最终报告..."
                    })

    except Exception as e:
        task["status"] = ResearchStatus.FAILED
        task["updated_at"] = datetime.now()
        persist_task(task_id)

        await manager.send_message(task_id, {
            "type": "error",
            "task_id": task_id,
            "message": f"研究过程中出错: {str(e)}"
        })


@router.websocket("/research/{task_id}")
async def websocket_research(websocket: WebSocket, task_id: str):
    """
    WebSocket 端点，用于研究任务的实时通信。

    客户端连接后，如果任务尚未开始，将自动启动研究工作流。
    """
    # 检查任务是否存在
    if task_id not in tasks_store:
        await websocket.close(code=1008, reason="任务不存在")
        return

    # 连接 WebSocket
    await manager.connect(websocket, task_id)

    try:
        task = tasks_store[task_id]

        # 如果任务尚未开始，启动研究工作流
        if task["status"] == ResearchStatus.PENDING:
            # 在后台任务中运行研究工作流
            # 注意：这里简化处理，实际应该使用 Celery 等任务队列
            request_data = task["request"]
            asyncio.create_task(run_research_workflow(task_id, request_data))

        # 监听客户端消息（用于审批等）
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                if message.get("type") == "approve_plan":
                    # 处理计划审批
                    approved = message.get("approved", False)
                    feedback = message.get("feedback")

                    if task_id in tasks_store:
                        task = tasks_store[task_id]
                        workflow = task.get("workflow")

                        if workflow:
                            # 保存审批结果到任务状态
                            task['plan_approved'] = bool(approved)
                            task['user_feedback'] = feedback
                            task['updated_at'] = datetime.now()
                            persist_task(task_id)

                            # 触发可能在等待的审批事件
                            evt = active_approval_events.get(task_id)
                            if isinstance(evt, asyncio.Event):
                                evt.set()

                            # 尝试直接将审批结果写入 workflow 的状态，促使图继续执行
                            cfg_obj = task.get('graph_config', task.get('config'))
                            if cfg_obj:
                                snapshot = workflow.graph.get_state(cfg_obj)
                                state_obj = snapshot.values if hasattr(snapshot, "values") else snapshot
                                if isinstance(state_obj, dict):
                                    state_obj['plan_approved'] = bool(approved)
                                    state_obj['user_feedback'] = feedback
                                    workflow.graph.update_state(cfg_obj, state_obj)
                                    print(f"[websocket_research] Successfully updated workflow state: plan_approved={bool(approved)}")

                            # 发布 Redis 通知（如果配置了 REDIS_URL），以便在使用 RQ worker 时触发 worker
                            redis_url = os.getenv("REDIS_URL")
                            if redis_url:
                                import importlib
                                redis_mod = importlib.import_module("redis")
                                rcli = redis_mod.from_url(redis_url)
                                channel = f"tasks:updates:{task_id}"
                                message = {"task_id": task_id, "payload": {"plan_approved": task.get('plan_approved', False), "user_feedback": task.get('user_feedback')}, "updated_at": datetime.now().isoformat()}
                                rcli.publish(channel, json.dumps(message, ensure_ascii=False, default=repr))

                            # 通知前端已接收审批
                            await manager.send_message(task_id, {
                                "type": "approval_received",
                                "task_id": task_id,
                                "approved": approved
                            })

            except json.JSONDecodeError:
                await manager.send_message(task_id, {
                    "type": "error",
                    "message": "无效的 JSON 格式"
                })

    except WebSocketDisconnect:
        manager.disconnect(task_id)

