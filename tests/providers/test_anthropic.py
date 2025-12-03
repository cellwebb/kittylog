"""Tests for Anthropic provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.anthropic import call_anthropic_api

API_KEY = "test-key"
API_ENDPOINT = "https://api.anthropic.com/v1/messages"


class TestAnthropicProvider:
    """Test Anthropic provider functionality."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": API_KEY})
    @patch("kittylog.providers.anthropic.httpx.post")
    def test_call_anthropic_api_success(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test successful Anthropic API call."""
        response_data = {"content": [{"text": "Test response"}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_anthropic_api(
            model="claude-3-haiku-20240307",
            messages=dummy_messages_with_system,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call URL and headers
        url = api_test_helper.extract_call_url(mock_post)
        assert url == API_ENDPOINT

        headers = api_test_helper.extract_call_headers(mock_post)
        assert "x-api-key" in headers
        assert headers["anthropic-version"] == "2023-06-01"

        # Verify request data
        data = api_test_helper.extract_call_data(mock_post)
        assert data["model"] == "claude-3-haiku-20240307"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100
        assert data["system"] == "You are a helpful assistant."
        assert len(data["messages"]) == 1
        assert data["messages"][0]["role"] == "user"

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": API_KEY})
    @patch("kittylog.providers.anthropic.httpx.post")
    def test_call_anthropic_api_no_system_message(
        self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper
    ):
        """Test Anthropic API call without system message."""
        response_data = {"content": [{"text": "Test response"}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_anthropic_api(
            model="claude-3-haiku-20240307",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert "system" not in data

    def test_call_anthropic_api_missing_api_key(self, monkeypatch, dummy_messages):
        """Test Anthropic API call fails without API key."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_anthropic_api(
                model="claude-3-haiku-20240307",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "ANTHROPIC_API_KEY not found" in str(exc_info.value)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": API_KEY})
    @patch("kittylog.providers.anthropic.httpx.post")
    def test_call_anthropic_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Anthropic API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            call_anthropic_api(
                model="claude-3-haiku-20240307",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Error calling Anthropic API" in str(exc_info.value)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": API_KEY})
    @patch("kittylog.providers.anthropic.httpx.post")
    def test_call_anthropic_api_general_error(self, mock_post, dummy_messages):
        """Test Anthropic API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            call_anthropic_api(
                model="claude-3-haiku-20240307",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Error calling Anthropic API" in str(exc_info.value)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": API_KEY})
    @patch("kittylog.providers.anthropic.httpx.post")
    def test_call_anthropic_api_with_conversation(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Anthropic API call with conversation history."""
        response_data = {"content": [{"text": "Test response"}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_anthropic_api(
            model="claude-3-haiku-20240307",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 3

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
    def test_anthropic_provider_integration(self):
        """Test Anthropic provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'anthropic test success'",
            }
        ]

        result = call_anthropic_api(
            model="claude-3-haiku-20240307",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
