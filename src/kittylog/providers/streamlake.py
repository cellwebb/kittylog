"""StreamLake (Vanchin) API provider for kittylog."""

import os

from kittylog.errors import AIError
from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class StreamLakeProvider(OpenAICompatibleProvider):
    """StreamLake API provider with dual API key support."""

    config = ProviderConfig(
        name="StreamLake",
        api_key_env="STREAMLAKE_API_KEY",
        base_url="https://vanchin.streamlake.ai",
        path="/api/gateway/v1/endpoints/chat/completions",
    )

    def _get_api_key(self) -> str:
        """Get API key from environment with alias support."""
        api_key = os.getenv("STREAMLAKE_API_KEY") or os.getenv("VC_API_KEY")
        if not api_key:
            raise AIError.authentication_error(
                "STREAMLAKE_API_KEY not found in environment variables (VC_API_KEY alias also not set)"
            )
        return api_key
