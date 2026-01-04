# RAG集成说明

## 项目RAG集成状态

### 当前状态：❌ 未集成

ResearchSync-Agent项目目前**未集成RAG（Retrieval-Augmented Generation）技术**。当前的信息检索方式主要依赖外部搜索工具（Tavily、ArXiv、MCP客户端）进行实时搜索，没有本地知识库和向量检索能力。

### 当前检索机制

- **Tavily Search**: 通用网页搜索
- **ArXiv Search**: 学术论文搜索
- **MCP Client**: 模型上下文协议客户端，支持扩展工具
- **检索方式**: 实时API调用，无本地缓存和向量化存储

## RAG技术概述

RAG（Retrieval-Augmented Generation）是一种将检索与生成相结合的AI技术，通过以下步骤工作：

1. **文档处理**: 将文档分割成块并向量化存储
2. **检索**: 根据用户查询检索相关文档片段
3. **增强生成**: 将检索到的信息作为上下文提供给LLM生成答案

### RAG的优势

- **知识更新**: 可以实时更新知识库，无需重新训练模型
- **可解释性**: 生成的答案基于可检索的文档片段
- **成本效益**: 比完全微调模型更经济
- **准确性**: 减少幻觉，提高事实准确性

## 集成方案设计

### 架构设计

```
ResearchSync-Agent with RAG
├── Knowledge Base Layer (新增)
│   ├── Document Loader        # 文档加载器
│   ├── Text Splitter         # 文本分割器
│   ├── Embedding Model       # 嵌入模型
│   └── Vector Database       # 向量数据库
├── Enhanced Researcher Agent (增强)
│   ├── RAG Retriever         # RAG检索器
│   ├── Hybrid Search         # 混合搜索
│   └── Context Augmentation  # 上下文增强
└── API Extensions (扩展)
    ├── Knowledge Management  # 知识库管理API
    └── RAG Configuration     # RAG配置API
```

### 核心组件

#### 1. 向量数据库选择

推荐使用以下向量数据库之一：

**ChromaDB** (推荐用于开发/小型部署)
- 轻量级，易于集成
- 支持本地部署
- Python原生支持

**Pinecone**
- 云原生向量数据库
- 高性能，适合生产环境
- 支持元数据过滤

**Weaviate**
- 开源向量数据库
- 支持混合搜索
- GraphQL API

#### 2. 嵌入模型选择

**OpenAI Embeddings**
- `text-embedding-3-small` (推荐)
- `text-embedding-3-large` (高质量)

**开源替代方案**
- `sentence-transformers/all-MiniLM-L6-v2`
- `sentence-transformers/all-mpnet-base-v2`
- `BAAI/bge-large-zh-v1.5` (中文支持)

#### 3. 文档处理组件

**LangChain Document Loaders**
- WebBaseLoader: 网页加载
- PyPDFLoader: PDF文档
- DirectoryLoader: 目录批量加载
- TextLoader: 纯文本文件

**Text Splitters**
- RecursiveCharacterTextSplitter
- CharacterTextSplitter
- MarkdownHeaderTextSplitter

### 集成步骤

#### 阶段1: 依赖安装

更新 `requirements.txt`:

```txt
# 向量数据库
chromadb>=0.4.0
# 或 pinecone-client>=2.2.0
# 或 weaviate-client>=3.25.0

# 嵌入模型
sentence-transformers>=2.2.0
# 或 openai>=1.0.0 (如果使用OpenAI embeddings)

# 文档处理
langchain-community>=0.0.20
pypdf>=3.0.0
beautifulsoup4>=4.12.0
unstructured>=0.10.0

# 其他工具
faiss-cpu>=1.7.0  # 可选，用于本地向量搜索
```

#### 阶段2: 创建RAG核心模块

##### 2.1 向量存储管理器 (`backend/rag/vector_store.py`)

```python
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

class VectorStoreManager:
    """向量存储管理器"""

    def __init__(self, persist_directory: str = "./data/chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    def add_documents(self, documents: List[Document], collection_name: str = "research_kb"):
        """添加文档到向量数据库"""
        collection = self.client.get_or_create_collection(name=collection_name)

        texts = [doc.page_content for doc in documents]
        embeddings = self.embedding_model.encode(texts).tolist()

        metadatas = [doc.metadata for doc in documents]
        ids = [f"doc_{i}" for i in range(len(documents))]

        collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

    def similarity_search(self, query: str, n_results: int = 5, collection_name: str = "research_kb"):
        """相似度搜索"""
        collection = self.client.get_collection(name=collection_name)
        query_embedding = self.embedding_model.encode([query]).tolist()[0]

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return results
```

##### 2.2 RAG检索器 (`backend/rag/retriever.py`)

```python
from typing import List, Dict, Any, Optional
from .vector_store import VectorStoreManager
from ..llm.base import BaseLLM

class RAGRetriever:
    """RAG检索器"""

    def __init__(self, vector_store: VectorStoreManager, llm: BaseLLM):
        self.vector_store = vector_store
        self.llm = llm

    def retrieve_and_generate(self, query: str, context_docs: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        检索相关文档并生成增强回答

        Args:
            query: 用户查询
            context_docs: 可选的额外上下文文档

        Returns:
            包含检索结果和生成回答的字典
        """
        # 检索相关文档
        search_results = self.vector_store.similarity_search(query, n_results=5)

        retrieved_docs = []
        if search_results['documents']:
            for i, doc in enumerate(search_results['documents'][0]):
                metadata = search_results['metadatas'][0][i] if search_results['metadatas'] else {}
                retrieved_docs.append({
                    'content': doc,
                    'metadata': metadata,
                    'score': search_results['distances'][0][i] if search_results['distances'] else None
                })

        # 构建增强上下文
        context = self._build_context(retrieved_docs, context_docs)

        # 生成回答
        prompt = f"""基于以下检索到的相关信息，回答用户的问题。
如果信息不足，请说明无法完全回答。

检索到的信息：
{context}

用户问题：{query}

请提供准确、基于事实的回答："""

        response = self.llm.generate(prompt, temperature=0.3)

        return {
            'query': query,
            'retrieved_documents': retrieved_docs,
            'generated_response': response,
            'context_used': bool(retrieved_docs)
        }

    def _build_context(self, retrieved_docs: List[Dict], context_docs: Optional[List[str]] = None) -> str:
        """构建上下文字符串"""
        context_parts = []

        # 添加检索到的文档
        for i, doc in enumerate(retrieved_docs, 1):
            context_parts.append(f"[文档{i}]\n{doc['content']}\n")

        # 添加额外上下文
        if context_docs:
            for i, doc in enumerate(context_docs, len(retrieved_docs) + 1):
                context_parts.append(f"[额外上下文{i}]\n{doc}\n")

        return "\n".join(context_parts)
```

##### 2.3 知识库管理器 (`backend/rag/knowledge_manager.py`)

```python
from typing import List, Dict, Any
from pathlib import Path
from langchain.document_loaders import (
    WebBaseLoader,
    PyPDFLoader,
    DirectoryLoader,
    TextLoader
)
from langchain.docstore.document import Document
from .vector_store import VectorStoreManager

class KnowledgeManager:
    """知识库管理器"""

    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store

    def load_from_url(self, url: str, collection_name: str = "research_kb") -> int:
        """从URL加载文档"""
        loader = WebBaseLoader(url)
        documents = loader.load()

        # 分割文档
        split_docs = self.vector_store.text_splitter.split_documents(documents)

        # 添加到向量数据库
        self.vector_store.add_documents(split_docs, collection_name)

        return len(split_docs)

    def load_from_pdf(self, pdf_path: str, collection_name: str = "research_kb") -> int:
        """从PDF文件加载文档"""
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        split_docs = self.vector_store.text_splitter.split_documents(documents)
        self.vector_store.add_documents(split_docs, collection_name)

        return len(split_docs)

    def load_from_directory(self, directory_path: str, collection_name: str = "research_kb") -> int:
        """从目录批量加载文档"""
        loader = DirectoryLoader(
            directory_path,
            glob="**/*.txt",
            loader_cls=TextLoader
        )
        documents = loader.load()

        split_docs = self.vector_store.text_splitter.split_documents(documents)
        self.vector_store.add_documents(split_docs, collection_name)

        return len(split_docs)

    def get_collection_stats(self, collection_name: str = "research_kb") -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            collection = self.vector_store.client.get_collection(name=collection_name)
            return {
                'collection_name': collection_name,
                'document_count': collection.count(),
                'exists': True
            }
        except:
            return {
                'collection_name': collection_name,
                'document_count': 0,
                'exists': False
            }
```

#### 阶段3: 增强Researcher Agent

修改 `backend/agents/researcher.py` 以支持RAG：

```python
# 添加RAG相关导入
from ..rag.retriever import RAGRetriever
from ..rag.vector_store import VectorStoreManager
from ..rag.knowledge_manager import KnowledgeManager

class Researcher:
    def __init__(
        self,
        llm: BaseLLM,
        tavily_api_key: Optional[str] = None,
        mcp_server_url: Optional[str] = None,
        mcp_api_key: Optional[str] = None,
        enable_rag: bool = True,
        rag_vector_store_path: str = "./data/chroma_db"
    ):
        # ... 现有初始化代码 ...

        # RAG相关组件
        self.enable_rag = enable_rag
        if enable_rag:
            self.vector_store = VectorStoreManager(rag_vector_store_path)
            self.rag_retriever = RAGRetriever(self.vector_store, llm)
            self.knowledge_manager = KnowledgeManager(self.vector_store)

    def execute_task(self, state: ResearchState, task: SubTask) -> ResearchState:
        """执行研究任务（增强版）"""
        results = []

        # 为每个检索语句执行检索操作
        for query in task.get('search_queries', []):
            # 首先尝试RAG检索（如果启用）
            if self.enable_rag:
                rag_result = self._rag_search(query)
                if rag_result:
                    results.append(rag_result)

            # 然后执行传统搜索
            for source in task.get('sources', []):
                result = self._search(query, source)
                if result:
                    result['task_id'] = task['task_id']
                    results.append(result)

        # ... 其余代码保持不变 ...

    def _rag_search(self, query: str) -> Optional[SearchResult]:
        """RAG增强搜索"""
        try:
            rag_response = self.rag_retriever.retrieve_and_generate(query)

            return {
                'query': query,
                'source': 'rag',
                'results': [{
                    'title': f"RAG检索结果 - {query}",
                    'snippet': rag_response['generated_response'][:500],
                    'url': 'internal://rag',
                    'content': rag_response['generated_response'],
                    'retrieved_docs_count': len(rag_response['retrieved_documents'])
                }],
                'rag_metadata': {
                    'retrieved_docs': rag_response['retrieved_documents'],
                    'context_used': rag_response['context_used']
                }
            }
        except Exception as e:
            return None
```

#### 阶段4: 添加RAG管理API

创建 `backend/api/routes/rag.py`：

```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
import os
from pathlib import Path

router = APIRouter()

# 全局RAG组件（在实际应用中应该通过依赖注入管理）
from ...rag.knowledge_manager import KnowledgeManager
from ...rag.vector_store import VectorStoreManager

vector_store = VectorStoreManager()
knowledge_manager = KnowledgeManager(vector_store)

@router.post("/knowledge/upload-url")
async def upload_from_url(url: str, collection: str = "research_kb"):
    """从URL上传文档到知识库"""
    try:
        doc_count = knowledge_manager.load_from_url(url, collection)
        return {
            "status": "success",
            "message": f"Successfully loaded {doc_count} document chunks from URL",
            "collection": collection
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge/upload-file")
async def upload_file(file: UploadFile = File(...), collection: str = "research_kb"):
    """上传文件到知识库"""
    try:
        # 保存上传的文件
        upload_dir = Path("./data/uploads")
        upload_dir.mkdir(exist_ok=True)

        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 根据文件类型加载文档
        if file.filename.endswith('.pdf'):
            doc_count = knowledge_manager.load_from_pdf(str(file_path), collection)
        elif file.filename.endswith('.txt'):
            # 简单的文本文件处理
            from langchain.docstore.document import Document
            text_content = content.decode('utf-8')
            doc = Document(page_content=text_content, metadata={"source": file.filename})
            vector_store.add_documents([doc], collection)
            doc_count = 1
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # 清理临时文件
        os.remove(file_path)

        return {
            "status": "success",
            "message": f"Successfully loaded {doc_count} document chunks from file",
            "collection": collection
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge/stats")
async def get_knowledge_stats(collection: str = "research_kb"):
    """获取知识库统计信息"""
    try:
        stats = knowledge_manager.get_collection_stats(collection)
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/knowledge/collection/{collection_name}")
async def delete_collection(collection_name: str):
    """删除知识库集合"""
    try:
        vector_store.client.delete_collection(name=collection_name)
        return {
            "status": "success",
            "message": f"Collection '{collection_name}' deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 阶段5: 前端集成

##### 5.1 添加RAG管理页面

创建 `frontend/src/pages/KnowledgeBase.tsx`：

```tsx
import React, { useState, useEffect } from 'react';
import { Upload, Button, Table, message, Input, Space, Card } from 'antd';
import { UploadOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

interface KnowledgeStats {
  collection_name: string;
  document_count: number;
  exists: boolean;
}

const KnowledgeBase: React.FC = () => {
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [url, setUrl] = useState('');

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/rag/knowledge/stats');
      const data = await response.json();
      setStats(data.stats);
    } catch (error) {
      message.error('获取知识库统计信息失败');
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleUrlUpload = async () => {
    if (!url.trim()) {
      message.error('请输入有效的URL');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/rag/knowledge/upload-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url.trim() }),
      });

      const data = await response.json();
      message.success(data.message);
      fetchStats();
      setUrl('');
    } catch (error) {
      message.error('上传失败');
    } finally {
      setLoading(false);
    }
  };

  const uploadProps = {
    name: 'file',
    action: '/api/v1/rag/knowledge/upload-file',
    onChange(info: any) {
      if (info.file.status === 'done') {
        message.success(`${info.file.name} 上传成功`);
        fetchStats();
      } else if (info.file.status === 'error') {
        message.error(`${info.file.name} 上传失败`);
      }
    },
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>RAG知识库管理</h1>

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 知识库统计 */}
        <Card title="知识库统计" extra={<Button icon={<ReloadOutlined />} onClick={fetchStats}>刷新</Button>}>
          {stats ? (
            <div>
              <p><strong>集合名称:</strong> {stats.collection_name}</p>
              <p><strong>文档数量:</strong> {stats.document_count}</p>
              <p><strong>状态:</strong> {stats.exists ? '正常' : '未创建'}</p>
            </div>
          ) : (
            <p>加载中...</p>
          )}
        </Card>

        {/* URL上传 */}
        <Card title="从URL添加文档">
          <Space.Compact style={{ width: '100%' }}>
            <Input
              placeholder="输入文档URL"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onPressEnter={handleUrlUpload}
            />
            <Button
              type="primary"
              loading={loading}
              onClick={handleUrlUpload}
            >
              添加
            </Button>
          </Space.Compact>
        </Card>

        {/* 文件上传 */}
        <Card title="上传文件">
          <Upload {...uploadProps}>
            <Button icon={<UploadOutlined />}>选择文件</Button>
          </Upload>
          <p style={{ marginTop: 8, color: '#666' }}>
            支持的文件类型: PDF, TXT
          </p>
        </Card>
      </Space>
    </div>
  );
};

export default KnowledgeBase;
```

##### 5.2 更新路由配置

在 `frontend/src/App.tsx` 中添加RAG管理页面路由：

```tsx
import KnowledgeBase from './pages/KnowledgeBase';

// 在路由配置中添加
<Route path="/knowledge" element={<KnowledgeBase />} />
```

### 配置管理

#### 配置文件扩展

更新 `config.json` 添加RAG相关配置：

```json
{
  "rag": {
    "enabled": true,
    "vector_store": {
      "type": "chromadb",
      "persist_directory": "./data/chroma_db",
      "collection_name": "research_kb"
    },
    "embedding": {
      "model": "all-MiniLM-L6-v2",
      "device": "cpu"
    },
    "retrieval": {
      "top_k": 5,
      "similarity_threshold": 0.7
    }
  }
}
```

### 测试和验证

#### 集成测试

创建测试文件 `test/test_rag.py`：

```python
import pytest
from backend.rag.vector_store import VectorStoreManager
from backend.rag.retriever import RAGRetriever
from backend.llm.openai_llm import OpenAILLM

def test_vector_store_basic():
    """测试向量存储基本功能"""
    manager = VectorStoreManager(persist_directory="./test_data/chroma_db")

    # 创建测试文档
    from langchain.docstore.document import Document
    docs = [
        Document(page_content="RAG是一种检索增强生成技术", metadata={"source": "test"}),
        Document(page_content="向量数据库用于存储文档嵌入", metadata={"source": "test"}),
    ]

    # 添加文档
    manager.add_documents(docs, "test_collection")

    # 搜索测试
    results = manager.similarity_search("什么是RAG", n_results=2, collection_name="test_collection")

    assert len(results['documents'][0]) > 0
    assert "RAG" in results['documents'][0][0]

def test_rag_retrieval():
    """测试RAG检索功能"""
    llm = OpenAILLM(api_key="test_key")  # 使用测试key
    manager = VectorStoreManager()
    retriever = RAGRetriever(manager, llm)

    # 注意：实际测试需要真实的LLM和向量数据库
    # 这里只是结构验证
    assert hasattr(retriever, 'retrieve_and_generate')
```

#### 性能基准测试

```python
import time
from backend.rag.vector_store import VectorStoreManager

def benchmark_retrieval():
    """检索性能基准测试"""
    manager = VectorStoreManager()

    queries = [
        "什么是机器学习",
        "深度学习算法",
        "自然语言处理技术"
    ]

    for query in queries:
        start_time = time.time()
        results = manager.similarity_search(query, n_results=5)
        end_time = time.time()

        print(f"Query: {query}")
        print(f"Time: {end_time - start_time:.3f}s")
        print(f"Results: {len(results['documents'][0])}")
        print("-" * 50)
```

### 部署和维护

#### 生产环境部署

1. **向量数据库部署**
   ```bash
   # ChromaDB持久化目录
   mkdir -p /data/chroma_db

   # 设置正确的权限
   chown -R app:app /data/chroma_db
   ```

2. **环境变量配置**
   ```bash
   export RAG_ENABLED=true
   export RAG_VECTOR_STORE_PATH=/data/chroma_db
   export RAG_EMBEDDING_MODEL=all-mpnet-base-v2
   ```

3. **监控和日志**
   - 添加向量数据库性能监控
   - 记录RAG检索统计信息
   - 监控嵌入模型内存使用

#### 维护任务

1. **定期更新知识库**
   - 设置定时任务更新过期的文档
   - 清理低质量或重复的文档

2. **性能优化**
   - 监控检索延迟
   - 优化向量索引
   - 考虑使用更高效的嵌入模型

3. **备份策略**
   ```bash
   # 备份向量数据库
   cp -r /data/chroma_db /backup/chroma_db_$(date +%Y%m%d)

   # 备份配置
   cp config.json /backup/config_$(date +%Y%m%d).json
   ```

### 迁移路径

#### 渐进式集成

1. **阶段1**: 基础RAG功能
   - 实现向量存储和检索
   - 添加基本的知识库管理API

2. **阶段2**: 增强检索
   - 实现混合搜索（向量+关键词）
   - 添加元数据过滤
   - 实现重排序机制

3. **阶段3**: 高级功能
   - 支持多语言文档
   - 添加文档版本控制
   - 实现增量更新

4. **阶段4**: 生产优化
   - 性能监控和调优
   - 高可用部署
   - 自动化维护

### 总结

通过以上步骤，ResearchSync-Agent项目可以成功集成RAG技术，大幅提升研究能力和回答质量。RAG集成将为用户提供：

- 基于本地知识库的快速检索
- 更准确的答案生成
- 可扩展的知识管理能力
- 更好的用户体验

建议从ChromaDB开始进行原型开发，然后根据需求扩展到更强大的向量数据库解决方案。
