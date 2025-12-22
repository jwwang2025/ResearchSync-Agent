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
        # Whitelist Origin header if WS_ALLOWED_ORIGINS is set; otherwise allow.
        origin = None
        try:
            for (k, v) in websocket.scope.get("headers", []):
                if k.lower() == b"origin":
                    origin = v.decode("utf-8", errors="ignore")
                    break
        except Exception:
            origin = None

        allowed_env = os.getenv("WS_ALLOWED_ORIGINS")
        if allowed_env:
            allowed = [o.strip() for o in allowed_env.split(",") if o.strip()]
            if origin is None or origin not in allowed:
                # Reject unknown origins with 1008 (policy violation)
                try:
                    await websocket.close(code=1008, reason="Origin not allowed")
                except Exception:
                    pass
                # raise disconnect to stop further handling
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

                # 检查是否需要审批
                if step == 'awaiting_approval' and not auto_approve:
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
                    # 这里需要实现一个等待机制
                    break

                # 发送进度更新
                elif step == 'researching':
                    task["status"] = ResearchStatus.RESEARCHING
                    task["updated_at"] = datetime.now()
                    persist_task(task_id)

                    await manager.send_message(task_id, {
                        "type": "progress",
                        "task_id": task_id,
                        "step": step,
                        "iteration": current_state.get('iteration_count', 0),
                        "max_iterations": max_iterations,
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

        # 获取最终报告
        if current_state and current_state.get('final_report'):
            task["status"] = ResearchStatus.COMPLETED
            task["updated_at"] = datetime.now()
            persist_task(task_id)

            await manager.send_message(task_id, {
                "type": "report_ready",
                "task_id": task_id,
                "report": current_state['final_report'],
                "format": request_data.get("output_format", "markdown")
            })
        else:
            task["status"] = ResearchStatus.FAILED
            task["updated_at"] = datetime.now()
            persist_task(task_id)

            # No final report produced — include diagnostic snapshot for debugging
            debug_info = None
            try:
                debug_info = repr(current_state)
            except Exception:
                debug_info = "unserializable current_state"
            await manager.send_message(task_id, {
                "type": "error",
                "task_id": task_id,
                "message": "研究未成功完成",
                "debug": debug_info
            })
            # Also log server-side
            try:
                print(f"[run_research_workflow] Task {task_id} finished without final_report. state={debug_info}")
            except Exception:
                pass

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
                            # 更新状态并继续工作流
                            # 这里需要实现继续工作流的逻辑
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
    except Exception as e:
        await manager.send_message(task_id, {
            "type": "error",
            "message": f"WebSocket 错误: {str(e)}"
        })
        manager.disconnect(task_id)

