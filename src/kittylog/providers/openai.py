"""OpenAI provider implementation."""

import os

import httpx

from kittylog.errors import AIError


def call_openai_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call OpenAI API directly."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AIError.generation_error("OPENAI_API_KEY not found in environment variables")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    data = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise AIError.generation_error(f"OpenAI API error: {e.response.status_code} - {e.response.text}") from e
    except Exception as e:
        raise AIError.generation_error(f"Error calling OpenAI API: {str(e)}") from e
