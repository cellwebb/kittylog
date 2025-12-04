"""Kimi Coding AI provider implementation."""

import json
import logging

from kittylog.providers.base_configured import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors

logger = logging.getLogger(__name__)


class KimiCodingProvider(OpenAICompatibleProvider):
    """Kimi Coding AI provider with OpenAI-compatible API."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.custom_base_url = "https://api.kimi.com/coding/v1"

    def _get_api_url(self, model: str | None = None) -> str:
        """Get Kimi Coding API URL."""
        return f"{self.custom_base_url}/chat/completions"

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict:
        """Build Kimi Coding request body with max_completion_tokens."""
        data = super()._build_request_body(messages, temperature, max_tokens, model, **kwargs)

        # Use max_completion_tokens instead of max_tokens
        if "max_tokens" in data:
            data["max_completion_tokens"] = data.pop("max_tokens")

        return data

    def _parse_response(self, response: dict) -> str:
        """Parse Kimi Coding response with enhanced validation and logging."""
        try:
            choices = response.get("choices")
            if not choices or not isinstance(choices, list):
                logger.error(f"Unexpected response format from Kimi Coding API. Response: {json.dumps(response)}")
                from kittylog.errors import AIError

                raise AIError.model_error(
                    "Kimi Coding API returned unexpected format. Expected OpenAI-compatible response with "
                    "'choices[0].message.content', but got: missing choices. Check logs for full response structure."
                )

            content = choices[0].get("message", {}).get("content")
            if content is None:
                logger.error(f"Unexpected response format from Kimi Coding API. Response: {json.dumps(response)}")
                from kittylog.errors import AIError

                raise AIError.model_error(
                    "Kimi Coding API returned unexpected format. Expected OpenAI-compatible response with "
                    "'choices[0].message.content', but got: missing content. Check logs for full response structure."
                )

            if content == "":
                from kittylog.errors import AIError

                raise AIError.model_error("Kimi Coding API returned empty content")

            return content
        except Exception as e:
            if "Unexpected response format" not in str(e):
                raise
            raise


# Create provider configuration
_kimi_coding_config = ProviderConfig(
    name="Kimi Coding",
    api_key_env="KIMI_CODING_API_KEY",
    base_url="https://api.kimi.com/coding/v1/chat/completions",  # Will be overridden in _get_api_url
)

# Create provider instance
kimi_coding_provider = KimiCodingProvider(_kimi_coding_config)


@handle_provider_errors("Kimi Coding")
def call_kimi_coding_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Kimi Coding API using OpenAI-compatible endpoint.

    Environment variables:
        KIMI_CODING_API_KEY: Kimi Coding API key (required)

    Args:
        model: Model name
        messages: List of message dictionaries
        temperature: Temperature parameter
        max_tokens: Maximum tokens in response

    Returns:
        Generated text content

    Raises:
        AIError: For any API-related errors
    """
    return kimi_coding_provider.generate(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
