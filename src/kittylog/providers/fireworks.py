"""Fireworks AI provider implementation for kittylog."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig
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


def _get_fireworks_provider() -> FireworksProvider:
    """Lazy getter to initialize Fireworks AI provider at call time."""
    return FireworksProvider(FireworksProvider.config)


@handle_provider_errors("Fireworks AI")
def call_fireworks_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Fireworks AI API."""
    provider = _get_fireworks_provider()
    return provider.generate(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
