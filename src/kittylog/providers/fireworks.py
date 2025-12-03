"""Fireworks AI provider implementation for kittylog."""

import httpx

from kittylog.errors import AIError
from kittylog.providers.base import BaseAPIProvider


class FireworksProvider(BaseAPIProvider):
    """Fireworks AI API provider."""

    API_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
    API_KEY_ENV = "FIREWORKS_API_KEY"
    PROVIDER_NAME = "Fireworks AI"

    def _get_headers(self):
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _process_response_data(self, response_data):
        """Process Fireworks-specific response with additional validation."""
        content = super()._process_response_data(response_data)

        if content == "":
            raise AIError.model_error("Fireworks AI API returned empty content")

        return content

    def call(self, model, messages, temperature, max_tokens, **kwargs):
        """Override to handle Fireworks-specific error handling."""
        headers = self._get_headers()
        data = self._prepare_request_data(model, messages, temperature, max_tokens, **kwargs)

        try:
            response = httpx.post(self.API_URL, headers=headers, json=data, timeout=self.TIMEOUT)
            response.raise_for_status()
            response_data = response.json()
            return self._process_response_data(response_data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise AIError.rate_limit_error(f"Fireworks AI API rate limit exceeded: {e.response.text}") from e
            raise AIError.model_error(f"Fireworks AI API error: {e.response.status_code} - {e.response.text}") from e
        except httpx.TimeoutException as e:
            raise AIError.timeout_error(f"Fireworks AI API request timed out: {e!s}") from e
        except httpx.RequestError as e:
            raise AIError.model_error(f"Fireworks AI API network error: {e}") from e
        except (KeyError, IndexError, TypeError) as e:
            raise AIError.model_error(f"Fireworks AI API invalid response format: {e}") from e
        except Exception as e:
            raise AIError.model_error(f"Error calling Fireworks AI API: {e!s}") from e


# Create provider instance
_fireworks_provider = FireworksProvider()


def call_fireworks_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Fireworks AI API.

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
    return _fireworks_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
