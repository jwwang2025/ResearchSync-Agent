"""
大语言模型（LLM）工厂类

该模块提供了创建LLM实例的工厂模式实现，支持便捷管理不同厂商的LLM实例化逻辑。
"""

from typing import Optional
from .base import BaseLLM


class LLMFactory:
    """
    用于创建 LLM 实例的工厂类。

    该工厂类支持便捷地实例化不同的大语言模型提供商实例，
    无需在业务代码中直接导入各提供商的实现类。
    """

    _providers = {}

    @classmethod
    def register_provider(cls, name: str, provider_class):
        """
        注册新的大语言模型提供商。

        参数:
            name: 提供商名称（示例：'openai'、'claude'、'gemini'）
            provider_class: 待注册的LLM实现类（需继承BaseLLM）
        """
        cls._providers[name.lower()] = provider_class

    @classmethod
    def create_llm(
        cls,
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        **kwargs
    ) -> BaseLLM:
        """
        创建指定类型的LLM实例。

        参数:
            provider: 提供商名称（支持：'openai'、'claude'、'gemini'、'deepseek'）
            api_key: 对应提供商的API密钥
            model: 可选的模型名称，若未指定则使用提供商的默认模型
            **kwargs: 额外的配置参数（如超时时间、代理地址等）

        返回:
            已初始化的指定LLM提供商实例（继承自BaseLLM）

        异常:
            ValueError: 当指定的提供商未被支持/注册时抛出
        """
        provider = provider.lower()

        if provider not in cls._providers:
            # 尝试对提供者进行懒加载
            cls._lazy_load_provider(provider)

        if provider not in cls._providers:
            available = ', '.join(cls._providers.keys())
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                f"Available providers: {available}"
            )

        llm_class = cls._providers[provider]

        # 实例化LLM类（支持传/不传model参数）
        # 注意：base_url参数仅用于OpenAILLM类以支持代理配置，
        # 其他提供商（claude、gemini、deepseek）会通过**kwargs自动忽略该参数
        if model:
            return llm_class(api_key=api_key, model=model, **kwargs)
        else:
            return llm_class(api_key=api_key, **kwargs)

    @classmethod
    def _lazy_load_provider(cls, provider: str):
        """
        按需懒加载指定的LLM提供商模块（避免初始化时加载所有依赖）。

        参数:
            provider: 待加载的提供商名称
        """
        try:
            if provider == 'openai':
                from .openai_llm import OpenAILLM
                cls.register_provider('openai', OpenAILLM)
            elif provider == 'claude':
                from .claude_llm import ClaudeLLM
                cls.register_provider('claude', ClaudeLLM)
            elif provider == 'gemini':
                from .gemini_llm import GeminiLLM
                cls.register_provider('gemini', GeminiLLM)
            elif provider == 'deepseek':
                from .deepseek_llm import DeepSeekLLM
                cls.register_provider('deepseek', DeepSeekLLM)
        except ImportError as e:
            # 若提供商对应的模块未安装/不存在，静默忽略
            pass

    @classmethod
    def list_providers(cls) -> list[str]:
        """
        获取所有已注册的LLM提供商名称列表。

        返回:
            已注册提供商名称的列表（如['openai', 'claude']）
        """
        return list(cls._providers.keys())
