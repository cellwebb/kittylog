"""OpenRouter provider for kittylog."""

from kittylog.providers.base_configured import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class OpenRouterProvider(OpenAICompatibleProvider):
    """OpenRouter AI API provider with custom headers."""

    config = ProviderConfig(
        name="OpenRouter", api_key_env="OPENROUTER_API_KEY", base_url="https://openrouter.ai/api/v1/chat/completions"
    )

    def _build_headers(self) -> dict:
        """Build headers with OpenRouter-specific additions."""
        headers = super()._build_headers()
        headers["HTTP-Referer"] = "https://github.com/kittylog/kittylog"
        return headers


# Create provider instance for backward compatibility
openrouter_provider = OpenRouterProvider(OpenRouterProvider.config)


@handle_provider_errors("OpenRouter")
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
    return openrouter_provider.generate(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
