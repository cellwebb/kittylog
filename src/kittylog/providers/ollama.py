"""Ollama AI provider implementation."""

import os

import httpx

from kittylog.errors import AIError


def call_ollama_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Ollama API directly."""
    api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")

    url = f"{api_url.rstrip('/')}/api/chat"
    data = {"model": model, "messages": messages, "temperature": temperature, "stream": False}

    try:
        response = httpx.post(url, json=data, timeout=120)
        response.raise_for_status()
        response_data = response.json()

        # Handle different response formats from Ollama
        if "message" in response_data and "content" in response_data["message"]:
            return response_data["message"]["content"]
        elif "response" in response_data:
            return response_data["response"]
        else:
            # Fallback: return the full response as string
            return str(response_data)
    except httpx.ConnectError as e:
        raise AIError.generation_error(f"Ollama connection failed. Make sure Ollama is running: {e!s}") from e
    except httpx.HTTPStatusError as e:
        raise AIError.generation_error(f"Ollama API error: {e.response.status_code} - {e.response.text}") from e
    except Exception as e:
        raise AIError.generation_error(f"Error calling Ollama API: {e!s}") from e
