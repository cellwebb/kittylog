"""Tests for Replicate provider."""

import os
from unittest.mock import patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.replicate import call_replicate_api

API_KEY = "test-key"
API_ENDPOINT = "https://api.replicate.com/v1/predictions"


class TestReplicateProvider:
    """Test Replicate provider functionality."""

    @patch("kittylog.providers.replicate.httpx.get")
    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"REPLICATE_API_TOKEN": API_KEY})
    def test_call_replicate_api_success(
        self, mock_post, mock_get, dummy_messages, mock_http_response_factory, api_test_helper
    ):
        """Test successful Replicate API call."""
        # Mock prediction creation
        prediction_response = {"id": "test-prediction-id"}
        mock_post.return_value = mock_http_response_factory.create_success_response(prediction_response)

        # Mock status check
        status_response = {"status": "succeeded", "output": "Test response"}
        mock_get.return_value = mock_http_response_factory.create_success_response(status_response)

        result = call_replicate_api(
            model="meta/meta-llama-3-8b-instruct",
            messages=dummy_messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()
        mock_get.assert_called_once()

        # Verify call URL and headers
        url = api_test_helper.extract_call_url(mock_post)
        assert url == API_ENDPOINT

        headers = api_test_helper.extract_call_headers(mock_post)
        assert "Token test-key" in str(headers)
        assert headers["Content-Type"] == "application/json"

        # Verify request data structure
        data = api_test_helper.extract_call_data(mock_post)
        assert data["version"] == "meta/meta-llama-3-8b-instruct"
        assert data["input"]["temperature"] == 0.7
        assert data["input"]["max_tokens"] == 100
        assert "prompt" in data["input"]
        assert "Human: test" in data["input"]["prompt"]

    def test_call_replicate_api_missing_api_key(self, monkeypatch, dummy_messages):
        """Ensure Replicate provider fails fast when API keys are missing."""
        monkeypatch.delenv("REPLICATE_API_TOKEN", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_replicate_api("test-model", dummy_messages, 0.7, 32)

        assert "REPLICATE_API_TOKEN" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"REPLICATE_API_TOKEN": API_KEY})
    def test_call_replicate_api_http_error(self, mock_post, dummy_messages, mock_http_response_factory):
        """Test Replicate API call handles HTTP errors."""
        mock_post.return_value = mock_http_response_factory.create_error_response(
            status_code=429, error_message="Rate limit exceeded"
        )

        with pytest.raises(AIError) as exc_info:
            call_replicate_api(
                model="meta/meta-llama-3-8b-instruct",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Replicate API error" in str(exc_info.value) or "Replicate" in str(exc_info.value)

    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"REPLICATE_API_TOKEN": API_KEY})
    def test_call_replicate_api_general_error(self, mock_post, dummy_messages):
        """Test Replicate API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(AIError) as exc_info:
            call_replicate_api(
                model="meta/meta-llama-3-8b-instruct",
                messages=dummy_messages,
                temperature=0.7,
                max_tokens=100,
            )

        assert "Replicate" in str(exc_info.value)

    @patch("kittylog.providers.replicate.httpx.get")
    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"REPLICATE_API_TOKEN": API_KEY})
    def test_call_replicate_api_with_system_message(
        self, mock_post, mock_get, dummy_messages_with_system, mock_http_response_factory, api_test_helper
    ):
        """Test Replicate API call with system message."""
        # Mock prediction creation
        prediction_response = {"id": "test-prediction-id"}
        mock_post.return_value = mock_http_response_factory.create_success_response(prediction_response)

        # Mock status check
        status_response = {"status": "succeeded", "output": "Test response"}
        mock_get.return_value = mock_http_response_factory.create_success_response(status_response)

        result = call_replicate_api(
            model="meta/meta-llama-3-8b-instruct",
            messages=dummy_messages_with_system,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        prompt = data["input"]["prompt"]
        assert "System: You are a helpful assistant." in prompt
        assert "Human: Test message" in prompt
        assert "Assistant:" in prompt

    @patch("kittylog.providers.replicate.httpx.get")
    @patch("kittylog.providers.base.httpx.post")
    @patch.dict(os.environ, {"REPLICATE_API_TOKEN": API_KEY})
    def test_call_replicate_api_with_conversation(
        self, mock_post, mock_get, dummy_conversation, mock_http_response_factory, api_test_helper
    ):
        """Test Replicate API call with full conversation history."""
        # Mock prediction creation
        prediction_response = {"id": "test-prediction-id"}
        mock_post.return_value = mock_http_response_factory.create_success_response(prediction_response)

        # Mock status check
        status_response = {"status": "succeeded", "output": "Test response"}
        mock_get.return_value = mock_http_response_factory.create_success_response(status_response)

        result = call_replicate_api(
            model="meta/meta-llama-3-8b-instruct",
            messages=dummy_conversation,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"

        data = api_test_helper.extract_call_data(mock_post)
        prompt = data["input"]["prompt"]
        assert "Human: Hello" in prompt
        assert "Assistant: Hi there!" in prompt
        assert "Human: How are you?" in prompt

    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("REPLICATE_API_TOKEN"), reason="REPLICATE_API_TOKEN not set")
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
