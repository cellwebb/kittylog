"""Tests for Ollama provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers import PROVIDER_REGISTRY

API_URL = "http://localhost:11434"
API_ENDPOINT = "http://localhost:11434/api/chat"


class TestOllamaProvider:
    """Test Ollama provider functionality."""

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"OLLAMA_API_URL": API_URL})
    def test_call_ollama_api_success(self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper):
        """Test successful Ollama API call."""
        response_data = {"message": {"content": "Test response"}}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["ollama"](
            model="llama2",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call URL
        url = api_test_helper.extract_call_url(mock_post)
        assert url == API_ENDPOINT

        # Verify request data
        data = api_test_helper.extract_call_data(mock_post)
        assert data["model"] == "llama2"
        assert data["temperature"] == 0.7
        assert data["stream"] is False

    @patch("kittylog.providers.base.httpx.post")
    def test_call_ollama_api_default_url(
        self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper, monkeypatch
    ):
        """Test Ollama API uses default URL when no environment variable is set."""
        monkeypatch.delenv("OLLAMA_API_URL", raising=False)
        monkeypatch.delenv("OLLAMA_HOST", raising=False)

        response_data = {"message": {"content": "Test response"}}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["ollama"]("test-model", dummy_messages, 0.7, 32)

        assert result == "Test response"

        # Should use default URL
        url = api_test_helper.extract_call_url(mock_post)
        assert url == "http://localhost:11434/api/chat"

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"OLLAMA_HOST": "http://localhost:11434"}, clear=True)
    def test_call_ollama_api_legacy_host_support(
        self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper
    ):
        """Test Ollama API call supports legacy OLLAMA_HOST."""
        response_data = {"message": {"content": "Test response"}}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["ollama"](
            model="llama2",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        url = api_test_helper.extract_call_url(mock_post)
        assert url == "http://localhost:11434/api/chat"

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"OLLAMA_API_URL": API_URL})
    def test_call_ollama_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Ollama API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=500, error_message="Internal server error"
        )

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["ollama"](
                model="llama2",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Ollama" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"OLLAMA_API_URL": API_URL})
    def test_call_ollama_api_general_error(self, mock_post, dummy_messages):
        """Test Ollama API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["ollama"](
                model="llama2",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Ollama" in str(exc_info.value)

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("OLLAMA_API_URL"), reason="OLLAMA_API_URL not set")
    def test_ollama_provider_integration(self):
        """Test Ollama provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'ollama test success'",
            }
        ]

        result = PROVIDER_REGISTRY["ollama"](
            model="llama2",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"OLLAMA_API_URL": API_URL})
    def test_call_ollama_api_with_system_message(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test Ollama API call with system message."""
        response_data = {"message": {"content": "Test response"}}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["ollama"](
            model="llama2",
            messages=dummy_messages_with_system,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "system"
        assert data["messages"][1]["role"] == "user"

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"OLLAMA_API_URL": API_URL})
    def test_call_ollama_api_format_conversion(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Ollama message format conversion."""
        response_data = {"message": {"content": "Test response"}}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["ollama"](
            model="llama2",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 3

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"OLLAMA_API_URL": API_URL})
    def test_call_ollama_api_data_structure(
        self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper
    ):
        """Test Ollama API call data structure."""
        response_data = {"message": {"content": "Test response"}}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        PROVIDER_REGISTRY["ollama"](
            model="llama2",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        data = api_test_helper.extract_call_data(mock_post)
        assert data["temperature"] == 0.7
        assert data["stream"] is False
        assert data["model"] == "llama2"

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"OLLAMA_API_URL": "http://localhost:11434/"})
    def test_call_ollama_api_custom_url_trailing_slash(
        self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper
    ):
        """Test Ollama API call handles URLs with trailing slashes."""
        response_data = {"message": {"content": "Test response"}}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["ollama"](
            model="llama2",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        url = api_test_helper.extract_call_url(mock_post)
        assert url == "http://localhost:11434/api/chat"
