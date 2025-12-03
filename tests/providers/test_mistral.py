"""Tests for Mistral provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.mistral import call_mistral_api

API_KEY = "test-key"
API_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"


class TestMistralProvider:
    """Test Mistral provider functionality."""

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"MISTRAL_API_KEY": API_KEY})
    def test_call_mistral_api_success(self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper):
        """Test successful Mistral API call."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_mistral_api(
            model="mistral-tiny",
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
        assert data["model"] == "mistral-tiny"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100

    def test_call_mistral_api_missing_api_key(self, monkeypatch, dummy_messages):
        """Ensure Mistral provider fails fast when API keys are missing."""
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_mistral_api("test-model", dummy_messages, 0.7, 32)

        assert "MISTRAL_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"MISTRAL_API_KEY": API_KEY})
    def test_call_mistral_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Mistral API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            call_mistral_api(
                model="mistral-tiny",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Mistral API error" in str(exc_info.value) or "Error calling Mistral API" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"MISTRAL_API_KEY": API_KEY})
    def test_call_mistral_api_general_error(self, mock_post, dummy_messages):
        """Test Mistral API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            call_mistral_api(
                model="mistral-tiny",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Error calling Mistral API" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"MISTRAL_API_KEY": API_KEY})
    def test_call_mistral_api_with_system_message(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test Mistral API call with system message."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_mistral_api(
            model="mistral-tiny",
            messages=dummy_messages_with_system,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "system"
        assert data["messages"][1]["role"] == "user"

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"MISTRAL_API_KEY": API_KEY})
    def test_call_mistral_api_with_conversation(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Mistral API call with full conversation history."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_mistral_api(
            model="mistral-tiny",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 3

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("MISTRAL_API_KEY"), reason="MISTRAL_API_KEY not set")
    def test_mistral_provider_integration(self):
        """Test Mistral provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'mistral test success'",
            }
        ]

        result = call_mistral_api(
            model="mistral-tiny",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
