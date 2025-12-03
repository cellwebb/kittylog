"""OpenAI provider implementation."""

from kittylog.providers.base import BaseAPIProvider


class OpenAIProvider(BaseAPIProvider):
    """OpenAI API provider."""

    API_URL = "https://api.openai.com/v1/chat/completions"
    API_KEY_ENV = "OPENAI_API_KEY"
    PROVIDER_NAME = "OpenAI"

    def _get_headers(self):
        headers = super()._get_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _prepare_request_data(self, model, messages, temperature, max_tokens, **kwargs):
        """Prepare OpenAI-specific request data."""
        data = super()._prepare_request_data(model, messages, temperature, max_tokens, **kwargs)

        # OpenAI-specific adjustments
        if model.startswith("gpt-5") or model.startswith("o"):
            data["temperature"] = 1.0

        # Use max_completion_tokens instead of max_tokens for some models
        data["max_completion_tokens"] = data.pop("max_tokens")

        # Handle optional parameters
        if "response_format" in kwargs:
            data["response_format"] = kwargs["response_format"]
        if "stop" in kwargs:
            data["stop"] = kwargs["stop"]

        return data


# Create provider instance
_openai_provider = OpenAIProvider()


def call_openai_api(
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    stream: bool = False,
    response_format: dict | None = None,
    stop: list | None = None,
) -> str:
    """Call OpenAI API directly.

    Args:
        model: Model name
        messages: List of message dictionaries
        temperature: Temperature parameter
        max_tokens: Maximum tokens in response
        stream: Whether to stream response (not implemented yet)
        response_format: Response format specification
        stop: Stop sequences

    Returns:
        Generated text content

    Raises:
        AIError: For any API-related errors
    """
    return _openai_provider.call(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        stop=stop,
    )
