# AI Provider System

This directory contains AI provider implementations for kittylog's changelog generation.

## Architecture

Each provider is a standalone module that implements a `call_<provider>_api()` function with a consistent signature:

```python
def call_<provider>_api(
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int
) -> str:
```

### Parameters

- `model`: The model identifier (e.g., "gpt-4", "claude-3-opus")
- `messages`: List of message dicts with "role" and "content" keys
- `temperature`: Generation temperature (0.0-2.0)
- `max_tokens`: Maximum tokens in response

### Returns

- `str`: The generated content from the AI model

### Errors

All providers should raise `AIError.generation_error()` for any API failures.

## Adding a New Provider

1. Create a new file `src/kittylog/providers/<provider_name>.py`:

```python
"""<Provider Name> provider implementation."""

import os
import httpx
from kittylog.errors import AIError


def call_<provider>_api(
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int
) -> str:
    """Call <Provider Name> API."""
    api_key = os.getenv("<PROVIDER>_API_KEY")
    if not api_key:
        raise AIError.generation_error("<PROVIDER>_API_KEY not found in environment")

    url = "https://api.<provider>.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        response = httpx.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise AIError.generation_error(
            f"<Provider> API error: {e.response.status_code} - {e.response.text}"
        ) from e
    except Exception as e:
        raise AIError.generation_error(f"Error calling <Provider> API: {e!s}") from e
```

2. Export in `__init__.py`:

```python
from .<provider_name> import call_<provider>_api

__all__ = [
    # ... existing exports
    "call_<provider>_api",
]
```

3. Register in `ai.py` provider mapping:

```python
provider_funcs = {
    # ... existing providers
    "<provider>": call_<provider>_api,
}
```

4. Add API key to `config.py` API_KEYS list:

```python
API_KEYS = [
    # ... existing keys
    "<PROVIDER>_API_KEY",
]
```

## Available Providers

| Provider | Prefix | Environment Variable |
|----------|--------|---------------------|
| Anthropic | `anthropic:` | `ANTHROPIC_API_KEY` |
| OpenAI | `openai:` | `OPENAI_API_KEY` |
| Azure OpenAI | `azure-openai:` | `AZURE_OPENAI_API_KEY` |
| Groq | `groq:` | `GROQ_API_KEY` |
| Cerebras | `cerebras:` | `CEREBRAS_API_KEY` |
| Ollama | `ollama:` | `OLLAMA_HOST` (optional) |
| Gemini | `gemini:` | `GEMINI_API_KEY` |
| Mistral | `mistral:` | `MISTRAL_API_KEY` |
| DeepSeek | `deepseek:` | `DEEPSEEK_API_KEY` |
| Fireworks | `fireworks:` | `FIREWORKS_API_KEY` |
| Together | `together:` | `TOGETHER_API_KEY` |
| OpenRouter | `openrouter:` | `OPENROUTER_API_KEY` |
| Replicate | `replicate:` | `REPLICATE_API_TOKEN` |
| LM Studio | `lm-studio:` | `LMSTUDIO_API_URL` |
| Custom OpenAI | `custom-openai:` | `CUSTOM_OPENAI_API_KEY` |
| Custom Anthropic | `custom-anthropic:` | `CUSTOM_ANTHROPIC_API_KEY` |

## Usage

Models are specified as `<provider>:<model_name>`:

```bash
kittylog --model openai:gpt-4o-mini
kittylog --model anthropic:claude-3-haiku-20240307
kittylog --model ollama:llama3
```
