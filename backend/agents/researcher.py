"""
Researcher Agent

该模块实现了研究者智能体（Researcher agent），负责执行信息检索任务。
"""

from typing import Dict, List, Optional
from ..workflow.state import ResearchState, SubTask, SearchResult
from ..tools.tavily_search import TavilySearch
from ..tools.arxiv_search import ArxivSearch
from ..tools.mcp_client import MCPClient
from ..llm.base import BaseLLM
from ..prompts.loader import PromptLoader


class Researcher:
    """
    研究者智能体（Researcher agent） —— 信息收集组件

    职责：
    - 执行信息检索任务
    - 从多个数据源进行检索
    - 筛选并整理检索结果
    - 汇总不同数据源的检索结果
    - 提取相关信息
    """

    def __init__(
        self,
        llm: BaseLLM,
        tavily_api_key: Optional[str] = None,
        mcp_server_url: Optional[str] = None,
        mcp_api_key: Optional[str] = None
    ):
        """
        初始化研究者智能体

        参数:
            llm: 用于数据处理的大语言模型实例
            tavily_api_key: Tavily API 密钥（可选）
            mcp_server_url: MCP 服务器地址（可选）
            mcp_api_key: MCP API 密钥（可选）
        """
        self.llm = llm
        self.tavily = TavilySearch(tavily_api_key) if tavily_api_key else None
        self.arxiv = ArxivSearch()
        self.mcp = MCPClient(mcp_server_url, mcp_api_key) if mcp_server_url else None
        self.prompt_loader = PromptLoader()

    def execute_task(self, state: ResearchState, task: SubTask) -> ResearchState:
        """
        执行研究任务

        参数:
            state: 当前的研究状态
            task: 待执行的子任务

        返回:
            包含研究结果的更新后状态
        """
        results = []

        # 为每个检索语句执行检索操作
        for query in task.get('search_queries', []):
            for source in task.get('sources', []):
                result = self._search(query, source)
                if result:
                    result['task_id'] = task['task_id']
                    results.append(result)

        # 将检索结果添加到状态中
        if 'research_results' not in state:
            state['research_results'] = []

        state['research_results'].extend(results)

        # 将任务标记为已完成
        if state.get('research_plan'):
            for t in state['research_plan'].get('sub_tasks', []):
                if t.get('task_id') == task['task_id']:
                    t['status'] = 'completed'
                    break

        return state

    def _search(self, query: str, source: str) -> Optional[SearchResult]:
        """
        使用指定的数据源执行检索操作

        参数:
            query: 检索语句
            source: 数据源名称（可选值：'tavily'、'arxiv'、'mcp'）

        返回:
            检索结果（无有效结果时返回None）
        """
        try:
            if source == 'tavily' and self.tavily:
                return self.tavily.search(query)
            elif source == 'arxiv':
                return self.arxiv.search(query)
            elif source == 'mcp' and self.mcp:
                import asyncio
                return asyncio.run(self.mcp.search(query))
            else:
                return None
        except Exception as e:
            return {
                'query': query,
                'source': source,
                'results': [],
                'error': str(e)
            }

    def aggregate_results(self, results: List[SearchResult]) -> Dict:
        """
        汇总并整理检索结果

        参数:
            results: 检索结果列表

        返回:
            汇总后的结果摘要
        """
        # 按数据源分组结果
        by_source = {}
        for result in results:
            source = result.get('source', 'unknown')
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(result)

        # 计算统计信息
        total_results = sum(len(r.get('results', [])) for r in results)

        return {
            'total_searches': len(results),
            'total_results': total_results,
            'by_source': {
                source: {
                    'count': len(source_results),
                    'total_items': sum(len(r.get('results', [])) for r in source_results)
                }
                for source, source_results in by_source.items()
            }
        }

    def extract_relevant_info(self, state: ResearchState) -> str:
        """
        从所有研究结果中提取相关信息

        参数:
            state: 当前的研究状态

        返回:
            提取并汇总后的信息
        """
        results = state.get('research_results', [])

        if not results:
            return "No research results available."

        # 编译所有检索结果
        all_items = []
        for result in results:
            for item in result.get('results', []):
                all_items.append({
                    'source': result.get('source'),
                    'query': result.get('query'),
                    'title': item.get('title'),
                    'snippet': item.get('snippet'),
                    'url': item.get('url')
                })

        # 使用大语言模型进行信息提取和汇总
        prompt = self.prompt_loader.load(
            'researcher_extract_info',
            query=state['query'],
            search_results=self._format_results_for_prompt(all_items[:20])  # Limit to top 20 results
        )

        summary = self.llm.generate(prompt, temperature=0.5)
        return summary

    def _format_results_for_prompt(self, items: List[Dict]) -> str:
        """
        格式化检索结果，用于构建大语言模型提示词

        参数:
            items: 检索结果条目列表

        返回:
            格式化后的字符串
        """
        formatted = []
        for i, item in enumerate(items, 1):
            formatted.append(f"\n{i}. [{item.get('source')}] {item.get('title', 'No title')}")
            formatted.append(f"   URL: {item.get('url', 'N/A')}")
            formatted.append(f"   {item.get('snippet', 'No snippet')[:200]}...")

        return '\n'.join(formatted)

    def __repr__(self) -> str:
        """类的字符串表示形式"""
        sources = []
        if self.tavily:
            sources.append('tavily')
        if self.arxiv:
            sources.append('arxiv')
        if self.mcp:
            sources.append('mcp')
        return f"Researcher(sources={sources})"
