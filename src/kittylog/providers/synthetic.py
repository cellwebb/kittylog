"""Synthetic.new API provider for kittylog."""

from kittylog.providers.base_configured import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class SyntheticProvider(OpenAICompatibleProvider):
    """Synthetic.new API provider with hf: model prefix and dual API key support."""

    def _get_api_key(self) -> str:
        """Get API key from environment with alias support."""
        import os

        from kittylog.errors import AIError

        api_key = os.getenv("SYNTHETIC_API_KEY") or os.getenv("SYN_API_KEY")
        if not api_key:
            raise AIError.generation_error("SYNTHETIC_API_KEY or SYN_API_KEY not found in environment variables")
        return api_key

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict:
        """Build Synthetic request body with hf: model prefix."""
        data = super()._build_request_body(messages, temperature, max_tokens, model, **kwargs)

        # Handle model names without hf: prefix
        if not model.startswith("hf:"):
            data["model"] = f"hf:{model}"

        # Synthetic uses max_completion_tokens
        if "max_tokens" in data:
            data["max_completion_tokens"] = data.pop("max_tokens")

        return data

    def _parse_response(self, response: dict) -> str:
        """Parse Synthetic response with validation."""
        content = super()._parse_response(response)

        if content is None:
            from kittylog.errors import AIError

            raise AIError.generation_error("Synthetic.new API returned null content")
        if content == "":
            from kittylog.errors import AIError

            raise AIError.generation_error("Synthetic.new API returned empty content")

        return content


# Create provider configuration
_synthetic_config = ProviderConfig(
    name="Synthetic",
    api_key_env="SYNTHETIC_API_KEY",  # Will be overridden by _get_api_key to support SYN_API_KEY alias
    base_url="https://api.synthetic.new/openai/v1/chat/completions",
)

# Create provider instance
synthetic_provider = SyntheticProvider(_synthetic_config)


@handle_provider_errors("Synthetic")
def call_synthetic_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Synthetic.new API directly.

    Environment variables:
        SYNTHETIC_API_KEY: Synthetic API key (required)
        SYN_API_KEY: Alternative API key variable name (alias for SYNTHETIC_API_KEY)

    Args:
        model: Model name (will be prefixed with 'hf:' if not already)
        messages: List of message dictionaries
        temperature: Temperature parameter
        max_tokens: Maximum tokens in response

    Returns:
        Generated text content

    Raises:
        AIError: For any API-related errors
    """
    return synthetic_provider.generate(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
