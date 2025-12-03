"""DeepSeek provider implementation for kittylog."""

import httpx

from kittylog.errors import AIError
from kittylog.providers.base import BaseAPIProvider


class DeepSeekProvider(BaseAPIProvider):
    """DeepSeek API provider."""

    API_URL = "https://api.deepseek.com/v1/chat/completions"
    API_KEY_ENV = "DEEPSEEK_API_KEY"
    PROVIDER_NAME = "DeepSeek"

    def _get_headers(self):
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _process_response_data(self, response_data):
        """Process DeepSeek-specific response with additional validation."""
        content = super()._process_response_data(response_data)

        if content == "":
            raise AIError.model_error("DeepSeek API returned empty content")

        return content

    def call(self, model, messages, temperature, max_tokens, **kwargs):
        """Override to handle DeepSeek-specific error handling."""
        headers = self._get_headers()
        data = self._prepare_request_data(model, messages, temperature, max_tokens, **kwargs)

        try:
            response = httpx.post(self.API_URL, headers=headers, json=data, timeout=self.TIMEOUT)
            response.raise_for_status()
            response_data = response.json()
            return self._process_response_data(response_data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise AIError.rate_limit_error(f"DeepSeek API rate limit exceeded: {e.response.text}") from e
            raise AIError.model_error(f"DeepSeek API error: {e.response.status_code} - {e.response.text}") from e
        except httpx.TimeoutException as e:
            raise AIError.timeout_error(f"DeepSeek API request timed out: {e!s}") from e
        except (KeyError, IndexError, TypeError) as e:
            raise AIError.model_error(f"DeepSeek API invalid response format: {e}") from e
        except Exception as e:
            raise AIError.model_error(f"Error calling DeepSeek API: {e!s}") from e


# Create provider instance
_deepseek_provider = DeepSeekProvider()


def call_deepseek_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call DeepSeek API.

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
    return _deepseek_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
