"""
工作流性能测试

该模块提供完整研究工作流的性能测试功能，包括：
- 端到端响应时间测试
- 工作流步骤效率分析
- 资源使用情况监控
- 并发处理能力测试
"""

import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import threading

# 工作流相关导入
from ..backend.workflow.graph import create_research_graph
from ..backend.agents.coordinator import Coordinator
from ..backend.agents.planner import Planner
from ..backend.agents.researcher import Researcher
from ..backend.agents.rapporteur import Rapporteur

# LLM相关导入
from ..backend.llm.factory import LLMFactory

# 配置相关导入
from ..backend.utils.config import Config

logger = logging.getLogger(__name__)


@dataclass
class WorkflowBenchmarkResult:
    """工作流性能测试结果数据类"""
    workflow_id: str
    query: str
    total_duration: float
    success: bool
    error_message: Optional[str] = None
    step_durations: Dict[str, float] = None
    metrics: Dict[str, Any] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.step_durations is None:
            self.step_durations = {}
        if self.metrics is None:
            self.metrics = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class WorkflowBenchmark:
    """工作流性能测试器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化工作流性能测试器

        参数:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        self.config = Config(config_path) if config_path else Config()
        self.results: List[WorkflowBenchmarkResult] = []

        # 初始化工作流组件
        self.workflow_graph = None
        self._initialize_workflow()

        # 资源监控
        self.resource_monitoring = True
        self.resource_stats = []

    def _initialize_workflow(self):
        """初始化工作流"""
        try:
            # 初始化LLM
            llm_config = self.config.get('llm', {})
            llm_factory = LLMFactory()
            llm = llm_factory.create_llm(
                provider=llm_config.get('provider', 'deepseek'),
                api_key=llm_config.get('api_key', ''),
                model=llm_config.get('model'),
                temperature=llm_config.get('temperature', 0.7)
            )

            # 初始化Agent
            coordinator = Coordinator(llm)
            planner = Planner(llm)
            researcher = Researcher(llm)
            rapporteur = Rapporteur(llm)

            # 创建工作流图
            self.workflow_graph = create_research_graph(
                coordinator, planner, researcher, rapporteur
            )

            logger.info("Successfully initialized workflow")

        except Exception as e:
            logger.error(f"Failed to initialize workflow: {e}")
            raise

    def _monitor_resources(self, interval: float = 1.0):
        """
        监控系统资源使用情况

        参数:
            interval: 监控间隔（秒）
        """
        if not self.resource_monitoring:
            return

        def monitor():
            while self.resource_monitoring:
                stats = {
                    'timestamp': time.time(),
                    'cpu_percent': psutil.cpu_percent(interval=None),
                    'memory_percent': psutil.virtual_memory().percent,
                    'memory_used_mb': psutil.virtual_memory().used / 1024 / 1024,
                    'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
                }
                self.resource_stats.append(stats)
                time.sleep(interval)

        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()

    def benchmark_single_workflow(
        self,
        query: str,
        workflow_id: str = None,
        auto_approve: bool = True
    ) -> WorkflowBenchmarkResult:
        """
        测试单个工作流执行

        参数:
            query: 研究查询
            workflow_id: 工作流ID，如果为None则自动生成
            auto_approve: 是否自动批准计划

        返回:
            工作流测试结果
        """
        if workflow_id is None:
            workflow_id = f"workflow_{int(time.time() * 1000)}"

        start_time = time.time()
        step_durations = {}
        success = False
        error_message = None
        metrics = {}

        try:
            # 开始资源监控
            self.resource_stats = []
            self._monitor_resources()

            # 初始化状态
            initial_state = {
                'query': query,
                'auto_approve': auto_approve,
                'output_format': 'markdown'
            }

            # 执行工作流
            step_start = time.time()
            result = self.workflow_graph.invoke(initial_state)
            total_duration = time.time() - start_time

            # 记录步骤持续时间（简化版，实际需要更详细的步骤追踪）
            step_durations['total_execution'] = total_duration

            # 分析结果
            success = result.get('final_report') is not None
            metrics = {
                'query_type': result.get('query_type'),
                'has_plan': result.get('research_plan') is not None,
                'iterations': result.get('iteration_count', 0),
                'total_results': len(result.get('research_results', [])),
                'report_length': len(result.get('final_report', '')),
                'current_step': result.get('current_step'),
                'needs_more_research': result.get('needs_more_research', True)
            }

            # 停止资源监控
            self.resource_monitoring = False
            time.sleep(0.1)  # 等待监控线程停止

            # 计算资源使用统计
            if self.resource_stats:
                cpu_usage = [s['cpu_percent'] for s in self.resource_stats]
                memory_usage = [s['memory_percent'] for s in self.resource_stats]

                metrics.update({
                    'avg_cpu_percent': sum(cpu_usage) / len(cpu_usage),
                    'max_cpu_percent': max(cpu_usage),
                    'avg_memory_percent': sum(memory_usage) / len(memory_usage),
                    'max_memory_percent': max(memory_usage),
                    'resource_samples': len(self.resource_stats)
                })

        except Exception as e:
            total_duration = time.time() - start_time
            success = False
            error_message = str(e)
            self.resource_monitoring = False
            logger.error(f"Workflow execution failed: {e}")

        return WorkflowBenchmarkResult(
            workflow_id=workflow_id,
            query=query,
            total_duration=total_duration,
            success=success,
            error_message=error_message,
            step_durations=step_durations,
            metrics=metrics
        )

    def benchmark_concurrent_workflows(
        self,
        queries: List[str],
        max_concurrent: int = 3,
        auto_approve: bool = True
    ) -> List[WorkflowBenchmarkResult]:
        """
        测试并发工作流执行

        参数:
            queries: 查询列表
            max_concurrent: 最大并发数
            auto_approve: 是否自动批准计划

        返回:
            工作流测试结果列表
        """
        results = []

        def run_single_workflow(query: str, index: int) -> WorkflowBenchmarkResult:
            workflow_id = f"concurrent_workflow_{index}_{int(time.time() * 1000)}"
            return self.benchmark_single_workflow(query, workflow_id, auto_approve)

        # 使用线程池执行并发测试
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = [
                executor.submit(run_single_workflow, query, i)
                for i, query in enumerate(queries)
            ]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Completed workflow: {result.workflow_id}")
                except Exception as e:
                    logger.error(f"Workflow execution failed: {e}")

        return results

    def benchmark_workflow_scalability(
        self,
        base_query: str,
        concurrency_levels: List[int] = [1, 2, 3, 5],
        num_runs_per_level: int = 2
    ) -> Dict[int, List[WorkflowBenchmarkResult]]:
        """
        测试工作流可扩展性（不同并发级别下的性能）

        参数:
            base_query: 基础查询
            concurrency_levels: 并发级别列表
            num_runs_per_level: 每个级别的运行次数

        返回:
            不同并发级别的测试结果字典
        """
        scalability_results = {}

        for concurrency in concurrency_levels:
            logger.info(f"Testing scalability with {concurrency} concurrent workflows")

            # 为每个并发级别生成查询
            queries = [f"{base_query} (变体 {i+1})" for i in range(concurrency * num_runs_per_level)]

            # 执行测试
            results = self.benchmark_concurrent_workflows(
                queries=queries,
                max_concurrent=concurrency,
                auto_approve=True
            )

            scalability_results[concurrency] = results

            # 计算该并发级别的统计
            successful_results = [r for r in results if r.success]
            if successful_results:
                avg_duration = sum(r.total_duration for r in successful_results) / len(successful_results)
                success_rate = len(successful_results) / len(results) * 100
                logger.info(f"Concurrency {concurrency}: avg_duration={avg_duration:.2f}s, success_rate={success_rate:.1f}%")

        return scalability_results

    def benchmark_workflow_reliability(
        self,
        test_queries: List[str],
        num_runs_per_query: int = 3,
        auto_approve: bool = True
    ) -> List[WorkflowBenchmarkResult]:
        """
        测试工作流可靠性（多次运行的稳定性）

        参数:
            test_queries: 测试查询列表
            num_runs_per_query: 每个查询的运行次数
            auto_approve: 是否自动批准计划

        返回:
            可靠性测试结果列表
        """
        results = []

        for query in test_queries:
            logger.info(f"Testing reliability for query: {query}")

            for run in range(num_runs_per_query):
                workflow_id = f"reliability_{hash(query)}_{run}_{int(time.time() * 1000)}"
                result = self.benchmark_single_workflow(query, workflow_id, auto_approve)
                results.append(result)

                logger.info(f"Run {run + 1}/{num_runs_per_query} completed: success={result.success}, duration={result.total_duration:.2f}s")

        return results

    def run_comprehensive_benchmark(
        self,
        test_queries: List[str],
        include_scalability: bool = True,
        include_reliability: bool = True,
        include_concurrent: bool = True
    ) -> Dict[str, Any]:
        """
        运行全面的工作流性能测试

        参数:
            test_queries: 测试查询列表
            include_scalability: 是否包含可扩展性测试
            include_reliability: 是否包含可靠性测试
            include_concurrent: 是否包含并发测试

        返回:
            综合测试结果字典
        """
        logger.info("Starting comprehensive workflow benchmark...")

        results = {}

        # 1. 基础性能测试
        logger.info("Running basic performance benchmark...")
        basic_results = []
        for i, query in enumerate(test_queries):
            result = self.benchmark_single_workflow(query, f"basic_{i}")
            basic_results.append(result)

        results['basic_performance'] = basic_results

        # 2. 并发测试
        if include_concurrent:
            logger.info("Running concurrent workflow benchmark...")
            concurrent_results = self.benchmark_concurrent_workflows(
                queries=test_queries,
                max_concurrent=min(3, len(test_queries)),
                auto_approve=True
            )
            results['concurrent_performance'] = concurrent_results

        # 3. 可扩展性测试
        if include_scalability:
            logger.info("Running scalability benchmark...")
            scalability_results = self.benchmark_workflow_scalability(
                base_query=test_queries[0] if test_queries else "测试查询",
                concurrency_levels=[1, 2, 3],
                num_runs_per_level=2
            )
            results['scalability'] = scalability_results

        # 4. 可靠性测试
        if include_reliability:
            logger.info("Running reliability benchmark...")
            reliability_results = self.benchmark_workflow_reliability(
                test_queries=test_queries[:2],  # 只测试前两个查询
                num_runs_per_query=2,
                auto_approve=True
            )
            results['reliability'] = reliability_results

        # 合并所有结果
        all_results = []
        for benchmark_type, benchmark_results in results.items():
            if isinstance(benchmark_results, list):
                all_results.extend(benchmark_results)
            elif isinstance(benchmark_results, dict):
                for sub_results in benchmark_results.values():
                    if isinstance(sub_results, list):
                        all_results.extend(sub_results)

        self.results.extend(all_results)

        return results

    def save_results(self, output_path: str = "workflow_benchmark_results.json"):
        """
        保存测试结果到文件

        参数:
            output_path: 输出文件路径
        """
        results_dict = [result.to_dict() for result in self.results]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2)

        logger.info(f"Workflow benchmark results saved to {output_path}")

    def generate_report(self, results: Dict[str, Any]) -> str:
        """
        生成工作流性能测试报告

        参数:
            results: 测试结果字典

        返回:
            Markdown格式的报告
        """
        report_lines = [
            "# 工作流性能测试报告\n",
            f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            "## 总体统计\n"
        ]

        # 计算总体统计
        all_results = []
        for benchmark_type, benchmark_results in results.items():
            if isinstance(benchmark_results, list):
                all_results.extend(benchmark_results)
            elif isinstance(benchmark_results, dict):
                for sub_results in benchmark_results.values():
                    if isinstance(sub_results, list):
                        all_results.extend(sub_results)

        total_tests = len(all_results)
        successful_tests = sum(1 for r in all_results if r.success)
        success_rate = successful_tests / total_tests * 100 if total_tests > 0 else 0

        if all_results:
            avg_duration = sum(r.total_duration for r in all_results) / len(all_results)
            min_duration = min(r.total_duration for r in all_results)
            max_duration = max(r.total_duration for r in all_results)
        else:
            avg_duration = min_duration = max_duration = 0

        report_lines.extend([
            f"- 总测试数: {total_tests}",
            f"- 成功率: {success_rate:.1f}%"            f"- 平均执行时间: {avg_duration:.2f}秒",
            f"- 最短执行时间: {min_duration:.2f}秒",
            f"- 最长执行时间: {max_duration:.2f}秒\n",
            "## 详细测试结果\n"
        ])

        # 基础性能测试结果
        if 'basic_performance' in results and results['basic_performance']:
            basic_results = [r for r in results['basic_performance'] if r.success]
            if basic_results:
                avg_basic_duration = sum(r.total_duration for r in basic_results) / len(basic_results)
                success_rate_basic = len(basic_results) / len(results['basic_performance']) * 100

                report_lines.extend([
                    "### 基础性能测试",
                    f"- 测试数量: {len(results['basic_performance'])}",
                    f"- 成功率: {success_rate_basic:.1f}%",
                    f"- 平均执行时间: {avg_basic_duration:.2f}秒",
                    ""
                ])

        # 并发性能测试结果
        if 'concurrent_performance' in results and results['concurrent_performance']:
            concurrent_results = [r for r in results['concurrent_performance'] if r.success]
            if concurrent_results:
                avg_concurrent_duration = sum(r.total_duration for r in concurrent_results) / len(concurrent_results)
                success_rate_concurrent = len(concurrent_results) / len(results['concurrent_performance']) * 100

                report_lines.extend([
                    "### 并发性能测试",
                    f"- 测试数量: {len(results['concurrent_performance'])}",
                    f"- 成功率: {success_rate_concurrent:.1f}%",
                    f"- 平均执行时间: {avg_concurrent_duration:.2f}秒",
                    ""
                ])

        # 可扩展性测试结果
        if 'scalability' in results and results['scalability']:
            report_lines.append("### 可扩展性测试\n")
            for concurrency, scalability_results in results['scalability'].items():
                successful = [r for r in scalability_results if r.success]
                if successful:
                    avg_duration = sum(r.total_duration for r in successful) / len(successful)
                    success_rate = len(successful) / len(scalability_results) * 100

                    report_lines.extend([
                        f"#### 并发级别: {concurrency}",
                        f"- 测试数量: {len(scalability_results)}",
                        f"- 成功率: {success_rate:.1f}%",
                        f"- 平均执行时间: {avg_duration:.2f}秒",
                        ""
                    ])

        # 可靠性测试结果
        if 'reliability' in results and results['reliability']:
            reliability_results = [r for r in results['reliability'] if r.success]
            if reliability_results:
                success_rate_reliability = len(reliability_results) / len(results['reliability']) * 100

                # 按查询分组计算方差
                query_groups = {}
                for result in reliability_results:
                    if result.query not in query_groups:
                        query_groups[result.query] = []
                    query_groups[result.query].append(result.total_duration)

                avg_variance = sum(
                    sum((d - (sum(durations) / len(durations)))**2 for d in durations) / len(durations)
                    for durations in query_groups.values()
                ) / len(query_groups) if query_groups else 0

                report_lines.extend([
                    "### 可靠性测试",
                    f"- 测试数量: {len(results['reliability'])}",
                    f"- 成功率: {success_rate_reliability:.1f}%",
                    f"- 执行时间方差: {avg_variance:.4f}",
                    ""
                ])

        return "\n".join(report_lines)


def load_workflow_test_data(data_path: str = "benchmark/workflow_test_data.json") -> Dict[str, Any]:
    """
    加载工作流测试数据

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
                "什么是人工智能？请详细解释其主要分支和应用领域。",
                "分析当前机器学习的发展趋势和未来挑战。",
                "比较传统编程和机器学习方法的区别与联系。",
                "解释深度学习在图像识别中的应用原理。"
            ]
        }


def run_workflow_benchmark(
    config_path: Optional[str] = None,
    output_path: str = "workflow_benchmark_results.json",
    report_path: str = "workflow_benchmark_report.md"
):
    """
    运行工作流性能测试的主函数

    参数:
        config_path: 配置文件路径
        output_path: 结果输出路径
        report_path: 报告输出路径
    """
    # 加载测试数据
    test_data = load_workflow_test_data()

    # 创建性能测试器
    benchmark = WorkflowBenchmark(config_path)

    # 运行测试
    results = benchmark.run_comprehensive_benchmark(
        test_queries=test_data["queries"],
        include_scalability=True,
        include_reliability=True,
        include_concurrent=True
    )

    # 保存详细结果
    benchmark.save_results(output_path)

    # 生成并保存报告
    report = benchmark.generate_report(results)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info(f"Workflow benchmark completed. Results saved to {output_path}, report saved to {report_path}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 运行测试
    run_workflow_benchmark()
