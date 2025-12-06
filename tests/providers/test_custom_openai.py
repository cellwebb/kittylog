"""Tests for Custom OpenAI provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers import PROVIDER_REGISTRY

API_KEY = "test-key"
API_BASE_URL = "https://custom.openai.ai"


class TestCustomOpenAIProvider:
    """Test Custom OpenAI provider functionality."""

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"CUSTOM_OPENAI_API_KEY": API_KEY, "CUSTOM_OPENAI_BASE_URL": API_BASE_URL})
    def test_call_custom_openai_api_success(
        self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper
    ):
        """Test successful Custom OpenAI API call."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["custom-openai"](
            model="gpt-4",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call URL and headers
        url = api_test_helper.extract_call_url(mock_post)
        assert API_BASE_URL in url

        headers = api_test_helper.extract_call_headers(mock_post)
        assert api_test_helper.verify_bearer_token_header(headers, API_KEY)

        # Verify request data
        data = api_test_helper.extract_call_data(mock_post)
        assert data["model"] == "gpt-4"
        assert data["temperature"] == 0.7
        assert data["max_completion_tokens"] == 100

    def test_custom_openai_requires_base_url(self, monkeypatch, dummy_messages):
        """Custom OpenAI provider should require a base URL."""
        monkeypatch.setenv("CUSTOM_OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("CUSTOM_OPENAI_BASE_URL", raising=False)

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["custom-openai"]("test-model", dummy_messages, 0.7, 32)

        assert "CUSTOM_OPENAI_BASE_URL" in str(exc_info.value)

    def test_custom_openai_missing_api_key(self, monkeypatch, dummy_messages):
        """Test Custom OpenAI API call fails without API key."""
        monkeypatch.delenv("CUSTOM_OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("CUSTOM_OPENAI_BASE_URL", API_BASE_URL)

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["custom-openai"](
                model="gpt-4",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "CUSTOM_OPENAI_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"CUSTOM_OPENAI_API_KEY": API_KEY, "CUSTOM_OPENAI_BASE_URL": API_BASE_URL})
    def test_call_custom_openai_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Custom OpenAI API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["custom-openai"](
                model="gpt-4",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Custom OpenAI" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"CUSTOM_OPENAI_API_KEY": API_KEY, "CUSTOM_OPENAI_BASE_URL": API_BASE_URL})
    def test_call_custom_openai_api_general_error(self, mock_post, dummy_messages):
        """Test Custom OpenAI API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["custom-openai"](
                model="gpt-4",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Custom OpenAI" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"CUSTOM_OPENAI_API_KEY": API_KEY, "CUSTOM_OPENAI_BASE_URL": API_BASE_URL})
    def test_call_custom_openai_api_with_system_message(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test Custom OpenAI API call with system message."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["custom-openai"](
            model="gpt-4",
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
    @patch.dict(os.environ, {"CUSTOM_OPENAI_API_KEY": API_KEY, "CUSTOM_OPENAI_BASE_URL": API_BASE_URL})
    def test_call_custom_openai_api_with_conversation(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Custom OpenAI API call with full conversation history."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["custom-openai"](
            model="gpt-4",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 3

    @pytest.mark.integration
    @pytest.mark.skipif(
        not all(os.getenv(k) for k in ["CUSTOM_OPENAI_API_KEY", "CUSTOM_OPENAI_BASE_URL"]),
        reason="Custom OpenAI environment variables not set",
    )
    def test_custom_openai_provider_integration(self):
        """Test Custom OpenAI provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'custom openai test success'",
            }
        ]

        result = PROVIDER_REGISTRY["custom-openai"](
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
