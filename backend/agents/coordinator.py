"""
Coordinator Agent

该模块实现了协调器智能体（Coordinator agent），它是
研究工作流的入口节点与调度中枢。
"""

from typing import Dict, Optional, Any
from ..llm.base import BaseLLM
from ..prompts.loader import PromptLoader


class Coordinator:
    """
    Coordinator agent - the entry point for research workflow.

    协调器智能体（Coordinator agent）—— 研究工作流的入口节点
    职责说明：
    -接收用户的研究需求
    -对查询类型进行分类（问候类、不当内容类、研究类(greeting, inappropriate, or research)）
    -直接处理简单查询 (问候类、不当内容类请求 (greetings, inappropriate requests)）
    -针对复杂查询，初始化研究工作流的状态
    -将研究任务委派给规划器（Planner）
    -管理用户与系统的交互过程
    -负责工作流的全生命周期管理
    """

    def __init__(self, llm: BaseLLM):
        """
        初始化协调器实例

        参数:
            llm: 用于处理文本的语言模型实例
        """
        self.llm = llm
        self.prompt_loader = PromptLoader()

    def classify_query(self, user_query: str) -> str:
        """
        对用户查询类型进行分类

        参数:
            user_query: 用户输入的查询内容

        返回:
            查询类型：'GREETING'（问候）、'INAPPROPRIATE'（不当内容）或 'RESEARCH'（研究类）
        """
        prompt = self.prompt_loader.load(
            'coordinator_classify_query',
            user_query=user_query
        )

        query_type = self.llm.generate(prompt).strip().upper()

        # 验证分类结果的有效性
        if query_type not in ['GREETING', 'INAPPROPRIATE', 'RESEARCH']:
            # 如果分类结果不明确，默认归类为研究类查询
            query_type = 'RESEARCH'

        return query_type

    def handle_simple_query(self, user_query: str, query_type: str) -> str:
        """
        处理不需要进行研究的简单查询

        参数:
            user_query: 用户输入的查询内容
            query_type: 查询类型（'GREETING' 问候类 或 'INAPPROPRIATE' 不当内容类）

        返回:
            给用户的直接响应内容
        """
        prompt = self.prompt_loader.load(
            'coordinator_simple_response',
            user_query=user_query,
            query_type=query_type
        )

        response = self.llm.generate(prompt).strip()
        return response

    def initialize_research(self, user_query: str, auto_approve: bool = False, output_format: str = "markdown", max_iterations: int = 5) -> Dict[str, Any]:
        """
        初始化一个新的研究任务

        参数:
            user_query: 用户的研究问题/需求
            auto_approve: 是否自动批准研究计划
            output_format: 最终报告的输出格式（"markdown" 或 "html"）

        返回:
            初始化后的研究状态
        """
        # 先对查询进行分类
        query_type = self.classify_query(user_query)

        # 创建初始状态
        state = {
            'query': user_query,
            'query_type': query_type,  # 将查询类型存入状态
            'research_plan': None,
            'plan_approved': False,
            'research_results': [],
            'current_task': None,
            'iteration_count': 0,
            'max_iterations': max_iterations,
            'final_report': None,
            'current_step': 'initializing',
            'needs_more_research': True,
            'user_feedback': None,
            'auto_approve': auto_approve,  # 将自动批准标识存入状态
            'simple_response': None,  # 用于存储对简单查询的直接响应
            'output_format': output_format  # 将输出格式存入状态
        }

        # 直接处理简单查询
        if query_type in ['GREETING', 'INAPPROPRIATE']:
            state['simple_response'] = self.handle_simple_query(user_query, query_type)
            state['current_step'] = 'completed'
            state['needs_more_research'] = False

        return state

    def process_user_input(self, state: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """
        处理用户的反馈或输入内容

        参数:
            state: 当前的研究状态
            user_input: 用户输入的文本内容

        返回:
            更新后的研究状态
        """
        # 存储用户反馈
        state['user_feedback'] = user_input

        # 分析用户意图
        prompt = self.prompt_loader.load(
            'coordinator_analyze_intent',
            user_input=user_input,
            current_step=state['current_step']
        )

        intent = self.llm.generate(prompt).strip().upper()

        # 根据用户意图更新状态
        if intent == "APPROVE":
            state['plan_approved'] = True
        elif intent == "MODIFY":
            state['plan_approved'] = False
            # Plan will be revised by Planner
        elif intent == "REJECT":
            state['plan_approved'] = False
            state['research_plan'] = None
        # 对于QUESTION（提问）意图，保持状态不变，由规划器进行处理

        return state

    def delegate_to_planner(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        将任务委派给规划器（Planner）

        参数:
            state: 当前的研究状态

        返回:
            包含委派信息的更新后研究状态
        """
        state['current_step'] = 'planning'
        return state

    def handle_completion(self, state: Dict[str, Any]) -> Dict:
        """
        处理工作流的完成操作

        参数:
            state: 最终的研究状态

        返回:
            完成情况汇总
        """
        return {
            'status': 'completed',
            'query': state['query'],
            'iterations': state['iteration_count'],
            'report': state['final_report'],
            'total_results': len(state['research_results'])
        }

    def __repr__(self) -> str:
        """字符串表示形式。"""
        return f"Coordinator(llm={self.llm})"
