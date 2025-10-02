"""Integration tests for AI providers."""

import os
from pathlib import Path

import pytest
from dotenv import dotenv_values

from kittylog.providers import (
    call_anthropic_api,
    call_cerebras_api,
    call_groq_api,
    call_ollama_api,
    call_openai_api,
    call_openrouter_api,
)


class TestProviderIntegration:
    """Integration tests for AI providers."""

    @pytest.fixture(autouse=True)
    def load_test_env(self):
        """Load environment variables from .kittylog.env files for testing."""
        # Load from user config file (lowest precedence)
        user_config = Path.home() / ".kittylog.env"
        if user_config.exists():
            user_vars = dotenv_values(user_config)
            for key, value in user_vars.items():
                if (
                    key
                    in [
                        "ANTHROPIC_API_KEY",
                        "OPENAI_API_KEY",
                        "OPENROUTER_API_KEY",
                        "GROQ_API_KEY",
                        "CEREBRAS_API_KEY",
                        "OLLAMA_HOST",
                    ]
                    and value is not None
                ):
                    os.environ[key] = value

        # Load from project .env file (medium precedence)
        project_env = Path(".env")
        if project_env.exists():
            project_vars = dotenv_values(project_env)
            for key, value in project_vars.items():
                if (
                    key
                    in [
                        "ANTHROPIC_API_KEY",
                        "OPENAI_API_KEY",
                        "OPENROUTER_API_KEY",
                        "GROQ_API_KEY",
                        "CEREBRAS_API_KEY",
                        "OLLAMA_HOST",
                    ]
                    and value is not None
                ):
                    os.environ[key] = value

        # Load from project .kittylog.env file (highest precedence)
        project_config_env = Path(".kittylog.env")
        if project_config_env.exists():
            project_config_vars = dotenv_values(project_config_env)
            for key, value in project_config_vars.items():
                if (
                    key
                    in [
                        "ANTHROPIC_API_KEY",
                        "OPENAI_API_KEY",
                        "OPENROUTER_API_KEY",
                        "GROQ_API_KEY",
                        "CEREBRAS_API_KEY",
                        "OLLAMA_HOST",
                    ]
                    and value is not None
                ):
                    os.environ[key] = value

    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
    def test_anthropic_provider_integration(self):
        """Test Anthropic provider integration with a short message."""
        # Test with a simple message
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'anthropic test success'",
            }
        ]

        result = call_anthropic_api(
            model="claude-3-haiku-20240307",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
    def test_openai_provider_integration(self):
        """Test OpenAI provider integration with a short message."""
        # Test with a simple message
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'openai test success'",
            }
        ]

        result = call_openai_api(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY not set")
    def test_groq_provider_integration(self):
        """Test Groq provider integration with a short message."""
        # Test with a simple message
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'groq test success'",
            }
        ]

        result = call_groq_api(
            model="llama3-8b-8192",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @pytest.mark.skipif(not os.getenv("CEREBRAS_API_KEY"), reason="CEREBRAS_API_KEY not set")
    def test_cerebras_provider_integration(self):
        """Test Cerebras provider integration with a short message."""
        # Test with a simple message
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'cerebras test success'",
            }
        ]

        result = call_cerebras_api(
            model="llama3.1-8b",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @pytest.mark.skipif(
        os.getenv("GITHUB_ACTIONS") == "true",
        reason="Skipping Ollama integration tests in GitHub Actions",
    )
    def test_ollama_provider_integration(self):
        """Test Ollama provider integration with a short message."""
        # Test with a simple message
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'ollama test success'",
            }
        ]

        result = call_ollama_api(
            model="llama3",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY not set")
    def test_openrouter_provider_integration(self):
        """Test OpenRouter provider integration with a short message."""
        # Test with a simple message
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'openrouter test success'",
            }
        ]

        result = call_openrouter_api(
            model="openai/gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
