"""
规划器智能体（Planner Agent）

该模块实现了规划器智能体，核心职责是创建和管理研究计划。
"""

import json
from typing import Dict, List, Optional
from ..workflow.state import ResearchState, PlanStructure, SubTask
from ..llm.base import BaseLLM
from ..prompts.loader import PromptLoader


class Planner:
    """
    规划器智能体（Planner agent） - 战略规划组件。

    核心职责：
    - 分析研究目标
    - 创建结构化的研究计划
    - 将复杂任务拆解为子任务
    - 接收并处理用户的修改意见
    - 评估上下文信息的充分性
    - 决策是否继续研究或生成最终报告
    """

    def __init__(self, llm: BaseLLM):
        """
        初始化规划器智能体。

        参数:
            llm: 用于规划任务的大语言模型实例
        """
        self.llm = llm
        self.prompt_loader = PromptLoader()

    def create_research_plan(self, state: ResearchState) -> ResearchState:
        """
        根据用户查询创建研究计划。

        参数:
            state: 当前的研究状态（包含查询、反馈、结果等上下文）

        返回:
            已更新研究计划的状态对象
        """
        query = state['query']
        user_feedback = state.get('user_feedback', '')

        # 构建生成计划所需的提示词
        prompt = self.prompt_loader.load(
            'planner_create_plan',
            query=query,
            user_feedback=user_feedback if user_feedback else None
        )

        # 生成研究计划
        response = self.llm.generate(prompt, temperature=0.7)

        # 解析JSON格式的响应结果
        try:
            # 从响应中提取JSON内容（兼容LLM可能追加额外文本的情况）
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                plan = json.loads(json_str)
            else:
                # 解析失败时创建回退计划
                plan = self._create_fallback_plan(query)

            # 为所有子任务添加状态标识
            for task in plan.get('sub_tasks', []):
                task['status'] = 'pending'

            # 更新研究状态
            state['research_plan'] = plan
            state['max_iterations'] = plan.get('estimated_iterations', 3)

        except json.JSONDecodeError:
            # JSON解析失败时使用回退计划
            plan = self._create_fallback_plan(query)
            state['research_plan'] = plan

        return state

    def _create_fallback_plan(self, query: str) -> PlanStructure:
        """
        当JSON解析失败时，创建简易的回退研究计划。

        参数:
            query: 研究查询语句

        返回:
            基础版研究计划（保证功能可用）
        """
        return {
            'research_goal': query,
            'sub_tasks': [
                {
                    'task_id': 1,
                    'description': f'Research: {query}',
                    'search_queries': [query],
                    'sources': ['tavily'],
                    'status': 'pending',
                    'priority': 1
                }
            ],
            'completion_criteria': 'Gather sufficient information to answer the query',
            'estimated_iterations': 2
        }

    def modify_plan(self, state: ResearchState, modifications: str) -> ResearchState:
        """
        根据用户反馈修改研究计划。

        参数:
            state: 当前的研究状态
            modifications: 用户提出的计划修改要求

        返回:
            已更新修改后计划的状态对象
        """
        current_plan = state['research_plan']

        prompt = self.prompt_loader.load(
            'planner_modify_plan',
            current_plan=json.dumps(current_plan, indent=2),
            modifications=modifications
        )

        response = self.llm.generate(prompt, temperature=0.7)

        # 解析修改后的计划
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                modified_plan = json.loads(json_str)
                state['research_plan'] = modified_plan
        except json.JSONDecodeError:
            # 解析失败时保留原计划
            pass

        return state

    def evaluate_context_sufficiency(self, state: ResearchState) -> bool:
        """
        评估已收集的上下文信息是否足够回答研究问题。

        参数:
            state: 当前的研究状态

        返回:
            信息充足返回True，否则返回False
        """
        query = state['query']
        plan = state['research_plan']
        results = state['research_results']
        iteration = state['iteration_count']
        max_iterations = state['max_iterations']

        # 检查是否达到最大迭代次数（强制终止）
        if iteration >= max_iterations:
            return True

        # 检查是否有研究结果（无结果则信息不足）
        if not results:
            return False

        # 使用LLM评估信息充分性
        prompt = self.prompt_loader.load(
            'planner_evaluate_context',
            query=query,
            research_goal=plan.get('research_goal', query),
            completion_criteria=plan.get('completion_criteria', 'N/A'),
            results_count=len(results),
            current_iteration=iteration + 1,
            max_iterations=max_iterations
        )

        response = self.llm.generate(prompt, temperature=0.3).strip().upper()
        return response == "YES"

    def get_next_task(self, state: ResearchState) -> Optional[SubTask]:
        """
        从研究计划中获取下一个待执行的子任务。

        参数:
            state: 当前的研究状态

        返回:
            下一个待执行的子任务；若所有任务完成则返回None
        """
        plan = state.get('research_plan')
        if not plan:
            return None

        # 按优先级排序，找到第一个待执行任务
        tasks = sorted(
            plan.get('sub_tasks', []),
            key=lambda t: (t.get('priority', 99), t.get('task_id', 0))
        )

        for task in tasks:
            if task.get('status') == 'pending':
                return task

        return None

    def format_plan_for_display(self, plan: PlanStructure) -> str:
        """
        格式化研究计划，便于展示给用户。

        参数:
            plan: 研究计划对象

        返回:
            格式化后的计划字符串（易读的文本格式）
        """
        output = []
        output.append(f"=Ë Research Goal: {plan.get('research_goal', 'N/A')}")
        output.append(f"\n=Ê Estimated Iterations: {plan.get('estimated_iterations', 'N/A')}")
        output.append(f"\n Completion Criteria: {plan.get('completion_criteria', 'N/A')}")
        output.append("\n\n=Ý Subtasks:")

        for task in plan.get('sub_tasks', []):
            output.append(f"\n  {task['task_id']}. {task['description']}")
            output.append(f"     Queries: {', '.join(task.get('search_queries', []))}")
            output.append(f"     Sources: {', '.join(task.get('sources', []))}")
            output.append(f"     Priority: {task.get('priority', 'N/A')}")
            output.append(f"     Status: {task.get('status', 'pending')}")

        return ''.join(output)

    def __repr__(self) -> str:
        """返回规划器实例的字符串表示（便于调试）。"""
        return f"Planner(llm={self.llm})"
