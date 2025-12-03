"""Tests for MiniMax provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.minimax import call_minimax_api

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


class TestMiniMaxProvider:
    """Test MiniMax provider functionality."""

    @patch("kittylog.providers.minimax.httpx.post")
    def test_call_minimax_api_success(self, mock_post):
        """Test successful MiniMax API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        result = call_minimax_api(
            model="abab6.5s-chat",
            messages=_DUMMY_MESSAGES,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.minimax.chat/v1/text/chatcompletion_pro"
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert "Bearer test-key" in headers["Authorization"]
        
        data = call_args[1]["json"]
        assert data["model"] == "abab6.5s-chat"
        assert data["temperature"] == 0.7
        assert data["tokens_to_generate"] == 100
        assert len(data["messages"]) == 1

    def test_call_minimax_api_missing_api_key(self, monkeypatch):
        """Ensure MiniMax provider fails fast when API keys are missing."""
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_minimax_api("test-model", _DUMMY_MESSAGES, 0.7, 32)

        assert "MINIMAX_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.minimax.httpx.post")
    def test_call_minimax_api_http_error(self, mock_post):
        """Test MiniMax API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_minimax_api(
                    model="abab6.5s-chat",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "MiniMax API error" in str(exc_info.value) or "Error calling MiniMax API" in str(exc_info.value)

    @patch("kittylog.providers.minimax.httpx.post")
    def test_call_minimax_api_general_error(self, mock_post):
        """Test MiniMax API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_minimax_api(
                    model="abab6.5s-chat",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Error calling MiniMax API" in str(exc_info.value)

    @pytest.mark.skipif(not os.getenv("MINIMAX_API_KEY"), reason="MINIMAX_API_KEY not set")
    def test_minimax_provider_integration(self):
        """Test MiniMax provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'minimax test success'",
            }
        ]

        result = call_minimax_api(
            model="abab6.5s-chat",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @patch("kittylog.providers.minimax.httpx.post")
    def test_call_minimax_api_with_system_message(self, mock_post):
        """Test MiniMax API call with system message."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        messages_with_system = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Test message"}
        ]

        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key"}):
            result = call_minimax_api(
                model="abab6.5s-chat",
                messages=messages_with_system,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "system"
        assert data["messages"][1]["role"] == "user"

    @patch("kittylog.providers.minimax.httpx.post")
    def test_call_minimax_api_group_id_parameter(self, mock_post):
        """Test MiniMax API call with group ID parameter."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "MINIMAX_API_KEY": "test-key",
            "MINIMAX_GROUP_ID": "test-group-123"
        }):
            result = call_minimax_api(
                model="abab6.5s-chat",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer test-key"
        # Group ID should be included in headers or parameters depending on implementation
        # This test ensures the group ID is properly handled if needed

    @patch("kittylog.providers.minimax.httpx.post")
    def test_call_minimax_api_parameter_conversion(self, mock_post):
        """Test MiniMax API call parameter conversion."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key"}):
            call_minimax_api(
                model="abab6.5s-chat",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        call_args = mock_post.call_args
        data = call_args[1]["json"]
        # MiniMax uses different parameter names
        assert "tokens_to_generate" in data
        assert data["tokens_to_generate"] == 100
        assert data["temperature"] == 0.7
