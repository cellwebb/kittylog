"""Synthetic provider for kittylog."""

from kittylog.providers.base import BaseAPIProvider


class SyntheticProvider(BaseAPIProvider):
    """Synthetic AI API provider."""

    API_URL = "https://api.synthetic.ai/v1/chat/completions"
    API_KEY_ENV = "SYNTHETIC_API_KEY"
    PROVIDER_NAME = "Synthetic AI"

    def _get_headers(self):
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


# Create provider instance
_synthetic_provider = SyntheticProvider()


def call_synthetic_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Synthetic AI API directly.

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
    return _synthetic_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
