"""Moonshot AI provider for kittylog."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class MoonshotProvider(OpenAICompatibleProvider):
    """Moonshot AI API provider."""

    config = ProviderConfig(
        name="Moonshot",
        api_key_env="MOONSHOT_API_KEY",
        base_url="https://api.moonshot.ai",
        # Uses default path: /v1/chat/completions
    )
