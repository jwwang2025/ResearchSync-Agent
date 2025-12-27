"""
研究工作流图

该模块为研究系统创建并管理 LangGraph 工作流。
"""

from typing import Optional
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from .state import ResearchState
from .nodes import WorkflowNodes
from ..agents.coordinator import Coordinator
from ..agents.planner import Planner
from ..agents.researcher import Researcher
from ..agents.rapporteur import Rapporteur


def create_research_graph(
    coordinator: Coordinator,
    planner: Planner,
    researcher: Researcher,
    rapporteur: Rapporteur
):
    """
    创建研究工作流图。

    参数:
        coordinator: 协调器（Coordinator）智能体实例
        planner: 规划器（Planner）智能体实例
        researcher: 研究员（Researcher）智能体实例
        rapporteur: 报告生成器（Rapporteur）智能体实例

    返回:
        已编译的 LangGraph 工作流
    """
    # 创建工作流节点实例
    nodes = WorkflowNodes(coordinator, planner, researcher, rapporteur)

    # 初始化状态图
    workflow = StateGraph(dict)  # Use dict instead of TypedDict for compatibility

    # 向图中添加节点
    workflow.add_node("coordinator", nodes.coordinator_node)
    workflow.add_node("planner", nodes.planner_node)
    workflow.add_node("human_review", nodes.human_review_node)
    workflow.add_node("researcher", nodes.researcher_node)
    workflow.add_node("rapporteur", nodes.rapporteur_node)

    # 从 START 节点添加边，替代使用 set_entry_point 方法
    workflow.add_edge(START, "coordinator")

    # 协调器 -> 条件边（简单查询直接结束，研究类查询继续执行）
    workflow.add_conditional_edges(
        "coordinator",
        nodes.should_continue_to_planner,
        {
            "planner": "planner",  # 研究类查询
            "end": END             # 简单查询（问候/不恰当内容）
        }
    )

    # 规划器 -> 人工审核
    workflow.add_edge("planner", "human_review")

    # 人工审核 -> 条件边
    workflow.add_conditional_edges(
        "human_review",
        nodes.should_continue_research,
        {
            "planner": "planner",      # 用户需要修改计划
            "researcher": "researcher"  # 用户已批准，启动研究
        }
    )

    # 研究员 -> 条件边
    workflow.add_conditional_edges(
        "researcher",
        nodes.should_generate_report,
        {
            "researcher": "researcher",  # 继续执行研究任务
            "rapporteur": "rapporteur"   # 生成最终报告
        }
    )

    # 报告生成器 -> 结束节点
    workflow.add_edge("rapporteur", END)

    # 带检查点工具编译图
    # 在 human_review 节点前添加中断，支持人机协同流程
    checkpointer = MemorySaver()
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review"]
    )


class ResearchWorkflow:
    """
    研究工作流管理器。

    该类为运行研究工作流提供了高层级接口。
    """

    def __init__(
        self,
        coordinator: Coordinator,
        planner: Planner,
        researcher: Researcher,
        rapporteur: Rapporteur
    ):
        """
        初始化研究工作流。

        参数:
            coordinator: 协调器（Coordinator）智能体
            planner: 规划器（Planner）智能体
            researcher: 研究员（Researcher）智能体
            rapporteur: 报告生成器（Rapporteur）智能体
        """
        self.coordinator = coordinator
        self.planner = planner
        self.researcher = researcher
        self.rapporteur = rapporteur
        self.graph = create_research_graph(
            coordinator, planner, researcher, rapporteur
        )

    def run(
        self,
        query: str,
        max_iterations: Optional[int] = None,
        auto_approve: bool = False,
        output_format: str = "markdown"
    ) -> dict:
        """
        运行研究工作流（同步阻塞方式）。

        参数:
            query: 研究查询语句
            max_iterations: 研究的最大迭代次数（可选）
            auto_approve: 是否自动批准研究计划
            output_format: 最终报告的输出格式（支持 "markdown" 或 "html"）

        返回:
            最终的研究状态
        """
        # 初始化状态
        initial_state = self.coordinator.initialize_research(query, auto_approve=auto_approve, output_format=output_format)

        if max_iterations:
            initial_state['max_iterations'] = max_iterations

        # 使用线程配置运行图，适配检查点工具
        config = {"configurable": {"thread_id": "1"}}
        final_state = self.graph.invoke(initial_state, config=config)

        return final_state

    def stream(
        self,
        query: str,
        max_iterations: Optional[int] = None,
        auto_approve: bool = False,
        output_format: str = "markdown"
    ):
        """
        以流式方式运行研究工作流。

        参数:
            query: 研究查询语句
            max_iterations: 研究的最大迭代次数（可选）
            auto_approve: 是否自动批准研究计划
            output_format: 最终报告的输出格式（支持 "markdown" 或 "html"）

        生成器输出:
            执行过程中的状态更新数据
        """
        # 初始化状态
        initial_state = self.coordinator.initialize_research(query, auto_approve=auto_approve, output_format=output_format)

        if max_iterations:
            initial_state['max_iterations'] = max_iterations

        # 使用线程配置流式执行图，适配检查点工具
        config = {"configurable": {"thread_id": "1"}}
        for output in self.graph.stream(initial_state, config=config):
            yield output

    def stream_interactive(
        self,
        query: str,
        max_iterations: Optional[int] = None,
        auto_approve: bool = False,
        human_approval_callback = None,
        output_format: str = "markdown"
    ):
        """
        以交互式流式方式运行研究工作流，支持人工审批交互。

        参数:
            query: 研究查询语句
            max_iterations: 研究的最大迭代次数（可选）
            auto_approve: 是否自动批准研究计划
            human_approval_callback: 人工审批的回调函数
                                     该函数应返回 (approved: bool, feedback: str)（是否批准：布尔值，反馈信息：字符串）
            output_format: 最终报告的输出格式（支持 "markdown" 或 "html"）

        生成器输出:
            执行过程中的状态更新数据
        """
        # 初始化状态
        initial_state = self.coordinator.initialize_research(query, auto_approve=auto_approve, output_format=output_format)

        if max_iterations:
            initial_state['max_iterations'] = max_iterations

        config = {"configurable": {"thread_id": "1"}}

        # 标记是否已处理审批流程
        approval_handled = False

        # 流式执行工作流
        for output in self.graph.stream(initial_state, config=config):
            # 先输出当前状态更新
            yield output

            # 检查是否触发了中断，且审批流程尚未处理
            if "__interrupt__" in output and not approval_handled:
                # 从图中获取当前状态快照
                current_snapshot = self.graph.get_state(config)
                current_state = current_snapshot.values

                # 检查当前状态是否需要审批（我们在规划后、人工审核前触发中断）
                if isinstance(current_state, dict) and current_state.get('research_plan'):
                    # 如果开启自动批准，直接将计划标记为已批准
                    if auto_approve:
                        current_state['plan_approved'] = True
                        current_state['user_feedback'] = None
                        self.graph.update_state(config, current_state)
                    # 否则，通过回调函数获取用户审批结果
                    elif human_approval_callback and not current_state.get('plan_approved', False):
                        # 设置当前步骤用于前端展示
                        current_state['current_step'] = 'awaiting_approval'

                        # 调用审批回调函数
                        approved, feedback = human_approval_callback(current_state)

                        # 更新状态
                        if approved:
                            current_state['plan_approved'] = True
                            current_state['user_feedback'] = None
                        else:
                            current_state['plan_approved'] = False
                            current_state['user_feedback'] = feedback

                        # 更新图的状态
                        self.graph.update_state(config, current_state)

                    approval_handled = True

                    # 从当前中断点继续执行工作流
                    for continue_output in self.graph.stream(None, config=config):
                        yield continue_output
                    return  # 处理完审批后退出生成器

    def get_workflow_schema(self) -> dict:
        """
        获取工作流的结构描述（Schema）。

        返回:
            工作流结构描述字典
        """
        return {
            "nodes": [
                "coordinator",
                "planner",
                "human_review",
                "researcher",
                "rapporteur"
            ],
            "edges": [
                ("coordinator", "planner"),
                ("planner", "human_review"),
                ("human_review", ["planner", "researcher"]),
                ("researcher", ["researcher", "rapporteur"]),
                ("rapporteur", "END")
            ],
            "entry_point": "coordinator",
            "conditional_edges": [
                {
                    "from": "human_review",
                    "function": "should_continue_research",
                    "destinations": ["planner", "researcher"]
                },
                {
                    "from": "researcher",
                    "function": "should_generate_report",
                    "destinations": ["researcher", "rapporteur"]
                }
            ]
        }

    def visualize(self, output_path: Optional[str] = None) -> str:
        """
        可视化工作流图。

        参数:
            output_path: 可选参数，可视化文件的保存路径

        返回:
            可视化文件的路径或可视化字符串（Mermaid 格式）
        """
        try:
            # 尝试获取图的可视化内容
            from langgraph.graph import Graph

            mermaid = self.graph.get_graph().draw_mermaid()

            if output_path:
                with open(output_path, 'w') as f:
                    f.write(mermaid)
                return output_path
            else:
                return mermaid
        except Exception as e:
            return f"Visualization not available: {str(e)}"
