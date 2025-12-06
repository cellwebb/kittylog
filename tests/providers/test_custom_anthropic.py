"""Tests for Custom Anthropic provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers import PROVIDER_REGISTRY

API_KEY = "test-key"
API_BASE_URL = "https://custom.anthropic.ai"
API_VERSION = "2023-06-01"


class TestCustomAnthropicProvider:
    """Test Custom Anthropic provider functionality."""

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(
        os.environ,
        {
            "CUSTOM_ANTHROPIC_API_KEY": API_KEY,
            "CUSTOM_ANTHROPIC_BASE_URL": API_BASE_URL,
            "CUSTOM_ANTHROPIC_VERSION": API_VERSION,
        },
    )
    def test_call_custom_anthropic_api_success(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test successful Custom Anthropic API call."""
        response_data = {"content": [{"text": "Test response"}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["custom-anthropic"](
            model="claude-3-haiku-20240307",
            messages=dummy_messages_with_system,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call URL and headers
        url = api_test_helper.extract_call_url(mock_post)
        assert API_BASE_URL in url

        headers = api_test_helper.extract_call_headers(mock_post)
        assert api_test_helper.verify_api_key_header(headers, API_KEY, "x-api-key")
        assert headers["anthropic-version"] == API_VERSION

        # Verify request data
        data = api_test_helper.extract_call_data(mock_post)
        assert data["model"] == "claude-3-haiku-20240307"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100
        assert data["system"] == "You are a helpful assistant."

    def test_custom_anthropic_requires_base_url(self, monkeypatch, dummy_messages):
        """Custom Anthropic provider should require a base URL."""
        monkeypatch.setenv("CUSTOM_ANTHROPIC_API_KEY", "sk-test")
        monkeypatch.delenv("CUSTOM_ANTHROPIC_BASE_URL", raising=False)

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["custom-anthropic"]("test-model", dummy_messages, 0.7, 32)

        assert "CUSTOM_ANTHROPIC_BASE_URL" in str(exc_info.value)

    def test_custom_anthropic_missing_api_key(self, monkeypatch, dummy_messages):
        """Test Custom Anthropic API call fails without API key."""
        monkeypatch.delenv("CUSTOM_ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("CUSTOM_ANTHROPIC_BASE_URL", API_BASE_URL)

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["custom-anthropic"](
                model="claude-3-haiku-20240307",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "CUSTOM_ANTHROPIC_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(
        os.environ,
        {
            "CUSTOM_ANTHROPIC_API_KEY": API_KEY,
            "CUSTOM_ANTHROPIC_BASE_URL": API_BASE_URL,
            "CUSTOM_ANTHROPIC_VERSION": API_VERSION,
        },
    )
    def test_call_custom_anthropic_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Custom Anthropic API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["custom-anthropic"](
                model="claude-3-haiku-20240307",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Custom Anthropic" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(
        os.environ,
        {
            "CUSTOM_ANTHROPIC_API_KEY": API_KEY,
            "CUSTOM_ANTHROPIC_BASE_URL": API_BASE_URL,
            "CUSTOM_ANTHROPIC_VERSION": API_VERSION,
        },
    )
    def test_call_custom_anthropic_api_general_error(self, mock_post, dummy_messages):
        """Test Custom Anthropic API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            PROVIDER_REGISTRY["custom-anthropic"](
                model="claude-3-haiku-20240307",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Custom Anthropic" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(
        os.environ,
        {"CUSTOM_ANTHROPIC_API_KEY": API_KEY, "CUSTOM_ANTHROPIC_BASE_URL": API_BASE_URL},
        clear=True,
    )
    def test_call_custom_anthropic_api_default_version(
        self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper
    ):
        """Test Custom Anthropic API call with default version."""
        response_data = {"content": [{"text": "Test response"}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["custom-anthropic"](
            model="claude-3-haiku-20240307",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        headers = api_test_helper.extract_call_headers(mock_post)
        # Should default to "2023-06-01"
        assert headers["anthropic-version"] == "2023-06-01"

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(
        os.environ,
        {
            "CUSTOM_ANTHROPIC_API_KEY": API_KEY,
            "CUSTOM_ANTHROPIC_BASE_URL": API_BASE_URL,
            "CUSTOM_ANTHROPIC_VERSION": API_VERSION,
        },
    )
    def test_call_custom_anthropic_api_with_conversation(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Custom Anthropic API call with full conversation history."""
        response_data = {"content": [{"text": "Test response"}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = PROVIDER_REGISTRY["custom-anthropic"](
            model="claude-3-haiku-20240307",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 3

    @pytest.mark.integration
    @pytest.mark.skipif(
        not all(os.getenv(k) for k in ["CUSTOM_ANTHROPIC_API_KEY", "CUSTOM_ANTHROPIC_BASE_URL"]),
        reason="Custom Anthropic environment variables not set",
    )
    def test_custom_anthropic_provider_integration(self):
        """Test Custom Anthropic provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'custom anthropic test success'",
            }
        ]

        result = PROVIDER_REGISTRY["custom-anthropic"](
            model="claude-3-haiku-20240307",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
