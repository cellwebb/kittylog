"""Ollama AI provider for kittylog."""

import os

import httpx

from kittylog.errors import AIError
from kittylog.providers.base import BaseAPIProvider


class OllamaProvider(BaseAPIProvider):
    """Ollama AI API provider."""

    API_URL = "http://localhost:11434/api/chat"
    API_KEY_ENV = "OLLAMA_API_URL"  # Ollama doesn't use API key, uses URL
    PROVIDER_NAME = "Ollama"

    def __init__(self):
        # Ollama doesn't need API key, just URL
        self._api_key = None

    @property
    def api_key(self) -> str:
        """Ollama doesn't use API keys."""
        return "no-key-needed"

    def _get_headers(self):
        headers = super()._get_headers()
        # Ollama doesn't need auth headers
        return headers

    def get_api_url(self):
        """Get Ollama API URL from env or default."""
        base_url = os.getenv("OLLAMA_API_URL") or os.getenv("OLLAMA_HOST") or "http://localhost:11434"
        # Ensure the URL ends with /api/chat
        base_url = base_url.rstrip("/")
        if not base_url.endswith("/api/chat"):
            base_url = f"{base_url}/api/chat"
        return base_url


# Create provider instance
_ollama_provider = OllamaProvider()


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
    # Use dynamic URL for Ollama
    url = _ollama_provider.get_api_url()
    headers = _ollama_provider._get_headers()
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,  # Disable streaming for now
    }

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("message", {}).get("content", "")

    except httpx.HTTPStatusError as e:
        raise AIError.generation_error(f"Ollama API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.TimeoutException as e:
        raise AIError.generation_error("Ollama API request timed out") from e
    except httpx.RequestError as e:
        raise AIError.generation_error(f"Ollama API network error: {e}") from e
    except (KeyError, IndexError, TypeError) as e:
        raise AIError.generation_error(f"Ollama API invalid response format: {e}") from e
    except Exception as e:
        raise AIError.generation_error(f"Error calling Ollama API: {e!s}") from e
