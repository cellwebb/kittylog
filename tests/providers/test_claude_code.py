"""Tests for Claude Code provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.claude_code import call_claude_code_api

API_KEY = "test-access-token"
API_ENDPOINT = "https://api.anthropic.com/v1/messages"


class TestClaudeCodeProvider:
    """Test Claude Code provider functionality."""

    @patch("kittylog.providers.claude_code.httpx.post")
    @patch.dict(os.environ, {"CLAUDE_CODE_ACCESS_TOKEN": API_KEY})
    def test_call_claude_code_api_success(self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper):
        """Test successful Claude Code API call."""
        response_data = {"content": [{"text": "Test response"}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_claude_code_api(
            model="claude-code",
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
        assert data["model"] == "claude-code"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100
        assert data["system"] == "You are Claude Code, Anthropic's official CLI for Claude."

    def test_call_claude_code_api_missing_api_key(self, monkeypatch, dummy_messages):
        """Ensure Claude Code provider fails fast when API keys are missing."""
        monkeypatch.delenv("CLAUDE_CODE_ACCESS_TOKEN", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_claude_code_api("test-model", dummy_messages, 0.7, 32)

        assert "CLAUDE_CODE_ACCESS_TOKEN" in str(exc_info.value)

    @patch("kittylog.providers.claude_code.httpx.post")
    @patch.dict(os.environ, {"CLAUDE_CODE_ACCESS_TOKEN": API_KEY})
    def test_call_claude_code_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Claude Code API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            call_claude_code_api(
                model="claude-code",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Claude Code API error" in str(exc_info.value) or "Error calling Claude Code API" in str(exc_info.value)

    @patch("kittylog.providers.claude_code.httpx.post")
    @patch.dict(os.environ, {"CLAUDE_CODE_ACCESS_TOKEN": API_KEY})
    def test_call_claude_code_api_general_error(self, mock_post, dummy_messages):
        """Test Claude Code API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            call_claude_code_api(
                model="claude-code",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Error calling Claude Code API" in str(exc_info.value)

    @patch("kittylog.providers.claude_code.httpx.post")
    @patch.dict(os.environ, {"CLAUDE_CODE_ACCESS_TOKEN": API_KEY})
    def test_call_claude_code_api_with_system_message(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test Claude Code API call with system message."""
        response_data = {"content": [{"text": "Test response"}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_claude_code_api(
            model="claude-code",
            messages=dummy_messages_with_system,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 1  # System message merged into first user message
        assert data["messages"][0]["role"] == "user"
        assert "You are a helpful assistant." in data["messages"][0]["content"]
        assert "Test message" in data["messages"][0]["content"]

    @patch("kittylog.providers.claude_code.httpx.post")
    @patch.dict(os.environ, {"CLAUDE_CODE_ACCESS_TOKEN": API_KEY})
    def test_call_claude_code_api_with_conversation(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Claude Code API call with full conversation history."""
        response_data = {"content": [{"text": "Test response"}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_claude_code_api(
            model="claude-code",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 3

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("CLAUDE_CODE_API_KEY"), reason="CLAUDE_CODE_API_KEY not set")
    def test_claude_code_provider_integration(self):
        """Test Claude Code provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'claude code test success'",
            }
        ]

        result = call_claude_code_api(
            model="claude-code",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
