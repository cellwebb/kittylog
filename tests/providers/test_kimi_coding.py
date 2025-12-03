"""Tests for Kimi Coding provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.kimi_coding import call_kimi_coding_api

API_KEY = "test-key"
API_ENDPOINT = "https://api.kimi.com/coding/v1/chat/completions"


class TestKimiCodingProvider:
    """Test Kimi Coding provider functionality."""

    @patch("kittylog.providers.kimi_coding.httpx.post")
    @patch.dict(os.environ, {"KIMI_CODING_API_KEY": API_KEY})
    def test_call_kimi_coding_api_success(self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper):
        """Test successful Kimi Coding API call."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_kimi_coding_api(
            model="moonshot-v1-8k",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call URL and headers
        url = api_test_helper.extract_call_url(mock_post)
        assert url == API_ENDPOINT

        headers = api_test_helper.extract_call_headers(mock_post)
        assert api_test_helper.verify_bearer_token_header(headers, API_KEY)

        # Verify request data
        data = api_test_helper.extract_call_data(mock_post)
        assert data["model"] == "moonshot-v1-8k"
        assert data["temperature"] == 0.7
        assert data["max_completion_tokens"] == 100

    def test_call_kimi_coding_api_missing_api_key(self, monkeypatch, dummy_messages):
        """Ensure Kimi Coding provider fails fast when API keys are missing."""
        monkeypatch.delenv("KIMI_CODING_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_kimi_coding_api("test-model", dummy_messages, 0.7, 32)

        assert "KIMI_CODING_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.kimi_coding.httpx.post")
    @patch.dict(os.environ, {"KIMI_CODING_API_KEY": API_KEY})
    def test_call_kimi_coding_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Kimi Coding API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            call_kimi_coding_api(
                model="moonshot-v1-8k",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Kimi Coding API error" in str(exc_info.value) or "Error calling Kimi Coding API" in str(exc_info.value)

    @patch("kittylog.providers.kimi_coding.httpx.post")
    @patch.dict(os.environ, {"KIMI_CODING_API_KEY": API_KEY})
    def test_call_kimi_coding_api_general_error(self, mock_post, dummy_messages):
        """Test Kimi Coding API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            call_kimi_coding_api(
                model="moonshot-v1-8k",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Error calling Kimi Coding API" in str(exc_info.value)

    @patch("kittylog.providers.kimi_coding.httpx.post")
    @patch.dict(os.environ, {"KIMI_CODING_API_KEY": API_KEY})
    def test_call_kimi_coding_api_with_system_message(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test Kimi Coding API call with system message."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_kimi_coding_api(
            model="moonshot-v1-8k",
            messages=dummy_messages_with_system,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "system"
        assert data["messages"][1]["role"] == "user"

    @patch("kittylog.providers.kimi_coding.httpx.post")
    @patch.dict(os.environ, {"KIMI_CODING_API_KEY": API_KEY})
    def test_call_kimi_coding_api_with_conversation(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Kimi Coding API call with full conversation history."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_kimi_coding_api(
            model="moonshot-v1-8k",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 3

    @pytest.mark.integration
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
