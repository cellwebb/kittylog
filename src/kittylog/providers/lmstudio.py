"""LM Studio provider implementation for kittylog."""

import os
from typing import Any

from kittylog.errors import AIError
from kittylog.providers.base import NoAuthProvider, ProviderConfig


class LMStudioProvider(NoAuthProvider):
    """LM Studio API provider with configurable local URL and optional API key."""

    config = ProviderConfig(
        name="LM Studio",
        api_key_env="",
        base_url="http://localhost:1234",
        # Uses default path: /v1/chat/completions
    )

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # Allow configurable API URL via environment
        self.custom_api_url = os.getenv("LMSTUDIO_API_URL", "http://localhost:1234").rstrip("/")

    def _build_headers(self) -> dict[str, str]:
        """Build headers with optional API key."""
        headers = super()._build_headers()
        optional_api_key = os.getenv("LMSTUDIO_API_KEY")
        if optional_api_key:
            headers["Authorization"] = f"Bearer {optional_api_key}"
        return headers

    def _get_api_url(self, model: str | None = None) -> str:
        """Get LM Studio API URL."""
        return f"{self.custom_api_url}{self.default_path}"

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict[str, Any]:
        """Build LM Studio request body."""
        # Build OpenAI-compatible request body directly instead of calling super()
        data = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,  # LM Studio requires this for non-streaming
        }
        # Add any additional kwargs
        data.update(kwargs)
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
