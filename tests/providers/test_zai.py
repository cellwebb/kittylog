"""Tests for Z.AI provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.zai import call_zai_api, call_zai_coding_api


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
    def test_call_zai_coding_api_endpoint(self, mock_post):
        """Test Z.AI coding API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": "Coding response"}}]}
        mock_post.return_value = mock_response

        result = call_zai_coding_api(
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

    def test_call_zai_coding_api_no_api_key(self):
        """Test error when API key is missing for coding API."""
        # Remove API key from environment
        original_key = os.environ.get("ZAI_API_KEY")
        if "ZAI_API_KEY" in os.environ:
            del os.environ["ZAI_API_KEY"]

        try:
            with pytest.raises(AIError) as exc_info:
                call_zai_coding_api(
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

    def test_call_zai_api_missing_api_key_clean(self, monkeypatch):
        """Test Z.AI API call fails without API key using monkeypatch."""
        monkeypatch.delenv("ZAI_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_zai_api(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )

        assert "ZAI_API_KEY not found" in str(exc_info.value)

    def test_call_zai_coding_api_missing_api_key_clean(self, monkeypatch):
        """Test Z.AI coding API call fails without API key using monkeypatch."""
        monkeypatch.delenv("ZAI_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_zai_coding_api(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )

        assert "ZAI_API_KEY not found" in str(exc_info.value)

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_api_http_error(self, mock_post):
        """Test Z.AI API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_zai_api(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "Test"}],
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Z.AI API error" in str(exc_info.value) or "Error calling Z.AI API" in str(exc_info.value)

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_api_general_error(self, mock_post):
        """Test Z.AI API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_zai_api(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "Test"}],
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Error calling Z.AI API" in str(exc_info.value)

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_coding_api_http_error(self, mock_post):
        """Test Z.AI coding API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_zai_coding_api(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "Test"}],
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Z.AI coding API error" in str(exc_info.value) or "Error calling Z.AI coding API" in str(exc_info.value)

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_coding_api_general_error(self, mock_post):
        """Test Z.AI coding API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_zai_coding_api(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "Test"}],
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Error calling Z.AI coding API" in str(exc_info.value)

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
        assert "Z.AI API returned null content" in str(exc_info.value)

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_coding_api_null_content(self, mock_post):
        """Test handling of null content in coding API response."""
        # Mock response with null content
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": None}}]}
        mock_post.return_value = mock_response

        with pytest.raises(AIError) as exc_info:
            call_zai_coding_api(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )
        assert "Z.AI coding API returned null content" in str(exc_info.value)

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
        assert "Z.AI API returned empty content" in str(exc_info.value)

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_coding_api_empty_content(self, mock_post):
        """Test handling of empty content in coding API response."""
        # Mock response with empty content
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": ""}}]}
        mock_post.return_value = mock_response

        with pytest.raises(AIError) as exc_info:
            call_zai_coding_api(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )
        assert "Z.AI coding API returned empty content" in str(exc_info.value)

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
        assert "Z.AI API unexpected response structure" in str(exc_info.value)

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_coding_api_malformed_response(self, mock_post):
        """Test handling of malformed response for coding API."""
        # Mock response with missing choices
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": "no choices"}
        mock_post.return_value = mock_response

        with pytest.raises(AIError) as exc_info:
            call_zai_coding_api(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.7,
                max_tokens=100,
            )
        assert "Z.AI coding API unexpected response structure" in str(exc_info.value)

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

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_api_with_system_message(self, mock_post):
        """Test Z.AI API call with system message."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_response

        messages_with_system = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Test message"}
        ]

        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
            result = call_zai_api(
                model="gpt-4o",
                messages=messages_with_system,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "system"
        assert data["messages"][1]["role"] == "user"

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_coding_api_with_system_message(self, mock_post):
        """Test Z.AI coding API call with system message."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": "Coding response"}}]}
        mock_post.return_value = mock_response

        messages_with_system = [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": "Test message"}
        ]

        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
            result = call_zai_coding_api(
                model="gpt-4o",
                messages=messages_with_system,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Coding response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "system"
        assert data["messages"][1]["role"] == "user"

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_api_different_models(self, mock_post):
        """Test Z.AI API call with different models."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": "Test response"}}]}
        mock_post.return_value = mock_response

        test_models = ["gpt-4o", "gpt-4", "claude-3-sonnet"]
        
        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
            for model in test_models:
                result = call_zai_api(
                    model=model,
                    messages=[{"role": "user", "content": "Test"}],
                    temperature=0.7,
                    max_tokens=100,
                )
                assert result == "Test response"
                
                call_args = mock_post.call_args
                data = call_args[1]["json"]
                assert data["model"] == model

    @patch("kittylog.providers.zai.httpx.post")
    def test_call_zai_coding_api_different_models(self, mock_post):
        """Test Z.AI coding API call with different models."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": "Coding response"}}]}
        mock_post.return_value = mock_response

        test_models = ["gpt-4o", "gpt-4", "claude-3-sonnet"]
        
        with patch.dict(os.environ, {"ZAI_API_KEY": "test-key"}):
            for model in test_models:
                result = call_zai_coding_api(
                    model=model,
                    messages=[{"role": "user", "content": "Test"}],
                    temperature=0.7,
                    max_tokens=100,
                )
                assert result == "Coding response"
                
                call_args = mock_post.call_args
                data = call_args[1]["json"]
                assert data["model"] == model
