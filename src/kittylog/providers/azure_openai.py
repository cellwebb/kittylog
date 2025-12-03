"""Azure OpenAI provider for kittylog.

This provider provides native support for Azure OpenAI Service with proper
endpoint construction and API version handling.
"""

import logging
import os

import httpx

from kittylog.errors import AIError
from kittylog.providers.base import BaseAPIProvider

logger = logging.getLogger(__name__)


class AzureOpenAIProvider(BaseAPIProvider):
    """Azure OpenAI API provider."""

    API_KEY_ENV = "AZURE_OPENAI_API_KEY"
    PROVIDER_NAME = "Azure OpenAI"
    TIMEOUT = 120

    def __init__(self):
        super().__init__()
        # Azure OpenAI requires additional env vars for endpoint and version
        self.api_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    def _get_headers(self):
        headers = super()._get_headers()
        headers["api-key"] = self.api_key
        return headers

    def _prepare_request_data(self, model, messages, temperature, max_tokens, **kwargs):
        """Prepare Azure OpenAI-specific request data."""
        data = super()._prepare_request_data(model, messages, temperature, max_tokens, **kwargs)

        # Azure OpenAI uses max_tokens instead of max_completion_tokens
        if "max_completion_tokens" in data:
            data["max_tokens"] = data.pop("max_completion_tokens")

        return data

    def get_api_url(self, model: str) -> str:
        """Construct full API URL with version.

        Args:
            model: The deployment name to use in the URL
        """
        return f"{self.api_endpoint.rstrip('/')}/openai/deployments/{model}/chat/completions?api-version={self.api_version}"

    def call(self, model, messages, temperature, max_tokens, **kwargs):
        """Override to use custom Azure OpenAI URL."""
        headers = self._get_headers()
        data = self._prepare_request_data(model, messages, temperature, max_tokens, **kwargs)

        try:
            response = httpx.post(self.get_api_url(model), headers=headers, json=data, timeout=self.TIMEOUT)
            response.raise_for_status()
            response_data = response.json()
            return self._process_response_data(response_data)

        except httpx.HTTPStatusError as e:
            raise AIError.generation_error(
                f"Azure OpenAI API error: {e.response.status_code} - {e.response.text}"
            ) from e
        except httpx.TimeoutException as e:
            raise AIError.generation_error("Azure OpenAI API request timed out") from e
        except httpx.RequestError as e:
            raise AIError.generation_error(f"Azure OpenAI API network error: {e}") from e
        except (KeyError, IndexError, TypeError) as e:
            raise AIError.generation_error(f"Azure OpenAI API invalid response format: {e}") from e
        except Exception as e:
            raise AIError.generation_error(f"Error calling Azure OpenAI API: {e!s}") from e


# Create provider instance
_azure_openai_provider = AzureOpenAIProvider()


def call_azure_openai_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Azure OpenAI Service API.

    Environment variables:
        AZURE_OPENAI_API_KEY: Azure OpenAI API key (required)
        AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL (required)
            Example: https://your-resource.openai.azure.com
        AZURE_OPENAI_API_VERSION: Azure OpenAI API version (required)
            Example: 2025-01-01-preview
            Example: 2024-02-15-preview

    Args:
        model: The deployment name in Azure OpenAI (e.g., 'gpt-4o', 'gpt-35-turbo')
        messages: List of message dictionaries
        temperature: Temperature parameter (0.0-2.0)
        max_tokens: Maximum tokens in response

    Returns:
        Generated text content

    Raises:
        AIError: For any API-related errors
    """
    return _azure_openai_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
