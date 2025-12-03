"""Tests for Azure OpenAI provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.azure_openai import call_azure_openai_api


class TestAzureOpenAIProvider:
    """Test Azure OpenAI provider functionality."""

    @patch("kittylog.providers.azure_openai.httpx.post")
    def test_call_azure_openai_api_success(self, mock_post):
        """Test successful Azure OpenAI API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        # Set required environment variables
        with patch.dict(os.environ, {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_DEPLOYMENT": "test-deployment"
        }):
            result = call_azure_openai_api(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "System message"},
                    {"role": "user", "content": "Test message"}
                ],
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert "https://test.openai.azure.com" in call_args[0][0]
        assert "test-deployment" in call_args[0][0]
        headers = call_args[1]["headers"]
        assert "api-key" in headers
        assert headers["api-key"] == "test-key"

    def test_call_azure_openai_api_missing_api_key(self, monkeypatch):
        """Test Azure OpenAI API call fails without API key."""
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_azure_openai_api(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )

        assert "AZURE_OPENAI_API_KEY not found" in str(exc_info.value)

    def test_call_azure_openai_api_missing_endpoint(self, monkeypatch):
        """Test Azure OpenAI API call fails without endpoint."""
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_azure_openai_api(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )

        assert "AZURE_OPENAI_ENDPOINT not found" in str(exc_info.value)

    def test_call_azure_openai_api_missing_deployment(self, monkeypatch):
        """Test Azure OpenAI API call fails without deployment name."""
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
        monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_azure_openai_api(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )

        assert "AZURE_OPENAI_DEPLOYMENT not found" in str(exc_info.value)

    @patch("kittylog.providers.azure_openai.httpx.post")
    def test_call_azure_openai_api_http_error(self, mock_post):
        """Test Azure OpenAI API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_DEPLOYMENT": "test-deployment"
        }):
            with pytest.raises(AIError) as exc_info:
                call_azure_openai_api(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "Test"}],
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Azure OpenAI API error" in str(exc_info.value)

    @pytest.mark.skipif(
        not all(os.getenv(k) for k in ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]),
        reason="Azure OpenAI environment variables not set"
    )
    def test_azure_openai_provider_integration(self):
        """Test Azure OpenAI provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'azure openai test success'",
            }
        ]

        result = call_azure_openai_api(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success
