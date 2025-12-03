"""Tests for Together provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.together import call_together_api

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


class TestTogetherProvider:
    """Test Together provider functionality."""

    @patch("kittylog.providers.together.httpx.post")
    def test_call_together_api_success(self, mock_post):
        """Test successful Together API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        result = call_together_api(
            model="meta-llama/Llama-3-8b-chat-hf",
            messages=_DUMMY_MESSAGES,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.together.xyz/v1/chat/completions"
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert "Bearer test-key" in headers["Authorization"]
        
        data = call_args[1]["json"]
        assert data["model"] == "meta-llama/Llama-3-8b-chat-hf"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100

    def test_call_together_api_missing_api_key(self, monkeypatch):
        """Ensure Together provider fails fast when API keys are missing."""
        monkeypatch.delenv("TOGETHER_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_together_api("test-model", _DUMMY_MESSAGES, 0.7, 32)

        assert "TOGETHER_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.together.httpx.post")
    def test_call_together_api_http_error(self, mock_post):
        """Test Together API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_together_api(
                    model="meta-llama/Llama-3-8b-chat-hf",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Together API error" in str(exc_info.value) or "Error calling Together API" in str(exc_info.value)

    @patch("kittylog.providers.together.httpx.post")
    def test_call_together_api_general_error(self, mock_post):
        """Test Together API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_together_api(
                    model="meta-llama/Llama-3-8b-chat-hf",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Error calling Together API" in str(exc_info.value)

    @pytest.mark.skipif(not os.getenv("TOGETHER_API_KEY"), reason="TOGETHER_API_KEY not set")
    def test_together_provider_integration(self):
        """Test Together provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'together test success'",
            }
        ]

        result = call_together_api(
            model="meta-llama/Llama-3-8b-chat-hf",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @patch("kittylog.providers.together.httpx.post")
    def test_call_together_api_with_system_message(self, mock_post):
        """Test Together API call with system message."""
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

        with patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}):
            result = call_together_api(
                model="meta-llama/Llama-3-8b-chat-hf",
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

    @patch("kittylog.providers.together.httpx.post")
    def test_call_together_api_with_conversation(self, mock_post):
        """Test Together API call with full conversation history."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]

        with patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}):
            result = call_together_api(
                model="meta-llama/Llama-3-8b-chat-hf",
                messages=conversation,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert len(data["messages"]) == 3
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][2]["role"] == "user"

    @patch("kittylog.providers.together.httpx.post")
    def test_call_together_api_different_models(self, mock_post):
        """Test Together API call with different models."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        test_models = [
            "meta-llama/Llama-3-8b-chat-hf",
            "meta-llama/Llama-3-70b-chat-hf",
            "mistralai/Mixtral-8x7B-Instruct-v0.1"
        ]
        
        with patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}):
            for model in test_models:
                result = call_together_api(
                    model=model,
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )
                assert result == "Test response"
                
                call_args = mock_post.call_args
                data = call_args[1]["json"]
                assert data["model"] == model

    @patch("kittylog.providers.together.httpx.post")
    def test_call_together_api_with_stream(self, mock_post):
        """Test Together API call with streaming."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}):
            result = call_together_api(
                model="meta-llama/Llama-3-8b-chat-hf",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
                stream=False  # Explicitly set to False for testing
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert "stream" not in data or data.get("stream") is False

    @patch("kittylog.providers.together.httpx.post")
    def test_call_together_api_with_json_mode(self, mock_post):
        """Test Together API call with JSON mode."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"result": "test"}'}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}):
            result = call_together_api(
                model="meta-llama/Llama-3-8b-chat-hf",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
                response_format={"type": "json_object"}
            )

        assert result == '{"result": "test"}'
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert data["response_format"] == {"type": "json_object"}

    @patch("kittylog.providers.together.httpx.post")
    def test_call_together_api_with_max_tokens_validation(self, mock_post):
        """Test Together API call with max_tokens parameter."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}):
            # Test with different max_tokens values
            for max_tokens in [50, 100, 500, 1000]:
                result = call_together_api(
                    model="meta-llama/Llama-3-8b-chat-hf",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=max_tokens,
                )
                assert result == "Test response"
                
                call_args = mock_post.call_args
                data = call_args[1]["json"]
                assert data["max_tokens"] == max_tokens

    @patch("kittylog.providers.together.httpx.post")
    def test_call_together_api_with_stop_tokens(self, mock_post):
        """Test Together API call with stop tokens."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}):
            result = call_together_api(
                model="meta-llama/Llama-3-8b-chat-hf",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
                stop=["\n", "END"]
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert data["stop"] == ["\n", "END"]

    @patch("kittylog.providers.together.httpx.post")
    def test_call_together_api_empty_response(self, mock_post):
        """Test Together API call handles empty response."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": ""}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}):
            result = call_together_api(
                model="meta-llama/Llama-3-8b-chat-hf",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == ""  # Empty string should be returned
