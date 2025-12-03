"""LM Studio provider implementation for kittylog."""

import os
from typing import Any

import httpx

from kittylog.errors import AIError


def call_lmstudio_api(model: str, messages: list[dict[str, Any]], temperature: float, max_tokens: int) -> str:
    """Call the LM Studio OpenAI-compatible API."""
    api_url = os.getenv("LMSTUDIO_API_URL", "http://localhost:1234").rstrip("/")
    url = f"{api_url}/v1/chat/completions"

    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("LMSTUDIO_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        choices = response_data.get("choices") or []
        if not choices:
            raise AIError.model_error("LM Studio API response missing choices")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if content:
            return content

        fallback_content = choices[0].get("text")
        if fallback_content:
            return fallback_content

        raise AIError.model_error("LM Studio API response missing content")
    except httpx.ConnectError as e:
        raise AIError.connection_error(f"LM Studio connection failed: {e!s}") from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise AIError.rate_limit_error(f"LM Studio API rate limit exceeded: {e.response.text}") from e
        raise AIError.model_error(f"LM Studio API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.TimeoutException as e:
        raise AIError.timeout_error(f"LM Studio API request timed out: {e!s}") from e
    except Exception as e:
        raise AIError.model_error(f"Error calling LM Studio API: {e!s}") from e
