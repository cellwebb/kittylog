"""Custom Anthropic-compatible provider implementation for kittylog."""

import json
import logging
import os

from kittylog.errors import AIError
from kittylog.providers.base import AnthropicCompatibleProvider, ProviderConfig

logger = logging.getLogger(__name__)


class CustomAnthropicProvider(AnthropicCompatibleProvider):
    """Custom Anthropic-compatible API provider with configurable endpoint."""

    config = ProviderConfig(
        name="Custom Anthropic",
        api_key_env="CUSTOM_ANTHROPIC_API_KEY",
        base_url="https://custom-endpoint.com",
        # URL is configured via CUSTOM_ANTHROPIC_BASE_URL env var
    )

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # Defer validation until API call
        self.custom_base_url: str | None = None
        self.api_version: str | None = None

    def _validate_config(self):
        """Validate and initialize configuration."""
        # Always check environment variable to ensure validation works in tests
        base_url = os.getenv("CUSTOM_ANTHROPIC_BASE_URL")
        if not base_url:
            raise AIError.model_error("CUSTOM_ANTHROPIC_BASE_URL environment variable not set")

        # Check API key as well
        api_key = os.getenv("CUSTOM_ANTHROPIC_API_KEY")
        if not api_key:
            raise AIError.model_error("CUSTOM_ANTHROPIC_API_KEY environment variable not set")

        # Get custom API version
        self.api_version = os.getenv("CUSTOM_ANTHROPIC_VERSION", "2023-06-01")

        # If the user provided the full URL with path, use it directly
        # Otherwise, append the default Anthropic path
        if "/v1/messages" in base_url:
            self.custom_base_url = base_url
        else:
            self.custom_base_url = f"{base_url.rstrip('/')}{self.default_path}"

    def _get_api_url(self, model: str | None = None) -> str:
        """Get custom Anthropic API URL."""
        self._validate_config()
        return self.custom_base_url or ""

    def _build_headers(self) -> dict[str, str]:
        """Build headers with custom Anthropic version."""
        self._validate_config()
        headers = super()._build_headers()
        headers["anthropic-version"] = self.api_version or "2023-06-01"
        return headers

    def _parse_response(self, response: dict) -> str:
        """Parse custom Anthropic response with enhanced validation and logging."""
        try:
            content_list = response.get("content", [])
            if not content_list:
                raise AIError.model_error("Custom Anthropic API returned empty content array")

            if "text" in content_list[0]:
                content = content_list[0]["text"]
            else:
                text_item = next((item for item in content_list if item.get("type") == "text"), None)
                if text_item and "text" in text_item:
                    content = text_item["text"]
                else:
                    logger.error(
                        "Unexpected response format from Custom Anthropic API. Response: %s",
                        json.dumps(response),
                    )
                    raise AIError.model_error(
                        "Custom Anthropic API returned unexpected format. Expected content items with 'text'."
                    )

            if content is None:
                raise AIError.model_error("Custom Anthropic API returned null content")
            if content == "":
                raise AIError.model_error("Custom Anthropic API returned empty content")

            return content
        except (KeyError, IndexError, TypeError, StopIteration) as e:
            logger.error("Unexpected response format from Custom Anthropic API. Response: %s", json.dumps(response))
            raise AIError.model_error(
                "Custom Anthropic API returned unexpected format. Expected Anthropic-compatible response."
            ) from e
