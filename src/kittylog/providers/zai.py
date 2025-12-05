"""Z.AI API provider for kittylog."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class ZAIProvider(OpenAICompatibleProvider):
    """Z.AI API provider with content validation."""

    def _parse_response(self, response: dict) -> str:
        """Parse Z.AI response with validation."""
        content = super()._parse_response(response)

        if content is None:
            from kittylog.errors import AIError

            raise AIError.generation_error("Z.AI API returned null content")
        if content == "":
            from kittylog.errors import AIError

            raise AIError.generation_error("Z.AI API returned empty content")

        return content


# Provider configurations
_zai_config = ProviderConfig(
    name="Z.AI", api_key_env="ZAI_API_KEY", base_url="https://api.z.ai/api/paas/v4/chat/completions"
)

_zai_coding_config = ProviderConfig(
    name="Z.AI Coding", api_key_env="ZAI_API_KEY", base_url="https://api.z.ai/api/coding/paas/v4/chat/completions"
)


def _get_zai_provider() -> ZAIProvider:
    """Lazy getter to initialize Z.AI provider at call time."""
    return ZAIProvider(_zai_config)


def _get_zai_coding_provider() -> ZAIProvider:
    """Lazy getter to initialize Z.AI Coding provider at call time."""
    return ZAIProvider(_zai_coding_config)


@handle_provider_errors("Z.AI")
def call_zai_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Z.AI regular API directly."""
    provider = _get_zai_provider()
    return provider.generate(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)


@handle_provider_errors("Z.AI Coding")
def call_zai_coding_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call Z.AI coding API directly."""
    provider = _get_zai_coding_provider()
    return provider.generate(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
