"""Tests for OpenAI provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.openai import call_openai_api

API_KEY = "test-key"
API_ENDPOINT = "https://api.openai.com/v1/chat/completions"


class TestOpenAIProvider:
    """Test OpenAI provider functionality."""

    @patch("kittylog.providers.openai.httpx.post")
    @patch.dict(os.environ, {"OPENAI_API_KEY": API_KEY})
    def test_call_openai_api_success(self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper):
        """Test successful OpenAI API call."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_openai_api(
            model="gpt-4",
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
        assert data["model"] == "gpt-4"
        assert data["temperature"] == 0.7
        assert data["max_completion_tokens"] == 100

    def test_call_openai_api_missing_api_key(self, monkeypatch, dummy_messages):
        """Ensure OpenAI provider fails fast when API keys are missing."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_openai_api("test-model", dummy_messages, 0.7, 32)

        assert "OPENAI_API_KEY" in str(exc_info.value)

    @patch("kittylog.providers.openai.httpx.post")
    @patch.dict(os.environ, {"OPENAI_API_KEY": API_KEY})
    def test_call_openai_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test OpenAI API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            call_openai_api(
                model="gpt-4",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Error calling OpenAI API" in str(exc_info.value)

    @patch("kittylog.providers.openai.httpx.post")
    @patch.dict(os.environ, {"OPENAI_API_KEY": API_KEY})
    def test_call_openai_api_general_error(self, mock_post, dummy_messages):
        """Test OpenAI API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            call_openai_api(
                model="gpt-4",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Error calling OpenAI API" in str(exc_info.value)

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
    def test_openai_provider_integration(self):
        """Test OpenAI provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'openai test success'",
            }
        ]

        result = call_openai_api(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @patch("kittylog.providers.openai.httpx.post")
    @patch.dict(os.environ, {"OPENAI_API_KEY": API_KEY})
    def test_call_openai_api_with_system_message(
        self, mock_post, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test OpenAI API call with system message."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_openai_api(
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

    @patch("kittylog.providers.openai.httpx.post")
    @patch.dict(os.environ, {"OPENAI_API_KEY": API_KEY})
    def test_call_openai_api_with_conversation(
        self, mock_post, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test OpenAI API call with full conversation history."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_openai_api(
            model="gpt-4",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        assert len(data["messages"]) == 3

    @patch("kittylog.providers.openai.httpx.post")
    @patch.dict(os.environ, {"OPENAI_API_KEY": API_KEY})
    def test_call_openai_api_different_models(
        self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper, openai_models
    ):
        """Test OpenAI API call with different models."""
        response_data = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        for model in openai_models:
            result = call_openai_api(
                model=model,
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )
            assert result == "Test response"

            data = api_test_helper.extract_call_data(mock_post)
            assert data["model"] == model

    @patch("kittylog.providers.openai.httpx.post")
    @patch.dict(os.environ, {"OPENAI_API_KEY": API_KEY})
    def test_call_openai_api_with_json_mode(
        self, mock_post, dummy_messages, mock_http_response_factory, api_test_helper
    ):
        """Test OpenAI API call with JSON mode."""
        response_data = {"choices": [{"message": {"content": '{"result": "test"}'}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_openai_api(
            model="gpt-4",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
            response_format={"type": "json_object"},
        )

        assert result == '{"result": "test"}'

        data = api_test_helper.extract_call_data(mock_post)
        assert data["response_format"] == {"type": "json_object"}

    @patch("kittylog.providers.openai.httpx.post")
    @patch.dict(os.environ, {"OPENAI_API_KEY": API_KEY})
    def test_call_openai_api_empty_response(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test OpenAI API call handles empty response."""
        response_data = {"choices": [{"message": {"content": ""}}]}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        result = call_openai_api(
            model="gpt-4",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == ""  # Empty string should be returned

    @patch("kittylog.providers.openai.httpx.post")
    @patch.dict(os.environ, {"OPENAI_API_KEY": API_KEY})
    def test_call_openai_api_no_choices(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test OpenAI API call handles response with no choices."""
        response_data = {"choices": []}
        mock_post.return_value = mock_http_response_factory.create_success_response(response_data)

        with pytest.raises(AIError) as exc_info:
            call_openai_api(
                model="gpt-4",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Error calling OpenAI API" in str(exc_info.value)
