"""Tests for Z.AI provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.zai import call_zai_api


class TestZAIProvider:
    """Test Z.AI provider functionality."""

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_api_regular_endpoint(self, mock_post):
        """Test Z.AI API call with regular endpoint."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_response

        # Ensure coding plan is disabled
        os.environ["KITTYLOG_ZAI_USE_CODING_PLAN"] = "false"

        result = call_zai_api(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Test"}],
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify regular endpoint was used
        call_args = mock_post.call_args
        assert "api.z.ai/api/paas/v4/chat/completions" in call_args[0][0]
        assert "coding" not in call_args[0][0]

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_api_coding_endpoint(self, mock_post):
        """Test Z.AI API call with coding endpoint."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": "Coding response"}}]}
        mock_post.return_value = mock_response

        # Enable coding plan
        os.environ["KITTYLOG_ZAI_USE_CODING_PLAN"] = "true"

        result = call_zai_api(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Test"}],
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Coding response"
        mock_post.assert_called_once()

        # Verify coding endpoint was used
        call_args = mock_post.call_args
        assert "api.z.ai/api/coding/paas/v4/chat/completions" in call_args[0][0]

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_api_coding_endpoint_various_values(self, mock_post):
        """Test Z.AI API call with coding endpoint enabled with various truthy values."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": "Coding response"}}]}
        mock_post.return_value = mock_response

        truthy_values = ["true", "1", "yes", "on"]

        for value in truthy_values:
            os.environ["KITTYLOG_ZAI_USE_CODING_PLAN"] = value

            result = call_zai_api(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )

            assert result == "Coding response"

            # Verify coding endpoint was used
            call_args = mock_post.call_args
            assert "api.z.ai/api/coding/paas/v4/chat/completions" in call_args[0][0]

    def test_call_zai_api_no_api_key(self):
        """Test error when API key is missing."""
        # Remove API key from environment
        original_key = os.environ.get("ZAI_API_KEY")
        if "ZAI_API_KEY" in os.environ:
            del os.environ["ZAI_API_KEY"]

        try:
            with pytest.raises(AIError) as exc_info:
                call_zai_api(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "Test"}],
                    temperature=0.7,
                    max_tokens=100,
                )
            assert "ZAI_API_KEY not found" in str(exc_info.value)
        finally:
            # Restore API key
            if original_key:
                os.environ["ZAI_API_KEY"] = original_key

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_api_null_content(self, mock_post):
        """Test handling of null content in response."""
        # Mock response with null content
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": None}}]}
        mock_post.return_value = mock_response

        with pytest.raises(AIError) as exc_info:
            call_zai_api(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )
        assert "returned null content" in str(exc_info.value)

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_api_empty_content(self, mock_post):
        """Test handling of empty content in response."""
        # Mock response with empty content
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": ""}}]}
        mock_post.return_value = mock_response

        with pytest.raises(AIError) as exc_info:
            call_zai_api(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )
        assert "returned empty content" in str(exc_info.value)

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_api_malformed_response(self, mock_post):
        """Test handling of malformed response."""
        # Mock response with missing choices
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": "no choices"}
        mock_post.return_value = mock_response

        with pytest.raises(AIError) as exc_info:
            call_zai_api(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )
        assert "unexpected response structure" in str(exc_info.value)
