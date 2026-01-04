# RAG使用指南

## 概述

ResearchSync-Agent现已集成了RAG（Retrieval-Augmented Generation）功能，为您的研究工作提供强大的本地知识库支持。通过RAG，您可以：

- 📚 **构建专用知识库**：上传文档、网页和研究资料
- 🔍 **智能检索增强**：基于本地知识进行精确回答
- 🤖 **提升研究质量**：减少幻觉，提高答案准确性
- 📈 **渐进式学习**：系统随知识库扩充而变得更聪明

## 快速开始

### 1. 访问知识库管理

启动系统后，在浏览器中访问 `http://localhost:5173/knowledge` 或点击导航栏的"知识库"选项卡。

### 2. 添加您的第一个文档

#### 方法一：上传文件
1. 点击"添加文档"按钮
2. 选择文件上传，支持格式：
   - **PDF文档** (.pdf) - 学术论文、报告
   - **文本文件** (.txt) - 笔记、摘要
   - **Markdown** (.md) - 结构化文档
   - **网页文件** (.html) - 保存的网页

#### 方法二：从URL导入
1. 在"从URL添加文档"对话框中输入网页地址
2. 点击"添加"，系统将自动下载并处理网页内容

#### 方法三：批量上传目录
使用API直接上传整个目录的内容。

### 3. 开始智能问答

1. 点击"智能查询"按钮
2. 输入您的问题，例如：
   - "什么是机器学习？"
   - "解释一下深度学习的工作原理"
   - "总结这篇论文的主要贡献"

3. 系统将基于您的知识库内容提供准确回答

## 功能详解

### 知识库管理

#### 📊 统计信息
知识库页面显示：
- **文档块数量**：已处理的文档片段总数
- **集合名称**：当前知识库的标识符
- **状态**：知识库是否正常工作

#### 🔄 数据管理
- **刷新统计**：实时更新知识库状态
- **集合管理**：创建、删除不同的知识库集合
- **内容清理**：清空或重新构建知识库

### 智能检索

#### 🎯 检索机制
RAG系统使用以下策略：
1. **语义搜索**：基于含义而非关键词匹配
2. **相关度排序**：优先显示最相关的结果
3. **上下文增强**：提供完整的背景信息

#### 📋 查询结果
每次查询返回：
- **智能回答**：基于检索内容的生成回答
- **上下文状态**：是否找到相关信息
- **参考来源**：答案基于的文档片段
- **相关度评分**：结果的可信度评估

### 研究集成

#### 🔗 与研究流程的结合
RAG功能已集成到核心研究流程中：

1. **规划阶段**：使用RAG检查现有知识
2. **检索阶段**：优先从本地知识库检索
3. **合成阶段**：结合本地和外部信息生成报告

#### ⚙️ 配置选项
在 `config.json` 中配置RAG参数：

```json
{
  "rag": {
    "enabled": true,
    "vector_store": {
      "persist_directory": "./data/chroma_db",
      "collection_name": "research_kb"
    },
    "embedding": {
      "model": "all-MiniLM-L6-v2"
    },
    "retrieval": {
      "top_k": 5,
      "similarity_threshold": 0.7,
      "max_context_length": 4000
    }
  }
}
```

## 最佳实践

### 📚 知识库建设

#### 内容选择
- **质量优先**：选择权威、准确的资料
- **主题相关**：针对您的研究领域收集资料
- **格式统一**：使用一致的文档格式便于管理

#### 组织策略
- **分类存储**：为不同主题创建独立的集合
- **版本管理**：定期更新过时的文档
- **元数据标注**：添加来源、日期等元信息

### ❓ 问题提出

#### 查询技巧
- **具体明确**：提出具体的技术问题
- **上下文丰富**：提供足够的背景信息
- **分层提问**：从基础概念到深入细节逐步提问

#### 示例查询
```
✅ 好的查询：
"解释Transformer架构的工作原理"
"机器学习中过拟合的成因和解决方法"
"对比CNN和RNN在图像处理中的应用"

❌ 不良查询：
"这个怎么样？"
"解释一切"
"告诉我关于AI的事情"
```

### 🔧 性能优化

#### 检索调优
- **相似度阈值**：调整 `similarity_threshold` 控制结果质量
- **结果数量**：设置 `top_k` 平衡全面性和精准性
- **上下文长度**：控制 `max_context_length` 管理回答详细度

#### 知识库维护
- **定期清理**：移除过时或不相关的文档
- **索引重建**：在大量更新后重建向量索引
- **备份策略**：定期备份重要的知识库数据

## API使用

### REST API端点

#### 知识库管理
```http
# 上传URL文档
POST /api/v1/rag/knowledge/upload-url
Content-Type: application/json

{
  "url": "https://example.com/article.html",
  "collection": "research_kb"
}

# 上传文件
POST /api/v1/rag/knowledge/upload-file
Content-Type: multipart/form-data

# 获取统计信息
GET /api/v1/rag/knowledge/stats

# 列出集合
GET /api/v1/rag/knowledge/collections

# 删除集合
DELETE /api/v1/rag/knowledge/collection/{collection_name}
```

#### 智能查询
```http
# RAG增强查询
POST /api/v1/rag/query
Content-Type: application/json

{
  "query": "什么是机器学习？",
  "collection": "research_kb",
  "top_k": 5,
  "include_sources": true
}

# 仅检索（不生成）
GET /api/v1/rag/query/retrieve-only?query=机器学习&top_k=3
```

#### 健康检查
```http
GET /api/v1/rag/health
```

### Python SDK使用

```python
from backend.rag.knowledge_manager import KnowledgeManager
from backend.rag.retriever import RAGRetriever
from backend.rag.vector_store import VectorStoreManager

# 初始化组件
vector_store = VectorStoreManager()
knowledge_manager = KnowledgeManager(vector_store)

# 添加文档
result = knowledge_manager.load_from_url(
    "https://example.com/research-paper.html",
    "research_kb"
)

# 执行查询
retriever = RAGRetriever(vector_store, llm)
result = retriever.retrieve_and_generate(
    "总结这篇论文的主要发现",
    collection_name="research_kb"
)

print(result['generated_response'])
```

## 故障排除

### 常见问题

#### Q: 上传文档失败
**解决方案**：
- 检查文件格式是否支持
- 确认文件大小不超过限制（50MB）
- 验证网络连接（URL上传）

#### Q: 查询无结果
**解决方案**：
- 检查知识库是否为空
- 降低相似度阈值
- 使用更通用的查询词

#### Q: 回答质量不佳
**解决方案**：
- 添加更多相关文档
- 使用更精确的问题描述
- 检查文档质量和相关性

#### Q: 性能问题
**解决方案**：
- 减少 `top_k` 值
- 清理不需要的文档
- 考虑使用更高效的嵌入模型

### 日志和调试

系统日志位置：
- 后端日志：`logs/backend.log`
- RAG相关日志会标记 `[RAG]` 前缀

启用调试模式：
```bash
export LOG_LEVEL=DEBUG
```

### 技术支持

如果遇到问题，请：
1. 查看系统日志
2. 检查配置文件
3. 运行测试用例：`python -m pytest test/test_rag.py`
4. 查看GitHub Issues获取帮助

## 更新计划

### 近期功能
- [ ] 支持更多文档格式（Word、Excel等）
- [ ] 实现文档版本控制
- [ ] 添加知识库导入/导出功能
- [ ] 支持多语言文档处理

### 长期规划
- [ ] 混合搜索（向量+关键词+语义）
- [ ] 知识图谱集成
- [ ] 自动文档摘要和标签
- [ ] 协作知识库功能

---

**💡 提示**: RAG功能会随着您知识库的扩充而变得更加强大。建议从您的核心研究领域开始，逐步构建专属的智能知识库！
