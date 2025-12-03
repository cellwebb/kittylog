"""Tests for Custom Anthropic provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.custom_anthropic import call_custom_anthropic_api

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


class TestCustomAnthropicProvider:
    """Test Custom Anthropic provider functionality."""

    @patch("kittylog.providers.custom_anthropic.httpx.post")
    def test_call_custom_anthropic_api_success(self, mock_post):
        """Test successful Custom Anthropic API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "content": [{"text": "Test response"}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "CUSTOM_ANTHROPIC_API_KEY": "test-key",
            "CUSTOM_ANTHROPIC_BASE_URL": "https://custom.anthropic.ai",
            "CUSTOM_ANTHROPIC_VERSION": "2023-06-01"
        }):
            result = call_custom_anthropic_api(
                model="claude-3-haiku-20240307",
                messages=[
                    {"role": "system", "content": "System message"},
                    {"role": "user", "content": "Test message"}
                ],
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert "https://custom.anthropic.ai" in call_args[0][0]
        headers = call_args[1]["headers"]
        assert "x-api-key" in headers
        assert headers["x-api-key"] == "test-key"
        assert headers["anthropic-version"] == "2023-06-01"
        
        data = call_args[1]["json"]
        assert data["model"] == "claude-3-haiku-20240307"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100
        assert data["system"] == "System message"

    def test_custom_anthropic_requires_base_url(self, monkeypatch):
        """Custom Anthropic provider should require a base URL."""
        monkeypatch.setenv("CUSTOM_ANTHROPIC_API_KEY", "sk-test")
        monkeypatch.delenv("CUSTOM_ANTHROPIC_BASE_URL", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_custom_anthropic_api("test-model", _DUMMY_MESSAGES, 0.7, 32)

        assert "CUSTOM_ANTHROPIC_BASE_URL" in str(exc_info.value)

    def test_custom_anthropic_missing_api_key(self, monkeypatch):
        """Test Custom Anthropic API call fails without API key."""
        monkeypatch.delenv("CUSTOM_ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("CUSTOM_ANTHROPIC_BASE_URL", "https://custom.anthropic.ai")

        with pytest.raises(AIError) as exc_info:
            call_custom_anthropic_api(
                model="claude-3-haiku-20240307",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert "CUSTOM_ANTHROPIC_API_KEY not found" in str(exc_info.value)

    @patch("kittylog.providers.custom_anthropic.httpx.post")
    def test_call_custom_anthropic_api_http_error(self, mock_post):
        """Test Custom Anthropic API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "CUSTOM_ANTHROPIC_API_KEY": "test-key",
            "CUSTOM_ANTHROPIC_BASE_URL": "https://custom.anthropic.ai",
            "CUSTOM_ANTHROPIC_VERSION": "2023-06-01"
        }):
            with pytest.raises(AIError) as exc_info:
                call_custom_anthropic_api(
                    model="claude-3-haiku-20240307",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Custom Anthropic API error" in str(exc_info.value) or "Error calling Custom Anthropic API" in str(exc_info.value)

    @patch("kittylog.providers.custom_anthropic.httpx.post")
    def test_call_custom_anthropic_api_default_version(self, mock_post):
        """Test Custom Anthropic API call with default version."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "content": [{"text": "Test response"}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "CUSTOM_ANTHROPIC_API_KEY": "test-key",
            "CUSTOM_ANTHROPIC_BASE_URL": "https://custom.anthropic.ai"
        }, clear=True):
            # Don't set CUSTOM_ANTHROPIC_VERSION to test default
            result = call_custom_anthropic_api(
                model="claude-3-haiku-20240307",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        # Should default to "2023-06-01"
        assert headers["anthropic-version"] == "2023-06-01"

    @pytest.mark.skipif(
        not all(os.getenv(k) for k in ["CUSTOM_ANTHROPIC_API_KEY", "CUSTOM_ANTHROPIC_BASE_URL"]),
        reason="Custom Anthropic environment variables not set"
    )
    def test_custom_anthropic_provider_integration(self):
        """Test Custom Anthropic provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'custom anthropic test success'",
            }
        ]

        result = call_custom_anthropic_api(
            model="claude-3-haiku-20240307",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
