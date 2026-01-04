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

# RAG相关导入（可选）
try:
    from ..rag.retriever import RAGRetriever
    from ..rag.vector_store import VectorStoreManager
    from ..rag.knowledge_manager import KnowledgeManager
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


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
        mcp_api_key: Optional[str] = None,
        enable_rag: bool = True,
        rag_vector_store_path: str = "./data/chroma_db",
        rag_collection_name: str = "research_kb"
    ):
        """
        初始化研究者智能体

        参数:
            llm: 用于数据处理的大语言模型实例
            tavily_api_key: Tavily API 密钥（可选）
            mcp_server_url: MCP 服务器地址（可选）
            mcp_api_key: MCP API 密钥（可选）
            enable_rag: 是否启用RAG功能
            rag_vector_store_path: RAG向量存储路径
            rag_collection_name: RAG知识库集合名称
        """
        self.llm = llm
        self.tavily = TavilySearch(tavily_api_key) if tavily_api_key else None
        self.arxiv = ArxivSearch()
        self.mcp = MCPClient(mcp_server_url, mcp_api_key) if mcp_server_url else None
        self.prompt_loader = PromptLoader()

        # RAG相关组件
        self.enable_rag = enable_rag and RAG_AVAILABLE
        self.rag_collection_name = rag_collection_name

        if self.enable_rag:
            try:
                self.vector_store = VectorStoreManager(rag_vector_store_path)
                self.rag_retriever = RAGRetriever(self.vector_store, llm)
                self.knowledge_manager = KnowledgeManager(self.vector_store)
            except Exception as e:
                print(f"Warning: Failed to initialize RAG components: {e}")
                self.enable_rag = False
        else:
            self.vector_store = None
            self.rag_retriever = None
            self.knowledge_manager = None

    def execute_task(self, state: ResearchState, task: SubTask) -> ResearchState:
        """
        执行研究任务（支持RAG增强）

        参数:
            state: 当前的研究状态
            task: 待执行的子任务

        返回:
            包含研究结果的更新后状态
        """
        results = []

        # 为每个检索语句执行检索操作
        for query in task.get('search_queries', []):
            # 首先尝试RAG检索（如果启用且有知识库）
            if self.enable_rag and self._has_rag_knowledge():
                rag_result = self._rag_search(query, task)
                if rag_result:
                    results.append(rag_result)

            # 然后执行传统搜索
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

    def _rag_search(self, query: str, task: SubTask) -> Optional[SearchResult]:
        """
        执行RAG增强搜索

        参数:
            query: 搜索查询
            task: 任务信息

        返回:
            RAG检索结果
        """
        if not self.enable_rag or not self.rag_retriever:
            return None

        try:
            # 执行RAG检索和生成
            rag_response = self.rag_retriever.retrieve_and_generate(
                query=query,
                collection_name=self.rag_collection_name,
                top_k=5,
                temperature=0.3
            )

            return {
                'query': query,
                'source': 'rag',
                'task_id': task['task_id'],
                'results': [{
                    'title': f"RAG检索结果 - {query}",
                    'snippet': rag_response['generated_response'][:500] + "..." if len(rag_response['generated_response']) > 500 else rag_response['generated_response'],
                    'url': 'internal://rag',
                    'content': rag_response['generated_response'],
                    'relevance_score': rag_response.get('retrieved_documents', [{}])[0].get('score') if rag_response.get('retrieved_documents') else None,
                    'metadata': {
                        'retrieved_docs_count': len(rag_response.get('retrieved_documents', [])),
                        'context_used': rag_response.get('context_used', False),
                        'total_retrieved': rag_response.get('total_retrieved', 0),
                        'filtered_count': rag_response.get('filtered_count', 0)
                    }
                }],
                'rag_metadata': {
                    'retrieved_documents': rag_response.get('retrieved_documents', []),
                    'context_used': rag_response.get('context_used', False)
                },
                'timestamp': rag_response.get('timestamp', None)
            }

        except Exception as e:
            print(f"RAG search failed for query '{query}': {str(e)}")
            return {
                'query': query,
                'source': 'rag',
                'task_id': task['task_id'],
                'results': [],
                'error': f"RAG search failed: {str(e)}"
            }

    def _has_rag_knowledge(self) -> bool:
        """
        检查是否有可用的RAG知识库

        返回:
            是否有知识库可用
        """
        if not self.enable_rag or not self.knowledge_manager:
            return False

        try:
            stats = self.knowledge_manager.get_collection_stats(self.rag_collection_name)
            return stats.get('exists', False) and stats.get('document_count', 0) > 0
        except Exception:
            return False

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
        if self.enable_rag:
            sources.append('rag')

        rag_status = "enabled" if self.enable_rag else "disabled"
        return f"Researcher(sources={sources}, rag={rag_status})"
