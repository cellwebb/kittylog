"""OpenRouter provider for kittylog."""

from kittylog.providers.base import BaseAPIProvider


class OpenRouterProvider(BaseAPIProvider):
    """OpenRouter AI API provider."""

    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    API_KEY_ENV = "OPENROUTER_API_KEY"
    PROVIDER_NAME = "OpenRouter"

    def _get_headers(self):
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        headers["HTTP-Referer"] = "https://github.com/kittylog/kittylog"
        return headers


# Create provider instance
_openrouter_provider = OpenRouterProvider()


def call_openrouter_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call OpenRouter API directly.

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
    return _openrouter_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
