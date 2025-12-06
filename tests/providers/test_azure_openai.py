"""Tests for Azure OpenAI provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers import PROVIDER_REGISTRY

API_KEY = "test-key"
API_ENDPOINT = "https://test.openai.azure.com"
API_VERSION = "2024-02-15-preview"


class TestAzureOpenAIProvider:
    """Test Azure OpenAI provider functionality."""

    @patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_API_KEY": API_KEY,
            "AZURE_OPENAI_ENDPOINT": API_ENDPOINT,
            "AZURE_OPENAI_API_VERSION": API_VERSION,
        },
    )
    @patch("kittylog.providers.base.httpx.post")
    def test_call_azure_openai_api_success(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test successful Azure OpenAI API call."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["azure-openai"](
            model="gpt-4",
            messages=dummy_messages_with_system,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call URL and headers
        url = api_test_helper.extract_call_url(mock_post)
        assert API_ENDPOINT in url
        assert "gpt-4" in url

        headers = api_test_helper.extract_call_headers(mock_post)
        assert api_test_helper.verify_api_key_header(headers, API_KEY, "api-key")

    def test_call_azure_openai_api_missing_api_key(self, monkeypatch, dummy_messages):
        """Test Azure OpenAI API call fails without API key."""
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["azure-openai"](
                model="gpt-4",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "AZURE_OPENAI_ENDPOINT is required" in str(exc_info.value)

    def test_call_azure_openai_api_missing_endpoint(self, monkeypatch, dummy_messages):
        """Test Azure OpenAI API call fails without endpoint."""
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", API_KEY)
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["azure-openai"](
                model="gpt-4",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "AZURE_OPENAI_ENDPOINT is required" in str(exc_info.value)

    @patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_API_KEY": API_KEY,
            "AZURE_OPENAI_ENDPOINT": API_ENDPOINT,
        },
    )
    @patch("kittylog.providers.base.httpx.post")
    def test_call_azure_openai_api_missing_api_version(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Azure OpenAI API call uses default version when not set."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        # Should succeed with default version
        result = PROVIDER_REGISTRY["azure-openai"](
            model="gpt-4",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

    @patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_API_KEY": API_KEY,
            "AZURE_OPENAI_ENDPOINT": API_ENDPOINT,
            "AZURE_OPENAI_API_VERSION": API_VERSION,
        },
    )
    @patch("kittylog.providers.base.httpx.post")
    def test_call_azure_openai_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Azure OpenAI API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["azure-openai"](
                model="gpt-4",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Azure OpenAI" in str(exc_info.value)

    @patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_API_KEY": API_KEY,
            "AZURE_OPENAI_ENDPOINT": API_ENDPOINT,
            "AZURE_OPENAI_API_VERSION": API_VERSION,
        },
    )
    @patch("kittylog.providers.base.httpx.post")
    def test_call_azure_openai_api_general_error(self, mock_post, dummy_messages):
        """Test Azure OpenAI API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["azure-openai"](
                model="gpt-4",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Azure OpenAI" in str(exc_info.value)

    @patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_API_KEY": API_KEY,
            "AZURE_OPENAI_ENDPOINT": API_ENDPOINT,
            "AZURE_OPENAI_API_VERSION": API_VERSION,
        },
    )
    @patch("kittylog.providers.base.httpx.post")
    def test_call_azure_openai_api_with_conversation(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Azure OpenAI API call with full conversation history."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["azure-openai"](
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
        not all(os.getenv(k) for k in ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_VERSION"]),
        reason="Azure OpenAI environment variables not set",
    )
    def test_azure_openai_provider_integration(self):
        """Test Azure OpenAI provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'azure openai test success'",
            }
        ]

        result = PROVIDER_REGISTRY["azure-openai"](
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
