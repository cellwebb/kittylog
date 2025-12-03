"""Tests for Gemini provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.gemini import call_gemini_api

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


class TestGeminiProvider:
    """Test Gemini provider functionality."""

    @patch("kittylog.providers.gemini.httpx.post")
    def test_call_gemini_api_success(self, mock_post):
        """Test successful Gemini API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Test response"}]}}]
        }
        mock_post.return_value = mock_response

        result = call_gemini_api(
            model="gemini-pro",
            messages=_DUMMY_MESSAGES,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert "generativelanguage.googleapis.com" in call_args[0][0]
        assert "gemini-pro" in call_args[0][0]
        headers = call_args[1]["headers"]
        assert "x-goog-api-key" in headers
        assert headers["x-goog-api-key"] == "test-key"
        
        data = call_args[1]["json"]
        assert "contents" in data
        assert len(data["contents"]) == 1
        assert data["contents"][0]["parts"][0]["text"] == "test"
        assert data["generationConfig"]["temperature"] == 0.7
        assert data["generationConfig"]["maxOutputTokens"] == 100

    def test_call_gemini_api_missing_api_key(self, monkeypatch):
        """Ensure Gemini provider fails fast when API keys are missing."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_gemini_api("test-model", _DUMMY_MESSAGES, 0.7, 32)

        assert "GEMINI_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.gemini.httpx.post")
    def test_call_gemini_api_http_error(self, mock_post):
        """Test Gemini API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_gemini_api(
                    model="gemini-pro",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Gemini API error" in str(exc_info.value) or "Error calling Gemini API" in str(exc_info.value)

    @patch("kittylog.providers.gemini.httpx.post")
    def test_call_gemini_api_general_error(self, mock_post):
        """Test Gemini API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_gemini_api(
                    model="gemini-pro",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Error calling Gemini API" in str(exc_info.value)

    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
    def test_gemini_provider_integration(self):
        """Test Gemini provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'gemini test success'",
            }
        ]

        result = call_gemini_api(
            model="gemini-pro",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @patch("kittylog.providers.gemini.httpx.post")
    def test_call_gemini_api_with_system_message(self, mock_post):
        """Test Gemini API call with system message."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Test response"}]}}]
        }
        mock_post.return_value = mock_response

        messages_with_system = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Test message"}
        ]

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            result = call_gemini_api(
                model="gemini-pro",
                messages=messages_with_system,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        # Gemini should handle system message differently
        assert len(data["contents"]) == 1  # System message should be integrated

    @patch("kittylog.providers.gemini.httpx.post")
    def test_call_gemini_api_message_conversion(self, mock_post):
        """Test Gemini message format conversion."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Test response"}]}}]
        }
        mock_post.return_value = mock_response

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            call_gemini_api(
                model="gemini-pro",
                messages=messages,
                temperature=0.7,
                max_tokens=100,
            )

        call_args = mock_post.call_args
        data = call_args[1]["json"]
        
        # Check that messages are converted to Gemini format
        assert len(data["contents"]) == 3
        assert data["contents"][0]["role"] == "user"
        assert data["contents"][0]["parts"][0]["text"] == "Hello"
        assert data["contents"][1]["role"] == "model"  # Assistant becomes "model"
        assert data["contents"][1]["parts"][0]["text"] == "Hi there!"
        assert data["contents"][2]["role"] == "user"
        assert data["contents"][2]["parts"][0]["text"] == "How are you?"
