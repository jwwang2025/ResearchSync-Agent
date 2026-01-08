"""
向量存储管理器

该模块负责管理向量数据库的存储、检索和维护操作。
支持ChromaDB向量数据库，提供文档向量化存储和相似度搜索功能。
"""

from typing import List, Dict, Any, Optional
import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class VectorStoreManager:
    """
    向量存储管理器

    负责文档的向量化存储、检索和管理操作。
    使用ChromaDB作为向量数据库，sentence-transformers进行嵌入编码。
    """

    def __init__(
        self,
        persist_directory: str = "./data/chroma_db",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        初始化向量存储管理器

        参数:
            persist_directory: 向量数据库持久化存储目录
            embedding_model_name: 嵌入模型名称
            chunk_size: 文档分割块大小
            chunk_overlap: 文档分割重叠大小
        """
        # 确保目录存在
        os.makedirs(persist_directory, exist_ok=True)

        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(path=persist_directory)

        # 初始化嵌入模型
        self.embedding_model = SentenceTransformer(embedding_model_name)

        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        # 缓存已创建的集合
        self._collections_cache = {}

    def add_documents(
        self,
        documents: List[Document],
        collection_name: str = "research_kb",
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        添加文档到向量数据库

        参数:
            documents: LangChain Document对象列表
            collection_name: 集合名称
            metadata: 额外的元数据

        返回:
            添加的文档块数量
        """
        if not documents:
            return 0

        # 获取或创建集合
        collection = self._get_or_create_collection(collection_name)

        # 分割文档
        split_docs = self.text_splitter.split_documents(documents)

        if not split_docs:
            return 0

        # 准备数据
        texts = [doc.page_content for doc in split_docs]
        embeddings = self.embedding_model.encode(texts).tolist()

        # 合并元数据
        metadatas = []
        for doc in split_docs:
            doc_metadata = doc.metadata.copy() if doc.metadata else {}
            if metadata:
                doc_metadata.update(metadata)
            # 确保元数据值是字符串类型（ChromaDB要求）
            doc_metadata = {k: str(v) for k, v in doc_metadata.items()}
            metadatas.append(doc_metadata)

        # 生成唯一ID
        ids = [f"{collection_name}_doc_{i}_{hash(text[:100])}" for i, text in enumerate(texts)]

        # 添加到集合
        collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

        return len(split_docs)

    def similarity_search(
        self,
        query: str,
        n_results: int = 5,
        collection_name: str = "research_kb",
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        执行相似度搜索

        参数:
            query: 搜索查询
            n_results: 返回结果数量
            collection_name: 集合名称
            where: 元数据过滤条件
            where_document: 文档内容过滤条件

        返回:
            包含搜索结果的字典
        """
        collection = self.client.get_collection(name=collection_name)

        # 生成查询嵌入
        query_embedding = self.embedding_model.encode([query]).tolist()[0]

        # 执行搜索
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document
        )

        return results

    def delete_collection(self, collection_name: str) -> bool:
        """
        删除集合

        参数:
            collection_name: 要删除的集合名称

        返回:
            删除是否成功
        """
        self.client.delete_collection(name=collection_name)
        if collection_name in self._collections_cache:
            del self._collections_cache[collection_name]
        return True

    def list_collections(self) -> List[str]:
        """
        列出所有集合

        返回:
            集合名称列表
        """
        collections = self.client.list_collections()
        return [col.name for col in collections]

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        获取集合统计信息

        参数:
            collection_name: 集合名称

        返回:
            包含统计信息的字典
        """
        collection = self.client.get_collection(name=collection_name)
        count = collection.count()

        return {
            'collection_name': collection_name,
            'document_count': count,
            'exists': True,
            'status': 'active'
        }

    def _get_or_create_collection(self, collection_name: str):
        """
        获取或创建集合

        参数:
            collection_name: 集合名称

        返回:
            ChromaDB集合对象
        """
        if collection_name not in self._collections_cache:
            self._collections_cache[collection_name] = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": f"Research knowledge base: {collection_name}"}
            )

        return self._collections_cache[collection_name]

    def clear_collection(self, collection_name: str) -> bool:
        """
        清空集合内容（保留集合结构）

        参数:
            collection_name: 集合名称

        返回:
            清空是否成功
        """
        collection = self.client.get_collection(name=collection_name)
        # 获取所有文档ID
        all_ids = collection.get()['ids']
        if all_ids:
            collection.delete(ids=all_ids)
        return True
