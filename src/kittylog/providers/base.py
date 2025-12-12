"""Base configured provider class to eliminate code duplication."""

import json
import os
from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

import httpx

from kittylog.errors import AIError
from kittylog.providers.protocol import ProviderProtocol


@dataclass
class ProviderConfig:
    """Configuration for AI providers.

    Attributes:
        name: Display name of the provider (e.g., "OpenAI", "Anthropic")
        api_key_env: Environment variable name for the API key
        base_url: Base URL of the API (e.g., "https://api.openai.com")
        path: API endpoint path (e.g., "/v1/chat/completions"). If None, uses class default.
        timeout: Request timeout in seconds
        headers: Default HTTP headers
    """

    name: str
    api_key_env: str
    base_url: str
    path: str | None = None  # If None, use the class's default_path
    timeout: int = 120
    headers: dict[str, str] | None = None

    def __post_init__(self):
        """Initialize default headers if not provided."""
        if self.headers is None:
            self.headers = {"Content-Type": "application/json"}


class BaseConfiguredProvider(ABC, ProviderProtocol):
    """Base class for configured AI providers.

    This class eliminates code duplication by providing:
    - Standardized HTTP handling with httpx
    - Common error handling patterns
    - Flexible configuration via ProviderConfig
    - Template methods for customization

    Implements ProviderProtocol for type safety.

    Class Attributes:
        default_path: Default API path for this provider type. Subclasses should override.
    """

    default_path: str = ""  # Subclasses should override with their default path

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._api_key: str | None = None  # Lazy load

    @property
    def api_key(self) -> str:
        """Lazy-load API key when needed."""
        if self.config.api_key_env:
            # Always check environment for fresh value to support test isolation
            return self._get_api_key()
        return ""

    @property
    def name(self) -> str:
        """Get the provider name."""
        return self.config.name

    @property
    def api_key_env(self) -> str:
        """Get the environment variable name for the API key."""
        return self.config.api_key_env

    @property
    def base_url(self) -> str:
        """Get the base URL for the API."""
        return self.config.base_url

    @property
    def timeout(self) -> int:
        """Get the timeout in seconds."""
        return self.config.timeout

    def _get_api_key(self) -> str:
        """Get API key from environment variables."""
        api_key = os.getenv(self.config.api_key_env)
        if not api_key:
            raise AIError.authentication_error(f"{self.config.api_key_env} not found in environment variables")
        return api_key

    @abstractmethod
    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict[str, Any]:
        """Build the request body for the API call.

        Args:
            messages: List of message dictionaries
            temperature: Temperature parameter
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific parameters

        Returns:
            Request body dictionary
        """
        pass

    @abstractmethod
    def _parse_response(self, response: dict[str, Any]) -> str:
        """Parse the API response and extract content.

        Args:
            response: Response dictionary from API

        Returns:
            Generated text content
        """
        pass

    def _build_headers(self) -> dict[str, str]:
        """Build headers for the API request.

        Can be overridden by subclasses to add provider-specific headers.
        """
        headers = self.config.headers.copy() if self.config.headers else {}
        return headers

    def _get_api_url(self, model: str | None = None) -> str:
        """Get the API URL for the request.

        Constructs URL from base_url + path. The path is determined by:
        1. config.path if explicitly set
        2. class's default_path otherwise

        Can be overridden by subclasses for dynamic URLs (e.g., model in URL).

        Args:
            model: Model name (for providers that need model-specific URLs)

        Returns:
            Full API URL string
        """
        base = self.config.base_url.rstrip("/")
        path = self.config.path if self.config.path is not None else self.default_path
        return f"{base}{path}"

    def _make_http_request(self, url: str, body: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        """Make the HTTP request with standardized error handling.

        Args:
            url: API URL
            body: Request body
            headers: Request headers

        Returns:
            Response JSON dictionary

        Raises:
            AIError: For any API-related errors
        """
        try:
            response = httpx.post(url, json=body, headers=headers, timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AIError.authentication_error(
                    f"{self.config.name} API: Invalid API key or authentication failed"
                ) from e
            elif e.response.status_code == 429:
                raise AIError.rate_limit_error(f"{self.config.name} API: Rate limit exceeded") from e
            elif e.response.status_code >= 500:
                raise AIError.connection_error(
                    f"{self.config.name} API: Server error (HTTP {e.response.status_code})"
                ) from e
            else:
                raise AIError.model_error(
                    f"{self.config.name} API error: HTTP {e.response.status_code} - {e.response.text}"
                ) from e
        except httpx.TimeoutException as e:
            raise AIError.timeout_error(f"{self.config.name} API request timed out") from e
        except httpx.RequestError as e:
            raise AIError.connection_error(f"{self.config.name} API network error: {e}") from e
        except Exception as e:
            raise AIError.model_error(f"Error calling {self.config.name} AI API: {e!s}") from e

    def generate(
        self, model: str, messages: list[dict], temperature: float = 0.7, max_tokens: int = 1024, **kwargs
    ) -> str:
        """Generate text using the AI provider.

        Args:
            model: Model name to use
            messages: List of message dictionaries
            temperature: Temperature parameter (0.0-2.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text content

        Raises:
            AIError: For any API-related errors
        """
        # Build request components
        try:
            url = self._get_api_url(model)
        except AIError:
            raise
        except Exception as e:
            raise AIError.model_error(f"Error calling {self.config.name} AI API: {e!s}") from e

        try:
            headers = self._build_headers()
        except AIError:
            raise
        except Exception as e:
            raise AIError.model_error(f"Error calling {self.config.name} AI API: {e!s}") from e

        try:
            body = self._build_request_body(messages, temperature, max_tokens, model, **kwargs)
        except AIError:
            raise
        except Exception as e:
            raise AIError.model_error(f"Error calling {self.config.name} AI API: {e!s}") from e

        # Add model to body if not already present
        if "model" not in body:
            body["model"] = model

        # Make HTTP request
        response_data = self._make_http_request(url, body, headers)

        # Parse response
        return self._parse_response(response_data)

    @abstractmethod
    def _parse_stream_chunk(self, line: str) -> tuple[str | None, dict | None]:
        """Parse a single SSE chunk from the streaming response.

        Args:
            line: A single line from the SSE stream

        Returns:
            Tuple of (content_chunk, usage_dict):
            - content_chunk: Text content if present, None otherwise
            - usage_dict: Token usage if present, None otherwise
        """
        pass

    def generate_stream(
        self, model: str, messages: list[dict], temperature: float = 0.7, max_tokens: int = 1024, **kwargs
    ) -> Generator[tuple[str, dict | None], None, None]:
        """Generate text with streaming support.

        Args:
            model: Model name to use
            messages: List of message dictionaries
            temperature: Temperature parameter (0.0-2.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific parameters

        Yields:
            Tuple[str, dict | None]:
            - (chunk_text, None) for content chunks
            - ("", usage_dict) for final yield with token usage

        Raises:
            AIError: For any API-related errors
        """
        # Build request components
        try:
            url = self._get_api_url(model)
        except AIError:
            raise
        except Exception as e:
            raise AIError.model_error(f"Error calling {self.config.name} AI API: {e!s}") from e

        try:
            headers = self._build_headers()
        except AIError:
            raise
        except Exception as e:
            raise AIError.model_error(f"Error calling {self.config.name} AI API: {e!s}") from e

        try:
            body = self._build_request_body(messages, temperature, max_tokens, model, **kwargs)
        except AIError:
            raise
        except Exception as e:
            raise AIError.model_error(f"Error calling {self.config.name} AI API: {e!s}") from e

        # Add model to body if not already present
        if "model" not in body:
            body["model"] = model

        # Enable streaming in request body
        body["stream"] = True

        # Make streaming HTTP request
        accumulated_content = []
        usage_dict: dict | None = None

        try:
            with (
                httpx.Client(timeout=self.config.timeout) as client,
                client.stream("POST", url, json=body, headers=headers) as response,
            ):
                response.raise_for_status()

                # Parse SSE stream
                for line in response.iter_lines():
                    if not line or line.startswith(":"):
                        continue

                    # Remove "data: " prefix from SSE
                    if line.startswith("data: "):
                        line = line[6:]

                    # Check for stream end marker
                    if line == "[DONE]":
                        break

                    # Parse the chunk
                    content_chunk, chunk_usage = self._parse_stream_chunk(line)

                    # Yield content chunks as they arrive
                    if content_chunk:
                        accumulated_content.append(content_chunk)
                        yield (content_chunk, None)

                    # Capture usage data if present
                    if chunk_usage:
                        usage_dict = chunk_usage

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AIError.authentication_error(
                    f"{self.config.name} API: Invalid API key or authentication failed"
                ) from e
            elif e.response.status_code == 429:
                raise AIError.rate_limit_error(f"{self.config.name} API: Rate limit exceeded") from e
            elif e.response.status_code >= 500:
                raise AIError.connection_error(
                    f"{self.config.name} API: Server error (HTTP {e.response.status_code})"
                ) from e
            else:
                raise AIError.model_error(
                    f"{self.config.name} API error: HTTP {e.response.status_code} - {e.response.text}"
                ) from e
        except httpx.TimeoutException as e:
            raise AIError.timeout_error(f"{self.config.name} API request timed out") from e
        except httpx.RequestError as e:
            raise AIError.connection_error(f"{self.config.name} API network error: {e}") from e
        except Exception as e:
            raise AIError.model_error(f"Error calling {self.config.name} AI API: {e!s}") from e

        # Final yield with token usage
        if usage_dict is None:
            # Estimate usage if not provided
            usage_dict = {
                "prompt_tokens": 0,
                "completion_tokens": len("".join(accumulated_content)) // 4,
                "total_tokens": 0,
            }

        yield ("", usage_dict)


class OpenAICompatibleProvider(BaseConfiguredProvider):
    """Base class for OpenAI-compatible providers.

    Handles standard OpenAI API format with minimal customization needed.
    """

    default_path: str = "/v1/chat/completions"

    def _build_headers(self) -> dict[str, str]:
        """Build headers with OpenAI-style authorization."""
        headers = super()._build_headers()
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict[str, Any]:
        """Build OpenAI-style request body."""
        return {"messages": messages, "temperature": temperature, "max_tokens": max_tokens, **kwargs}

    def _parse_response(self, response: dict[str, Any]) -> str:
        """Parse OpenAI-style response."""
        choices = response.get("choices")
        if not choices or not isinstance(choices, list):
            raise AIError.model_error("Invalid response: missing choices")
        content = choices[0].get("message", {}).get("content")
        if content is None:
            raise AIError.model_error("Invalid response: null content")
        if content == "":
            raise AIError.model_error("Invalid response: empty content")
        return content

    def _parse_stream_chunk(self, line: str) -> tuple[str | None, dict | None]:
        """Parse OpenAI-style SSE chunk.

        Expected format:
        {"choices": [{"delta": {"content": "chunk"}}], "usage": {...}}
        """
        try:
            data = json.loads(line)

            # Extract content from delta
            choices = data.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                content = delta.get("content")
                if content:
                    return (content, None)

            # Extract usage data if present
            usage = data.get("usage")
            if usage:
                return (None, usage)

            return (None, None)

        except json.JSONDecodeError:
            return (None, None)


class AnthropicCompatibleProvider(BaseConfiguredProvider):
    """Base class for Anthropic-compatible providers."""

    default_path: str = "/v1/messages"

    def _build_headers(self) -> dict[str, str]:
        """Build headers with Anthropic-style authorization."""
        headers = super()._build_headers()
        api_key = self._get_api_key()
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"
        return headers

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict[str, Any]:
        """Build Anthropic-style request body."""
        # Convert messages to Anthropic format
        anthropic_messages = []
        system_message = ""

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        body = {"messages": anthropic_messages, "temperature": temperature, "max_tokens": max_tokens, **kwargs}

        if system_message:
            body["system"] = system_message

        return body

    def _parse_response(self, response: dict[str, Any]) -> str:
        """Parse Anthropic-style response."""
        content = response.get("content")
        if not content or not isinstance(content, list):
            raise AIError.model_error("Invalid response: missing content")

        text_content = content[0].get("text")
        if text_content is None:
            raise AIError.model_error("Invalid response: null content")
        if text_content == "":
            raise AIError.model_error("Invalid response: empty content")
        return text_content

    def _parse_stream_chunk(self, line: str) -> tuple[str | None, dict | None]:
        """Parse Anthropic-style SSE chunk.

        Anthropic uses event-based streaming with different event types:
        - content_block_delta: Contains text chunks
        - message_delta: Contains usage information
        """
        try:
            data = json.loads(line)

            # Extract text from content_block_delta
            if data.get("type") == "content_block_delta":
                delta = data.get("delta", {})
                text = delta.get("text")
                if text:
                    return (text, None)

            # Extract usage from message_delta
            if data.get("type") == "message_delta":
                usage = data.get("usage")
                if usage:
                    return (None, usage)

            return (None, None)

        except json.JSONDecodeError:
            return (None, None)


class GenericHTTPProvider(BaseConfiguredProvider):
    """Base class for completely custom providers."""

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict[str, Any]:
        """Default implementation - override this in subclasses."""
        return {"messages": messages, "temperature": temperature, "max_tokens": max_tokens, **kwargs}

    def _parse_response(self, response: dict[str, Any]) -> str:
        """Default implementation - override this in subclasses."""
        # Try OpenAI-style first
        choices = response.get("choices")
        if choices and isinstance(choices, list):
            content = choices[0].get("message", {}).get("content")
            if content:
                return content

        # Try Anthropic-style
        content = response.get("content")
        if content and isinstance(content, list):
            return content[0].get("text", "")

        # Try Ollama-style
        message = response.get("message", {})
        if "content" in message:
            return message["content"]

        # Fallback - try to find any string content
        for value in response.values():
            if isinstance(value, str) and len(value) > 10:  # Assume longer strings are content
                return value

        raise AIError.model_error("Could not extract content from response")

    def _parse_stream_chunk(self, line: str) -> tuple[str | None, dict | None]:
        """Generic stream chunk parser - tries multiple formats."""
        try:
            data = json.loads(line)

            # Try OpenAI format first
            choices = data.get("choices", [])
            if choices:
                delta = choices[0].get("delta", {})
                content = delta.get("content")
                if content:
                    return (content, None)

            # Try Anthropic format
            if data.get("type") == "content_block_delta":
                delta = data.get("delta", {})
                text = delta.get("text")
                if text:
                    return (text, None)

            # Try to extract usage
            usage = data.get("usage")
            if usage:
                return (None, usage)

            return (None, None)

        except json.JSONDecodeError:
            return (None, None)


__all__ = [
    "AnthropicCompatibleProvider",
    "BaseConfiguredProvider",
    "GenericHTTPProvider",
    "OpenAICompatibleProvider",
    "ProviderConfig",
]
