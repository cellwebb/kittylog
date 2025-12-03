"""Custom OpenAI-compatible provider implementation for kittylog."""

import json
import logging
import os

import httpx

from kittylog.errors import AIError

logger = logging.getLogger(__name__)


def call_custom_openai_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call a custom OpenAI-compatible endpoint."""
    api_key = os.getenv("CUSTOM_OPENAI_API_KEY")
    if not api_key:
        raise AIError.authentication_error("CUSTOM_OPENAI_API_KEY environment variable not set")

    base_url = os.getenv("CUSTOM_OPENAI_BASE_URL")
    if not base_url:
        raise AIError.model_error("CUSTOM_OPENAI_BASE_URL environment variable not set")

    if "/chat/completions" not in base_url:
        base_url = base_url.rstrip("/")
        url = f"{base_url}/chat/completions"
    else:
        url = base_url

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    data = {"model": model, "messages": messages, "temperature": temperature, "max_completion_tokens": max_tokens}

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        response_data = response.json()

        choices = response_data.get("choices")
        if not choices or not isinstance(choices, list):
            raise AIError.generation_error("Invalid response: missing choices")
        content = choices[0].get("message", {}).get("content")
        if content is None:
            raise AIError.generation_error("Invalid response: missing content")
        if content == "":
            raise AIError.model_error("Custom OpenAI API returned empty content")
        return content
    except (KeyError, IndexError, TypeError) as e:
        logger.error("Unexpected response format from Custom OpenAI API. Response: %s", json.dumps(response_data))
        raise AIError.model_error(
            "Custom OpenAI API returned unexpected format. Expected OpenAI-compatible response."
        ) from e
    except httpx.ConnectError as e:
        raise AIError.connection_error(f"Custom OpenAI API connection failed: {e!s}") from e
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        error_text = e.response.text

        if status_code == 401:
            raise AIError.authentication_error(f"Custom OpenAI API authentication failed: {error_text}") from e
        if status_code == 429:
            raise AIError.rate_limit_error(f"Custom OpenAI API rate limit exceeded: {error_text}") from e
        raise AIError.model_error(f"Custom OpenAI API error: {status_code} - {error_text}") from e
    except httpx.TimeoutException as e:
        raise AIError.timeout_error(f"Custom OpenAI API request timed out: {e!s}") from e
    except AIError:
        raise
    except Exception as e:
        raise AIError.model_error(f"Error calling Custom OpenAI API: {e!s}") from e
