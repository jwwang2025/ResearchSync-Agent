"""
OpenAI LLM Implementation
"""

from typing import Iterator
import httpx
from openai import OpenAI
from .base import BaseLLM


class OpenAILLM(BaseLLM):
    """
    OpenAI LLM implementation.

    Supports GPT-4, GPT-3.5-turbo, and other OpenAI models.
    """

    def __init__(self, api_key: str, model: str = "gpt-4", base_url: str = None, timeout: float = 60.0, **kwargs):
        """
        Initialize OpenAI LLM.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4)
            base_url: API base URL for proxy (optional)
            timeout: Request timeout in seconds (default: 60.0)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, model, **kwargs)
        # Use timeout configuration matching DeepSeek implementation
        # Set connect timeout to 30s and read timeout to 120s for better reliability
        timeout_config = httpx.Timeout(30.0, read=120.0)
        # Use base_url if provided (for proxy), otherwise use default OpenAI API
        client_kwargs = {"api_key": api_key, "timeout": timeout_config}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = OpenAI(**client_kwargs)

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using OpenAI API.

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
        Stream generate text using OpenAI API.

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
