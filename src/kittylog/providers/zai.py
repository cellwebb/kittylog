"""Z.AI provider for kittylog."""

from kittylog.providers.base import BaseAPIProvider


class ZAIProvider(BaseAPIProvider):
    """Z.AI API provider."""

    API_URL = "https://api.zai.ai/v1/chat/completions"
    API_KEY_ENV = "ZAI_API_KEY"
    PROVIDER_NAME = "Z.AI"

    def _get_headers(self):
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


# Create provider instances
_zai_provider = ZAIProvider()
_zai_coding_provider = ZAIProvider()


def call_zai_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Z.AI API directly.

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
    return _zai_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def call_zai_coding_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Z.AI Coding API directly.

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
    return _zai_coding_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
