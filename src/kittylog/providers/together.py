"""Together AI provider implementation for kittylog."""

import os

import httpx

from kittylog.errors import AIError


def call_together_api(
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    stream: bool = False,
    response_format: dict | None = None,
    stop: list | None = None,
) -> str:
    """Call the Together AI API."""
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise AIError.authentication_error("TOGETHER_API_KEY not found in environment variables")

    url = "https://api.together.xyz/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    data = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}

    # Add optional parameters if provided
    if response_format:
        data["response_format"] = response_format
    if stop:
        data["stop"] = stop
    # Note: stream parameter ignored for now - not implemented

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        choices = response_data.get("choices")
        if not choices or not isinstance(choices, list):
            raise AIError.generation_error("Invalid response: missing choices")
        content = choices[0].get("message", {}).get("content")
        if content is None:
            raise AIError.model_error("Together AI API returned null content")
        return content  # Empty string is valid
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise AIError.rate_limit_error(f"Together AI API rate limit exceeded: {e.response.text}") from e
        raise AIError.model_error(f"Together API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.TimeoutException as e:
        raise AIError.timeout_error(f"Together AI API request timed out: {e!s}") from e
    except Exception as e:
        raise AIError.model_error(f"Error calling Together API: {e!s}") from e
