"""
DeepSeek LLM Implementation

DeepSeek uses OpenAI-compatible API, so we can use the OpenAI client.
"""

from typing import Iterator
import httpx
from openai import OpenAI
from .base import BaseLLM


class DeepSeekLLM(BaseLLM):
    """
    DeepSeek LLM implementation.

    Supports DeepSeek models via OpenAI-compatible API.
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
        Initialize DeepSeek LLM.

        Args:
            api_key: DeepSeek API key
            model: Model name (default: deepseek-chat)
            base_url: API base URL (default: https://api.deepseek.com)
            timeout: Request timeout in seconds (default: 60.0)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, model, **kwargs)
        # Use default base_url if not provided
        if base_url is None:
            base_url = "https://api.deepseek.com"
        # Use timeout configuration matching test script
        # Set connect timeout to 30s and read timeout to 120s for better reliability
        timeout_config = httpx.Timeout(30.0, read=120.0)
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_config
        )

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using DeepSeek API.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text
        """
        # Merge default config with kwargs
        params = {**self.config, **kwargs}

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **params
        )
        return response.choices[0].message.content

    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        Stream generate text using DeepSeek API.

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Yields:
            Text chunks
        """
        # Merge default config with kwargs
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
