"""Unit tests for newly added AI providers."""

import pytest

from kittylog.errors import AIError
from kittylog.providers import PROVIDER_REGISTRY

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


@pytest.mark.parametrize(
    ("provider_key", "required_env"),
    [
        ("chutes", "CHUTES_API_KEY"),
        ("deepseek", "DEEPSEEK_API_KEY"),
        ("fireworks", "FIREWORKS_API_KEY"),
        ("gemini", "GEMINI_API_KEY"),
        ("minimax", "MINIMAX_API_KEY"),
        ("mistral", "MISTRAL_API_KEY"),
        ("streamlake", "STREAMLAKE_API_KEY"),
        ("together", "TOGETHER_API_KEY"),
    ],
)
def test_provider_missing_api_key(provider_key, required_env, monkeypatch):
    """Ensure providers fail fast when API keys are missing."""
    monkeypatch.delenv(required_env, raising=False)
    if required_env == "STREAMLAKE_API_KEY":
        monkeypatch.delenv("VC_API_KEY", raising=False)

    with pytest.raises(AIError) as exc_info:
        PROVIDER_REGISTRY[provider_key]("test-model", _DUMMY_MESSAGES, 0.7, 32)

    assert required_env in str(exc_info.value)


def test_custom_anthropic_requires_base_url(monkeypatch):
    """Custom Anthropic provider should require a base URL."""
    monkeypatch.setenv("CUSTOM_ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("CUSTOM_ANTHROPIC_BASE_URL", raising=False)

    with pytest.raises(AIError) as exc_info:
        PROVIDER_REGISTRY["custom-anthropic"]("claude-test", _DUMMY_MESSAGES, 0.7, 32)

    assert "CUSTOM_ANTHROPIC_BASE_URL" in str(exc_info.value)


def test_custom_openai_requires_base_url(monkeypatch):
    """Custom OpenAI provider should require a base URL."""
    monkeypatch.setenv("CUSTOM_OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("CUSTOM_OPENAI_BASE_URL", raising=False)

    with pytest.raises(AIError) as exc_info:
        PROVIDER_REGISTRY["custom-openai"]("gpt-4o-mini", _DUMMY_MESSAGES, 0.7, 32)

    assert "CUSTOM_OPENAI_BASE_URL" in str(exc_info.value)
