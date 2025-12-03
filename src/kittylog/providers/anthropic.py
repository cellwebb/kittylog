"""Anthropic AI provider implementation."""

import os

import httpx

from kittylog.errors import AIError


def call_anthropic_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Anthropic API directly."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise AIError.generation_error("ANTHROPIC_API_KEY not found in environment variables")

    url = "https://api.anthropic.com/v1/messages"
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}

    # Convert messages to Anthropic format
    anthropic_messages = []
    system_message = ""

    for msg in messages:
        if msg["role"] == "system":
            system_message = msg["content"]
        else:
            anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

    data = {"model": model, "messages": anthropic_messages, "temperature": temperature, "max_tokens": max_tokens}

    if system_message:
        data["system"] = system_message

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        return response_data["content"][0]["text"]
    except httpx.HTTPStatusError as e:
        raise AIError.generation_error(f"Anthropic API error: {e.response.status_code} - {e.response.text}") from e
    except Exception as e:
        raise AIError.generation_error(f"Error calling Anthropic API: {e!s}") from e
