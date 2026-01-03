"""
Tavily 搜索工具

该模块提供基于 Tavily API 的网页搜索功能。
"""

from typing import List, Dict, Optional
from tavily import TavilyClient
from datetime import datetime


class TavilySearch:
    """
    用于网页信息检索的 Tavily 搜索工具。
    """

    def __init__(self, api_key: str):
        """
        初始化 Tavily 搜索工具。

        参数:
            api_key: Tavily API 密钥
        """
        self.client = TavilyClient(api_key=api_key)

    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> Dict:
        """
        使用 Tavily 执行网页搜索。

        参数:
            query: 搜索关键词
            max_results: 要返回的最大结果数量（默认5条）
            search_depth: 搜索深度（可选值："basic" 基础搜索 / "advanced" 高级搜索）
            include_domains: 需纳入搜索范围的域名列表（可选）
            exclude_domains: 需排除在搜索范围外的域名列表（可选）

        返回:
            包含搜索结果的字典，结构如下：
            - query: 搜索关键词
            - source: 数据源（固定为'tavily'）
            - results: 搜索结果列表，每个结果包含标题、URL、摘要等信息
            - timestamp: 搜索时间戳（ISO格式）
            - total_results: 实际返回的结果数量
        """
        # 执行搜索
        response = self.client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_domains=include_domains,
            exclude_domains=exclude_domains
        )

        # 格式化结果
        results = []
        for item in response.get('results', []):
            results.append({
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'snippet': item.get('content', ''),
                'relevance_score': item.get('score', 0.0),
                'metadata': {
                    'published_date': item.get('published_date'),
                    'raw_content': item.get('raw_content')
                }
            })

        return {
            'query': query,
            'source': 'tavily',
            'results': results,
            'timestamp': datetime.now().isoformat(),
            'total_results': len(results)
        }

    def get_search_context(
        self,
        query: str,
        max_results: int = 5
    ) -> str:
        """
        获取格式化文本形式的搜索上下文（整合后的搜索结果）。

        参数:
            query: 搜索关键词
            max_results: 用于生成上下文的最大结果数量（默认5条）

        返回:
            格式化的搜索上下文字符串（整合了关键信息的纯文本）
        """
        context = self.client.get_search_context(
            query=query,
            max_results=max_results
        )
        return context
