"""
Rapporteur Agent

该模块实现了报告生成智能体（Rapporteur agent），其核心职责是生成最终的研究报告。
"""

from typing import Dict, List
from datetime import datetime
from ..workflow.state import ResearchState
from ..llm.base import BaseLLM
from ..prompts.loader import PromptLoader


class Rapporteur:
    """
    报告生成智能体（Rapporteur agent） —— 报告生成组件

    职责：
    - 汇总研究发现
    - 整理收集到的信息
    - 生成结构化报告（Markdown 或 HTML 格式）
    - 格式化引用格式与参考文献
    - 确保报告的连贯性与可读性
    """

    def __init__(self, llm: BaseLLM):
        """
        初始化报告生成智能体

        参数:
            llm: 用于生成报告的大语言模型实例
        """
        self.llm = llm
        self.prompt_loader = PromptLoader()

    def generate_report(self, state: ResearchState) -> ResearchState:
        """
        生成一份全面的研究报告

        参数:
            state: 包含所有研究结果的当前研究状态

        返回:
            包含最终报告的更新后状态
        """
        query = state['query']
        plan = state.get('research_plan', {})
        results = state.get('research_results', [])
        output_format = state.get('output_format', 'markdown')

        # 汇总研究发现
        summary = self._summarize_findings(query, results)

        # 整理信息
        organized_info = self._organize_information(summary, results)

        # 根据指定格式生成报告
        if output_format == 'html':
            report = self._generate_html_report(
                query=query,
                plan=plan,
                summary=summary,
                organized_info=organized_info,
                results=results
            )
        else:
            # 默认使用 Markdown 格式
            report = self._generate_markdown_report(
                query=query,
                plan=plan,
                summary=summary,
                organized_info=organized_info,
                results=results
            )

        # 更新状态
        state['final_report'] = report
        state['current_step'] = 'completed'

        return state

    def _summarize_findings(self, query: str, results: List[Dict]) -> str:
        """
        汇总所有研究发现

        参数:
            query: 研究查询语句
            results: 研究结果列表

        返回:
            研究发现的汇总内容
        """
        # 编译所有结果摘要
        all_content = []
        for result in results:
            for item in result.get('results', []):
                all_content.append(f"- {item.get('title', 'No title')}: {item.get('snippet', '')[:200]}")

        content_text = '\n'.join(all_content[:30])  # Limit to 30 items

        prompt = self.prompt_loader.load(
            'rapporteur_summarize',
            query=query,
            research_findings=content_text
        )

        summary = self.llm.generate(prompt, temperature=0.5, max_tokens=2000)
        return summary

    def _organize_information(self, summary: str, results: List[Dict]) -> Dict:
        """
        将信息整理为结构化章节

        参数:
            summary: 研究汇总内容
            results: 研究结果列表

        返回:
            结构化的信息整理结果
        """
        # 使用大预言模型提取核心主题
        prompt = self.prompt_loader.load(
            'rapporteur_organize_info',
            summary=summary
        )

        response = self.llm.generate(prompt, temperature=0.5)

        # 尝试解析 JSON 格式
        import json
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response[start:end]
                organized = json.loads(json_str)
                return organized
        except json.JSONDecodeError:
            pass

        # 备用结构
        return {
            'themes': [
                {
                    'name': '核心发现',
                    'key_points': [summary[:500]]
                }
            ]
        }

    def _generate_markdown_report(
        self,
        query: str,
        plan: Dict,
        summary: str,
        organized_info: Dict,
        results: List[Dict]
    ) -> str:
        """
        生成一份结构化的 Markdown 格式报告

        参数:
            query: 研究查询语句
            plan: 研究计划
            summary: 研究汇总内容
            organized_info: 整理后的结构化信息
            results: 研究结果

        返回:
            Markdown 格式的报告字符串
        """
        # 构建报告各个章节
        sections = []

        # 标题
        sections.append(f"# 研究报告：{query}\n")

        # 元数据
        sections.append(f"**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        sections.append(f"**研究目标：** {plan.get('research_goal', query)}\n")
        sections.append(f"**信息来源数量：** {len(results)}\n")

        # 执行摘要
        sections.append("\n## 执行摘要\n")
        sections.append(summary)

        # 核心发现（按主题分类）
        sections.append("\n## 核心发现\n")
        for theme in organized_info.get('themes', []):
            sections.append(f"\n### {theme['name']}\n")
            for point in theme.get('key_points', []):
                sections.append(f"- {point}\n")

        # 综合分析（新增：生成整合式分析，而非简单罗列）
        sections.append("\n## 深度分析\n")
        sections.append(self._generate_synthesized_analysis(query, summary, organized_info, results))

        # 参考资料
        sections.append("\n## 参考资料\n")
        sections.append(self._format_citations(results))

        # 结论
        sections.append("\n## 结论\n")
        sections.append(self._generate_conclusion(query, summary))

        return '\n'.join(sections)

    def _format_detailed_results(self, results: List[Dict]) -> str:
        """
        格式化详细结果章节

        参数:
            results: 研究结果

        返回:
            格式化后的结果字符串
        """
        formatted = []
        result_num = 1

        for result in results:
            source = result.get('source', 'Unknown')
            query = result.get('query', 'N/A')

            formatted.append(f"\n### Source: {source.capitalize()}")
            formatted.append(f"**Query:** {query}\n")

            for item in result.get('results', [])[:5]:  # Top 5 per source
                title = item.get('title', 'No title')
                snippet = item.get('snippet', 'No description')
                url = item.get('url', '')

                formatted.append(f"{result_num}. **{title}**")
                if url:
                    formatted.append(f"   - URL: {url}")
                formatted.append(f"   - {snippet[:300]}...\n")
                result_num += 1

        return '\n'.join(formatted)

    def _format_citations(self, results: List[Dict]) -> str:
        """
        格式化引用格式与参考文献

        参数:
            results: 研究结果

        返回:
            格式化后的引用内容
        """
        citations = []
        citation_num = 1

        for result in results:
            for item in result.get('results', []):
                title = item.get('title', 'Untitled')
                url = item.get('url', '')
                source = result.get('source', 'Unknown')

                if url:
                    citations.append(f"{citation_num}. {title} - {source.capitalize()} - [{url}]({url})")
                else:
                    citations.append(f"{citation_num}. {title} - {source.capitalize()}")

                citation_num += 1

        return '\n'.join(citations[:50])  # Limit to 50 citations

    def _generate_synthesized_analysis(
        self,
        query: str,
        summary: str,
        organized_info: Dict,
        results: List[Dict]
    ) -> str:
        """
        生成整合所有研究发现的综合分析

        参数:
            query: 研究查询语句
            summary: 研究汇总内容
            organized_info: 整理后的核心主题
            results: 研究结果

        返回:
            整合后的分析文本
        """
        # 从结果中提取关键内容
        key_content = []
        for result in results[:10]:  # 限制取前10条研究结果
            for item in result.get('results', [])[:3]:  # 每条结果取前三条详情
                key_content.append(f"- {item.get('snippet', '')[:300]}")

        content_text = '\n'.join(key_content)

        prompt = self.prompt_loader.load(
            'rapporteur_synthesized_analysis',
            query=query,
            summary=summary[:1500],
            key_content=content_text
        )

        analysis = self.llm.generate(prompt, temperature=0.6, max_tokens=2000)
        return analysis

    def _generate_conclusion(self, query: str, summary: str) -> str:
        """
        生成报告的结论章节

        参数:
            query: 研究查询语句
            summary: 研究汇总内容

        返回:
            结论文本
        """
        prompt = self.prompt_loader.load(
            'rapporteur_conclusion',
            query=query,
            summary=summary[:1000]
        )

        conclusion = self.llm.generate(prompt, temperature=0.5, max_tokens=800)
        return conclusion

    def _generate_html_report(
        self,
        query: str,
        plan: Dict,
        summary: str,
        organized_info: Dict,
        results: List[Dict]
    ) -> str:
        """
        生成一份结构化的 HTML 格式报告

        参数:
            query: 研究查询语句
            plan: 研究计划
            summary: 研究汇总内容
            organized_info: 整理后的结构化信息
            results: 研究结果

        返回:
            HTML 格式的报告字符串
        """
        # 生成分析内容与结论
        analysis = self._generate_synthesized_analysis(query, summary, organized_info, results)
        conclusion = self._generate_conclusion(query, summary)

        # 将核心主题格式化为适用于 HTML 的文本
        themes_text = ""
        for theme in organized_info.get('themes', []):
            themes_text += f"<h3>{theme['name']}</h3>\n<ul>\n"
            for point in theme.get('key_points', []):
                themes_text += f"<li>{point}</li>\n"
            themes_text += "</ul>\n"

        # 格式化参考文献
        citations = self._format_citations(results)

        # 使用大语言模型生成 HTML 内容
        prompt = self.prompt_loader.load(
            'rapporteur_generate_html',
            query=query,
            research_goal=plan.get('research_goal', query),
            summary=summary,
            themes=themes_text,
            analysis=analysis,
            citations=citations,
            conclusion=conclusion
        )

        html_report = self.llm.generate(prompt, temperature=0.3, max_tokens=4000)

        # 清理 HTML 内容（移除大语言模型可能添加的 Markdown 代码块标记）
        if '```html' in html_report:
            html_report = html_report.split('```html')[1].split('```')[0].strip()
        elif '```' in html_report:
            html_report = html_report.split('```')[1].split('```')[0].strip()

        return html_report

    def save_report(self, report: str, filepath: str) -> bool:
        """
        将报告保存到文件

        参数:
            report: 报告内容
            filepath: 报告保存路径

        返回:
            保存成功返回 True，失败返回 False
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            return True
        except Exception as e:
            print(f"Error saving report: {e}")
            return False

    def __repr__(self) -> str:
        """类的字符串表示形式"""
        return f"Rapporteur(llm={self.llm})"
