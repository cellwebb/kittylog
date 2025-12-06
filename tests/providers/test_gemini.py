"""Tests for Gemini provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers import PROVIDER_REGISTRY

API_KEY = "test-key"
API_ENDPOINT_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class TestGeminiProvider:
    """Test Gemini provider functionality."""

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"GEMINI_API_KEY": API_KEY})
    def test_call_gemini_api_success(self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper):
        """Test successful Gemini API call."""
        response_data = {"candidates": [{"content": {"parts": [{"text": "Test response"}]}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["gemini"](
            model="gemini-pro",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call URL and headers
        url = api_test_helper.extract_call_url(mock_post)
        assert "generativelanguage.googleapis.com" in url
        assert "gemini-pro" in url

        headers = api_test_helper.extract_call_headers(mock_post)
        assert api_test_helper.verify_api_key_header(headers, API_KEY, "x-goog-api-key")

        # Verify request data (Gemini format)
        data = api_test_helper.extract_call_data(mock_post)
        assert "contents" in data
        assert len(data["contents"]) == 1
        assert data["contents"][0]["parts"][0]["text"] == "test"
        assert data["generationConfig"]["temperature"] == 0.7
        assert data["generationConfig"]["maxOutputTokens"] == 100

    def test_call_gemini_api_missing_api_key(self, monkeypatch, dummy_messages):
        """Ensure Gemini provider fails fast when API keys are missing."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["gemini"]("test-model", dummy_messages, 0.7, 32)

        assert "GEMINI_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"GEMINI_API_KEY": API_KEY})
    def test_call_gemini_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Gemini API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["gemini"](
                model="gemini-pro",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Gemini API error" in str(exc_info.value) or "Gemini" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"GEMINI_API_KEY": API_KEY})
    def test_call_gemini_api_general_error(self, mock_post, dummy_messages):
        """Test Gemini API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["gemini"](
                model="gemini-pro",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Gemini" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"GEMINI_API_KEY": API_KEY})
    def test_call_gemini_api_with_system_message(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test Gemini API call with system message."""
        response_data = {"candidates": [{"content": {"parts": [{"text": "Test response"}]}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["gemini"](
            model="gemini-pro",
            messages=dummy_messages_with_system,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        # Gemini should handle system message differently
        assert len(data["contents"]) == 1  # System message should be integrated

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"GEMINI_API_KEY": API_KEY})
    def test_call_gemini_api_message_conversion(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Gemini message format conversion."""
        response_data = {"candidates": [{"content": {"parts": [{"text": "Test response"}]}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["gemini"](
            model="gemini-pro",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        # Check that messages are converted to Gemini format
        assert len(data["contents"]) == 3
        assert data["contents"][0]["role"] == "user"
        assert data["contents"][0]["parts"][0]["text"] == "Hello"
        assert data["contents"][1]["role"] == "model"  # Assistant becomes "model"
        assert data["contents"][1]["parts"][0]["text"] == "Hi there!"
        assert data["contents"][2]["role"] == "user"
        assert data["contents"][2]["parts"][0]["text"] == "How are you?"

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
    def test_gemini_provider_integration(self):
        """Test Gemini provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'gemini test success'",
            }
        ]

        result = PROVIDER_REGISTRY["gemini"](
            model="gemini-2.0-flash",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
