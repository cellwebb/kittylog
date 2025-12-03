"""Together AI provider for kittylog."""

from kittylog.providers.base import BaseAPIProvider


class TogetherProvider(BaseAPIProvider):
    """Together AI API provider."""

    API_URL = "https://api.together.xyz/v1/chat/completions"
    API_KEY_ENV = "TOGETHER_API_KEY"
    PROVIDER_NAME = "Together AI"

    def _get_headers(self):
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


# Create provider instance
_together_provider = TogetherProvider()


def call_together_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Together AI API directly.

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
    return _together_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
