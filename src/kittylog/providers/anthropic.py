"""Anthropic AI provider implementation."""

from kittylog.providers.base import AnthropicCompatibleProvider, ProviderConfig


class AnthropicProvider(AnthropicCompatibleProvider):
    config = ProviderConfig(
        name="Anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        base_url="https://api.anthropic.com",
        # Uses default path: /v1/messages
    )
