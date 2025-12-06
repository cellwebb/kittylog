"""OpenRouter provider for kittylog."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class OpenRouterProvider(OpenAICompatibleProvider):
    """OpenRouter AI API provider with custom headers."""

    config = ProviderConfig(
        name="OpenRouter",
        api_key_env="OPENROUTER_API_KEY",
        base_url="https://openrouter.ai",
        path="/api/v1/chat/completions",
    )

    def _build_headers(self) -> dict:
        """Build headers with OpenRouter-specific additions."""
        headers = super()._build_headers()
        headers["HTTP-Referer"] = "https://github.com/kittylog/kittylog"
        return headers
