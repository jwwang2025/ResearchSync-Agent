"""
RAG检索器

该模块实现检索增强生成的核心逻辑，负责：
- 从向量数据库检索相关文档
- 构建上下文信息
- 调用LLM生成增强回答
"""

from typing import List, Dict, Any, Optional
import logging
from .vector_store import VectorStoreManager
from ..llm.base import BaseLLM

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    RAG检索器

    结合向量检索和LLM生成能力，提供检索增强的回答生成。
    """

    def __init__(
        self,
        vector_store: VectorStoreManager,
        llm: BaseLLM,
        similarity_threshold: float = 0.7,
        max_context_length: int = 4000
    ):
        """
        初始化RAG检索器

        参数:
            vector_store: 向量存储管理器实例
            llm: 大语言模型实例
            similarity_threshold: 相似度阈值（0-1之间）
            max_context_length: 最大上下文长度
        """
        self.vector_store = vector_store
        self.llm = llm
        self.similarity_threshold = similarity_threshold
        self.max_context_length = max_context_length

    def retrieve_and_generate(
        self,
        query: str,
        context_docs: Optional[List[str]] = None,
        collection_name: str = "research_kb",
        top_k: int = 5,
        temperature: float = 0.3,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        检索相关文档并生成增强回答

        参数:
            query: 用户查询
            context_docs: 可选的额外上下文文档
            collection_name: 知识库集合名称
            top_k: 检索的文档数量
            temperature: LLM生成温度
            custom_prompt: 自定义提示词模板

        返回:
            包含检索结果和生成回答的字典
        """
        try:
            # 检索相关文档
            retrieved_docs = self._retrieve_documents(query, collection_name, top_k)

            # 过滤低质量结果
            filtered_docs = self._filter_by_similarity(retrieved_docs, self.similarity_threshold)

            # 构建增强上下文
            context = self._build_context(filtered_docs, context_docs)

            # 生成回答
            prompt = custom_prompt or self._get_default_prompt(query, context)
            response = self.llm.generate(prompt, temperature=temperature)

            return {
                'query': query,
                'retrieved_documents': filtered_docs,
                'generated_response': response,
                'context_used': bool(filtered_docs or context_docs),
                'collection_name': collection_name,
                'total_retrieved': len(retrieved_docs),
                'filtered_count': len(filtered_docs)
            }

        except Exception as e:
            logger.error(f"RAG retrieval and generation failed: {str(e)}")
            return {
                'query': query,
                'retrieved_documents': [],
                'generated_response': f"检索增强生成过程中出现错误: {str(e)}",
                'context_used': False,
                'error': str(e)
            }

    def retrieve_only(
        self,
        query: str,
        collection_name: str = "research_kb",
        top_k: int = 5,
        include_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """
        仅执行检索操作，不进行生成

        参数:
            query: 搜索查询
            collection_name: 集合名称
            top_k: 返回结果数量
            include_scores: 是否包含相似度分数

        返回:
            检索到的文档列表
        """
        retrieved_docs = self._retrieve_documents(query, collection_name, top_k)

        if not include_scores:
            # 移除分数信息
            for doc in retrieved_docs:
                doc.pop('score', None)

        return retrieved_docs

    def _retrieve_documents(
        self,
        query: str,
        collection_name: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        从向量数据库检索相关文档

        参数:
            query: 搜索查询
            collection_name: 集合名称
            top_k: 返回结果数量

        返回:
            检索到的文档列表
        """
        search_results = self.vector_store.similarity_search(
            query=query,
            n_results=top_k,
            collection_name=collection_name
        )

        retrieved_docs = []
        if search_results.get('documents') and search_results['documents'][0]:
            for i, doc in enumerate(search_results['documents'][0]):
                metadata = search_results['metadatas'][0][i] if search_results.get('metadatas') else {}
                distance = search_results['distances'][0][i] if search_results.get('distances') else None

                # 将距离转换为相似度分数（ChromaDB返回的是距离，越小越相似）
                score = 1.0 - (distance or 0.0) if distance is not None else None

                retrieved_docs.append({
                    'content': doc,
                    'metadata': metadata,
                    'score': score,
                    'distance': distance,
                    'id': search_results['ids'][0][i] if search_results.get('ids') else None
                })

        return retrieved_docs

    def _filter_by_similarity(
        self,
        documents: List[Dict[str, Any]],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        根据相似度阈值过滤文档

        参数:
            documents: 文档列表
            threshold: 相似度阈值

        返回:
            过滤后的文档列表
        """
        if threshold <= 0:
            return documents

        filtered = []
        for doc in documents:
            score = doc.get('score')
            if score is not None and score >= threshold:
                filtered.append(doc)

        return filtered

    def _build_context(
        self,
        retrieved_docs: List[Dict],
        context_docs: Optional[List[str]] = None
    ) -> str:
        """
        构建上下文字符串

        参数:
            retrieved_docs: 检索到的文档列表
            context_docs: 额外的上下文文档

        返回:
            格式化的上下文字符串
        """
        context_parts = []

        # 添加检索到的文档
        for i, doc in enumerate(retrieved_docs, 1):
            content = doc.get('content', '')[:1000]  # 限制单文档长度
            score = doc.get('score', 0)
            metadata = doc.get('metadata', {})

            context_parts.append(f"[检索文档{i}] (相关度: {score:.3f})")
            if metadata.get('source'):
                context_parts.append(f"来源: {metadata['source']}")
            context_parts.append(f"内容: {content}")
            context_parts.append("")  # 空行分隔

        # 添加额外上下文
        if context_docs:
            for i, doc in enumerate(context_docs, len(retrieved_docs) + 1):
                context_parts.append(f"[额外上下文{i}]")
                context_parts.append(f"内容: {doc[:1000]}")  # 限制长度
                context_parts.append("")

        # 限制总上下文长度
        full_context = "\n".join(context_parts)
        if len(full_context) > self.max_context_length:
            full_context = full_context[:self.max_context_length] + "\n[内容已截断...]"

        return full_context

    def _get_default_prompt(self, query: str, context: str) -> str:
        """
        获取默认的RAG提示词模板

        参数:
            query: 用户查询
            context: 检索到的上下文

        返回:
            完整的提示词
        """
        if context.strip():
            prompt = f"""基于以下检索到的相关信息，回答用户的问题。
如果检索到的信息不足以完全回答问题，请基于现有知识提供帮助，并说明信息来源。

检索到的信息：
{context}

用户问题：{query}

请提供准确、基于事实的回答，并说明答案主要基于哪些信息来源。"""
        else:
            prompt = f"""用户问题：{query}

我没有找到相关的参考信息。请基于您的知识提供帮助。"""

        return prompt

    def search_with_metadata_filter(
        self,
        query: str,
        metadata_filter: Dict[str, Any],
        collection_name: str = "research_kb",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        使用元数据过滤的搜索

        参数:
            query: 搜索查询
            metadata_filter: 元数据过滤条件
            collection_name: 集合名称
            top_k: 返回结果数量

        返回:
            过滤后的搜索结果
        """
        search_results = self.vector_store.similarity_search(
            query=query,
            n_results=top_k,
            collection_name=collection_name,
            where=metadata_filter
        )

        retrieved_docs = []
        if search_results.get('documents') and search_results['documents'][0]:
            for i, doc in enumerate(search_results['documents'][0]):
                metadata = search_results['metadatas'][0][i] if search_results.get('metadatas') else {}
                distance = search_results['distances'][0][i] if search_results.get('distances') else None
                score = 1.0 - (distance or 0.0) if distance is not None else None

                retrieved_docs.append({
                    'content': doc,
                    'metadata': metadata,
                    'score': score,
                    'distance': distance
                })

        return retrieved_docs
