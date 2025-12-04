"""Z.AI API provider for kittylog."""

from kittylog.providers.base_configured import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class ZAIProvider(OpenAICompatibleProvider):
    """Z.AI API provider with content validation."""

    def _parse_response(self, response: dict) -> str:
        """Parse Z.AI response with validation."""
        content = super()._parse_response(response)

        if content is None:
            from kittylog.errors import AIError

            raise AIError.generation_error("Z.AI API returned null content")
        if content == "":
            from kittylog.errors import AIError

            raise AIError.generation_error("Z.AI API returned empty content")

        return content


# Create provider configurations
_zai_config = ProviderConfig(
    name="Z.AI", api_key_env="ZAI_API_KEY", base_url="https://api.z.ai/api/paas/v4/chat/completions"
)

_zai_coding_config = ProviderConfig(
    name="Z.AI Coding", api_key_env="ZAI_API_KEY", base_url="https://api.z.ai/api/coding/paas/v4/chat/completions"
)

# Create provider instances
zai_provider = ZAIProvider(_zai_config)
zai_coding_provider = ZAIProvider(_zai_coding_config)


@handle_provider_errors("Z.AI")
def call_zai_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Z.AI regular API directly.

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
    return zai_provider.generate(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def call_zai_coding_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Z.AI coding API directly.

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
    return zai_coding_provider.generate(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
