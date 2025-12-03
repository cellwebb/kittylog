"""Tests for Ollama provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.ollama import call_ollama_api

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


class TestOllamaProvider:
    """Test Ollama provider functionality."""

    @patch("kittylog.providers.ollama.httpx.post")
    def test_call_ollama_api_success(self, mock_post):
        """Test successful Ollama API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "message": {"content": "Test response"}
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OLLAMA_API_URL": "http://localhost:11434"}):
            result = call_ollama_api(
                model="llama2",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/chat"
        headers = call_args[1]["headers"]
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        
        data = call_args[1]["json"]
        assert data["model"] == "llama2"
        assert data["temperature"] == 0.7
        # Ollama uses different parameter names
        assert "options" in data
        assert "num_predict" in data["options"]

    def test_call_ollama_api_missing_api_url(self, monkeypatch):
        """Ensure Ollama provider fails fast when API URL is missing."""
        monkeypatch.delenv("OLLAMA_API_URL", raising=False)
        # Also clear legacy OLLAMA_HOST if it exists
        monkeypatch.delenv("OLLAMA_HOST", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_ollama_api("test-model", _DUMMY_MESSAGES, 0.7, 32)

        assert "OLLAMA_API_URL not found" in str(exc_info.value)

    @patch("kittylog.providers.ollama.httpx.post")
    def test_call_ollama_api_legacy_host_support(self, mock_post):
        """Test Ollama API call supports legacy OLLAMA_HOST."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "message": {"content": "Test response"}
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "OLLAMA_HOST": "http://localhost:11434"
        }, clear=True):  # Clear to avoid interference
            result = call_ollama_api(
                model="llama2",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/chat"

    @patch("kittylog.providers.ollama.httpx.post")
    def test_call_ollama_api_http_error(self, mock_post):
        """Test Ollama API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 500")
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OLLAMA_API_URL": "http://localhost:11434"}):
            with pytest.raises(AIError) as exc_info:
                call_ollama_api(
                    model="llama2",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Ollama API error" in str(exc_info.value) or "Error calling Ollama API" in str(exc_info.value)

    @patch("kittylog.providers.ollama.httpx.post")
    def test_call_ollama_api_general_error(self, mock_post):
        """Test Ollama API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with patch.dict(os.environ, {"OLLAMA_API_URL": "http://localhost:11434"}):
            with pytest.raises(AIError) as exc_info:
                call_ollama_api(
                    model="llama2",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Error calling Ollama API" in str(exc_info.value)

    @pytest.mark.skipif(not os.getenv("OLLAMA_API_URL"), reason="OLLAMA_API_URL not set")
    def test_ollama_provider_integration(self):
        """Test Ollama provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'ollama test success'",
            }
        ]

        result = call_ollama_api(
            model="llama2",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @patch("kittylog.providers.ollama.httpx.post")
    def test_call_ollama_api_with_system_message(self, mock_post):
        """Test Ollama API call with system message."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "message": {"content": "Test response"}
        }
        mock_post.return_value = mock_response

        messages_with_system = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Test message"}
        ]

        with patch.dict(os.environ, {"OLLAMA_API_URL": "http://localhost:11434"}):
            result = call_ollama_api(
                model="llama2",
                messages=messages_with_system,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        # Ollama includes system message in the messages list
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "system"
        assert data["messages"][1]["role"] == "user"

    @patch("kittylog.providers.ollama.httpx.post")
    def test_call_ollama_api_format_conversion(self, mock_post):
        """Test Ollama message format conversion."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "message": {"content": "Test response"}
        }
        mock_post.return_value = mock_response

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]

        with patch.dict(os.environ, {"OLLAMA_API_URL": "http://localhost:11434"}):
            result = call_ollama_api(
                model="llama2",
                messages=messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        
        # Check that messages are converted to Ollama format
        assert len(data["messages"]) == 3
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Hello"
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][1]["content"] == "Hi there!"
        assert data["messages"][2]["role"] == "user"
        assert data["messages"][2]["content"] == "How are you?"

    @patch("kittylog.providers.ollama.httpx.post")
    def test_call_ollama_api_options_structure(self, mock_post):
        """Test Ollama API call options structure."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "message": {"content": "Test response"}
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OLLAMA_API_URL": "http://localhost:11434"}):
            call_ollama_api(
                model="llama2",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        call_args = mock_post.call_args
        data = call_args[1]["json"]
        
        # Verify options structure
        assert "options" in data
        assert data["options"]["temperature"] == 0.7
        assert data["options"]["num_predict"] == 100

    @patch("kittylog.providers.ollama.httpx.post")
    def test_call_ollama_api_custom_url_trailing_slash(self, mock_post):
        """Test Ollama API call handles URLs with trailing slashes."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "message": {"content": "Test response"}
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OLLAMA_API_URL": "http://localhost:11434/"}):
            result = call_ollama_api(
                model="llama2",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        # Should handle trailing slash properly
        assert call_args[0][0] == "http://localhost:11434/api/chat"
