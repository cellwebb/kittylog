"""Chutes.ai provider implementation for kittylog."""

import os

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class ChutesProvider(OpenAICompatibleProvider):
    """Chutes.ai API provider with configurable base URL."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # Allow configurable base URL via environment
        self.custom_base_url = os.getenv("CHUTES_BASE_URL", "https://llm.chutes.ai").rstrip("/")

    def _get_api_url(self, model: str | None = None) -> str:
        """Get custom Chutes API URL."""
        return f"{self.custom_base_url}/v1/chat/completions"

    def _parse_response(self, response: dict) -> str:
        """Parse Chutes response with validation."""
        content = super()._parse_response(response)

        if content is None:
            from kittylog.errors import AIError

            raise AIError.model_error("Chutes.ai API returned null content")
        if content == "":
            from kittylog.errors import AIError

            raise AIError.model_error("Chutes.ai API returned empty content")

        return content


# Provider configuration
_chutes_config = ProviderConfig(
    name="Chutes",
    api_key_env="CHUTES_API_KEY",
    base_url="https://llm.chutes.ai/v1/chat/completions",
)


def _get_chutes_provider() -> ChutesProvider:
    """Lazy getter to initialize Chutes provider at call time."""
    return ChutesProvider(_chutes_config)


@handle_provider_errors("Chutes")
def call_chutes_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call the Chutes.ai API using an OpenAI-compatible endpoint."""
    provider = _get_chutes_provider()
    return provider.generate(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
