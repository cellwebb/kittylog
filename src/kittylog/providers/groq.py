"""Groq AI provider implementation."""

from kittylog.providers.base import OpenAICompatibleProvider, ProviderConfig


class GroqProvider(OpenAICompatibleProvider):
    config = ProviderConfig(
        name="Groq",
        api_key_env="GROQ_API_KEY",
        base_url="https://api.groq.com",
        path="/openai/v1/chat/completions",
    )
