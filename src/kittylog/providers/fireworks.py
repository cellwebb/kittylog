"""Fireworks AI provider implementation for kittylog."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class FireworksProvider(OpenAICompatibleProvider):
    """Fireworks AI API provider."""

    config = ProviderConfig(
        name="Fireworks AI",
        api_key_env="FIREWORKS_API_KEY",
        base_url="https://api.fireworks.ai",
        path="/inference/v1/chat/completions",
    )
