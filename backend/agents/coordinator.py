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
        Initialize the Coordinator.

        Args:
            llm: Language model instance for processing
        """
        self.llm = llm
        self.prompt_loader = PromptLoader()

    def classify_query(self, user_query: str) -> str:
        """
        Classify the user query type.

        Args:
            user_query: User's input query

        Returns:
            Query type: 'GREETING', 'INAPPROPRIATE', or 'RESEARCH'
        """
        prompt = self.prompt_loader.load(
            'coordinator_classify_query',
            user_query=user_query
        )

        query_type = self.llm.generate(prompt).strip().upper()

        # Validate classification
        if query_type not in ['GREETING', 'INAPPROPRIATE', 'RESEARCH']:
            # Default to RESEARCH if classification is unclear
            query_type = 'RESEARCH'

        return query_type

    def handle_simple_query(self, user_query: str, query_type: str) -> str:
        """
        Handle simple queries that don't require research.

        Args:
            user_query: User's input query
            query_type: Type of query ('GREETING' or 'INAPPROPRIATE')

        Returns:
            Direct response to the user
        """
        prompt = self.prompt_loader.load(
            'coordinator_simple_response',
            user_query=user_query,
            query_type=query_type
        )

        response = self.llm.generate(prompt).strip()
        return response

    def initialize_research(self, user_query: str, auto_approve: bool = False, output_format: str = "markdown") -> Dict[str, Any]:
        """
        Initialize a new research task.

        Args:
            user_query: User's research question/request
            auto_approve: Whether to auto-approve the research plan
            output_format: Output format for the final report ("markdown" or "html")

        Returns:
            Initialized research state
        """
        # Classify the query first
        query_type = self.classify_query(user_query)

        # Create initial state
        state = {
            'query': user_query,
            'query_type': query_type,  # Add query type to state
            'research_plan': None,
            'plan_approved': False,
            'research_results': [],
            'current_task': None,
            'iteration_count': 0,
            'max_iterations': 5,  # Default maximum iterations
            'final_report': None,
            'current_step': 'initializing',
            'needs_more_research': True,
            'user_feedback': None,
            'auto_approve_plan': auto_approve,  # Add auto_approve flag to state
            'simple_response': None,  # For storing direct responses to simple queries
            'output_format': output_format  # Add output format to state
        }

        # Handle simple queries directly
        if query_type in ['GREETING', 'INAPPROPRIATE']:
            state['simple_response'] = self.handle_simple_query(user_query, query_type)
            state['current_step'] = 'completed'
            state['needs_more_research'] = False

        return state

    def process_user_input(self, state: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """
        Process user feedback or input.

        Args:
            state: Current research state
            user_input: User's input text

        Returns:
            Updated research state
        """
        # Store user feedback
        state['user_feedback'] = user_input

        # Analyze user intent
        prompt = self.prompt_loader.load(
            'coordinator_analyze_intent',
            user_input=user_input,
            current_step=state['current_step']
        )

        intent = self.llm.generate(prompt).strip().upper()

        # Update state based on intent
        if intent == "APPROVE":
            state['plan_approved'] = True
        elif intent == "MODIFY":
            state['plan_approved'] = False
            # Plan will be revised by Planner
        elif intent == "REJECT":
            state['plan_approved'] = False
            state['research_plan'] = None
        # For QUESTION, we keep state as is and let Planner handle it

        return state

    def delegate_to_planner(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delegate the task to Planner.

        Args:
            state: Current research state

        Returns:
            Updated research state with delegation info
        """
        state['current_step'] = 'planning'
        return state

    def handle_completion(self, state: Dict[str, Any]) -> Dict:
        """
        Handle workflow completion.

        Args:
            state: Final research state

        Returns:
            Completion summary
        """
        return {
            'status': 'completed',
            'query': state['query'],
            'iterations': state['iteration_count'],
            'report': state['final_report'],
            'total_results': len(state['research_results'])
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"Coordinator(llm={self.llm})"
