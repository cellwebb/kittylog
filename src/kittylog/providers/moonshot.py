"""Moonshot AI provider for kittylog."""

from kittylog.providers.base import BaseAPIProvider


class MoonshotProvider(BaseAPIProvider):
    """Moonshot AI API provider."""

    API_URL = "https://api.moonshot.cn/v1/chat/completions"
    API_KEY_ENV = "MOONSHOT_API_KEY"
    PROVIDER_NAME = "Moonshot AI"

    def _get_headers(self):
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


# Create provider instance
_moonshot_provider = MoonshotProvider()


def call_moonshot_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Moonshot AI API directly.

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
    return _moonshot_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
