"""Together AI provider for kittylog."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class TogetherProvider(OpenAICompatibleProvider):
    config = ProviderConfig(
        name="Together AI",
        api_key_env="TOGETHER_API_KEY",
        base_url="https://api.together.xyz",
        # Uses default path: /v1/chat/completions
    )
