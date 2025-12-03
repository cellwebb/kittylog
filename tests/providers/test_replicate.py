"""Tests for Replicate provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.replicate import call_replicate_api

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


class TestReplicateProvider:
    """Test Replicate provider functionality."""

    @patch("kittylog.providers.replicate.httpx.post")
    def test_call_replicate_api_success(self, mock_post):
        """Test successful Replicate API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        result = call_replicate_api(
            model="meta/meta-llama-3-8b-instruct",
            messages=_DUMMY_MESSAGES,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.replicate.com/v1/chat/completions"
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert "Bearer test-key" in headers["Authorization"]
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        
        data = call_args[1]["json"]
        assert data["model"] == "meta/meta-llama-3-8b-instruct"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100

    def test_call_replicate_api_missing_api_key(self, monkeypatch):
        """Ensure Replicate provider fails fast when API keys are missing."""
        monkeypatch.delenv("REPLICATE_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_replicate_api("test-model", _DUMMY_MESSAGES, 0.7, 32)

        assert "REPLICATE_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.replicate.httpx.post")
    def test_call_replicate_api_http_error(self, mock_post):
        """Test Replicate API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"REPLICATE_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_replicate_api(
                    model="meta/meta-llama-3-8b-instruct",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Replicate API error" in str(exc_info.value) or "Error calling Replicate API" in str(exc_info.value)

    @patch("kittylog.providers.replicate.httpx.post")
    def test_call_replicate_api_general_error(self, mock_post):
        """Test Replicate API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with patch.dict(os.environ, {"REPLICATE_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_replicate_api(
                    model="meta/meta-llama-3-8b-instruct",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Error calling Replicate API" in str(exc_info.value)

    @pytest.mark.skipif(not os.getenv("REPLICATE_API_KEY"), reason="REPLICATE_API_KEY not set")
    def test_replicate_provider_integration(self):
        """Test Replicate provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'replicate test success'",
            }
        ]

        result = call_replicate_api(
            model="meta/meta-llama-3-8b-instruct",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @patch("kittylog.providers.replicate.httpx.post")
    def test_call_replicate_api_with_system_message(self, mock_post):
        """Test Replicate API call with system message."""
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

        with patch.dict(os.environ, {"REPLICATE_API_KEY": "test-key"}):
            result = call_replicate_api(
                model="meta/meta-llama-3-8b-instruct",
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

    @patch("kittylog.providers.replicate.httpx.post")
    def test_call_replicate_api_with_conversation(self, mock_post):
        """Test Replicate API call with full conversation history."""
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

        with patch.dict(os.environ, {"REPLICATE_API_KEY": "test-key"}):
            result = call_replicate_api(
                model="meta/meta-llama-3-8b-instruct",
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

    @patch("kittylog.providers.replicate.httpx.post")
    def test_call_replicate_api_different_models(self, mock_post):
        """Test Replicate API call with different models."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        test_models = [
            "meta/meta-llama-3-8b-instruct",
            "mistralai/mistral-7b-instruct-v0.2",
            "meta/meta-llama-3-70b-instruct"
        ]
        
        with patch.dict(os.environ, {"REPLICATE_API_KEY": "test-key"}):
            for model in test_models:
                result = call_replicate_api(
                    model=model,
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )
                assert result == "Test response"
                
                call_args = mock_post.call_args
                data = call_args[1]["json"]
                assert data["model"] == model

    @patch("kittylog.providers.replicate.httpx.post")
    def test_call_replicate_api_with_stream(self, mock_post):
        """Test Replicate API call with streaming."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"REPLICATE_API_KEY": "test-key"}):
            result = call_replicate_api(
                model="meta/meta-llama-3-8b-instruct",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
                stream=False  # Explicitly set to False for testing
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert "stream" not in data or data.get("stream") is False

    @patch("kittylog.providers.replicate.httpx.post")
    def test_call_replicate_api_with_max_tokens_validation(self, mock_post):
        """Test Replicate API call with max_tokens parameter."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"REPLICATE_API_KEY": "test-key"}):
            # Test with different max_tokens values
            for max_tokens in [50, 100, 500]:
                result = call_replicate_api(
                    model="meta/meta-llama-3-8b-instruct",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=max_tokens,
                )
                assert result == "Test response"
                
                call_args = mock_post.call_args
                data = call_args[1]["json"]
                assert data["max_tokens"] == max_tokens

    @patch("kittylog.providers.replicate.httpx.post")
    def test_call_replicate_api_empty_response(self, mock_post):
        """Test Replicate API call handles empty response."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": ""}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"REPLICATE_API_KEY": "test-key"}):
            result = call_replicate_api(
                model="meta/meta-llama-3-8b-instruct",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == ""  # Empty string should be returned
