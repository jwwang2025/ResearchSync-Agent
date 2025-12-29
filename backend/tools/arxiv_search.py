"""
arXiv 学术论文搜索工具

该模块提供基于 arXiv API 的学术论文检索功能。
"""

from typing import List, Dict, Optional
import arxiv
from datetime import datetime


class ArxivSearch:
    """
    用于学术论文检索的 arXiv 搜索工具。
    """

    def __init__(self):
        """
        初始化 arXiv 搜索工具.
        """
        self.client = arxiv.Client()

    def search(
        self,
        query: str,
        max_results: int = 5,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.Relevance,
        sort_order: arxiv.SortOrder = arxiv.SortOrder.Descending
    ) -> Dict:
        """
        在 arXiv 平台检索学术论文。

        参数:
            query: 搜索关键词
            max_results: 要返回的最大结果数量（默认5条）
            sort_by: 排序依据（可选值：Relevance 相关度、LastUpdatedDate 最后更新日期、SubmittedDate 提交日期）
            sort_order: 排序顺序（可选值：Ascending 升序、Descending 降序）

        返回:
            包含搜索结果的字典
        """
        try:
            # 创建搜索对象
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=sort_by,
                sort_order=sort_order
            )

            # 执行检索
            results = []
            for paper in self.client.results(search):
                results.append({
                    'title': paper.title,
                    'url': paper.entry_id,
                    'snippet': paper.summary,
                    'relevance_score': None,  # arXiv doesn't provide relevance scores
                    'metadata': {
                        'authors': [author.name for author in paper.authors],
                        'published': paper.published.isoformat() if paper.published else None,
                        'updated': paper.updated.isoformat() if paper.updated else None,
                        'categories': paper.categories,
                        'primary_category': paper.primary_category,
                        'pdf_url': paper.pdf_url,
                        'doi': paper.doi,
                        'journal_ref': paper.journal_ref,
                        'comment': paper.comment
                    }
                })

            return {
                'query': query,
                'source': 'arxiv',
                'results': results,
                'timestamp': datetime.now().isoformat(),
                'total_results': len(results)
            }

        except Exception as e:
            # 未知错误仍返回空结果并携带错误信息
            return {
                'query': query,
                'source': 'arxiv',
                'results': [],
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    def get_paper_by_id(self, paper_id: str) -> Optional[Dict]:
        """
        根据 arXiv 论文ID获取指定论文的详细信息。

        参数:
            paper_id: arXiv 论文ID（示例："2301.07041"）

        返回:
            论文详细信息字典；若未找到对应论文则返回 None
        """
        try:
            search = arxiv.Search(id_list=[paper_id])
            paper = next(self.client.results(search))

            return {
                'title': paper.title,
                'url': paper.entry_id,
                'summary': paper.summary,
                'authors': [author.name for author in paper.authors],
                'published': paper.published.isoformat() if paper.published else None,
                'pdf_url': paper.pdf_url,
                'categories': paper.categories
            }
        except (StopIteration, arxiv.exceptions.ArxivError):
            # 未找到或 arXiv 客户端错误
            return None

    def download_pdf(self, paper_id: str, dirpath: str = "./") -> Optional[str]:
        """
        下载指定论文的 PDF 文件。

        参数:
            paper_id: arXiv 论文ID
            dirpath: PDF 文件保存目录（默认值：当前目录 "./"）

        返回:
            下载后的 PDF 文件路径；若下载失败则返回 None
        """
        try:
            search = arxiv.Search(id_list=[paper_id])
            paper = next(self.client.results(search))
            filepath = paper.download_pdf(dirpath=dirpath)
            return filepath
        except (StopIteration, arxiv.exceptions.ArxivError):
            return None
