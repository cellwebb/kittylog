"""Groq AI provider implementation."""

from kittylog.providers.base import BaseAPIProvider


class GroqProvider(BaseAPIProvider):
    """Groq API provider."""

    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    API_KEY_ENV = "GROQ_API_KEY"
    PROVIDER_NAME = "Groq"

    def _get_headers(self):
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


# Create provider instance
_groq_provider = GroqProvider()


def call_groq_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Groq API directly.

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
    return _groq_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
