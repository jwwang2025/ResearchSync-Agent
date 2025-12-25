"""
Google Gemini 大语言模型（LLM）实现
"""

from typing import Iterator
import google.generativeai as genai
from .base import BaseLLM


class GeminiLLM(BaseLLM):
    """
    Google Gemini 大语言模型（LLM）实现类。

    支持 Gemini Pro、Gemini Ultra 及其他 Gemini 系列模型。
    """

    def __init__(self, api_key: str, model: str = "gemini-pro", **kwargs):
        """
        初始化 Gemini 大语言模型实例。

        参数:
            api_key: Google 平台的 API 密钥
            model: 模型名称（默认值：gemini-pro）
            **kwargs: 额外的配置参数
        """
        super().__init__(api_key, model, **kwargs)
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)

    def generate(self, prompt: str, **kwargs) -> str:
        """
        调用 Gemini API 生成文本。

        参数:
            prompt: 输入提示词
            **kwargs: 额外的生成参数（如temperature温度、max_output_tokens最大输出令牌数等）

        返回:
            生成的文本内容
        """
        # 合并默认配置与传入的参数
        params = {**self.config, **kwargs}

        response = self.client.generate_content(prompt, **params)
        return response.text

    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        通过 Gemini API 流式生成文本（逐块返回）。

        参数:
            prompt: 输入提示词
            **kwargs: 额外的生成参数

        生成器输出:
            逐块返回的文本内容（流式输出的每个文本片段）
        """
        # 合并默认配置与传入的参数
        params = {**self.config, **kwargs}

        response = self.client.generate_content(prompt, stream=True, **params)

        for chunk in response:
            if chunk.text:
                yield chunk.text
