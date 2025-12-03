"""Tests for OpenRouter provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.openrouter import call_openrouter_api

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


class TestOpenRouterProvider:
    """Test OpenRouter provider functionality."""

    @patch("kittylog.providers.openrouter.httpx.post")
    def test_call_openrouter_api_success(self, mock_post):
        """Test successful OpenRouter API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        result = call_openrouter_api(
            model="meta-llama/llama-3-8b-instruct",
            messages=_DUMMY_MESSAGES,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://openrouter.ai/api/v1/chat/completions"
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert "Bearer test-key" in headers["Authorization"]
        assert "HTTP-Referer" in headers
        assert "X-Title" in headers
        
        data = call_args[1]["json"]
        assert data["model"] == "meta-llama/llama-3-8b-instruct"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100

    def test_call_openrouter_api_missing_api_key(self, monkeypatch):
        """Ensure OpenRouter provider fails fast when API keys are missing."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_openrouter_api("test-model", _DUMMY_MESSAGES, 0.7, 32)

        assert "OPENROUTER_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.openrouter.httpx.post")
    def test_call_openrouter_api_http_error(self, mock_post):
        """Test OpenRouter API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_openrouter_api(
                    model="meta-llama/llama-3-8b-instruct",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "OpenRouter API error" in str(exc_info.value) or "Error calling OpenRouter API" in str(exc_info.value)

    @patch("kittylog.providers.openrouter.httpx.post")
    def test_call_openrouter_api_general_error(self, mock_post):
        """Test OpenRouter API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_openrouter_api(
                    model="meta-llama/llama-3-8b-instruct",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Error calling OpenRouter API" in str(exc_info.value)

    @pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY not set")
    def test_openrouter_provider_integration(self):
        """Test OpenRouter provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'openrouter test success'",
            }
        ]

        result = call_openrouter_api(
            model="meta-llama/llama-3-8b-instruct",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @patch("kittylog.providers.openrouter.httpx.post")
    def test_call_openrouter_api_with_system_message(self, mock_post):
        """Test OpenRouter API call with system message."""
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

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            result = call_openrouter_api(
                model="meta-llama/llama-3-8b-instruct",
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

    @patch("kittylog.providers.openrouter.httpx.post")
    def test_call_openrouter_api_with_conversation(self, mock_post):
        """Test OpenRouter API call with full conversation history."""
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

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            result = call_openrouter_api(
                model="meta-llama/llama-3-8b-instruct",
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

    @patch("kittylog.providers.openrouter.httpx.post")
    def test_call_openrouter_api_different_models(self, mock_post):
        """Test OpenRouter API call with different models."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        test_models = [
            "meta-llama/llama-3-8b-instruct",
            "anthropic/claude-3-haiku",
            "openai/gpt-4-turbo"
        ]
        
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            for model in test_models:
                result = call_openrouter_api(
                    model=model,
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )
                assert result == "Test response"
                
                call_args = mock_post.call_args
                data = call_args[1]["json"]
                assert data["model"] == model

    @patch("kittylog.providers.openrouter.httpx.post")
    def test_call_openrouter_api_custom_headers(self, mock_post):
        """Test OpenRouter API call includes required headers."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            call_openrouter_api(
                model="meta-llama/llama-3-8b-instruct",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        
        # Check for OpenRouter-specific headers
        assert "HTTP-Referer" in headers
        assert "X-Title" in headers
        assert headers["X-Title"] == "kittylog - AI-powered changelog generator"
        assert headers["HTTP-Referer"] == "https://github.com/pf-michael/kittylog"

    @patch("kittylog.providers.openrouter.httpx.post")
    def test_call_openrouter_api_with_json_mode(self, mock_post):
        """Test OpenRouter API call with JSON mode."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"result": "test"}'}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            result = call_openrouter_api(
                model="meta-llama/llama-3-8b-instruct",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
                response_format={"type": "json_object"}
            )

        assert result == '{"result": "test"}'
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert data["response_format"] == {"type": "json_object"}

    @patch("kittylog.providers.openrouter.httpx.post")
    def test_call_openrouter_api_with_provider_preferences(self, mock_post):
        """Test OpenRouter API call with provider preferences."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            result = call_openrouter_api(
                model="meta-llama/llama-3-8b-instruct",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
                models=[{"provider": "together", "model": "meta-llama/Meta-Llama-3-8B-Instruct-Lite"}]
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert "models" in data
        assert len(data["models"]) == 1
        assert data["models"][0]["provider"] == "together"
