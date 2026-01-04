"""
批量运行基准测试

该脚本用于批量执行所有性能测试，并生成综合报告。
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from benchmark.agent_benchmark import run_agent_benchmark
from benchmark.rag_benchmark import run_rag_benchmark
from benchmark.workflow_benchmark import run_workflow_benchmark
from benchmark.test_data_generator import TestDataGenerator

logger = logging.getLogger(__name__)


def load_config(config_path: str = "benchmark/benchmark_config.json") -> dict:
    """
    加载配置文件

    参数:
        config_path: 配置文件路径

    返回:
        配置字典
    """
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return {
            "agent_benchmark": {"enabled": True},
            "rag_benchmark": {"enabled": True},
            "workflow_benchmark": {"enabled": True},
            "output": {
                "results_dir": "benchmark/results",
                "reports_dir": "benchmark/reports"
            },
            "data": {"regenerate_data": True}
        }


def setup_directories(config: dict):
    """创建必要的目录"""
    results_dir = config["output"]["results_dir"]
    reports_dir = config["output"]["reports_dir"]

    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    return results_dir, reports_dir


def generate_test_data_if_needed(config: dict):
    """根据配置生成测试数据"""
    if config["data"].get("regenerate_data", False):
        logger.info("Regenerating test data...")
        generator = TestDataGenerator()
        generator.generate_comprehensive_test_data(
            num_queries=config["data"].get("num_queries", 20),
            num_documents=config["data"].get("num_documents", 50)
        )
    else:
        logger.info("Using existing test data")


def run_all_benchmarks(config: dict, results_dir: str, reports_dir: str):
    """运行所有启用的基准测试"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Agent性能测试
    if config["agent_benchmark"].get("enabled", True):
        logger.info("Running Agent benchmark...")
        try:
            agent_results = os.path.join(results_dir, f"agent_benchmark_{timestamp}.json")
            agent_report = os.path.join(reports_dir, f"agent_benchmark_{timestamp}.md")

            run_agent_benchmark(
                config_path=None,  # 使用默认配置
                output_path=agent_results,
                report_path=agent_report
            )
            logger.info("Agent benchmark completed successfully")
        except Exception as e:
            logger.error(f"Agent benchmark failed: {e}")

    # 2. RAG性能测试
    if config["rag_benchmark"].get("enabled", True):
        logger.info("Running RAG benchmark...")
        try:
            rag_results = os.path.join(results_dir, f"rag_benchmark_{timestamp}.json")
            rag_report = os.path.join(reports_dir, f"rag_benchmark_{timestamp}.md")

            run_rag_benchmark(
                config_path=None,  # 使用默认配置
                output_path=rag_results,
                report_path=rag_report
            )
            logger.info("RAG benchmark completed successfully")
        except Exception as e:
            logger.error(f"RAG benchmark failed: {e}")

    # 3. 工作流性能测试
    if config["workflow_benchmark"].get("enabled", True):
        logger.info("Running Workflow benchmark...")
        try:
            workflow_results = os.path.join(results_dir, f"workflow_benchmark_{timestamp}.json")
            workflow_report = os.path.join(reports_dir, f"workflow_benchmark_{timestamp}.md")

            run_workflow_benchmark(
                config_path=None,  # 使用默认配置
                output_path=workflow_results,
                report_path=workflow_report
            )
            logger.info("Workflow benchmark completed successfully")
        except Exception as e:
            logger.error(f"Workflow benchmark failed: {e}")


def generate_comprehensive_report(config: dict, results_dir: str, reports_dir: str):
    """生成综合测试报告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(reports_dir, f"comprehensive_report_{timestamp}.md")

    report_content = f"""# ResearchSync-Agent 综合性能测试报告

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 测试概览

本次测试包含以下模块：

### 已执行测试
"""

    # 检查哪些测试已执行
    executed_tests = []
    if config["agent_benchmark"].get("enabled", True):
        executed_tests.append("- ✅ Agent性能测试")
    if config["rag_benchmark"].get("enabled", True):
        executed_tests.append("- ✅ RAG性能测试")
    if config["workflow_benchmark"].get("enabled", True):
        executed_tests.append("- ✅ 工作流性能测试")

    report_content += "\n".join(executed_tests) + "\n\n"

    # 汇总各测试的结果
    report_content += "## 测试结果汇总\n\n"

    # 读取并汇总各测试报告
    for test_type in ["agent", "rag", "workflow"]:
        report_file = None
        for file in os.listdir(reports_dir):
            if file.startswith(f"{test_type}_benchmark_") and file.endswith(".md"):
                report_file = os.path.join(reports_dir, file)
                break

        if report_file:
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 提取关键统计信息
                    lines = content.split('\n')
                    key_stats = []
                    in_summary = False
                    for line in lines:
                        if "## 总体统计" in line:
                            in_summary = True
                        elif in_summary and line.startswith("##"):
                            break
                        elif in_summary and line.startswith("- "):
                            key_stats.append(f"  {line}")

                    if key_stats:
                        report_content += f"### {test_type.title()} 测试结果\n"
                        report_content += "\n".join(key_stats) + "\n\n"
            except Exception as e:
                logger.warning(f"Failed to read {test_type} report: {e}")

    # 添加性能分析
    report_content += """## 性能分析建议

### 优化建议

1. **响应时间优化**
   - 分析各组件的瓶颈点
   - 考虑缓存策略
   - 优化数据库查询

2. **资源使用优化**
   - 监控内存使用情况
   - 优化并发处理
   - 考虑分布式部署

3. **准确性提升**
   - 改进检索算法
   - 优化提示词工程
   - 增强数据质量

### 后续测试建议

1. **压力测试**: 在更高负载下测试系统性能
2. **长时间运行测试**: 验证系统的稳定性和内存泄漏
3. **端到端集成测试**: 测试完整用户工作流
4. **A/B测试**: 比较不同配置下的性能差异

---

*报告由自动化测试系统生成*
"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logger.info(f"Comprehensive report generated: {report_path}")


def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting ResearchSync-Agent benchmark suite...")

    # 加载配置
    config = load_config()
    logger.info("Configuration loaded")

    # 创建目录
    results_dir, reports_dir = setup_directories(config)
    logger.info(f"Directories created: {results_dir}, {reports_dir}")

    # 生成测试数据
    generate_test_data_if_needed(config)

    # 运行所有基准测试
    run_all_benchmarks(config, results_dir, reports_dir)

    # 生成综合报告
    generate_comprehensive_report(config, results_dir, reports_dir)

    logger.info("All benchmarks completed successfully!")
    logger.info(f"Results saved to: {results_dir}")
    logger.info(f"Reports saved to: {reports_dir}")


if __name__ == "__main__":
    main()
