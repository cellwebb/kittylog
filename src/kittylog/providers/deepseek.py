"""DeepSeek provider implementation for kittylog."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class DeepSeekProvider(OpenAICompatibleProvider):
    """DeepSeek API provider."""

    config = ProviderConfig(
        name="DeepSeek",
        api_key_env="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com",
        # Uses default path: /v1/chat/completions
    )
