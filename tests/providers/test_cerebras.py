"""Tests for Cerebras provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.cerebras import call_cerebras_api


class TestCerebrasProvider:
    """Test Cerebras provider functionality."""

    @patch("kittylog.providers.cerebras.httpx.post")
    def test_call_cerebras_api_success(self, mock_post):
        """Test successful Cerebras API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        result = call_cerebras_api(
            model="llama3.1-8b",
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
        assert call_args[0][0] == "https://api.cerebras.ai/v2/chat/completions"
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert "Bearer test-key" in headers["Authorization"]
        
        data = call_args[1]["json"]
        assert data["model"] == "llama3.1-8b"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100
        assert len(data["messages"]) == 2

    @patch("kittylog.providers.cerebras.httpx.post")
    @patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key"})
    def test_call_cerebras_api_success_with_key(self, mock_post):
        """Test successful Cerebras API callwith environment key."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        result = call_cerebras_api(
            model="llama3.1-8b",
            messages=[{"role": "user", "content": "Test message"}],
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

    def test_call_cerebras_api_missing_api_key(self, monkeypatch):
        """Test Cerebras API call fails without API key."""
        monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_cerebras_api(
                model="llama3.1-8b",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )

        assert "CEREBRAS_API_KEY not found" in str(exc_info.value)

    @patch("kittylog.providers.cerebras.httpx.post")
    def test_call_cerebras_api_http_error(self, mock_post):
        """Test Cerebras API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_cerebras_api(
                    model="llama3.1-8b",
                    messages=[{"role": "user", "content": "Test"}],
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Cerebras API error" in str(exc_info.value)

    @patch("kittylog.providers.cerebras.httpx.post")
    def test_call_cerebras_api_general_error(self, mock_post):
        """Test Cerebras API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_cerebras_api(
                    model="llama3.1-8b",
                    messages=[{"role": "user", "content": "Test"}],
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Error calling Cerebras API" in str(exc_info.value)

    @pytest.mark.skipif(not os.getenv("CEREBRAS_API_KEY"), reason="CEREBRAS_API_KEY not set")
    def test_cerebras_provider_integration(self):
        """Test Cerebras provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'cerebras test success'",
            }
        ]

        result = call_cerebras_api(
            model="llama3.1-8b",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
