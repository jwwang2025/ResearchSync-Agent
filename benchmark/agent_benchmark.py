"""
Agent性能测试

该模块提供对各种Agent的性能测试功能，包括：
- 响应时间测试
- 准确性评估
- 资源使用情况监控
- 压力测试
"""

import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Agent相关导入
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
class BenchmarkResult:
    """性能测试结果数据类"""
    agent_name: str
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


class AgentBenchmark:
    """Agent性能测试器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化Agent性能测试器

        参数:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        self.config = Config(config_path) if config_path else Config()
        self.llm_factory = LLMFactory()
        self.results: List[BenchmarkResult] = []

        # 初始化LLM实例
        llm_config = self.config.get('llm', {})
        self.llm = self.llm_factory.create_llm(
            provider=llm_config.get('provider', 'deepseek'),
            api_key=llm_config.get('api_key', ''),
            model=llm_config.get('model'),
            temperature=llm_config.get('temperature', 0.7)
        )

        # 初始化Agent实例
        self.agents = self._initialize_agents()

    def _initialize_agents(self) -> Dict[str, Any]:
        """初始化所有Agent实例"""
        agents = {}

        try:
            agents['coordinator'] = Coordinator(self.llm)
            agents['planner'] = Planner(self.llm)
            agents['researcher'] = Researcher(self.llm)
            agents['rapporteur'] = Rapporteur(self.llm)
            logger.info("Successfully initialized all agents")
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            raise

        return agents

    def benchmark_coordinator(self, test_queries: List[str]) -> List[BenchmarkResult]:
        """
        测试协调器性能

        参数:
            test_queries: 测试查询列表

        返回:
            性能测试结果列表
        """
        results = []
        coordinator = self.agents['coordinator']

        for query in test_queries:
            start_time = time.time()

            try:
                # 测试查询分类
                query_type = coordinator.classify_query(query)
                duration_classify = time.time() - start_time

                # 测试初始化研究
                start_time = time.time()
                state = coordinator.initialize_research(query)
                duration_init = time.time() - start_time

                # 记录结果
                results.append(BenchmarkResult(
                    agent_name="coordinator",
                    operation="classify_query",
                    duration=duration_classify,
                    success=True,
                    metrics={"query_type": query_type, "query_length": len(query)}
                ))

                results.append(BenchmarkResult(
                    agent_name="coordinator",
                    operation="initialize_research",
                    duration=duration_init,
                    success=True,
                    metrics={"has_simple_response": state.get('simple_response') is not None}
                ))

            except Exception as e:
                results.append(BenchmarkResult(
                    agent_name="coordinator",
                    operation="query_processing",
                    duration=time.time() - start_time,
                    success=False,
                    error_message=str(e)
                ))

        return results

    def benchmark_planner(self, test_queries: List[str]) -> List[BenchmarkResult]:
        """
        测试规划器性能

        参数:
            test_queries: 测试查询列表

        返回:
            性能测试结果列表
        """
        results = []
        planner = self.agents['planner']

        for query in test_queries:
            start_time = time.time()

            try:
                # 创建初始状态
                initial_state = {
                    'query': query,
                    'query_type': 'RESEARCH',
                    'research_plan': None,
                    'plan_approved': False,
                    'current_step': 'planning'
                }

                # 测试创建计划
                plan_state = planner.create_plan(initial_state)
                duration = time.time() - start_time

                # 分析计划质量
                plan = plan_state.get('research_plan', {})
                plan_metrics = {
                    'has_plan': plan is not None,
                    'plan_length': len(str(plan)),
                    'num_tasks': len(plan.get('tasks', [])),
                    'has_milestones': 'milestones' in plan,
                    'has_resources': 'resources' in plan
                }

                results.append(BenchmarkResult(
                    agent_name="planner",
                    operation="create_plan",
                    duration=duration,
                    success=True,
                    metrics=plan_metrics
                ))

            except Exception as e:
                results.append(BenchmarkResult(
                    agent_name="planner",
                    operation="create_plan",
                    duration=time.time() - start_time,
                    success=False,
                    error_message=str(e)
                ))

        return results

    def benchmark_researcher(self, test_tasks: List[Dict[str, Any]]) -> List[BenchmarkResult]:
        """
        测试研究员性能

        参数:
            test_tasks: 测试任务列表，每个任务包含query和context

        返回:
            性能测试结果列表
        """
        results = []
        researcher = self.agents['researcher']

        for task in test_tasks:
            start_time = time.time()

            try:
                # 创建研究状态
                research_state = {
                    'query': task['query'],
                    'current_task': {
                        'id': 'test_task',
                        'description': task['query'],
                        'type': 'research',
                        'context': task.get('context', [])
                    },
                    'research_results': [],
                    'current_step': 'researching'
                }

                # 执行研究任务
                result_state = researcher.execute_research(research_state)
                duration = time.time() - start_time

                # 分析研究结果
                research_results = result_state.get('research_results', [])
                result_metrics = {
                    'num_results': len(research_results),
                    'has_findings': any(r.get('findings') for r in research_results),
                    'has_sources': any(r.get('sources') for r in research_results),
                    'total_findings': sum(len(r.get('findings', [])) for r in research_results)
                }

                results.append(BenchmarkResult(
                    agent_name="researcher",
                    operation="execute_research",
                    duration=duration,
                    success=True,
                    metrics=result_metrics
                ))

            except Exception as e:
                results.append(BenchmarkResult(
                    agent_name="researcher",
                    operation="execute_research",
                    duration=time.time() - start_time,
                    success=False,
                    error_message=str(e)
                ))

        return results

    def benchmark_rapporteur(self, test_data: List[Dict[str, Any]]) -> List[BenchmarkResult]:
        """
        测试报告生成器性能

        参数:
            test_data: 测试数据列表，每个包含research_results

        返回:
            性能测试结果列表
        """
        results = []
        rapporteur = self.agents['rapporteur']

        for data in test_data:
            start_time = time.time()

            try:
                # 创建报告生成状态
                report_state = {
                    'query': data['query'],
                    'research_results': data['research_results'],
                    'final_report': None,
                    'current_step': 'reporting',
                    'output_format': 'markdown'
                }

                # 生成报告
                final_state = rapporteur.generate_report(report_state)
                duration = time.time() - start_time

                # 分析报告质量
                report = final_state.get('final_report', '')
                report_metrics = {
                    'report_length': len(report),
                    'has_sections': '##' in report,  # 检查是否有章节
                    'has_conclusion': '结论' in report or '总结' in report,
                    'word_count': len(report.split()) if report else 0
                }

                results.append(BenchmarkResult(
                    agent_name="rapporteur",
                    operation="generate_report",
                    duration=duration,
                    success=True,
                    metrics=report_metrics
                ))

            except Exception as e:
                results.append(BenchmarkResult(
                    agent_name="rapporteur",
                    operation="generate_report",
                    duration=time.time() - start_time,
                    success=False,
                    error_message=str(e)
                ))

        return results

    def run_comprehensive_benchmark(
        self,
        test_queries: List[str],
        test_tasks: List[Dict[str, Any]],
        test_reports: List[Dict[str, Any]],
        num_threads: int = 4
    ) -> Dict[str, List[BenchmarkResult]]:
        """
        运行全面的Agent性能测试

        参数:
            test_queries: 测试查询列表
            test_tasks: 测试任务列表
            test_reports: 测试报告数据列表
            num_threads: 并行线程数

        返回:
            各Agent的测试结果字典
        """
        logger.info("Starting comprehensive agent benchmark...")

        # 并行执行不同Agent的测试
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {
                'coordinator': executor.submit(self.benchmark_coordinator, test_queries),
                'planner': executor.submit(self.benchmark_planner, test_queries),
                'researcher': executor.submit(self.benchmark_researcher, test_tasks),
                'rapporteur': executor.submit(self.benchmark_rapporteur, test_reports)
            }

            results = {}
            for agent_name, future in futures.items():
                try:
                    results[agent_name] = future.result()
                    logger.info(f"Completed benchmark for {agent_name}")
                except Exception as e:
                    logger.error(f"Failed to benchmark {agent_name}: {e}")
                    results[agent_name] = []

        # 合并所有结果
        self.results.extend([r for agent_results in results.values() for r in agent_results])

        return results

    def save_results(self, output_path: str = "benchmark_results.json"):
        """
        保存测试结果到文件

        参数:
            output_path: 输出文件路径
        """
        results_dict = [result.to_dict() for result in self.results]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, ensure_ascii=False, indent=2)

        logger.info(f"Benchmark results saved to {output_path}")

    def generate_report(self, results: Dict[str, List[BenchmarkResult]]) -> str:
        """
        生成性能测试报告

        参数:
            results: 测试结果字典

        返回:
            Markdown格式的报告
        """
        report_lines = [
            "# Agent性能测试报告\n",
            f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            "## 总体统计\n"
        ]

        # 计算总体统计
        total_tests = sum(len(agent_results) for agent_results in results.values())
        successful_tests = sum(
            sum(1 for r in agent_results if r.success)
            for agent_results in results.values()
        )
        success_rate = successful_tests / total_tests * 100 if total_tests > 0 else 0

        report_lines.extend([
            f"- 总测试数: {total_tests}",
            f"- 成功率: {success_rate:.1f}%\n",
            "## 各Agent详细结果\n"
        ])

        # 各Agent统计
        for agent_name, agent_results in results.items():
            if not agent_results:
                continue

            successful = sum(1 for r in agent_results if r.success)
            total = len(agent_results)
            avg_duration = sum(r.duration for r in agent_results) / total

            report_lines.extend([
                f"### {agent_name.title()} Agent",
                f"- 测试数量: {total}",
                f"- 成功率: {successful/total*100:.1f}%" if total > 0 else "- 成功率: 0%",
                f"- 平均响应时间: {avg_duration:.3f}秒",
                ""
            ])

            # 各操作统计
            operations = {}
            for result in agent_results:
                op = result.operation
                if op not in operations:
                    operations[op] = []
                operations[op].append(result)

            for op_name, op_results in operations.items():
                op_successful = sum(1 for r in op_results if r.success)
                op_avg_duration = sum(r.duration for r in op_results) / len(op_results)
                report_lines.extend([
                    f"#### {op_name}",
                    f"- 执行次数: {len(op_results)}",
                    f"- 成功率: {op_successful/len(op_results)*100:.1f}%" if op_results else "- 成功率: 0%",
                    f"- 平均时间: {op_avg_duration:.3f}秒",
                    ""
                ])

        return "\n".join(report_lines)


def load_test_data(data_path: str = "benchmark/test_data.json") -> Dict[str, Any]:
    """
    加载测试数据

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
                "请介绍一下深度学习的发展历程",
                "人工智能在医疗领域的应用有哪些？",
                "你好，请介绍一下自己"
            ],
            "tasks": [
                {
                    "query": "机器学习算法",
                    "context": ["监督学习", "无监督学习", "强化学习"]
                },
                {
                    "query": "神经网络结构",
                    "context": ["卷积神经网络", "循环神经网络", "Transformer"]
                }
            ],
            "reports": [
                {
                    "query": "AI发展趋势",
                    "research_results": [
                        {
                            "task_id": "research_1",
                            "findings": ["AI正在快速发展", "应用领域广泛"],
                            "sources": ["论文1", "论文2"]
                        }
                    ]
                }
            ]
        }


def run_agent_benchmark(
    config_path: Optional[str] = None,
    output_path: str = "agent_benchmark_results.json",
    report_path: str = "agent_benchmark_report.md"
):
    """
    运行Agent性能测试的主函数

    参数:
        config_path: 配置文件路径
        output_path: 结果输出路径
        report_path: 报告输出路径
    """
    # 加载测试数据
    test_data = load_test_data()

    # 创建性能测试器
    benchmark = AgentBenchmark(config_path)

    # 运行测试
    results = benchmark.run_comprehensive_benchmark(
        test_queries=test_data["queries"],
        test_tasks=test_data["tasks"],
        test_reports=test_data["reports"]
    )

    # 保存详细结果
    benchmark.save_results(output_path)

    # 生成并保存报告
    report = benchmark.generate_report(results)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info(f"Agent benchmark completed. Results saved to {output_path}, report saved to {report_path}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 运行测试
    run_agent_benchmark()
