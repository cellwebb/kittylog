"""Mistral provider implementation for kittylog."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class MistralProvider(OpenAICompatibleProvider):
    config = ProviderConfig(
        name="Mistral",
        api_key_env="MISTRAL_API_KEY",
        base_url="https://api.mistral.ai",
        # Uses default path: /v1/chat/completions
    )
