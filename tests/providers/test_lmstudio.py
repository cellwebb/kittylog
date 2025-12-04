"""Tests for Lmstudio provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.lmstudio import call_lmstudio_api

API_KEY = "test-key"
API_ENDPOINT = "http://localhost:1234/v1/chat/completions"


class TestLmstudioProvider:
    """Test Lmstudio provider functionality."""

    @patch("kittylog.providers.base_configured.httpx.post")
    @patch.dict(os.environ, {"LMSTUDIO_API_KEY": API_KEY})
    def test_call_lmstudio_api_success(self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper):
        """Test successful Lmstudio API call."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_lmstudio_api(
            model="local-model",
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
        assert data["model"] == "local-model"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100

    def test_call_lmstudio_api_missing_api_key(self, monkeypatch, dummy_messages):
        """Test Lmstudio provider works without API key (optional)."""
        monkeypatch.delenv("LMSTUDIO_API_KEY", raising=False)

        # This should not raise an error since API key is optional for LM Studio
        try:
            # We expect this to fail due to connection error (no running server), not auth
            call_lmstudio_api("test-model", dummy_messages, 0.7, 32)
        except AIError as exc_info:
            # Should be connection error, not auth error
            assert (
                "connection failed" in str(exc_info.value).lower() or "connection error" in str(exc_info.value).lower()
            )

    @patch("kittylog.providers.base_configured.httpx.post")
    @patch.dict(os.environ, {"LMSTUDIO_API_KEY": API_KEY})
    def test_call_lmstudio_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Lmstudio API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            call_lmstudio_api(
                model="local-model",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "LM Studio API error" in str(exc_info.value) or "Error calling LM Studio API" in str(exc_info.value)

    @patch("kittylog.providers.base_configured.httpx.post")
    @patch.dict(os.environ, {"LMSTUDIO_API_KEY": API_KEY})
    def test_call_lmstudio_api_general_error(self, mock_post, dummy_messages):
        """Test Lmstudio API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            call_lmstudio_api(
                model="local-model",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Error calling LM Studio API" in str(exc_info.value)

    @patch("kittylog.providers.base_configured.httpx.post")
    @patch.dict(os.environ, {"LMSTUDIO_API_KEY": API_KEY})
    def test_call_lmstudio_api_with_system_message(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test Lmstudio API call with system message."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_lmstudio_api(
            model="local-model",
            messages=dummy_messages_with_system,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "system"
        assert data["messages"][1]["role"] == "user"

    @patch("kittylog.providers.base_configured.httpx.post")
    @patch.dict(os.environ, {"LMSTUDIO_API_KEY": API_KEY})
    def test_call_lmstudio_api_with_conversation(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Lmstudio API call with full conversation history."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_lmstudio_api(
            model="local-model",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 3

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("LMSTUDIO_API_KEY"), reason="LMSTUDIO_API_KEY not set")
    def test_lmstudio_provider_integration(self):
        """Test Lmstudio provider integration with real API."""
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
