"""Kimi Coding AI provider implementation."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class KimiCodingProvider(OpenAICompatibleProvider):
    """Kimi Coding AI provider with OpenAI-compatible API."""

    config = ProviderConfig(
        name="Kimi Coding",
        api_key_env="KIMI_CODING_API_KEY",
        base_url="https://api.kimi.com",
        path="/coding/v1/chat/completions",
    )

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict:
        """Build Kimi Coding request body with max_completion_tokens."""
        data = super()._build_request_body(messages, temperature, max_tokens, model, **kwargs)

        # Use max_completion_tokens instead of max_tokens
        if "max_tokens" in data:
            data["max_completion_tokens"] = data.pop("max_tokens")

        return data
