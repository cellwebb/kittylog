"""Chutes.ai provider implementation for kittylog."""

import os

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class ChutesProvider(OpenAICompatibleProvider):
    """Chutes.ai API provider with configurable base URL."""

    config = ProviderConfig(
        name="Chutes",
        api_key_env="CHUTES_API_KEY",
        base_url="https://llm.chutes.ai",
        # Uses default path: /v1/chat/completions
    )

    def _get_api_url(self, model: str | None = None) -> str:
        """Get Chutes API URL, allowing override via environment."""
        env_url = os.getenv("CHUTES_BASE_URL")
        base_url = env_url.rstrip("/") if env_url else self.config.base_url.rstrip("/")
        return f"{base_url}{self.default_path}"
