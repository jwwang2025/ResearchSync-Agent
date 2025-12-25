"""
DeepSeek 大语言模型（LLM）实现

DeepSeek 采用兼容 OpenAI 规范的 API，因此可直接使用 OpenAI 客户端进行调用。
"""

from typing import Iterator
import httpx
from openai import OpenAI
from .base import BaseLLM


class DeepSeekLLM(BaseLLM):
    """
    DeepSeek 大语言模型（LLM）实现类。

    通过兼容 OpenAI 规范的 API 实现对 DeepSeek 系列模型的调用。
    """

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
        timeout: float = 60.0,
        **kwargs
    ):
        """
        初始化 DeepSeek 大语言模型实例。

        参数:
            api_key: DeepSeek 平台的 API 密钥
            model: 模型名称（默认值：deepseek-chat）
            base_url: API 基础地址（默认值：https://api.deepseek.com）
            timeout: 请求超时时间（单位：秒，默认值：60.0）
            **kwargs: 额外的配置参数
        """
        super().__init__(api_key, model, **kwargs)
        # 若未传入 base_url 则使用默认值
        if base_url is None:
            base_url = "https://api.deepseek.com"
        # 采用与测试脚本一致的超时配置
        # 连接超时设为30秒，读取超时设为120秒，提升请求可靠性
        timeout_config = httpx.Timeout(30.0, read=120.0)
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_config
        )

    def generate(self, prompt: str, **kwargs) -> str:
        """
        调用 DeepSeek API 生成文本。

        参数:
            prompt: 输入提示词
            **kwargs: 额外的生成参数（如temperature温度、max_tokens最大令牌数等）

        返回:
            生成的文本内容
        """
        # 合并默认配置与传入的参数
        params = {**self.config, **kwargs}

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **params
        )
        return response.choices[0].message.content

    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        通过 DeepSeek API 流式生成文本（逐块返回）。

        参数:
            prompt: 输入提示词
            **kwargs: 额外的生成参数

        生成器输出:
            逐块返回的文本内容（流式输出的每个文本片段）
        """
        # 合并默认配置与传入的参数
        params = {**self.config, **kwargs}

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **params
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
