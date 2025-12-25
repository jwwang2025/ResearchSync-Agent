"""
Claude 大语言模型（LLM）实现
"""

from typing import Iterator
from anthropic import Anthropic
from .base import BaseLLM


class ClaudeLLM(BaseLLM):
    """
    Anthropic Claude 大语言模型（LLM）实现类。

     支持 Claude 3.5 Sonnet、Claude 3 Opus 及其他 Claude 系列模型。
    """

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", **kwargs):
        """
        初始化 Claude 大语言模型实例。

        参数:
            api_key: Anthropic 平台的 API 密钥
            model: 模型名称（默认值：claude-3-5-sonnet-20241022）
            **kwargs: 额外的配置参数
        """
        super().__init__(api_key, model, **kwargs)
        self.client = Anthropic(api_key=api_key)

    def generate(self, prompt: str, **kwargs) -> str:
        """
        调用 Claude API 生成文本。

        参数:
            prompt: 输入提示词
            **kwargs: 额外的生成参数（如temperature温度、max_tokens最大令牌数等）

        返回:
            生成的文本内容
        """
        # 合并默认配置与传入的参数
        params = {**self.config, **kwargs}

        # 若未传入max_tokens则设置默认值（避免接口参数缺失）
        if 'max_tokens' not in params:
            params['max_tokens'] = 4096

        response = self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **params
        )
        return response.content[0].text

    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        通过 Claude API 流式生成文本（逐块返回）。

        参数:
            prompt: 输入提示词
            **kwargs: 额外的生成参数

        生成器输出:
            逐块返回的文本内容（流式输出的每个文本片段）
        """
        # 合并默认配置与传入的参数
        params = {**self.config, **kwargs}

        # 若未传入max_tokens则设置默认值（避免接口参数缺失）
        if 'max_tokens' not in params:
            params['max_tokens'] = 4096

        with self.client.messages.stream(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **params
        ) as stream:
            for text in stream.text_stream:
                yield text
