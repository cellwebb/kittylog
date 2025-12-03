"""Cerebras AI provider implementation."""

from kittylog.providers.base import BaseAPIProvider


class CerebrasProvider(BaseAPIProvider):
    """Cerebras API provider."""

    API_URL = "https://api.cerebras.ai/v2/chat/completions"
    API_KEY_ENV = "CEREBRAS_API_KEY"
    PROVIDER_NAME = "Cerebras"

    def _get_headers(self):
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


# Create provider instance
_cerebras_provider = CerebrasProvider()


def call_cerebras_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Cerebras API directly.

    Args:
        model: Model name
        messages: List of message dictionaries
        temperature: Temperature parameter
        max_tokens: Maximum tokens in response

    Returns:
        Generated text content

    Raises:
        AIError: For any API-related errors
    """
    return _cerebras_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
