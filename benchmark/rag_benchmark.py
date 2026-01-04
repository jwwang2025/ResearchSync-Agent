"""
RAG性能测试

该模块提供RAG系统的性能测试功能，包括：
- 检索准确性测试
- 响应时间测试
- 生成质量评估
- 内存使用情况监控
"""

import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# RAG相关导入
from ..backend.rag.vector_store import VectorStoreManager
from ..backend.rag.retriever import RAGRetriever
from ..backend.rag.knowledge_manager import KnowledgeManager

# LLM相关导入
from ..backend.llm.factory import LLMFactory

# 配置相关导入
from ..backend.utils.config import Config

logger = logging.getLogger(__name__)


@dataclass
class RAGBenchmarkResult:
    """RAG性能测试结果数据类"""
    operation: str
    duration: float
    success: bool
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metrics is None:
            self.metrics = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class RAGBenchmark:
    """RAG性能测试器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化RAG性能测试器

        参数:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        self.config = Config(config_path) if config_path else Config()
        self.results: List[RAGBenchmarkResult] = []

        # 初始化RAG组件
        self.vector_store = None
        self.knowledge_manager = None
        self.rag_retriever = None
        self.llm = None

        self._initialize_components()

    def _initialize_components(self):
        """初始化RAG组件"""
        try:
            # 初始化向量存储
            rag_config = self.config.get('rag', {})
            persist_dir = rag_config.get('vector_store', {}).get('persist_directory', './data/chroma_db')
            self.vector_store = VectorStoreManager(persist_directory=persist_dir)

            # 初始化知识管理器
            self.knowledge_manager = KnowledgeManager(self.vector_store)

            # 初始化LLM
            llm_config = self.config.get('llm', {})
            llm_factory = LLMFactory()
            self.llm = llm_factory.create_llm(
                provider=llm_config.get('provider', 'deepseek'),
                api_key=llm_config.get('api_key', ''),
                model=llm_config.get('model'),
                temperature=llm_config.get('temperature', 0.7)
            )

            # 初始化RAG检索器
            retrieval_config = rag_config.get('retrieval', {})
            self.rag_retriever = RAGRetriever(
                vector_store=self.vector_store,
                llm=self.llm,
                similarity_threshold=retrieval_config.get('similarity_threshold', 0.7),
                max_context_length=retrieval_config.get('max_context_length', 4000)
            )

            logger.info("Successfully initialized RAG components")

        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {e}")
            raise

    def benchmark_retrieval_accuracy(
        self,
        test_queries: List[str],
        relevant_docs: Dict[str, List[str]],
        collection_name: str = "research_kb",
        top_k: int = 5
    ) -> List[RAGBenchmarkResult]:
        """
        测试检索准确性

        参数:
            test_queries: 测试查询列表
            relevant_docs: 查询对应的相关文档ID字典
            collection_name: 集合名称
            top_k: 检索文档数量

        返回:
            性能测试结果列表
        """
        results = []

        for query in test_queries:
            start_time = time.time()

            try:
                # 执行检索
                retrieved_docs = self.rag_retriever.retrieve_only(
                    query=query,
                    collection_name=collection_name,
                    top_k=top_k,
                    include_scores=True
                )

                duration = time.time() - start_time

                # 计算准确性指标
                retrieved_ids = [doc.get('id', '') for doc in retrieved_docs]
                expected_ids = relevant_docs.get(query, [])

                # 计算精确率和召回率
                if expected_ids:
                    true_positives = len(set(retrieved_ids) & set(expected_ids))
                    precision = true_positives / len(retrieved_ids) if retrieved_ids else 0
                    recall = true_positives / len(expected_ids)
                    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                else:
                    precision = recall = f1_score = 0

                # 计算MRR (Mean Reciprocal Rank)
                mrr = 0
                if expected_ids and retrieved_ids:
                    for i, doc_id in enumerate(retrieved_ids):
                        if doc_id in expected_ids:
                            mrr = 1 / (i + 1)
                            break

                metrics = {
                    'query': query,
                    'retrieved_count': len(retrieved_docs),
                    'expected_count': len(expected_ids),
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1_score,
                    'mrr': mrr,
                    'avg_score': np.mean([doc.get('score', 0) for doc in retrieved_docs]) if retrieved_docs else 0,
                    'top_score': max([doc.get('score', 0) for doc in retrieved_docs]) if retrieved_docs else 0
                }

                results.append(RAGBenchmarkResult(
                    operation="retrieval_accuracy",
                    duration=duration,
                    success=True,
                    metrics=metrics
                ))

            except Exception as e:
                results.append(RAGBenchmarkResult(
                    operation="retrieval_accuracy",
                    duration=time.time() - start_time,
                    success=False,
                    error_message=str(e),
                    metrics={'query': query}
                ))

        return results

    def benchmark_generation_quality(
        self,
        test_queries: List[str],
        collection_name: str = "research_kb",
        top_k: int = 5
    ) -> List[RAGBenchmarkResult]:
        """
        测试生成质量

        参数:
            test_queries: 测试查询列表
            collection_name: 集合名称
            top_k: 检索文档数量

        返回:
            性能测试结果列表
        """
        results = []

        for query in test_queries:
            start_time = time.time()

            try:
                # 执行检索和生成
                result = self.rag_retriever.retrieve_and_generate(
                    query=query,
                    collection_name=collection_name,
                    top_k=top_k,
                    temperature=0.3
                )

                duration = time.time() - start_time

                # 分析生成质量
                response = result.get('generated_response', '')
                retrieved_docs = result.get('retrieved_documents', [])
                context_used = result.get('context_used', False)

                metrics = {
                    'query': query,
                    'response_length': len(response),
                    'word_count': len(response.split()) if response else 0,
                    'context_used': context_used,
                    'retrieved_count': len(retrieved_docs),
                    'avg_relevance_score': np.mean([doc.get('score', 0) for doc in retrieved_docs]) if retrieved_docs else 0,
                    'has_citations': '[' in response and ']' in response,  # 检查是否有引用标记
                    'response_quality_score': self._evaluate_response_quality(response, retrieved_docs)
                }

                results.append(RAGBenchmarkResult(
                    operation="generation_quality",
                    duration=duration,
                    success=True,
                    metrics=metrics
                ))

            except Exception as e:
                results.append(RAGBenchmarkResult(
                    operation="generation_quality",
                    duration=time.time() - start_time,
                    success=False,
                    error_message=str(e),
                    metrics={'query': query}
                ))

        return results

    def benchmark_response_time(
        self,
        test_queries: List[str],
        collection_name: str = "research_kb",
        top_k: int = 5,
        num_runs: int = 3
    ) -> List[RAGBenchmarkResult]:
        """
        测试响应时间

        参数:
            test_queries: 测试查询列表
            collection_name: 集合名称
            top_k: 检索文档数量
            num_runs: 每个查询的运行次数

        返回:
            性能测试结果列表
        """
        results = []

        for query in test_queries:
            durations = []

            for _ in range(num_runs):
                start_time = time.time()

                try:
                    self.rag_retriever.retrieve_and_generate(
                        query=query,
                        collection_name=collection_name,
                        top_k=top_k,
                        temperature=0.3
                    )
                    durations.append(time.time() - start_time)

                except Exception as e:
                    logger.warning(f"Query failed: {e}")
                    continue

            if durations:
                avg_duration = np.mean(durations)
                min_duration = np.min(durations)
                max_duration = np.max(durations)
                std_duration = np.std(durations)
                p95_duration = np.percentile(durations, 95)

                metrics = {
                    'query': query,
                    'num_runs': len(durations),
                    'avg_duration': avg_duration,
                    'min_duration': min_duration,
                    'max_duration': max_duration,
                    'std_duration': std_duration,
                    'p95_duration': p95_duration
                }

                results.append(RAGBenchmarkResult(
                    operation="response_time",
                    duration=avg_duration,
                    success=True,
                    metrics=metrics
                ))
            else:
                results.append(RAGBenchmarkResult(
                    operation="response_time",
                    duration=0,
                    success=False,
                    error_message="All runs failed",
                    metrics={'query': query, 'num_runs': 0}
                ))

        return results

    def benchmark_knowledge_base_operations(
        self,
        test_documents: List[Dict[str, Any]],
        collection_name: str = "test_kb"
    ) -> List[RAGBenchmarkResult]:
        """
        测试知识库操作性能

        参数:
            test_documents: 测试文档列表
            collection_name: 测试集合名称

        返回:
            性能测试结果列表
        """
        results = []

        # 测试文档上传
        for i, doc in enumerate(test_documents):
            start_time = time.time()

            try:
                result = self.knowledge_manager.load_from_text(
                    text=doc['content'],
                    collection=collection_name,
                    metadata=doc.get('metadata', {})
                )

                duration = time.time() - start_time

                metrics = {
                    'operation': 'upload_document',
                    'doc_index': i,
                    'chunks_loaded': result.get('chunks_loaded', 0),
                    'success': result.get('success', False),
                    'content_length': len(doc['content'])
                }

                results.append(RAGBenchmarkResult(
                    operation="knowledge_upload",
                    duration=duration,
                    success=result.get('success', False),
                    metrics=metrics
                ))

            except Exception as e:
                results.append(RAGBenchmarkResult(
                    operation="knowledge_upload",
                    duration=time.time() - start_time,
                    success=False,
                    error_message=str(e),
                    metrics={'doc_index': i}
                ))

        # 测试集合统计
        try:
            start_time = time.time()
            stats = self.knowledge_manager.get_collection_stats(collection_name)
            duration = time.time() - start_time

            results.append(RAGBenchmarkResult(
                operation="collection_stats",
                duration=duration,
                success=True,
                metrics={'stats': stats}
            ))

        except Exception as e:
            results.append(RAGBenchmarkResult(
                operation="collection_stats",
                duration=time.time() - start_time,
                success=False,
                error_message=str(e)
            ))

        return results

    def _evaluate_response_quality(self, response: str, retrieved_docs: List[Dict]) -> float:
        """
        评估响应质量的简单指标

        参数:
            response: 生成的响应
            retrieved_docs: 检索到的文档

        返回:
            质量评分 (0-1之间)
        """
        if not response or not retrieved_docs:
            return 0.0

        score = 0.0

        # 检查响应长度合理性
        if 50 <= len(response) <= 2000:
            score += 0.2

        # 检查是否使用了检索到的信息
        retrieved_texts = [doc.get('content', '') for doc in retrieved_docs]
        response_lower = response.lower()

        # 检查关键词匹配
        matched_keywords = 0
        total_keywords = 0

        for doc_text in retrieved_texts:
            keywords = set(doc_text.lower().split()[:10])  # 取前10个词作为关键词
            total_keywords += len(keywords)
            matched_keywords += sum(1 for keyword in keywords if keyword in response_lower)

        if total_keywords > 0:
            keyword_coverage = matched_keywords / total_keywords
            score += keyword_coverage * 0.3

        # 检查响应结构
        if any(indicator in response for indicator in ['。', '！', '？', '\n']):
            score += 0.2

        # 检查是否有引用
        if any(indicator in response for indicator in ['[', ']', '来源', '参考']):
            score += 0.3

        return min(score, 1.0)

    def run_comprehensive_benchmark(
        self,
        test_queries: List[str],
        relevant_docs: Dict[str, List[str]],
        test_documents: List[Dict[str, Any]],
        collection_name: str = "benchmark_kb"
    ) -> Dict[str, List[RAGBenchmarkResult]]:
        """
        运行全面的RAG性能测试

        参数:
            test_queries: 测试查询列表
            relevant_docs: 查询对应的相关文档
            test_documents: 测试文档列表
            collection_name: 集合名称

        返回:
            各测试类型的测试结果字典
        """
        logger.info("Starting comprehensive RAG benchmark...")

        results = {}

        # 1. 检索准确性测试
        logger.info("Running retrieval accuracy benchmark...")
        results['retrieval_accuracy'] = self.benchmark_retrieval_accuracy(
            test_queries, relevant_docs, collection_name
        )

        # 2. 生成质量测试
        logger.info("Running generation quality benchmark...")
        results['generation_quality'] = self.benchmark_generation_quality(
            test_queries, collection_name
        )

        # 3. 响应时间测试
        logger.info("Running response time benchmark...")
        results['response_time'] = self.benchmark_response_time(
            test_queries, collection_name
        )

        # 4. 知识库操作测试
        logger.info("Running knowledge base operations benchmark...")
        results['knowledge_operations'] = self.benchmark_knowledge_base_operations(
            test_documents, collection_name
        )

        # 合并所有结果
        self.results.extend([r for benchmark_results in results.values() for r in benchmark_results])

        return results

    def save_results(self, output_path: str = "rag_benchmark_results.json"):
        """
        保存测试结果到文件

        参数:
            output_path: 输出文件路径
        """
        results_dict = [result.to_dict() for result in self.results]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2)

        logger.info(f"RAG benchmark results saved to {output_path}")

    def generate_report(self, results: Dict[str, List[RAGBenchmarkResult]]) -> str:
        """
        生成RAG性能测试报告

        参数:
            results: 测试结果字典

        返回:
            Markdown格式的报告
        """
        report_lines = [
            "# RAG性能测试报告\n",
            f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            "## 总体统计\n"
        ]

        # 计算总体统计
        total_tests = sum(len(benchmark_results) for benchmark_results in results.values())
        successful_tests = sum(
            sum(1 for r in benchmark_results if r.success)
            for benchmark_results in results.values()
        )
        success_rate = successful_tests / total_tests * 100 if total_tests > 0 else 0

        report_lines.extend([
            f"- 总测试数: {total_tests}",
            f"- 成功率: {success_rate:.1f}%\n",
            "## 详细测试结果\n"
        ])

        # 检索准确性结果
        if 'retrieval_accuracy' in results and results['retrieval_accuracy']:
            accuracy_results = [r for r in results['retrieval_accuracy'] if r.success]
            if accuracy_results:
                avg_precision = np.mean([r.metrics.get('precision', 0) for r in accuracy_results])
                avg_recall = np.mean([r.metrics.get('recall', 0) for r in accuracy_results])
                avg_f1 = np.mean([r.metrics.get('f1_score', 0) for r in accuracy_results])
                avg_mrr = np.mean([r.metrics.get('mrr', 0) for r in accuracy_results])

                report_lines.extend([
                    "### 检索准确性测试",
                    f"- 平均精确率: {avg_precision:.3f}",
                    f"- 平均召回率: {avg_recall:.3f}",
                    f"- 平均F1分数: {avg_f1:.3f}",
                    f"- 平均MRR: {avg_mrr:.3f}",
                    ""
                ])

        # 生成质量结果
        if 'generation_quality' in results and results['generation_quality']:
            quality_results = [r for r in results['generation_quality'] if r.success]
            if quality_results:
                avg_response_length = np.mean([r.metrics.get('response_length', 0) for r in quality_results])
                avg_quality_score = np.mean([r.metrics.get('response_quality_score', 0) for r in quality_results])
                context_usage_rate = sum(1 for r in quality_results if r.metrics.get('context_used', False)) / len(quality_results)

                report_lines.extend([
                    "### 生成质量测试",
                    f"- 平均响应长度: {avg_response_length:.0f}字符",
                    f"- 平均质量评分: {avg_quality_score:.3f}",
                    f"- 上下文使用率: {context_usage_rate:.1%}",
                    ""
                ])

        # 响应时间结果
        if 'response_time' in results and results['response_time']:
            time_results = [r for r in results['response_time'] if r.success]
            if time_results:
                avg_duration = np.mean([r.duration for r in time_results])
                p95_duration = np.percentile([r.duration for r in time_results], 95)

                report_lines.extend([
                    "### 响应时间测试",
                    f"- 平均响应时间: {avg_duration:.3f}秒",
                    f"- 95%响应时间: {p95_duration:.3f}秒",
                    ""
                ])

        # 知识库操作结果
        if 'knowledge_operations' in results and results['knowledge_operations']:
            kb_results = results['knowledge_operations']
            upload_results = [r for r in kb_results if r.operation == 'knowledge_upload' and r.success]

            if upload_results:
                total_chunks = sum(r.metrics.get('chunks_loaded', 0) for r in upload_results)
                avg_upload_time = np.mean([r.duration for r in upload_results])

                report_lines.extend([
                    "### 知识库操作测试",
                    f"- 总上传文档块数: {total_chunks}",
                    f"- 平均上传时间: {avg_upload_time:.3f}秒",
                    ""
                ])

        return "\n".join(report_lines)


def load_rag_test_data(data_path: str = "benchmark/rag_test_data.json") -> Dict[str, Any]:
    """
    加载RAG测试数据

    参数:
        data_path: 测试数据文件路径

    返回:
        测试数据字典
    """
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 返回默认测试数据
        return {
            "queries": [
                "什么是机器学习？",
                "深度学习和机器学习的区别是什么？",
                "人工智能的发展历程",
                "神经网络的基本原理"
            ],
            "relevant_docs": {
                "什么是机器学习？": ["doc_ml_001", "doc_ai_001"],
                "深度学习和机器学习的区别是什么？": ["doc_dl_001", "doc_ml_001"],
                "人工智能的发展历程": ["doc_ai_history_001"],
                "神经网络的基本原理": ["doc_nn_001", "doc_dl_001"]
            },
            "documents": [
                {
                    "content": "机器学习是人工智能的一个分支，它通过算法让计算机从数据中学习模式，而无需明确编程。机器学习算法可以分为监督学习、无监督学习和强化学习三种主要类型。",
                    "metadata": {"topic": "machine_learning", "doc_id": "doc_ml_001"}
                },
                {
                    "content": "深度学习是机器学习的一个子集，使用神经网络来模拟人脑的工作方式。深度学习在图像识别、自然语言处理等领域取得了重大突破。",
                    "metadata": {"topic": "deep_learning", "doc_id": "doc_dl_001"}
                },
                {
                    "content": "人工智能的发展可以追溯到20世纪50年代，经历了多次兴衰。近年来，随着计算能力的提升和大数据的可用性，人工智能进入了快速发展期。",
                    "metadata": {"topic": "ai_history", "doc_id": "doc_ai_history_001"}
                }
            ]
        }


def run_rag_benchmark(
    config_path: Optional[str] = None,
    output_path: str = "rag_benchmark_results.json",
    report_path: str = "rag_benchmark_report.md"
):
    """
    运行RAG性能测试的主函数

    参数:
        config_path: 配置文件路径
        output_path: 结果输出路径
        report_path: 报告输出路径
    """
    # 加载测试数据
    test_data = load_rag_test_data()

    # 创建性能测试器
    benchmark = RAGBenchmark(config_path)

    # 运行测试
    results = benchmark.run_comprehensive_benchmark(
        test_queries=test_data["queries"],
        relevant_docs=test_data["relevant_docs"],
        test_documents=test_data["documents"],
        collection_name="benchmark_kb"
    )

    # 保存详细结果
    benchmark.save_results(output_path)

    # 生成并保存报告
    report = benchmark.generate_report(results)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info(f"RAG benchmark completed. Results saved to {output_path}, report saved to {report_path}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 运行测试
    run_rag_benchmark()
