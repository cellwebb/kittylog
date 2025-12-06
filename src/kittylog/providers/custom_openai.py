"""Custom OpenAI-compatible provider implementation for kittylog."""

import json
import logging
import os

from kittylog.errors import AIError
from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig

logger = logging.getLogger(__name__)


class CustomOpenAIProvider(OpenAICompatibleProvider):
    """Custom OpenAI-compatible API provider with configurable endpoint."""

    config = ProviderConfig(
        name="Custom OpenAI",
        api_key_env="CUSTOM_OPENAI_API_KEY",
        base_url="https://custom-endpoint.com",
        # URL is configured via CUSTOM_OPENAI_BASE_URL env var
    )

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # Defer validation until API call
        self.custom_base_url = None

    def _validate_config(self):
        """Validate and initialize configuration."""
        # Always check environment variable to ensure validation works in tests
        base_url = os.getenv("CUSTOM_OPENAI_BASE_URL")
        if not base_url:
            raise AIError.model_error("CUSTOM_OPENAI_BASE_URL environment variable not set")

        # Check API key as well
        api_key = os.getenv("CUSTOM_OPENAI_API_KEY")
        if not api_key:
            raise AIError.model_error("CUSTOM_OPENAI_API_KEY environment variable not set")

        # If the user provided the full URL with path, use it directly
        # Otherwise, append the default OpenAI path
        if "/chat/completions" in base_url:
            self.custom_base_url = base_url
        else:
            self.custom_base_url = f"{base_url.rstrip('/')}{self.default_path}"

    def _get_api_url(self, model: str | None = None) -> str:
        """Get custom OpenAI API URL."""
        self._validate_config()
        return self.custom_base_url or ""

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict:
        """Build custom OpenAI request body with max_completion_tokens."""
        data = super()._build_request_body(messages, temperature, max_tokens, model, **kwargs)

        # Use max_completion_tokens instead of max_tokens
        if "max_tokens" in data:
            data["max_completion_tokens"] = data.pop("max_tokens")

        return data

    def _parse_response(self, response: dict) -> str:
        """Parse custom OpenAI response with validation and logging."""
        try:
            content = super()._parse_response(response)

            if content is None:
                raise AIError.generation_error("Invalid response: missing content")
            if content == "":
                raise AIError.model_error("Custom OpenAI API returned empty content")

            return content
        except Exception as e:
            logger.error("Unexpected response format from Custom OpenAI API. Response: %s", json.dumps(response))
            if "Unexpected response format" not in str(e):
                raise AIError.model_error(
                    "Custom OpenAI API returned unexpected format. Expected OpenAI-compatible response."
                ) from e
            raise
