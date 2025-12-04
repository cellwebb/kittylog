"""Tests for Z.AI provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.zai import call_zai_api, call_zai_coding_api

API_KEY = "test-key"
API_ENDPOINT = "https://api.z.ai/api/paas/v4/chat/completions"
API_CODING_ENDPOINT = "https://api.z.ai/api/coding/paas/v4/chat/completions"


class TestZAIProvider:
    """Test Z.AI provider functionality."""

    @patch("kittylog.providers.base_configured.httpx.post")
    @patch.dict(os.environ, {"ZAI_API_KEY": API_KEY})
    def test_call_zai_api_regular_endpoint(
        self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper
    ):
        """Test Z.AI API call with regular endpoint."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_zai_api(
            model="gpt-4o",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify regular endpoint was used
        url = api_test_helper.extract_call_url(mock_post)
        assert url == API_ENDPOINT

    @patch("kittylog.providers.base_configured.httpx.post")
    @patch.dict(os.environ, {"ZAI_API_KEY": API_KEY})
    def test_call_zai_coding_api_endpoint(self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper):
        """Test Z.AI coding API call."""
        response_data = {"choices": [{"message": {"content": "Coding response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_zai_coding_api(
            model="gpt-4o",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Coding response"
        mock_post.assert_called_once()

        # Verify coding endpoint was used
        url = api_test_helper.extract_call_url(mock_post)
        assert url == API_CODING_ENDPOINT

    def test_call_zai_api_missing_api_key(self, monkeypatch, dummy_messages):
        """Test error when API key is missing."""
        monkeypatch.delenv("ZAI_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_zai_api("gpt-4o", dummy_messages, 0.7, 100)

        assert "ZAI_API_KEY" in str(exc_info.value)

    def test_call_zai_coding_api_missing_api_key(self, monkeypatch, dummy_messages):
        """Test error when API key is missing for coding endpoint."""
        monkeypatch.delenv("ZAI_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_zai_coding_api("gpt-4o", dummy_messages, 0.7, 100)

        assert "ZAI_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.base_configured.httpx.post")
    @patch.dict(os.environ, {"ZAI_API_KEY": API_KEY})
    def test_call_zai_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Z.AI API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            call_zai_api(
                model="gpt-4o",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Z.AI API error" in str(exc_info.value) or "Error calling Z.AI API" in str(exc_info.value)

    @patch("kittylog.providers.base_configured.httpx.post")
    @patch.dict(os.environ, {"ZAI_API_KEY": API_KEY})
    def test_call_zai_api_general_error(self, mock_post, dummy_messages):
        """Test Z.AI API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            call_zai_api(
                model="gpt-4o",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Error calling Z.AI API" in str(exc_info.value)

    @patch("kittylog.providers.base_configured.httpx.post")
    @patch.dict(os.environ, {"ZAI_API_KEY": API_KEY})
    def test_call_zai_api_with_system_message(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test Z.AI API call with system message."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_zai_api(
            model="gpt-4o",
            messages=dummy_messages_with_system,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "system"
        assert data["messages"][1]["role"] == "user"

    @patch("kittylog.providers.base_configured.httpx.post")
    @patch.dict(os.environ, {"ZAI_API_KEY": API_KEY})
    def test_call_zai_api_with_conversation(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Z.AI API call with full conversation history."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_zai_api(
            model="gpt-4o",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 3

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("ZAI_API_KEY"), reason="ZAI_API_KEY not set")
    def test_zai_provider_integration(self):
        """Test Z.AI provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'zai test success'",
            }
        ]

        result = call_zai_api(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("ZAI_API_KEY"), reason="ZAI_API_KEY not set")
    def test_zai_coding_provider_integration(self):
        """Test Z.AI coding provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'zai coding test success'",
            }
        ]

        result = call_zai_coding_api(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
