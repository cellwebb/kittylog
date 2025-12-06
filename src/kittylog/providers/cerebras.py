"""Cerebras AI provider implementation."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class CerebrasProvider(OpenAICompatibleProvider):
    """Cerebras provider."""

    config = ProviderConfig(
        name="Cerebras",
        api_key_env="CEREBRAS_API_KEY",
        base_url="https://api.cerebras.ai",
        # Uses default path: /v1/chat/completions
    )
