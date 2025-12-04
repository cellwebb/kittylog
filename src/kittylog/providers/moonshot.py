"""Moonshot AI provider for kittylog."""

from kittylog.providers.base_configured import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class MoonshotProvider(OpenAICompatibleProvider):
    """Moonshot AI API provider with content validation."""

    config = ProviderConfig(
        name="Moonshot", api_key_env="MOONSHOT_API_KEY", base_url="https://api.moonshot.ai/v1/chat/completions"
    )

    def _parse_response(self, response: dict) -> str:
        """Parse Moonshot response with validation."""
        content = super()._parse_response(response)

        if content is None:
            from kittylog.errors import AIError

            raise AIError.generation_error("Moonshot AI API returned null content")
        if content == "":
            from kittylog.errors import AIError

            raise AIError.generation_error("Moonshot AI API returned empty content")

        return content


# Create provider instance for backward compatibility
moonshot_provider = MoonshotProvider(MoonshotProvider.config)


@handle_provider_errors("Moonshot")
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
    return moonshot_provider.generate(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
