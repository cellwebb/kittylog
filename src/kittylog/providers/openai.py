"""OpenAI provider implementation."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class OpenAIProvider(OpenAICompatibleProvider):
    """OpenAI API provider with model-specific adjustments."""

    config = ProviderConfig(
        name="OpenAI",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com",
        # Uses default path: /v1/chat/completions
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
