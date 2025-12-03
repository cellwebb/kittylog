"""Tests for Kimi Coding provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.kimi_coding import call_kimi_coding_api

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


class TestKimiCodingProvider:
    """Test Kimi Coding provider functionality."""

    @patch("kittylog.providers.kimi_coding.httpx.post")
    def test_call_kimi_coding_api_success(self, mock_post):
        """Test successful Kimi Coding API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        result = call_kimi_coding_api(
            model="moonshot-v1-8k",
            messages=_DUMMY_MESSAGES,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.moonshot.cn/v1/chat/completions"
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert "Bearer test-key" in headers["Authorization"]
        
        data = call_args[1]["json"]
        assert data["model"] == "moonshot-v1-8k"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100

    def test_call_kimi_coding_api_missing_api_key(self, monkeypatch):
        """Ensure Kimi Coding provider fails fast when API keys are missing."""
        monkeypatch.delenv("KIMI_CODING_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_kimi_coding_api("test-model", _DUMMY_MESSAGES, 0.7, 32)

        assert "KIMI_CODING_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.kimi_coding.httpx.post")
    def test_call_kimi_coding_api_http_error(self, mock_post):
        """Test Kimi Coding API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"KIMI_CODING_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_kimi_coding_api(
                    model="moonshot-v1-8k",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Kimi Coding API error" in str(exc_info.value) or "Error calling Kimi Coding API" in str(exc_info.value)

    @patch("kittylog.providers.kimi_coding.httpx.post")
    def test_call_kimi_coding_api_general_error(self, mock_post):
        """Test Kimi Coding API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with patch.dict(os.environ, {"KIMI_CODING_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_kimi_coding_api(
                    model="moonshot-v1-8k",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Error calling Kimi Coding API" in str(exc_info.value)

    @pytest.mark.skipif(not os.getenv("KIMI_CODING_API_KEY"), reason="KIMI_CODING_API_KEY not set")
    def test_kimi_coding_provider_integration(self):
        """Test Kimi Coding provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'kimi coding test success'",
            }
        ]

        result = call_kimi_coding_api(
            model="moonshot-v1-8k",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @patch("kittylog.providers.kimi_coding.httpx.post")
    def test_call_kimi_coding_api_with_system_message(self, mock_post):
        """Test Kimi Coding API call with system message."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        messages_with_system = [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": "Test message"}
        ]

        with patch.dict(os.environ, {"KIMI_CODING_API_KEY": "test-key"}):
            result = call_kimi_coding_api(
                model="moonshot-v1-8k",
                messages=messages_with_system,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "system"
        assert data["messages"][1]["role"] == "user"
