"""Tests for Anthropic provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.anthropic import call_anthropic_api


class TestAnthropicProvider:
    """Test Anthropic provider functionality."""

    @patch("kittylog.providers.anthropic.httpx.post")
    def test_call_anthropic_api_success(self, mock_post):
        """Test successful Anthropic API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "content": [{"text": "Test response"}]
        }
        mock_post.return_value = mock_response

        result = call_anthropic_api(
            model="claude-3-haiku-20240307",
            messages=[
                {"role": "system", "content": "System message"},
                {"role": "user", "content": "Test message"}
            ],
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.anthropic.com/v1/messages"
        headers = call_args[1]["headers"]
        assert "x-api-key" in headers
        assert headers["anthropic-version"] == "2023-06-01"
        
        data = call_args[1]["json"]
        assert data["model"] == "claude-3-haiku-20240307"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100
        assert data["system"] == "System message"
        assert len(data["messages"]) == 1
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Test message"

    @patch("kittylog.providers.anthropic.httpx.post")
    def test_call_anthropic_api_no_system_message(self, mock_post):
        """Test Anthropic API call without system message."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "content": [{"text": "Test response"}]
        }
        mock_post.return_value = mock_response

        result = call_anthropic_api(
            model="claude-3-haiku-20240307",
            messages=[
                {"role": "user", "content": "Test message"}
            ],
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert "system" not in data

    def test_call_anthropic_api_missing_api_key(self, monkeypatch):
        """Test Anthropic API call fails without API key."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_anthropic_api(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )

        assert "ANTHROPIC_API_KEY not found" in str(exc_info.value)

    @patch("kittylog.providers.anthropic.httpx.post")
    def test_call_anthropic_api_http_error(self, mock_post):
        """Test Anthropic API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with pytest.raises(AIError) as exc_info:
            call_anthropic_api(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )

        assert "Anthropic API error" in str(exc_info.value)

    @patch("kittylog.providers.anthropic.httpx.post")
    def test_call_anthropic_api_general_error(self, mock_post):
        """Test Anthropic API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            call_anthropic_api(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )

        assert "Error calling Anthropic API" in str(exc_info.value)

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
