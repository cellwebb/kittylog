"""Fireworks AI provider implementation for kittylog."""

import os

import httpx

from kittylog.errors import AIError


def call_fireworks_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call the Fireworks AI API."""
    api_key = os.getenv("FIREWORKS_API_KEY")
    if not api_key:
        raise AIError.authentication_error("FIREWORKS_API_KEY not found in environment variables")

    url = "https://api.fireworks.ai/inference/v1/chat/completions"
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
            raise AIError.model_error("Fireworks AI API returned null content")
        if content == "":
            raise AIError.model_error("Fireworks AI API returned empty content")
        return content
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise AIError.rate_limit_error(f"Fireworks AI API rate limit exceeded: {e.response.text}") from e
        raise AIError.model_error(f"Fireworks AI API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.TimeoutException as e:
        raise AIError.timeout_error(f"Fireworks AI API request timed out: {e!s}") from e
    except Exception as e:
        raise AIError.model_error(f"Error calling Fireworks AI API: {e!s}") from e
