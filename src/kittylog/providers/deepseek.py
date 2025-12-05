"""DeepSeek provider implementation for kittylog."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class DeepSeekProvider(OpenAICompatibleProvider):
    """DeepSeek API provider with empty content validation."""

    config = ProviderConfig(
        name="DeepSeek", api_key_env="DEEPSEEK_API_KEY", base_url="https://api.deepseek.com/v1/chat/completions"
    )

    def _parse_response(self, response: dict) -> str:
        """Parse DeepSeek response with additional validation."""
        content = super()._parse_response(response)

        if content == "":
            from kittylog.errors import AIError

            raise AIError.model_error("DeepSeek API returned empty content")

        return content


def _get_deepseek_provider() -> DeepSeekProvider:
    """Lazy getter to initialize DeepSeek provider at call time."""
    return DeepSeekProvider(DeepSeekProvider.config)


@handle_provider_errors("DeepSeek")
def call_deepseek_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call DeepSeek API."""
    provider = _get_deepseek_provider()
    return provider.generate(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
