"""Tests for Custom OpenAI provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.custom_openai import call_custom_openai_api

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


class TestCustomOpenAIProvider:
    """Test Custom OpenAI provider functionality."""

    @patch("kittylog.providers.custom_openai.httpx.post")
    def test_call_custom_openai_api_success(self, mock_post):
        """Test successful Custom OpenAI API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "CUSTOM_OPENAI_API_KEY": "test-key",
            "CUSTOM_OPENAI_BASE_URL": "https://custom.openai.ai"
        }):
            result = call_custom_openai_api(
                model="gpt-4",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert "https://custom.openai.ai" in call_args[0][0]
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert "Bearer test-key" in headers["Authorization"]
        
        data = call_args[1]["json"]
        assert data["model"] == "gpt-4"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100

    def test_custom_openai_requires_base_url(self, monkeypatch):
        """Custom OpenAI provider should require a base URL."""
        monkeypatch.setenv("CUSTOM_OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("CUSTOM_OPENAI_BASE_URL", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_custom_openai_api("test-model", _DUMMY_MESSAGES, 0.7, 32)

        assert "CUSTOM_OPENAI_BASE_URL" in str(exc_info.value)

    def test_custom_openai_missing_api_key(self, monkeypatch):
        """Test Custom OpenAI API call fails without API key."""
        monkeypatch.delenv("CUSTOM_OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("CUSTOM_OPENAI_BASE_URL", "https://custom.openai.ai")

        with pytest.raises(AIError) as exc_info:
            call_custom_openai_api(
                model="gpt-4",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert "CUSTOM_OPENAI_API_KEY not found" in str(exc_info.value)

    @patch("kittylog.providers.custom_openai.httpx.post")
    def test_call_custom_openai_api_http_error(self, mock_post):
        """Test Custom OpenAI API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "CUSTOM_OPENAI_API_KEY": "test-key",
            "CUSTOM_OPENAI_BASE_URL": "https://custom.openai.ai"
        }):
            with pytest.raises(AIError) as exc_info:
                call_custom_openai_api(
                    model="gpt-4",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Custom OpenAI API error" in str(exc_info.value) or "Error calling Custom OpenAI API" in str(exc_info.value)

    @patch("kittylog.providers.custom_openai.httpx.post")
    def test_call_custom_openai_api_custom_headers(self, mock_post):
        """Test Custom OpenAI API call with custom headers support."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "CUSTOM_OPENAI_API_KEY": "test-key",
            "CUSTOM_OPENAI_BASE_URL": "https://custom.openai.ai"
        }):
            result = call_custom_openai_api(
                model="gpt-4",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
                extra_headers={"X-Custom-Header": "custom-value"}
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["X-Custom-Header"] == "custom-value"

    @pytest.mark.skipif(
        not all(os.getenv(k) for k in ["CUSTOM_OPENAI_API_KEY", "CUSTOM_OPENAI_BASE_URL"]),
        reason="Custom OpenAI environment variables not set"
    )
    def test_custom_openai_provider_integration(self):
        """Test Custom OpenAI provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'custom openai test success'",
            }
        ]

        result = call_custom_openai_api(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
