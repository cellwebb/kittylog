"""Cerebras AI provider implementation."""

import os

import httpx

from kittylog.errors import AIError


def call_cerebras_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Cerebras API directly."""
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        raise AIError.generation_error("CEREBRAS_API_KEY not found in environment variables")

    url = "https://api.cerebras.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    data = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise AIError.generation_error(f"Cerebras API error: {e.response.status_code} - {e.response.text}") from e
    except Exception as e:
        raise AIError.generation_error(f"Error calling Cerebras API: {str(e)}") from e
