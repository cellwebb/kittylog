"""Cerebras AI provider implementation."""

import os

import httpx

from kittylog.errors import AIError


def call_cerebras_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Cerebras API directly."""
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        raise AIError.generation_error("CEREBRAS_API_KEY not found in environment variables")

    url = "https://api.cerebras.ai/v2/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    data = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}

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
        return content
    except httpx.HTTPStatusError as e:
        raise AIError.generation_error(f"Cerebras API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.TimeoutException as e:
        raise AIError.generation_error("Cerebras API request timed out") from e
    except httpx.RequestError as e:
        raise AIError.generation_error(f"Cerebras API network error: {e}") from e
    except (KeyError, IndexError, TypeError) as e:
        raise AIError.generation_error(f"Cerebras API invalid response format: {e}") from e
    except Exception as e:
        raise AIError.generation_error(f"Error calling Cerebras API: {e!s}") from e
