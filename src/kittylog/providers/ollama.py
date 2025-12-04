"""Ollama AI provider for kittylog."""

import os

from kittylog.providers.base_configured import NoAuthProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class OllamaProvider(NoAuthProvider):
    """Ollama AI API provider with dynamic URL support."""

    def _get_api_url(self, model: str | None = None) -> str:
        """Get Ollama API URL from env or default."""
        base_url = os.getenv("OLLAMA_API_URL") or os.getenv("OLLAMA_HOST") or "http://localhost:11434"
        # Ensure the URL ends with /api/chat
        base_url = base_url.rstrip("/")
        if not base_url.endswith("/api/chat"):
            base_url = f"{base_url}/api/chat"
        return base_url

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


# Create provider configuration
_ollama_config = ProviderConfig(
    name="Ollama",
    api_key_env="",  # No API key needed
    base_url="http://localhost:11434/api/chat",  # Will be overridden by _get_api_url
)

# Create provider instance
ollama_provider = OllamaProvider(_ollama_config)


@handle_provider_errors("Ollama")
def call_ollama_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Ollama API directly.

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
    return ollama_provider.generate(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
