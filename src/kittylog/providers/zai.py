"""Z.AI API provider for kittylog."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class ZAIProvider(OpenAICompatibleProvider):
    """Z.AI API provider."""

    config = ProviderConfig(
        name="Z.AI",
        api_key_env="ZAI_API_KEY",
        base_url="https://api.z.ai",
        path="/api/paas/v4/chat/completions",
    )


class ZAICodingProvider(OpenAICompatibleProvider):
    """Z.AI Coding API provider."""

    config = ProviderConfig(
        name="Z.AI Coding",
        api_key_env="ZAI_API_KEY",
        base_url="https://api.z.ai",
        path="/api/coding/paas/v4/chat/completions",
    )
