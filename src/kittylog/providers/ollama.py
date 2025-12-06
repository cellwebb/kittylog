"""Ollama AI provider for kittylog."""

import os

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class OllamaProvider(OpenAICompatibleProvider):
    """Ollama AI API provider with dynamic URL support and optional API key."""

    default_path: str = "/api/chat"

    config = ProviderConfig(
        name="Ollama",
        api_key_env="OLLAMA_API_KEY",
        base_url="http://localhost:11434",
        # Uses default_path: /api/chat
    )

    def _get_api_key(self) -> str:
        """Get optional API key - Ollama doesn't require one by default."""
        return os.getenv("OLLAMA_API_KEY", "")

    def _get_api_url(self, model: str | None = None) -> str:
        """Get Ollama API URL from env or default."""
        env_url = os.getenv("OLLAMA_API_URL") or os.getenv("OLLAMA_HOST")
        base_url = env_url.rstrip("/") if env_url else self.config.base_url.rstrip("/")
        return f"{base_url}{self.default_path}"

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict:
        """Build Ollama-specific request body."""
        return {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,  # Disable streaming for now
            **kwargs,
        }

    def _parse_response(self, response: dict) -> str:
        """Parse Ollama response format."""
        return response.get("message", {}).get("content", "")
