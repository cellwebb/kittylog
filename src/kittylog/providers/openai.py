"""OpenAI provider implementation."""

from kittylog.providers.base_configured import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class OpenAIProvider(OpenAICompatibleProvider):
    """OpenAI API provider with model-specific adjustments."""

    config = ProviderConfig(
        name="OpenAI", api_key_env="OPENAI_API_KEY", base_url="https://api.openai.com/v1/chat/completions"
    )

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict:
        """Build OpenAI-specific request body."""
        data = super()._build_request_body(messages, temperature, max_tokens, model, **kwargs)

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


# Create provider instance for backward compatibility
openai_provider = OpenAIProvider(OpenAIProvider.config)


@handle_provider_errors("OpenAI")
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
    return openai_provider.generate(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        stop=stop,
    )
