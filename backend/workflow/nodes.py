"""
工作流节点

该模块为LangGraph工作流定义了节点函数。
"""

from typing import Dict, Any
from ..agents.coordinator import Coordinator
from ..agents.planner import Planner
from ..agents.researcher import Researcher
from ..agents.rapporteur import Rapporteur


class WorkflowNodes:
    """
    工作流节点函数的容器类。
    """

    def __init__(
        self,
        coordinator: Coordinator,
        planner: Planner,
        researcher: Researcher,
        rapporteur: Rapporteur
    ):
        """
        初始化工作流节点。

        参数:
            coordinator: 协调器（Coordinator）智能体实例
            planner: 规划器（Planner）智能体实例
            researcher: 研究员（Researcher）智能体实例
            rapporteur: 报告生成器（Rapporteur）智能体实例
        """
        self.coordinator = coordinator
        self.planner = planner
        self.researcher = researcher
        self.rapporteur = rapporteur

    def coordinator_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        协调器节点 - 工作流的入口点。

        参数:
            state: 当前的研究状态

        返回:
            更新后的状态
        """
        # 检查是否是已处理完毕的简单查询
        if state.get('query_type') in ['GREETING', 'INAPPROPRIATE']:
            # 简单查询已在初始化研究（initialize_research）中处理完毕
            state['current_step'] = 'completed'
            return state

        # 对于研究类查询, 将任务委托给规划器
        state['current_step'] = 'coordinating'
        state = self.coordinator.delegate_to_planner(state)
        return state

    def planner_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        规划器节点 - 创建或更新研究计划。

        参数:
            state: 当前的研究状态

        返回:
            包含研究计划的更新后状态
        """
        state['current_step'] = 'planning'

        # 如果存在用户反馈且已有研究计划，则修改该计划
        if state.get('user_feedback') and state.get('research_plan'):
            state = self.planner.modify_plan(state, state['user_feedback'])
        # 否则创建一个新的研究计划
        elif not state.get('research_plan'):
            state = self.planner.create_research_plan(state)

        return state

    def human_review_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        人工审核节点 - 暂停流程等待用户批准。

        参数:
            state: 当前的研究状态

        返回:
            更新后的状态
        """
        state['current_step'] = 'awaiting_approval'

        # 检查是否启动了自动批准功能
        if state.get('auto_approve', False):
            state['plan_approved'] = True

        # 在实际的实现中，此节点会暂停流程并等待用户输入
        # 目前，我们仅标记对应的状态
        return state

    def researcher_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        研究员节点 - 执行研究任务。

        参数:
            state: 当前的研究状态

        返回:
            包含研究结果的更新后状态
        """
        state['current_step'] = 'researching'

        # 从研究计划中获取下一个任务
        next_task = self.planner.get_next_task(state)

        if next_task:
            # 执行该任务
            state = self.researcher.execute_task(state, next_task)
            state['current_task'] = next_task
            state['iteration_count'] += 1
        else:
            # 没有更多待执行的任务
            state['needs_more_research'] = False

        return state

    def rapporteur_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        报告生成器节点 - 生成最终研究报告。

        参数:
            state: 当前的研究状态

        返回:
            包含最终报告的更新后状态
        """
        state['current_step'] = 'generating_report'
        state = self.rapporteur.generate_report(state)
        return state

    def should_continue_to_planner(self, state: Dict[str, Any]) -> str:
        """
        条件边函数 - 决定流程是继续进入规划器还是直接结束。

        参数:
            state: 当前的研究状态

        返回:
            下一个节点的名称：对于研究类查询返回"planner"，对于简单查询返回"end"
        """
        # 如果是简单查询（问候或不恰当内容），结束工作流
        if state.get('query_type') in ['GREETING', 'INAPPROPRIATE']:
            return "end"

        # 否则，继续进入规划器执行研究流程
        return "planner"

    def should_continue_research(self, state: Dict[str, Any]) -> str:
        """
        条件边函数 - 决定人工审核后的下一步流程。

        参数:
            state: 当前的研究状态

        返回:
            下一个节点的名称
        """
        # 如果计划未被批准，返回规划器重新修改计划
        if not state.get('plan_approved'):
            return "planner"

        # 如果计划已被批准，开始执行研究任务
        return "researcher"

    def should_generate_report(self, state: Dict[str, Any]) -> str:
        """
        条件边函数 - 决定是否应该生成最终研究报告。

        参数:
            state: 当前的研究状态

        返回:
            下一个节点的名称
        """
        # 检查是否已达到最大迭代次数
        if state['iteration_count'] >= state['max_iterations']:
            return "rapporteur"

        # 检查上下文信息是否足够充分
        if self.planner.evaluate_context_sufficiency(state):
            return "rapporteur"

        # 检查是否还有剩余待执行的任务
        next_task = self.planner.get_next_task(state)
        if next_task:
            return "researcher"
        else:
            return "rapporteur"


def create_node_functions(
    coordinator: Coordinator,
    planner: Planner,
    researcher: Researcher,
    rapporteur: Rapporteur
) -> WorkflowNodes:
    """
    创建工作流节点函数实例。

    参数:
        coordinator: 协调器（Coordinator）智能体
        planner: 规划器（Planner）智能体
        researcher: 研究员（Researcher）智能体
        rapporteur: 报告生成器（Rapporteur）智能体

    返回:
        WorkflowNodes类的实例
    """
    return WorkflowNodes(coordinator, planner, researcher, rapporteur)
