"""Mistral provider implementation for kittylog."""

from kittylog.providers.base import BaseAPIProvider


class MistralProvider(BaseAPIProvider):
    """Mistral API provider."""

    API_URL = "https://api.mistral.ai/v1/chat/completions"
    API_KEY_ENV = "MISTRAL_API_KEY"
    PROVIDER_NAME = "Mistral"

    def _get_headers(self):
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


# Create provider instance
_mistral_provider = MistralProvider()


def call_mistral_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Mistral API.

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
    return _mistral_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
