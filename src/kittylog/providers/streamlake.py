"""StreamLake (Vanchin) API provider for kittylog."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig
from kittylog.providers.error_handler import handle_provider_errors


class StreamLakeProvider(OpenAICompatibleProvider):
    """StreamLake API provider with dual API key support."""

    def _get_api_key(self) -> str:
        """Get API key from environment with alias support."""
        import os

        from kittylog.errors import AIError

        api_key = os.getenv("STREAMLAKE_API_KEY") or os.getenv("VC_API_KEY")
        if not api_key:
            raise AIError.generation_error(
                "STREAMLAKE_API_KEY not found in environment variables (VC_API_KEY alias also not set)"
            )
        return api_key

    def _parse_response(self, response: dict) -> str:
        """Parse StreamLake response with validation."""
        content = super()._parse_response(response)

        if content is None:
            from kittylog.errors import AIError

            raise AIError.generation_error("StreamLake API returned null content")
        if content == "":
            from kittylog.errors import AIError

            raise AIError.generation_error("StreamLake API returned empty content")

        return content


# Provider configuration
_streamlake_config = ProviderConfig(
    name="StreamLake",
    api_key_env="STREAMLAKE_API_KEY",
    base_url="https://vanchin.streamlake.ai/api/gateway/v1/endpoints/chat/completions",
)


def _get_streamlake_provider() -> StreamLakeProvider:
    """Lazy getter to initialize StreamLake provider at call time."""
    return StreamLakeProvider(_streamlake_config)


@handle_provider_errors("StreamLake")
def call_streamlake_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
    """Call StreamLake (Vanchin) chat completions API."""
    provider = _get_streamlake_provider()
    return provider.generate(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
