"""Tests for Moonshot provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.moonshot import call_moonshot_api

API_KEY = "test-key"
API_ENDPOINT = "https://api.moonshot.ai/v1/chat/completions"


class TestMoonshotProvider:
    """Test Moonshot provider functionality."""

    @patch("kittylog.providers.moonshot.httpx.post")
    @patch.dict(os.environ, {"MOONSHOT_API_KEY": API_KEY})
    def test_call_moonshot_api_success(self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper):
        """Test successful Moonshot API call."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_moonshot_api(
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
        assert data["max_tokens"] == 100

    def test_call_moonshot_api_missing_api_key(self, monkeypatch, dummy_messages):
        """Ensure Moonshot provider fails fast when API keys are missing."""
        monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_moonshot_api("test-model", dummy_messages, 0.7, 32)

        assert "MOONSHOT_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.moonshot.httpx.post")
    @patch.dict(os.environ, {"MOONSHOT_API_KEY": API_KEY})
    def test_call_moonshot_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Moonshot API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            call_moonshot_api(
                model="moonshot-v1-8k",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Moonshot AI API error" in str(exc_info.value) or "Error calling Moonshot AI API" in str(exc_info.value)

    @patch("kittylog.providers.moonshot.httpx.post")
    @patch.dict(os.environ, {"MOONSHOT_API_KEY": API_KEY})
    def test_call_moonshot_api_general_error(self, mock_post, dummy_messages):
        """Test Moonshot API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            call_moonshot_api(
                model="moonshot-v1-8k",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Error calling Moonshot AI API" in str(exc_info.value)

    @patch("kittylog.providers.moonshot.httpx.post")
    @patch.dict(os.environ, {"MOONSHOT_API_KEY": API_KEY})
    def test_call_moonshot_api_with_system_message(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test Moonshot API call with system message."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_moonshot_api(
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

    @patch("kittylog.providers.moonshot.httpx.post")
    @patch.dict(os.environ, {"MOONSHOT_API_KEY": API_KEY})
    def test_call_moonshot_api_with_conversation(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Moonshot API call with full conversation history."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_moonshot_api(
            model="moonshot-v1-8k",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 3

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("MOONSHOT_API_KEY"), reason="MOONSHOT_API_KEY not set")
    def test_moonshot_provider_integration(self):
        """Test Moonshot provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'moonshot test success'",
            }
        ]

        result = call_moonshot_api(
            model="moonshot-v1-8k",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
