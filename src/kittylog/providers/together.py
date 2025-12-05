"""Together AI provider for kittylog."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class TogetherProvider(OpenAICompatibleProvider):
    config = ProviderConfig(
        name="Together AI",
        api_key_env="TOGETHER_API_KEY",
        base_url="https://api.together.xyz/v1/chat/completions",
    )


def _get_together_provider() -> TogetherProvider:
    """Lazy getter to initialize Together AI provider at call time."""
    return TogetherProvider(TogetherProvider.config)


@handle_provider_errors("Together AI")
def call_together_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Together AI API directly."""
    provider = _get_together_provider()
    return provider.generate(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
