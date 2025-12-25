"""
OpenAI 大语言模型（LLM）实现
"""

from typing import Iterator
import httpx
from openai import OpenAI
from .base import BaseLLM


class OpenAILLM(BaseLLM):
    """
    OpenAI 大语言模型（LLM）实现类。

    支持 GPT-4、GPT-3.5-turbo 及其他 OpenAI 系列模型。
    """

    def __init__(self, api_key: str, model: str = "gpt-4", base_url: str = None, timeout: float = 60.0, **kwargs):
        """
        初始化 OpenAI 大语言模型实例。

        参数:
            api_key: OpenAI 平台的 API 密钥
            model: 模型名称（默认值：gpt-4）
            base_url: 用于代理的 API 基础地址（可选，如自定义代理/中转地址）
            timeout: 请求超时时间（单位：秒，默认值：60.0）
            **kwargs: 额外的配置参数
        """
        super().__init__(api_key, model, **kwargs)
        # 采用与 DeepSeek 实现一致的超时配置
        # 连接超时设为30秒，读取超时设为120秒，提升请求可靠性
        timeout_config = httpx.Timeout(30.0, read=120.0)
        # 若传入base_url则使用（用于代理场景），否则使用OpenAI默认API地址
        client_kwargs = {"api_key": api_key, "timeout": timeout_config}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = OpenAI(**client_kwargs)

    def generate(self, prompt: str, **kwargs) -> str:
        """
        调用 OpenAI API 生成文本。

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
        通过 OpenAI API 流式生成文本（逐块返回）。

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
