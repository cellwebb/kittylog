"""Tests for Groq provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers import PROVIDER_REGISTRY

API_KEY = "test-key"
API_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


class TestGroqProvider:
    """Test Groq provider functionality."""

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"GROQ_API_KEY": API_KEY})
    def test_call_groq_api_success(self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper):
        """Test successful Groq API call."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["groq"](
            model="llama3-8b-8192",
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
        assert data["model"] == "llama3-8b-8192"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100

    def test_call_groq_api_missing_api_key(self, monkeypatch, dummy_messages):
        """Ensure Groq provider fails fast when API keys are missing."""
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["groq"]("test-model", dummy_messages, 0.7, 32)

        assert "GROQ_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"GROQ_API_KEY": API_KEY})
    def test_call_groq_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Groq API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["groq"](
                model="llama3-8b-8192",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Groq" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"GROQ_API_KEY": API_KEY})
    def test_call_groq_api_general_error(self, mock_post, dummy_messages):
        """Test Groq API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["groq"](
                model="llama3-8b-8192",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Groq" in str(exc_info.value)

    @pytest.mark.integration
    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"GROQ_API_KEY": API_KEY})
    def test_groq_provider_integration(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Groq provider integration with mocked API call."""
        # Mock successful response
        response_data = {"choices": [{"message": {"content": "groq test success"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["groq"](
            model="llama3-70b-8192",  # Updated to use a current model
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "groq test success"
        mock_post.assert_called_once()

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"GROQ_API_KEY": API_KEY})
    def test_call_groq_api_with_system_message(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test Groq API call with system message."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["groq"](
            model="llama3-8b-8192",
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
    @patch.dict(os.environ, {"GROQ_API_KEY": API_KEY})
    def test_call_groq_api_with_conversation(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Groq API call with full conversation history."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["groq"](
            model="llama3-8b-8192",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 3
