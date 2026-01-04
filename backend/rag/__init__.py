"""
RAG (Retrieval-Augmented Generation) 模块

该模块提供完整的RAG功能实现，包括：
- 向量存储管理
- 文档检索和生成
- 知识库管理
- RAG增强的研究能力

主要组件：
- VectorStoreManager: 向量存储管理器
- RAGRetriever: RAG检索器
- KnowledgeManager: 知识库管理器
"""

from .vector_store import VectorStoreManager
from .retriever import RAGRetriever
from .knowledge_manager import KnowledgeManager

__all__ = [
    'VectorStoreManager',
    'RAGRetriever',
    'KnowledgeManager'
]
