"""Base provider class for AI API implementations."""

import os
from abc import ABC
from typing import Any

import httpx

from kittylog.errors import AIError


class BaseAPIProvider(ABC):
    """Base class for AI API providers.

    This class provides common functionality for API calls including:
    - API key validation
    - HTTP request handling with timeout
    - Standardized error handling
    - Response validation
    """

    # Provider-specific constants - to be overridden by subclasses
    API_URL: str
    API_KEY_ENV: str
    TIMEOUT: int = 120
    PROVIDER_NAME: str

    def __init__(self):
        self._api_key = None  # Lazy load

    @property
    def api_key(self) -> str:
        """Lazy-load API key when needed."""
        if self._api_key is None:
            self._api_key = self._get_api_key()
        return self._api_key

    def _get_api_key(self) -> str:
        """Get API key from environment variables."""
        api_key = os.getenv(self.API_KEY_ENV)
        if not api_key:
            raise AIError.generation_error(f"{self.API_KEY_ENV} not found in environment variables")
        return api_key

    def _get_headers(self) -> dict[str, str]:
        """Get default headers for the API request.

        Can be overridden by subclasses to add provider-specific headers.
        """
        return {
            "Content-Type": "application/json",
        }

    def _prepare_request_data(
        self, model: str, messages: list[dict], temperature: float, max_tokens: int, **kwargs
    ) -> dict[str, Any]:
        """Prepare request data payload.

        Can be overridden by subclasses to customize the request format.
        """
        return {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, **kwargs}

    def _process_response_data(self, response_data: dict[str, Any]) -> str:
        """Process response data and extract content.

        Default implementation expects OpenAI-style response format.
        Can be overridden by subclasses for different response formats.
        """
        choices = response_data.get("choices")
        if not choices or not isinstance(choices, list):
            raise AIError.generation_error("Invalid response: missing choices")
        content = choices[0].get("message", {}).get("content")
        if content is None:
            raise AIError.generation_error("Invalid response: missing content")
        return content

    def call(self, model: str, messages: list[dict], temperature: float, max_tokens: int, **kwargs) -> str:
        """Make API call with common error handling.

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
        headers = self._get_headers()
        data = self._prepare_request_data(model, messages, temperature, max_tokens, **kwargs)

        try:
            response = httpx.post(self.API_URL, headers=headers, json=data, timeout=self.TIMEOUT)
            response.raise_for_status()
            response_data = response.json()
            return self._process_response_data(response_data)

        except httpx.HTTPStatusError as e:
            raise AIError.generation_error(
                f"{self.PROVIDER_NAME} API error: {e.response.status_code} - {e.response.text}"
            ) from e
        except httpx.TimeoutException as e:
            raise AIError.generation_error(f"{self.PROVIDER_NAME} API request timed out") from e
        except httpx.RequestError as e:
            raise AIError.generation_error(f"{self.PROVIDER_NAME} API network error: {e}") from e
        except (KeyError, IndexError, TypeError) as e:
            raise AIError.generation_error(f"{self.PROVIDER_NAME} API invalid response format: {e}") from e
        except Exception as e:
            raise AIError.generation_error(f"Error calling {self.PROVIDER_NAME} API: {e!s}") from e
