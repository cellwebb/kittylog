"""StreamLake provider for kittylog."""

from kittylog.providers.base import BaseAPIProvider


class StreamLakeProvider(BaseAPIProvider):
    """StreamLake AI API provider."""

    API_URL = "https://api.streamlake.ai/v1/chat/completions"
    API_KEY_ENV = "STREAMLAKE_API_KEY"
    PROVIDER_NAME = "StreamLake"

    def _get_headers(self):
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


# Create provider instance
_streamlake_provider = StreamLakeProvider()


def call_streamlake_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call StreamLake API directly.

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
    return _streamlake_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
