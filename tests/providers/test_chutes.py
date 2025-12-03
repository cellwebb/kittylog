"""Tests for Chutes provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.chutes import call_chutes_api

API_KEY = "test-key"
API_ENDPOINT = "https://llm.chutes.ai/v1/chat/completions"


class TestChutesProvider:
    """Test Chutes provider functionality."""

    @patch("kittylog.providers.chutes.httpx.post")
    @patch.dict(os.environ, {"CHUTES_API_KEY": API_KEY})
    def test_call_chutes_api_success(self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper):
        """Test successful Chutes API call."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_chutes_api(
            model="chutes-chat",
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
        assert data["model"] == "chutes-chat"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100

    def test_call_chutes_api_missing_api_key(self, monkeypatch, dummy_messages):
        """Ensure Chutes provider fails fast when API keys are missing."""
        monkeypatch.delenv("CHUTES_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_chutes_api("test-model", dummy_messages, 0.7, 32)

        assert "CHUTES_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.chutes.httpx.post")
    @patch.dict(os.environ, {"CHUTES_API_KEY": API_KEY})
    def test_call_chutes_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Chutes API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            call_chutes_api(
                model="chutes-chat",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Chutes.ai API error" in str(exc_info.value) or "Error calling Chutes.ai API" in str(exc_info.value)

    @patch("kittylog.providers.chutes.httpx.post")
    @patch.dict(os.environ, {"CHUTES_API_KEY": API_KEY})
    def test_call_chutes_api_general_error(self, mock_post, dummy_messages):
        """Test Chutes API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            call_chutes_api(
                model="chutes-chat",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Error calling Chutes.ai API" in str(exc_info.value)

    @patch("kittylog.providers.chutes.httpx.post")
    @patch.dict(os.environ, {"CHUTES_API_KEY": API_KEY})
    def test_call_chutes_api_with_system_message(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test Chutes API call with system message."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_chutes_api(
            model="chutes-chat",
            messages=dummy_messages_with_system,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "system"
        assert data["messages"][1]["role"] == "user"

    @patch("kittylog.providers.chutes.httpx.post")
    @patch.dict(os.environ, {"CHUTES_API_KEY": API_KEY})
    def test_call_chutes_api_with_conversation(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Chutes API call with full conversation history."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_chutes_api(
            model="chutes-chat",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 3

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("CHUTES_API_KEY"), reason="CHUTES_API_KEY not set")
    def test_chutes_provider_integration(self):
        """Test Chutes provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'chutes test success'",
            }
        ]

        result = call_chutes_api(
            model="chutes-chat",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
