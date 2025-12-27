"""
研究工作流状态定义

该模块定义了研究工作流的状态结构。
"""

from typing import TypedDict, List, Annotated, Optional, Any
import operator


# 定义带有 Annotated 字段的状态类，供 LangGraph 使用
class ResearchState(TypedDict):
    """
    用于 LangGraph 的研究工作流状态。

    该状态会在工作流的所有节点之间传递。
    """
    query: str
    research_plan: Optional[dict]
    plan_approved: bool
    research_results: Annotated[list, operator.add]  # 研究结果（累加型字段）
    current_task: Optional[dict]
    iteration_count: int
    max_iterations: int
    final_report: Optional[str]
    current_step: str
    needs_more_research: bool
    user_feedback: Optional[str]
    output_format: str  # 输出格式（支持 "markdown" 或 "html"）


class PlanStructure(TypedDict):
    """
    研究计划的数据结构。
    """
    research_goal: str  # 整体研究目标
    sub_tasks: List[dict]  # 子任务列表
    completion_criteria: str  # 完成判定标准
    estimated_iterations: int  # 预估需要的迭代次数


class SubTask(TypedDict):
    """
    研究子任务的数据结构
    """
    task_id: int  # 唯一任务 ID
    description: str  # 任务描述
    search_queries: List[str]  # 搜索查询语句列表
    sources: List[str]  # 要使用的数据源（可选值：tavily、arxiv、mcp）
    status: str  # 任务状态（可选值：pending(待执行)、in_progress(执行中)、completed(已完成)）
    priority: Optional[int]  # 任务优先级（可选）


class SearchResult(TypedDict):
    """
    搜索结果的数据结构。
    """
    task_id: int  # 关联的任务ID
    query: str  # 搜索查询语句
    source: str  # 数据源（可选值：tavily、arxiv、mcp）
    results: List[dict]  # 单个搜索结果的集合
    timestamp: str  # 搜索时间戳


class IndividualResult(TypedDict):
    """
    单个搜索结果的数据结构。
    """
    title: str  # 结果标题
    url: Optional[str]  # 结果URL（仅在适用场景下提供）
    snippet: str  # 结果摘要/文本片段
    relevance_score: Optional[float]  # 相关性评分（可选）
    metadata: Optional[dict]  # 附加元数据（可选）
