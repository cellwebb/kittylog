"""Azure OpenAI provider for kittylog.

This provider provides native support for Azure OpenAI Service with proper
endpoint construction and API version handling.
"""

import os

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class AzureOpenAIProvider(OpenAICompatibleProvider):
    """Azure OpenAI API provider with custom URL handling."""

    config = ProviderConfig(
        name="Azure OpenAI",
        api_key_env="AZURE_OPENAI_API_KEY",
        base_url="https://placeholder.openai.azure.com",
    )

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
