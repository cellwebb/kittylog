"""MiniMax API provider for kittylog."""

from kittylog.errors import AIError
from kittylog.providers.base_configured import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class MiniMaxProvider(OpenAICompatibleProvider):
    """MiniMax provider with additional validation."""

    config = ProviderConfig(
        name="MiniMax", api_key_env="MINIMAX_API_KEY", base_url="https://api.minimax.io/v1/chat/completions"
    )

    def _parse_response(self, response: dict) -> str:
        """Parse MiniMax response with additional validation."""
        content = super()._parse_response(response)
        if content is None:
            raise AIError.generation_error("MiniMax API returned null content")
        if content == "":
            raise AIError.generation_error("MiniMax API returned empty content")
        return content


# Create provider instance for backward compatibility
minimax_provider = MiniMaxProvider(MiniMaxProvider.config)


@handle_provider_errors("MiniMax")
def call_minimax_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call MiniMax API directly.

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
    return minimax_provider.generate(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
