"""Tests for Claude Code provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.claude_code import call_claude_code_api

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


class TestClaudeCodeProvider:
    """Test Claude Code provider functionality."""

    @patch("kittylog.providers.claude_code.httpx.post")
    def test_call_claude_code_api_success(self, mock_post):
        """Test successful Claude Code API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        result = call_claude_code_api(
            model="claude-3-haiku-20240307",
            messages=_DUMMY_MESSAGES,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert "Bearer test-key" in headers["Authorization"]
        
        data = call_args[1]["json"]
        assert data["model"] == "claude-3-haiku-20240307"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100

    def test_call_claude_code_api_missing_api_key(self, monkeypatch):
        """Ensure Claude Code provider fails fast when API keys are missing."""
        monkeypatch.delenv("CLAUDE_CODE_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_claude_code_api("test-model", _DUMMY_MESSAGES, 0.7, 32)

        assert "CLAUDE_CODE_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.claude_code.httpx.post")
    def test_call_claude_code_api_http_error(self, mock_post):
        """Test Claude Code API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"CLAUDE_CODE_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_claude_code_api(
                    model="claude-3-haiku-20240307",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Claude Code API error" in str(exc_info.value) or "Error calling Claude Code API" in str(exc_info.value)

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
            model="claude-3-haiku-20240307",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @patch("kittylog.providers.claude_code.httpx.post")
    def test_call_claude_code_api_custom_base_url(self, mock_post):
        """Test Claude Code API call with custom base URL."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "CLAUDE_CODE_API_KEY": "test-key",
            "CLAUDE_CODE_BASE_URL": "https://custom.claude-code.ai"
        }):
            result = call_claude_code_api(
                model="claude-3-haiku-20240307",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        assert "https://custom.claude-code.ai" in call_args[0][0]
