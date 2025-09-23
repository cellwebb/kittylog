"""AI provider implementations for changelog generation.

This module contains direct API implementations for various AI providers.
"""

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
        raise AIError.generation_error(f"Error calling Anthropic API: {str(e)}") from e


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


def call_groq_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Groq API directly."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise AIError.generation_error("GROQ_API_KEY not found in environment variables")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    data = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise AIError.generation_error(f"Groq API error: {e.response.status_code} - {e.response.text}") from e
    except Exception as e:
        raise AIError.generation_error(f"Error calling Groq API: {str(e)}") from e


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
        raise AIError.generation_error(f"Ollama connection failed. Make sure Ollama is running: {str(e)}") from e
    except httpx.HTTPStatusError as e:
        raise AIError.generation_error(f"Ollama API error: {e.response.status_code} - {e.response.text}") from e
    except Exception as e:
        raise AIError.generation_error(f"Error calling Ollama API: {str(e)}") from e


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
