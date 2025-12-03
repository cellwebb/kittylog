"""Tests for DeepSeek provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.deepseek import call_deepseek_api

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


class TestDeepSeekProvider:
    """Test DeepSeek provider functionality."""

    @patch("kittylog.providers.deepseek.httpx.post")
    def test_call_deepseek_api_success(self, mock_post):
        """Test successful DeepSeek API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        result = call_deepseek_api(
            model="deepseek-chat",
            messages=_DUMMY_MESSAGES,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.deepseek.com/v1/chat/completions"
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert "Bearer test-key" in headers["Authorization"]
        
        data = call_args[1]["json"]
        assert data["model"] == "deepseek-chat"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100

    def test_call_deepseek_api_missing_api_key(self, monkeypatch):
        """Ensure DeepSeek provider fails fast when API keys are missing."""
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_deepseek_api("test-model", _DUMMY_MESSAGES, 0.7, 32)

        assert "DEEPSEEK_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.deepseek.httpx.post")
    def test_call_deepseek_api_http_error(self, mock_post):
        """Test DeepSeek API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_deepseek_api(
                    model="deepseek-chat",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "DeepSeek API error" in str(exc_info.value) or "Error calling DeepSeek API" in str(exc_info.value)

    @patch("kittylog.providers.deepseek.httpx.post")
    def test_call_deepseek_api_general_error(self, mock_post):
        """Test DeepSeek API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_deepseek_api(
                    model="deepseek-chat",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Error calling DeepSeek API" in str(exc_info.value)

    @pytest.mark.skipif(not os.getenv("DEEPSEEK_API_KEY"), reason="DEEPSEEK_API_KEY not set")
    def test_deepseek_provider_integration(self):
        """Test DeepSeek provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'deepseek test success'",
            }
        ]

        result = call_deepseek_api(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @patch("kittylog.providers.deepseek.httpx.post")
    def test_call_deepseek_api_with_system_message(self, mock_post):
        """Test DeepSeek API call with system message."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        messages_with_system = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Test message"}
        ]

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            result = call_deepseek_api(
                model="deepseek-chat",
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
