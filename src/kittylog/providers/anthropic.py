"""Anthropic AI provider implementation."""

from kittylog.providers.base import BaseAPIProvider


class AnthropicProvider(BaseAPIProvider):
    """Anthropic API provider."""

    API_URL = "https://api.anthropic.com/v1/messages"
    API_KEY_ENV = "ANTHROPIC_API_KEY"
    PROVIDER_NAME = "Anthropic"

    def _get_headers(self):
        headers = super()._get_headers()
        headers["x-api-key"] = self.api_key
        headers["anthropic-version"] = "2023-06-01"
        return headers

    def _prepare_request_data(self, model, messages, temperature, max_tokens, **kwargs):
        """Prepare Anthropic-specific request data."""
        # Convert messages to Anthropic format
        anthropic_messages = []
        system_message = ""

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        data = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if system_message:
            data["system"] = system_message

        return data

    def _process_response_data(self, response_data):
        """Process Anthropic-specific response format."""
        return response_data["content"][0]["text"]


# Create provider instance
_anthropic_provider = AnthropicProvider()


def call_anthropic_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Anthropic API directly.

    Args:
        model: Model name
        messages: List of message dictionaries
        temperature: Temperature parameter
        max_tokens: Maximum tokens in response

    Returns:
        Generated text content

    Raises:
        AIError: For any API-related errors
    """
    return _anthropic_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
