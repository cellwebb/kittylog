"""Custom OpenAI-compatible provider implementation for kittylog."""

import json
import logging
import os

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors

logger = logging.getLogger(__name__)


class CustomOpenAIProvider(OpenAICompatibleProvider):
    """Custom OpenAI-compatible API provider with configurable endpoint."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # Defer validation until API call
        self.custom_base_url = None

    def _validate_config(self):
        """Validate and initialize configuration."""
        # Always check environment variable to ensure validation works in tests
        base_url = os.getenv("CUSTOM_OPENAI_BASE_URL")
        if not base_url:
            from kittylog.errors import AIError

            raise AIError.model_error("CUSTOM_OPENAI_BASE_URL environment variable not set")

        # Check API key as well
        api_key = os.getenv("CUSTOM_OPENAI_API_KEY")
        if not api_key:
            from kittylog.errors import AIError

            raise AIError.model_error("CUSTOM_OPENAI_API_KEY environment variable not set")

        # Ensure proper URL format
        if "/chat/completions" not in base_url:
            base_url = base_url.rstrip("/")
            self.custom_base_url = f"{base_url}/chat/completions"
        else:
            self.custom_base_url = base_url

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
                from kittylog.errors import AIError

                raise AIError.generation_error("Invalid response: missing content")
            if content == "":
                from kittylog.errors import AIError

                raise AIError.model_error("Custom OpenAI API returned empty content")

            return content
        except Exception as e:
            logger.error("Unexpected response format from Custom OpenAI API. Response: %s", json.dumps(response))
            if "Unexpected response format" not in str(e):
                from kittylog.errors import AIError

                raise AIError.model_error(
                    "Custom OpenAI API returned unexpected format. Expected OpenAI-compatible response."
                ) from e
            raise


# Provider configuration
_custom_openai_config = ProviderConfig(
    name="Custom OpenAI",
    api_key_env="CUSTOM_OPENAI_API_KEY",
    base_url="https://custom-endpoint.com/chat/completions",
)


def _get_custom_openai_provider() -> CustomOpenAIProvider:
    """Lazy getter to initialize Custom OpenAI provider at call time."""
    return CustomOpenAIProvider(_custom_openai_config)


@handle_provider_errors("Custom OpenAI")
def call_custom_openai_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call a custom OpenAI-compatible endpoint."""
    provider = _get_custom_openai_provider()
    return provider.generate(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
