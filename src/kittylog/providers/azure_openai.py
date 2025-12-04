"""Azure OpenAI provider for kittylog.

This provider provides native support for Azure OpenAI Service with proper
endpoint construction and API version handling.
"""

import os

from kittylog.providers.base_configured import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class AzureOpenAIProvider(OpenAICompatibleProvider):
    """Azure OpenAI API provider with custom URL handling."""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # Azure OpenAI requires additional env vars for endpoint and version
        self.api_endpoint: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    def _build_headers(self):
        """Build headers with Azure OpenAI api-key format."""
        headers = super()._build_headers()
        if self.api_key:
            headers["api-key"] = self.api_key
            # Remove the Authorization header that OpenAICompatibleProvider adds
            headers.pop("Authorization", None)
        return headers

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict:
        """Build Azure OpenAI-specific request body."""
        data = super()._build_request_body(messages, temperature, max_tokens, model, **kwargs)

        # Azure OpenAI uses max_tokens instead of max_completion_tokens
        if "max_completion_tokens" in data:
            data["max_tokens"] = data.pop("max_completion_tokens")

        return data

    def _get_api_url(self, model: str | None = None) -> str:
        """Construct full API URL with version.

        Args:
            model: The deployment name to use in the URL

        Returns:
            Full Azure OpenAI API URL
        """
        if not model:
            raise ValueError("Model is required for Azure OpenAI")
        endpoint = self.api_endpoint
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required")
        return f"{endpoint.rstrip('/')}/openai/deployments/{model}/chat/completions?api-version={self.api_version}"


# Create provider configuration - base_url is placeholder since we override _get_api_url
_azure_openai_config = ProviderConfig(
    name="Azure OpenAI",
    api_key_env="AZURE_OPENAI_API_KEY",
    base_url="https://placeholder.openai.azure.com",  # Overridden in _get_api_url
)

# Create provider instance
azure_openai_provider = AzureOpenAIProvider(_azure_openai_config)


@handle_provider_errors("Azure OpenAI")
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
    return azure_openai_provider.generate(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )


# Backward compatibility alias for tests
_azure_openai_provider = azure_openai_provider
