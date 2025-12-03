"""Chutes.ai provider implementation for kittylog."""

import os

import httpx

from kittylog.errors import AIError


def call_chutes_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call the Chutes.ai API using an OpenAI-compatible endpoint."""
    api_key = os.getenv("CHUTES_API_KEY")
    if not api_key:
        raise AIError.authentication_error("CHUTES_API_KEY environment variable not set")

    base_url = os.getenv("CHUTES_BASE_URL", "https://llm.chutes.ai").rstrip("/")
    url = f"{base_url}/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        choices = response_data.get("choices")
        if not choices or not isinstance(choices, list):
            raise AIError.generation_error("Invalid response: missing choices")
        content = choices[0].get("message", {}).get("content")
        if content is None:
            raise AIError.model_error("Chutes.ai API returned null content")
        if content == "":
            raise AIError.model_error("Chutes.ai API returned empty content")
        return content
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        error_text = e.response.text

        if status_code == 429:
            raise AIError.rate_limit_error(f"Chutes.ai API rate limit exceeded: {error_text}") from e
        if status_code in (502, 503):
            raise AIError.connection_error(f"Chutes.ai API service unavailable: {status_code} - {error_text}") from e
        raise AIError.model_error(f"Chutes.ai API error: {status_code} - {error_text}") from e
    except httpx.ConnectError as e:
        raise AIError.connection_error(f"Chutes.ai API connection error: {e!s}") from e
    except httpx.TimeoutException as e:
        raise AIError.timeout_error(f"Chutes.ai API request timed out: {e!s}") from e
    except Exception as e:
        raise AIError.model_error(f"Error calling Chutes.ai API: {e!s}") from e
