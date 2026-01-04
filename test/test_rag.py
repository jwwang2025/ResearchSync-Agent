"""
RAG功能测试

测试RAG组件的基本功能，包括：
- 向量存储管理
- 文档加载和处理
- 检索和生成
- API端点测试
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# RAG组件导入
from backend.rag.vector_store import VectorStoreManager
from backend.rag.retriever import RAGRetriever
from backend.rag.knowledge_manager import KnowledgeManager


class TestVectorStoreManager:
    """测试向量存储管理器"""

    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = VectorStoreManager(persist_directory=self.temp_dir)

    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """测试初始化"""
        assert self.manager.client is not None
        assert self.manager.embedding_model is not None
        assert self.manager.text_splitter is not None

    def test_add_documents(self):
        """测试添加文档"""
        from langchain.docstore.document import Document

        docs = [
            Document(page_content="RAG是一种检索增强生成技术", metadata={"source": "test"}),
            Document(page_content="向量数据库用于存储文档嵌入", metadata={"source": "test"}),
        ]

        chunks_loaded = self.manager.add_documents(docs, "test_collection")
        assert chunks_loaded == 2  # 应该生成了2个文档块

    def test_similarity_search(self):
        """测试相似度搜索"""
        from langchain.docstore.document import Document

        # 添加测试文档
        docs = [
            Document(page_content="机器学习是人工智能的重要分支", metadata={"source": "test"}),
            Document(page_content="深度学习使用神经网络", metadata={"source": "test"}),
        ]
        self.manager.add_documents(docs, "test_collection")

        # 执行搜索
        results = self.manager.similarity_search("什么是机器学习", n_results=2, collection_name="test_collection")

        assert 'documents' in results
        assert 'metadatas' in results
        assert len(results['documents'][0]) > 0

    def test_collection_management(self):
        """测试集合管理"""
        # 列出集合
        collections = self.manager.list_collections()
        assert isinstance(collections, list)

        # 获取集合统计
        stats = self.manager.get_collection_stats("nonexistent")
        assert stats['exists'] is False
        assert stats['document_count'] == 0


class TestRAGRetriever:
    """测试RAG检索器"""

    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.vector_store = VectorStoreManager(persist_directory=self.temp_dir)

        # Mock LLM
        self.mock_llm = Mock()
        self.mock_llm.generate.return_value = "这是一个基于RAG的回答"

        self.retriever = RAGRetriever(self.vector_store, self.mock_llm)

    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """测试初始化"""
        assert self.retriever.vector_store is not None
        assert self.retriever.llm is not None
        assert self.retriever.similarity_threshold == 0.7

    def test_retrieve_only(self):
        """测试仅检索功能"""
        from langchain.docstore.document import Document

        # 添加测试文档
        docs = [
            Document(page_content="Python是一种编程语言", metadata={"source": "test"}),
        ]
        self.vector_store.add_documents(docs, "test_collection")

        # 执行检索
        results = self.retriever.retrieve_only("Python是什么", collection_name="test_collection")

        assert isinstance(results, list)
        assert len(results) > 0
        assert 'content' in results[0]
        assert 'score' in results[0]

    @patch('backend.rag.retriever.RAGRetriever._retrieve_documents')
    def test_retrieve_and_generate(self, mock_retrieve):
        """测试检索和生成功能"""
        # Mock检索结果
        mock_retrieve.return_value = [
            {
                'content': '测试文档内容',
                'metadata': {'source': 'test'},
                'score': 0.9
            }
        ]

        result = self.retriever.retrieve_and_generate("测试查询")

        assert 'query' in result
        assert 'generated_response' in result
        assert 'retrieved_documents' in result
        assert 'context_used' in result

        # 验证LLM被调用
        self.mock_llm.generate.assert_called_once()


class TestKnowledgeManager:
    """测试知识库管理器"""

    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.vector_store = VectorStoreManager(persist_directory=self.temp_dir)
        self.manager = KnowledgeManager(self.vector_store)

    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """测试初始化"""
        assert self.manager.vector_store is not None

    def test_load_from_file_text(self):
        """测试加载文本文件"""
        # 创建临时文本文件
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("这是一个测试文档\n包含多行内容")

        result = self.manager.load_from_file(test_file, "test_collection")

        assert result['success'] is True
        assert result['chunks_loaded'] > 0
        assert result['file_type'] == 'text'

    def test_load_from_directory(self):
        """测试批量加载目录"""
        # 创建测试文件
        test_dir = os.path.join(self.temp_dir, "test_docs")
        os.makedirs(test_dir)

        with open(os.path.join(test_dir, "doc1.txt"), "w", encoding="utf-8") as f:
            f.write("文档1内容")
        with open(os.path.join(test_dir, "doc2.txt"), "w", encoding="utf-8") as f:
            f.write("文档2内容")

        result = self.manager.load_from_directory(test_dir, "test_collection")

        assert result['success'] is True
        assert result['loaded_files'] == 2
        assert result['total_chunks'] > 0

    def test_get_collection_stats(self):
        """测试获取集合统计"""
        stats = self.manager.get_collection_stats("nonexistent")
        assert stats['exists'] is False
        assert stats['document_count'] == 0


class TestIntegration:
    """集成测试"""

    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_rag_pipeline(self):
        """测试完整的RAG流程"""
        from langchain.docstore.document import Document

        # 初始化组件
        vector_store = VectorStoreManager(persist_directory=self.temp_dir)
        mock_llm = Mock()
        mock_llm.generate.return_value = "基于提供的文档，回答用户的问题"
        retriever = RAGRetriever(vector_store, mock_llm)
        knowledge_manager = KnowledgeManager(vector_store)

        # 1. 添加文档到知识库
        docs = [
            Document(page_content="人工智能是计算机科学的一个分支", metadata={"source": "test"}),
            Document(page_content="机器学习是AI的重要方法", metadata={"source": "test"}),
        ]
        chunks_loaded = vector_store.add_documents(docs, "test_kb")
        assert chunks_loaded == 2

        # 2. 执行RAG查询
        result = retriever.retrieve_and_generate(
            "什么是人工智能？",
            collection_name="test_kb"
        )

        # 3. 验证结果
        assert result['query'] == "什么是人工智能？"
        assert 'generated_response' in result
        assert result['context_used'] is True
        assert len(result['retrieved_documents']) > 0

        # 4. 验证知识库统计
        stats = knowledge_manager.get_collection_stats("test_kb")
        assert stats['exists'] is True
        assert stats['document_count'] >= 2


# API测试
class TestRAGAPI:
    """RAG API测试"""

    def test_api_health_check(self):
        """测试API健康检查"""
        # 这里可以添加实际的API测试
        # 需要启动测试服务器
        pass

    def test_knowledge_upload(self):
        """测试知识上传API"""
        # 这里可以添加文件上传测试
        pass

    def test_rag_query(self):
        """测试RAG查询API"""
        # 这里可以添加查询测试
        pass


if __name__ == "__main__":
    # 运行基本测试
    print("Running RAG tests...")

    # 测试向量存储
    test_store = TestVectorStoreManager()
    test_store.setup_method()
    test_store.test_initialization()
    test_store.test_add_documents()
    test_store.teardown_method()
    print("✓ VectorStore tests passed")

    # 测试检索器
    test_retriever = TestRAGRetriever()
    test_retriever.setup_method()
    test_retriever.test_initialization()
    test_retriever.teardown_method()
    print("✓ RAGRetriever tests passed")

    # 测试知识管理器
    test_manager = TestKnowledgeManager()
    test_manager.setup_method()
    test_manager.test_initialization()
    test_manager.teardown_method()
    print("✓ KnowledgeManager tests passed")

    print("All basic tests passed!")
