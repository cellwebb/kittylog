"""Unit tests for newly added AI providers."""

import pytest

from kittylog.errors import AIError
from kittylog.providers import (
    call_chutes_api,
    call_custom_anthropic_api,
    call_custom_openai_api,
    call_deepseek_api,
    call_fireworks_api,
    call_gemini_api,
    call_minimax_api,
    call_mistral_api,
    call_streamlake_api,
    call_together_api,
)

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


@pytest.mark.parametrize(
    ("provider_func", "required_env"),
    [
        (call_chutes_api, "CHUTES_API_KEY"),
        (call_deepseek_api, "DEEPSEEK_API_KEY"),
        (call_fireworks_api, "FIREWORKS_API_KEY"),
        (call_gemini_api, "GEMINI_API_KEY"),
        (call_minimax_api, "MINIMAX_API_KEY"),
        (call_mistral_api, "MISTRAL_API_KEY"),
        (call_streamlake_api, "STREAMLAKE_API_KEY"),
        (call_together_api, "TOGETHER_API_KEY"),
    ],
)
def test_provider_missing_api_key(provider_func, required_env, monkeypatch):
    """Ensure providers fail fast when API keys are missing."""
    monkeypatch.delenv(required_env, raising=False)
    if required_env == "STREAMLAKE_API_KEY":
        monkeypatch.delenv("VC_API_KEY", raising=False)

    with pytest.raises(AIError) as exc_info:
        provider_func("test-model", _DUMMY_MESSAGES, 0.7, 32)

    assert required_env in str(exc_info.value)


def test_custom_anthropic_requires_base_url(monkeypatch):
    """Custom Anthropic provider should require a base URL."""
    monkeypatch.setenv("CUSTOM_ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("CUSTOM_ANTHROPIC_BASE_URL", raising=False)

    with pytest.raises(AIError) as exc_info:
        call_custom_anthropic_api("claude-test", _DUMMY_MESSAGES, 0.7, 32)

    assert "CUSTOM_ANTHROPIC_BASE_URL" in str(exc_info.value)


def test_custom_openai_requires_base_url(monkeypatch):
    """Custom OpenAI provider should require a base URL."""
    monkeypatch.setenv("CUSTOM_OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("CUSTOM_OPENAI_BASE_URL", raising=False)

    with pytest.raises(AIError) as exc_info:
        call_custom_openai_api("gpt-4o-mini", _DUMMY_MESSAGES, 0.7, 32)

    assert "CUSTOM_OPENAI_BASE_URL" in str(exc_info.value)
