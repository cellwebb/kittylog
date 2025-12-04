"""Fireworks AI provider implementation for kittylog."""

from kittylog.providers.base_configured import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class FireworksProvider(OpenAICompatibleProvider):
    """Fireworks AI API provider with empty content validation."""

    config = ProviderConfig(
        name="Fireworks AI",
        api_key_env="FIREWORKS_API_KEY",
        base_url="https://api.fireworks.ai/inference/v1/chat/completions",
    )

    def _parse_response(self, response: dict) -> str:
        """Parse Fireworks response with additional validation."""
        content = super()._parse_response(response)

        if content == "":
            from kittylog.errors import AIError

            raise AIError.model_error("Fireworks AI API returned empty content")

        return content


# Create provider instance for backward compatibility
fireworks_provider = FireworksProvider(FireworksProvider.config)


@handle_provider_errors("Fireworks AI")
def call_fireworks_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Fireworks AI API.

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
    return fireworks_provider.generate(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
