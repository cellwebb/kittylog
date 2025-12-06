"""MiniMax API provider for kittylog."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class MiniMaxProvider(OpenAICompatibleProvider):
    """MiniMax provider."""

    config = ProviderConfig(
        name="MiniMax",
        api_key_env="MINIMAX_API_KEY",
        base_url="https://api.minimax.io",
        # Uses default path: /v1/chat/completions
    )
