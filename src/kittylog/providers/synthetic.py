"""Synthetic.new API provider for kittylog."""

import os

from kittylog.errors import AIError
from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class SyntheticProvider(OpenAICompatibleProvider):
    """Synthetic.new API provider with hf: model prefix and dual API key support."""

    config = ProviderConfig(
        name="Synthetic",
        api_key_env="SYNTHETIC_API_KEY",
        base_url="https://api.synthetic.new",
        path="/openai/v1/chat/completions",
    )

    def _get_api_key(self) -> str:
        """Get API key from environment with alias support."""
        api_key = os.getenv("SYNTHETIC_API_KEY") or os.getenv("SYN_API_KEY")
        if not api_key:
            raise AIError.authentication_error("SYNTHETIC_API_KEY or SYN_API_KEY not found in environment variables")
        return api_key

    def _build_request_body(
        self, messages: list[dict], temperature: float, max_tokens: int, model: str, **kwargs
    ) -> dict:
        """Build Synthetic request body with hf: model prefix."""
        data = super()._build_request_body(messages, temperature, max_tokens, model, **kwargs)

        # Handle model names without hf: prefix
        if not model.startswith("hf:"):
            data["model"] = f"hf:{model}"

        # Synthetic uses max_completion_tokens
        if "max_tokens" in data:
            data["max_completion_tokens"] = data.pop("max_tokens")

        return data
