"""
大语言模型（LLM）基类

该模块定义了所有大语言模型提供商的抽象基类。
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Iterator


class BaseLLM(ABC):
    """
    大语言模型（LLM）提供商的抽象基类。

    所有LLM实现类（如OpenAI、Claude、Gemini）都应继承此类，
    并实现所有必需的抽象方法。
    """

    def __init__(self, api_key: str, model: str, **kwargs):
        """
        初始化大语言模型实例。

        参数:
            api_key: 大语言模型提供商的API密钥
            model: 模型名称/标识符（如gpt-4、claude-3-opus）
            **kwargs: 额外的配置参数（如超时时间、基础URL等）
        """
        self.api_key = api_key
        self.model = model
        self.config = kwargs

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        根据提示词生成文本。

        参数:
            prompt: 输入提示词
            **kwargs: 额外的生成参数（如temperature温度、max_tokens最大令牌数等）

        返回:
            生成的文本响应结果
        """
        pass

    @abstractmethod
    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        流式生成提示词对应的文本（逐块返回）。

        参数:
            prompt: 输入提示词
            **kwargs: 额外的生成参数

        生成器输出:
            文本生成过程中产生的逐块文本内容
        """
        pass

    def __repr__(self) -> str:
        """返回 LLM 实例的字符串表示形式"""
        return f"{self.__class__.__name__}(model={self.model})"
