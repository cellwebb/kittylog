"""Custom Anthropic-compatible provider implementation for kittylog."""

import json
import logging
import os

import httpx

from kittylog.errors import AIError

logger = logging.getLogger(__name__)


def call_custom_anthropic_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call a custom Anthropic-compatible endpoint."""
    api_key = os.getenv("CUSTOM_ANTHROPIC_API_KEY")
    if not api_key:
        raise AIError.authentication_error("CUSTOM_ANTHROPIC_API_KEY environment variable not set")

    base_url = os.getenv("CUSTOM_ANTHROPIC_BASE_URL")
    if not base_url:
        raise AIError.model_error("CUSTOM_ANTHROPIC_BASE_URL environment variable not set")

    api_version = os.getenv("CUSTOM_ANTHROPIC_VERSION", "2023-06-01")

    if "/v1/messages" not in base_url:
        base_url = base_url.rstrip("/")
        url = f"{base_url}/v1/messages"
    else:
        url = base_url

    headers = {"x-api-key": api_key, "anthropic-version": api_version, "content-type": "application/json"}

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

        try:
            content_list = response_data.get("content", [])
            if not content_list:
                raise AIError.model_error("Custom Anthropic API returned empty content array")

            if "text" in content_list[0]:
                content = content_list[0]["text"]
            else:
                text_item = next((item for item in content_list if item.get("type") == "text"), None)
                if text_item and "text" in text_item:
                    content = text_item["text"]
                else:
                    logger.error(
                        "Unexpected response format from Custom Anthropic API. Response: %s",
                        json.dumps(response_data),
                    )
                    raise AIError.model_error(
                        "Custom Anthropic API returned unexpected format. Expected content items with 'text'."
                    )
        except AIError:
            raise
        except (KeyError, IndexError, TypeError, StopIteration) as e:
            logger.error(
                "Unexpected response format from Custom Anthropic API. Response: %s", json.dumps(response_data)
            )
            raise AIError.model_error(
                "Custom Anthropic API returned unexpected format. Expected Anthropic-compatible response."
            ) from e

        if content is None:
            raise AIError.model_error("Custom Anthropic API returned null content")
        if content == "":
            raise AIError.model_error("Custom Anthropic API returned empty content")
        return content
    except httpx.ConnectError as e:
        raise AIError.connection_error(f"Custom Anthropic API connection failed: {str(e)}") from e
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        error_text = e.response.text

        if status_code == 401:
            raise AIError.authentication_error(f"Custom Anthropic API authentication failed: {error_text}") from e
        if status_code == 429:
            raise AIError.rate_limit_error(f"Custom Anthropic API rate limit exceeded: {error_text}") from e
        raise AIError.model_error(f"Custom Anthropic API error: {status_code} - {error_text}") from e
    except httpx.TimeoutException as e:
        raise AIError.timeout_error(f"Custom Anthropic API request timed out: {str(e)}") from e
    except AIError:
        raise
    except Exception as e:
        raise AIError.model_error(f"Error calling Custom Anthropic API: {str(e)}") from e

