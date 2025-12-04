"""Together AI provider for kittylog."""

from kittylog.providers.base_configured import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class TogetherProvider(OpenAICompatibleProvider):
    config = ProviderConfig(
        name="Together AI",
        api_key_env="TOGETHER_API_KEY",
        base_url="https://api.together.xyz/v1/chat/completions",
    )


# Create provider instance for backward compatibility
together_provider = TogetherProvider(TogetherProvider.config)


@handle_provider_errors("Together AI")
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
    return together_provider.generate(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
