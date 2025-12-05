"""Mistral provider implementation for kittylog."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class MistralProvider(OpenAICompatibleProvider):
    config = ProviderConfig(
        name="Mistral",
        api_key_env="MISTRAL_API_KEY",
        base_url="https://api.mistral.ai/v1/chat/completions",
    )


def _get_mistral_provider() -> MistralProvider:
    """Lazy getter to initialize Mistral provider at call time."""
    return MistralProvider(MistralProvider.config)


@handle_provider_errors("Mistral")
def call_mistral_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Mistral API."""
    provider = _get_mistral_provider()
    return provider.generate(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
