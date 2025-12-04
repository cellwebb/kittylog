"""Groq AI provider implementation."""

from kittylog.providers.base_configured import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class GroqProvider(OpenAICompatibleProvider):
    config = ProviderConfig(
        name="Groq",
        api_key_env="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1/chat/completions",
    )


# Create provider instance for backward compatibility
groq_provider = GroqProvider(GroqProvider.config)


@handle_provider_errors("Groq")
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
    return groq_provider.generate(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
