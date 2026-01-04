"""
测试数据生成器

该模块用于生成Agent和RAG系统的测试数据，包括：
- 测试查询生成
- 相关文档映射
- 知识库测试文档
- 性能测试配置
"""

import json
import os
import random
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TestDataGenerator:
    """测试数据生成器"""

    def __init__(self):
        # 测试查询模板
        self.query_templates = {
            "machine_learning": [
                "什么是{method}？",
                "{method}的基本原理是什么？",
                "{method}有哪些应用场景？",
                "{method}和{other_method}有什么区别？",
                "如何实现{task}的{method}？"
            ],
            "deep_learning": [
                "什么是{architecture}？",
                "{architecture}在{task}中的应用",
                "{algorithm}算法的工作原理",
                "如何训练{network_type}网络？",
                "{technique}技术的优势是什么？"
            ],
            "ai_general": [
                "人工智能的发展历程",
                "AI在{domain}领域的应用",
                "{concept}的基本概念",
                "未来AI的发展趋势",
                "AI伦理问题的讨论"
            ],
            "research": [
                "分析{topic}的当前研究状况",
                "{topic}的研究方法有哪些？",
                "{topic}领域的最新进展",
                "{topic}的挑战和解决方案",
                "关于{topic}的系统性综述"
            ]
        }

        # 实体词典
        self.entities = {
            "method": ["监督学习", "无监督学习", "强化学习", "迁移学习", "联邦学习"],
            "other_method": ["深度学习", "传统机器学习", "统计学习", "符号学习"],
            "task": ["分类", "回归", "聚类", "推荐", "预测"],
            "architecture": ["卷积神经网络", "循环神经网络", "Transformer", "生成对抗网络", "注意力机制"],
            "algorithm": ["反向传播", "梯度下降", "Adam优化", "Dropout", "批归一化"],
            "network_type": ["全连接", "卷积", "循环", "残差", "密集"],
            "technique": ["迁移学习", "多任务学习", "元学习", "自监督学习"],
            "domain": ["医疗", "金融", "教育", "交通", "制造"],
            "concept": ["神经网络", "大数据", "云计算", "物联网", "区块链"],
            "topic": ["计算机视觉", "自然语言处理", "机器人", "自动驾驶", "智能推荐"]
        }

        # 测试文档模板
        self.document_templates = [
            {
                "topic": "machine_learning",
                "template": "{method}是机器学习的重要分支，它通过{principle}的方式从数据中学习模式。{method}的主要特点包括{features}。在实际应用中，{method}被广泛用于{solutions}等领域。",
                "metadata": {"category": "机器学习基础", "difficulty": "beginner"}
            },
            {
                "topic": "deep_learning",
                "template": "{architecture}是一种特殊的神经网络结构，特别适用于{application}任务。它通过{layers}层级的特征提取，能够自动学习{features}的复杂表示。",
                "metadata": {"category": "深度学习", "difficulty": "intermediate"}
            },
            {
                "topic": "ai_applications",
                "template": "人工智能技术在{domain}领域的应用取得了显著进展。主要的应用场景包括{applications}。这些应用带来了{benefits}，同时也面临{challenges}等方面的挑战。",
                "metadata": {"category": "AI应用", "difficulty": "intermediate"}
            },
            {
                "topic": "research_methods",
                "template": "在{field}研究领域，常用的方法包括{methods}。这些方法各有特点：{characteristics}。当前的研究热点集中在{focus_areas}等方面。",
                "metadata": {"category": "研究方法", "difficulty": "advanced"}
            }
        ]

    def generate_queries(self, num_queries: int = 20) -> List[str]:
        """
        生成测试查询

        参数:
            num_queries: 生成的查询数量

        返回:
            查询列表
        """
        queries = []

        # 按类别分配查询数量
        categories = list(self.query_templates.keys())
        queries_per_category = num_queries // len(categories)
        extra_queries = num_queries % len(categories)

        for i, category in enumerate(categories):
            category_queries = queries_per_category + (1 if i < extra_queries else 0)

            for _ in range(category_queries):
                template = random.choice(self.query_templates[category])
                query = self._fill_template(template, category)
                queries.append(query)

        random.shuffle(queries)
        return queries

    def generate_relevant_docs_mapping(
        self,
        queries: List[str],
        num_docs_per_query: int = 3
    ) -> Dict[str, List[str]]:
        """
        生成查询与相关文档的映射关系

        参数:
            queries: 查询列表
            num_docs_per_query: 每个查询的相关文档数量

        返回:
            查询到文档ID列表的映射字典
        """
        mapping = {}

        for query in queries:
            # 基于查询内容生成相关的文档ID
            query_hash = hash(query) % 10000
            relevant_docs = []

            for i in range(num_docs_per_query):
                doc_id = "03d"
                relevant_docs.append(doc_id)

            mapping[query] = relevant_docs

        return mapping

    def generate_test_documents(self, num_documents: int = 50) -> List[Dict[str, Any]]:
        """
        生成测试文档

        参数:
            num_documents: 生成的文档数量

        返回:
            文档列表
        """
        documents = []

        for i in range(num_documents):
            # 随机选择文档模板
            template_info = random.choice(self.document_templates)
            template = template_info["template"]
            metadata = template_info["metadata"].copy()

            # 填充模板
            content = self._fill_document_template(template, template_info["topic"])

            # 生成文档ID和元数据
            doc_id = "03d"
            metadata.update({
                "doc_id": doc_id,
                "topic": template_info["topic"],
                "word_count": len(content.split()),
                "created_at": "2024-01-01"
            })

            documents.append({
                "content": content,
                "metadata": metadata
            })

        return documents

    def _fill_template(self, template: str, category: str) -> str:
        """
        填充查询模板

        参数:
            template: 查询模板
            category: 类别

        返回:
            填充后的查询
        """
        result = template

        # 替换所有占位符
        for placeholder, entity_list in self.entities.items():
            if "{" + placeholder + "}" in result:
                replacement = random.choice(entity_list)
                result = result.replace("{" + placeholder + "}", replacement)

        return result

    def _fill_document_template(self, template: str, topic: str) -> str:
        """
        填充文档模板

        参数:
            template: 文档模板
            topic: 主题

        返回:
            填充后的文档内容
        """
        # 根据主题选择合适的实体
        topic_entities = {
            "machine_learning": {
                "method": ["监督学习", "无监督学习", "强化学习"],
                "principle": ["有监督", "无监督", "试错"],
                "features": ["准确性高", "可解释性强", "计算效率高"],
                "solutions": ["图像分类", "文本分析", "推荐系统"]
            },
            "deep_learning": {
                "architecture": ["CNN", "RNN", "Transformer"],
                "application": ["图像识别", "序列预测", "语言理解"],
                "layers": ["多层", "深层", "层次化"],
                "features": ["局部特征", "时序特征", "全局依赖"]
            },
            "ai_applications": {
                "domain": ["医疗", "金融", "教育"],
                "applications": ["诊断辅助", "风险评估", "个性化教学"],
                "benefits": ["效率提升", "准确性提高", "成本降低"],
                "challenges": ["数据隐私", "模型解释", "技术集成"]
            },
            "research_methods": {
                "field": ["机器学习", "深度学习", "人工智能"],
                "methods": ["实验研究", "理论分析", "实证研究"],
                "characteristics": ["实验方法注重实践验证", "理论方法强调数学证明", "实证方法依赖数据支持"],
                "focus_areas": ["模型可解释性", "鲁棒性", "泛化能力"]
            }
        }

        entities = topic_entities.get(topic, {})
        result = template

        # 替换占位符
        for placeholder, value in entities.items():
            if "{" + placeholder + "}" in result:
                if isinstance(value, list):
                    replacement = random.choice(value)
                else:
                    replacement = value
                result = result.replace("{" + placeholder + "}", replacement)

        return result

    def generate_comprehensive_test_data(
        self,
        num_queries: int = 20,
        num_documents: int = 50,
        output_dir: str = "benchmark"
    ) -> Dict[str, Any]:
        """
        生成综合测试数据

        参数:
            num_queries: 查询数量
            num_documents: 文档数量
            output_dir: 输出目录

        返回:
            包含所有测试数据的字典
        """
        logger.info("Generating comprehensive test data...")

        # 生成查询
        queries = self.generate_queries(num_queries)
        logger.info(f"Generated {len(queries)} test queries")

        # 生成相关文档映射
        relevant_docs = self.generate_relevant_docs_mapping(queries)
        logger.info("Generated relevant document mappings")

        # 生成测试文档
        documents = self.generate_test_documents(num_documents)
        logger.info(f"Generated {len(documents)} test documents")

        # 生成Agent测试数据
        agent_test_data = {
            "queries": queries,
            "tasks": [
                {
                    "query": query,
                    "context": ["相关上下文信息"] * random.randint(1, 3)
                }
                for query in queries[:10]  # 只为前10个查询生成任务
            ],
            "reports": [
                {
                    "query": query,
                    "research_results": [
                        {
                            "task_id": f"task_{i}",
                            "findings": [f"发现{i+1}"] * random.randint(1, 3),
                            "sources": [f"来源{j+1}" for j in range(random.randint(1, 3))]
                        }
                        for i in range(random.randint(1, 3))
                    ]
                }
                for query in queries[:5]  # 只为前5个查询生成报告数据
            ]
        }

        # 生成RAG测试数据
        rag_test_data = {
            "queries": queries,
            "relevant_docs": relevant_docs,
            "documents": documents
        }

        # 生成工作流测试数据
        workflow_test_data = {
            "queries": queries
        }

        # 保存到文件
        os.makedirs(output_dir, exist_ok=True)

        with open(os.path.join(output_dir, "agent_test_data.json"), 'w', encoding='utf-8') as f:
            json.dump(agent_test_data, f, ensure_ascii=False, indent=2)

        with open(os.path.join(output_dir, "rag_test_data.json"), 'w', encoding='utf-8') as f:
            json.dump(rag_test_data, f, ensure_ascii=False, indent=2)

        with open(os.path.join(output_dir, "workflow_test_data.json"), 'w', encoding='utf-8') as f:
            json.dump(workflow_test_data, f, ensure_ascii=False, indent=2)

        logger.info("Test data saved to files")

        return {
            "agent_test_data": agent_test_data,
            "rag_test_data": rag_test_data,
            "workflow_test_data": workflow_test_data
        }

    def generate_benchmark_config(
        self,
        output_path: str = "benchmark/benchmark_config.json"
    ) -> Dict[str, Any]:
        """
        生成基准测试配置文件

        参数:
            output_path: 配置文件输出路径

        返回:
            配置字典
        """
        config = {
            "agent_benchmark": {
                "enabled": True,
                "num_threads": 4,
                "test_iterations": 3,
                "timeout_seconds": 300
            },
            "rag_benchmark": {
                "enabled": True,
                "collection_name": "benchmark_kb",
                "top_k_values": [3, 5, 10],
                "similarity_thresholds": [0.5, 0.7, 0.9],
                "num_runs": 3
            },
            "workflow_benchmark": {
                "enabled": True,
                "concurrency_levels": [1, 2, 3, 5],
                "auto_approve_plan": True,
                "max_execution_time": 600,
                "resource_monitoring": True
            },
            "output": {
                "results_dir": "benchmark/results",
                "reports_dir": "benchmark/reports",
                "log_level": "INFO"
            },
            "data": {
                "num_queries": 20,
                "num_documents": 50,
                "regenerate_data": False
            }
        }

        # 保存配置
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logger.info(f"Benchmark configuration saved to {output_path}")

        return config


def main():
    """主函数：生成所有测试数据"""
    logging.basicConfig(level=logging.INFO)

    generator = TestDataGenerator()

    # 生成综合测试数据
    test_data = generator.generate_comprehensive_test_data(
        num_queries=20,
        num_documents=50
    )

    # 生成配置文件
    config = generator.generate_benchmark_config()

    # 生成README文件
    readme_content = """# 性能测试基准

该目录包含ResearchSync-Agent系统的性能测试工具和数据。

## 文件说明

- `agent_benchmark.py`: Agent性能测试
- `rag_benchmark.py`: RAG系统性能测试
- `workflow_benchmark.py`: 完整工作流性能测试
- `test_data_generator.py`: 测试数据生成器
- `benchmark_config.json`: 测试配置
- `*test_data.json`: 测试数据文件
- `run_benchmarks.py`: 批量运行所有测试

## 快速开始

1. 生成测试数据：
```bash
python test_data_generator.py
```

2. 运行所有基准测试：
```bash
python run_benchmarks.py
```

3. 查看结果：
- 结果文件：`benchmark/results/`
- 报告文件：`benchmark/reports/`

## 测试内容

### Agent性能测试
- 协调器查询分类和响应
- 规划器计划生成
- 研究员研究执行
- 报告生成器文档生成

### RAG性能测试
- 检索准确性（精确率、召回率、F1、MRR）
- 生成质量评估
- 响应时间测试
- 知识库操作性能

### 工作流性能测试
- 端到端执行时间
- 并发处理能力
- 系统资源使用
- 可靠性和稳定性

## 配置说明

测试配置通过 `benchmark_config.json` 文件控制：

- `agent_benchmark`: Agent测试设置
- `rag_benchmark`: RAG测试设置
- `workflow_benchmark`: 工作流测试设置
- `output`: 输出目录配置
- `data`: 测试数据配置
"""

    with open("benchmark/README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)

    logger.info("Benchmark setup completed!")


if __name__ == "__main__":
    main()
