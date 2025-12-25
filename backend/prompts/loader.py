"""
提示词加载器

该模块提供加载和渲染提示词模板的功能。
"""

import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template


class PromptLoader:
    """
    集中式提示词管理系统。

    从Markdown文件加载提示词模板，并结合变量渲染模板内容。
    """

    def __init__(self, prompts_dir: str = None):
        """
        初始化提示词加载器。

        参数:
            prompts_dir: 包含提示词模板的目录路径。
                        若为None，则使用默认的提示词目录（当前文件所在目录）。
        """
        if prompts_dir is None:
            # 默认使用当前文件所在目录作为提示词目录
            prompts_dir = Path(__file__).parent

        self.prompts_dir = Path(prompts_dir)

        # 初始化 Jinja2 环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.prompts_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )

    def load(self, prompt_name: str, **variables: Any) -> str:
        """
        加载并渲染提示词模板。

        参数:
            prompt_name: 提示词文件名（无需传入.md扩展名）
            **variables: 用于模板渲染的变量（键值对形式）

        返回:
            渲染完成的提示词字符串

        异常:
            FileNotFoundError: 当指定的提示词文件不存在时抛出
        """
        # 默认添加当前时间变量
        if 'CURRENT_TIME' not in variables:
            variables['CURRENT_TIME'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 加载并渲染模板
        try:
            template = self.env.get_template(f"{prompt_name}.md")
            rendered = template.render(**variables)
            return rendered
        except Exception as e:
            raise FileNotFoundError(
                f"Could not load prompt '{prompt_name}' from {self.prompts_dir}: {e}"
            )

    def load_raw(self, prompt_name: str) -> str:
        """
        加载提示词模板（不执行渲染）。

        参数:
            prompt_name: 提示词文件名（无需传入.md扩展名）

        返回:
            原始的提示词模板字符串

        异常:
            FileNotFoundError: 当指定的提示词文件不存在时抛出
        """
        prompt_path = self.prompts_dir / f"{prompt_name}.md"

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}"
            )

        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def render_string(self, template_str: str, **variables: Any) -> str:
        """
        渲染模板字符串（结合变量）。

        参数:
            template_str: 待渲染的模板字符串
            **variables: 用于模板渲染的变量（键值对形式）

        返回:
            渲染完成的字符串
        """
        # 默认添加当前时间变量（若未传入）
        if 'CURRENT_TIME' not in variables:
            variables['CURRENT_TIME'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        template = Template(template_str)
        return template.render(**variables)


# 全局实例，方便快速使用
_default_loader = None


def get_default_loader() -> PromptLoader:
    """
    获取默认的全局PromptLoader实例。

    返回:
        默认的PromptLoader实例
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = PromptLoader()
    return _default_loader
