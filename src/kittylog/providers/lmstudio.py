"""LM Studio provider implementation for kittylog."""

import os
from typing import Any

from kittylog.errors import AIError
from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class LMStudioProvider(OpenAICompatibleProvider):
    """LM Studio API provider with configurable local URL and optional API key."""

    config = ProviderConfig(
        name="LM Studio",
        api_key_env="LMSTUDIO_API_KEY",
        base_url="http://localhost:1234",
        # Uses default path: /v1/chat/completions
    )

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # Allow configurable API URL via environment
        self.custom_api_url = os.getenv("LMSTUDIO_API_URL", "http://localhost:1234").rstrip("/")

    def _get_api_key(self) -> str:
        """Get optional API key - LM Studio doesn't require one."""
        return os.getenv("LMSTUDIO_API_KEY", "")

    def _get_api_url(self, model: str | None = None) -> str:
        """Get LM Studio API URL."""
        return f"{self.custom_api_url}{self.default_path}"

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict[str, Any]:
        """Build LM Studio request body."""
        data = super()._build_request_body(messages, temperature, max_tokens, model, **kwargs)
        data["stream"] = False  # LM Studio requires this for non-streaming
        return data

    def _parse_response(self, response: dict) -> str:
        """Parse LM Studio response with fallback handling."""
        # Try standard OpenAI-style first
        choices = response.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content")
            if content:
                return content

            # Try fallback to direct text field
            fallback_content = choices[0].get("text")
            if fallback_content:
                return fallback_content

        raise AIError.model_error("LM Studio API response missing content")
