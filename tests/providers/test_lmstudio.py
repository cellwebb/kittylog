"""Tests for LM Studio provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.lmstudio import call_lmstudio_api

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


class TestLMStudioProvider:
    """Test LM Studio provider functionality."""

    @patch("kittylog.providers.lmstudio.httpx.post")
    def test_call_lmstudio_api_success(self, mock_post):
        """Test successful LM Studio API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"LMSTUDIO_API_URL": "http://localhost:1234"}):
            result = call_lmstudio_api(
                model="local-model",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:1234/v1/chat/completions"
        headers = call_args[1]["headers"]
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        
        data = call_args[1]["json"]
        assert data["model"] == "local-model"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100

    def test_call_lmstudio_api_missing_api_url(self, monkeypatch):
        """Ensure LM Studio provider fails fast when API URL is missing."""
        monkeypatch.delenv("LMSTUDIO_API_URL", raising=False)
        # Also clear legacy OLLAMA_HOST if it exists
        monkeypatch.delenv("OLLAMA_HOST", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_lmstudio_api("test-model", _DUMMY_MESSAGES, 0.7, 32)

        assert "LMSTUDIO_API_URL not found" in str(exc_info.value)

    @patch("kittylog.providers.lmstudio.httpx.post")
    def test_call_lmstudio_api_legacy_host_support(self, mock_post):
        """Test LM Studio API call supports legacy OLLAMA_HOST."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "OLLAMA_HOST": "http://localhost:11434"
        }, clear=True):  # Clear to avoid interference
            result = call_lmstudio_api(
                model="local-model",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:11434/v1/chat/completions"

    @patch("kittylog.providers.lmstudio.httpx.post")
    def test_call_lmstudio_api_http_error(self, mock_post):
        """Test LM Studio API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 500")
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"LMSTUDIO_API_URL": "http://localhost:1234"}):
            with pytest.raises(AIError) as exc_info:
                call_lmstudio_api(
                    model="local-model",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "LM Studio API error" in str(exc_info.value) or "Error calling LM Studio API" in str(exc_info.value)

    @patch("kittylog.providers.lmstudio.httpx.post")
    def test_call_lmstudio_api_general_error(self, mock_post):
        """Test LM Studio API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with patch.dict(os.environ, {"LMSTUDIO_API_URL": "http://localhost:1234"}):
            with pytest.raises(AIError) as exc_info:
                call_lmstudio_api(
                    model="local-model",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Error calling LM Studio API" in str(exc_info.value)

    @pytest.mark.skipif(not os.getenv("LMSTUDIO_API_URL"), reason="LMSTUDIO_API_URL not set")
    def test_lmstudio_provider_integration(self):
        """Test LM Studio provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'lmstudio test success'",
            }
        ]

        result = call_lmstudio_api(
            model="local-model",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @patch("kittylog.providers.lmstudio.httpx.post")
    def test_call_lmstudio_api_with_system_message(self, mock_post):
        """Test LM Studio API call with system message."""
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

        with patch.dict(os.environ, {"LMSTUDIO_API_URL": "http://localhost:1234"}):
            result = call_lmstudio_api(
                model="local-model",
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

    @patch("kittylog.providers.lmstudio.httpx.post")
    def test_call_lmstudio_api_custom_url_trailing_slash(self, mock_post):
        """Test LM Studio API call handles URLs with trailing slashes."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"LMSTUDIO_API_URL": "http://localhost:1234/"}):
            result = call_lmstudio_api(
                model="local-model",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        # Should handle trailing slash properly
        assert call_args[0][0] == "http://localhost:1234/v1/chat/completions"
