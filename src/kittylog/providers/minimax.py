"""MiniMax provider implementation for kittylog."""

from kittylog.providers.base import BaseAPIProvider


class MiniMaxProvider(BaseAPIProvider):
    """MiniMax API provider."""

    API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"
    API_KEY_ENV = "MINIMAX_API_KEY"
    PROVIDER_NAME = "MiniMax"

    def _get_headers(self):
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


# Create provider instance
_minimax_provider = MiniMaxProvider()


def call_minimax_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call MiniMax API.

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
    return _minimax_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
