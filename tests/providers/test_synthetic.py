"""Tests for Synthetic provider."""

import os
from unittest.mock import Mock, patch

import pytest

from kittylog.errors import AIError
from kittylog.providers.synthetic import call_synthetic_api

_DUMMY_MESSAGES = [{"role": "user", "content": "test"}]


class TestSyntheticProvider:
    """Test Synthetic provider functionality."""

    @patch("kittylog.providers.synthetic.httpx.post")
    def test_call_synthetic_api_success(self, mock_post):
        """Test successful Synthetic API call."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        result = call_synthetic_api(
            model="gpt-4",
            messages=_DUMMY_MESSAGES,
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "Test response"
        mock_post.assert_called_once()

        # Verify call arguments
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.synthetic.ai/v1/chat/completions"
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert "Bearer test-key" in headers["Authorization"]
        
        data = call_args[1]["json"]
        assert data["model"] == "gpt-4"
        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 100

    def test_call_synthetic_api_missing_api_key(self, monkeypatch):
        """Ensure Synthetic provider fails fast when API keys are missing."""
        monkeypatch.delenv("SYNTHETIC_API_KEY", raising=False)
        # Also check legacy SY_API_KEY
        monkeypatch.delenv("SY_API_KEY", raising=False)

        with pytest.raises(AIError) as exc_info:
            call_synthetic_api("test-model", _DUMMY_MESSAGES, 0.7, 32)

        assert "SYNTHETIC_API_KEY" in str(exc_info.value) or "SY_API_KEY" in str(exc_info.value)

    def test_call_synthetic_api_legacy_api_key_support(self, monkeypatch):
        """Test Synthetic provider supports legacy SY_API_KEY."""
        monkeypatch.delenv("SYNTHETIC_API_KEY", raising=False)
        monkeypatch.setenv("SY_API_KEY", "test-legacy-key")

        with patch("kittylog.providers.synthetic.httpx.post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test response"}}]
            }
            mock_post.return_value = mock_response

            result = call_synthetic_api(
                model="gpt-4",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

            assert result == "Test response"
            
            call_args = mock_post.call_args
            headers = call_args[1]["headers"]
            assert "Bearer test-legacy-key" in headers["Authorization"]

    @patch("kittylog.providers.synthetic.httpx.post")
    def test_call_synthetic_api_http_error(self, mock_post):
        """Test Synthetic API call handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 429")
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"SYNTHETIC_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_synthetic_api(
                    model="gpt-4",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Synthetic API error" in str(exc_info.value) or "Error calling Synthetic API" in str(exc_info.value)

    @patch("kittylog.providers.synthetic.httpx.post")
    def test_call_synthetic_api_general_error(self, mock_post):
        """Test Synthetic API call handles general errors."""
        mock_post.side_effect = Exception("Connection failed")

        with patch.dict(os.environ, {"SYNTHETIC_API_KEY": "test-key"}):
            with pytest.raises(AIError) as exc_info:
                call_synthetic_api(
                    model="gpt-4",
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )

        assert "Error calling Synthetic API" in str(exc_info.value)

    @pytest.mark.skipif(
        not any(os.getenv(k) for k in ["SYNTHETIC_API_KEY", "SY_API_KEY"]), 
        reason="Synthetic API key not set"
    )
    def test_synthetic_provider_integration(self):
        """Test Synthetic provider integration with real API."""
        messages = [
            {
                "role": "user",
                "content": "Reply with exactly: 'synthetic test success'",
            }
        ]

        result = call_synthetic_api(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=100,
        )

        assert len(result) > 0  # Any response is considered success

    @patch("kittylog.providers.synthetic.httpx.post")
    def test_call_synthetic_api_with_system_message(self, mock_post):
        """Test Synthetic API call with system message."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        messages_with_system = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Test message"}
        ]

        with patch.dict(os.environ, {"SYNTHETIC_API_KEY": "test-key"}):
            result = call_synthetic_api(
                model="gpt-4",
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

    @patch("kittylog.providers.synthetic.httpx.post")
    def test_call_synthetic_api_with_conversation(self, mock_post):
        """Test Synthetic API call with full conversation history."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]

        with patch.dict(os.environ, {"SYNTHETIC_API_KEY": "test-key"}):
            result = call_synthetic_api(
                model="gpt-4",
                messages=conversation,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert len(data["messages"]) == 3
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][2]["role"] == "user"

    @patch("kittylog.providers.synthetic.httpx.post")
    def test_call_synthetic_api_different_models(self, mock_post):
        """Test Synthetic API call with different models."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        test_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "claude-3-haiku"]
        
        with patch.dict(os.environ, {"SYNTHETIC_API_KEY": "test-key"}):
            for model in test_models:
                result = call_synthetic_api(
                    model=model,
                    messages=_DUMMY_MESSAGES,
                    temperature=0.7,
                    max_tokens=100,
                )
                assert result == "Test response"
                
                call_args = mock_post.call_args
                data = call_args[1]["json"]
                assert data["model"] == model

    @patch("kittylog.providers.synthetic.httpx.post")
    def test_call_synthetic_api_priority_synthetic_key(self, mock_post):
        """Test Synthetic API prioritizes SYNTHETIC_API_KEY over SY_API_KEY."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "SYNTHETIC_API_KEY": "test-primary-key",
            "SY_API_KEY": "test-legacy-key"
        }):
            result = call_synthetic_api(
                model="gpt-4",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

            assert result == "Test response"
            
            call_args = mock_post.call_args
            headers = call_args[1]["headers"]
            # Should prioritize SYNTHETIC_API_KEY
            assert "Bearer test-primary-key" in headers["Authorization"]
            assert "test-legacy-key" not in str(headers)

    @patch("kittylog.providers.synthetic.httpx.post")
    def test_call_synthetic_api_with_json_mode(self, mock_post):
        """Test Synthetic API call with JSON mode."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"result": "test"}'}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"SYNTHETIC_API_KEY": "test-key"}):
            result = call_synthetic_api(
                model="gpt-4",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
                response_format={"type": "json_object"}
            )

        assert result == '{"result": "test"}'
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert data["response_format"] == {"type": "json_object"}

    @patch("kittylog.providers.synthetic.httpx.post")
    def test_call_synthetic_api_with_stream(self, mock_post):
        """Test Synthetic API call with streaming."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"SYNTHETIC_API_KEY": "test-key"}):
            result = call_synthetic_api(
                model="gpt-4",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
                stream=False  # Explicitly set to False for testing
            )

        assert result == "Test response"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert "stream" not in data or data.get("stream") is False

    @patch("kittylog.providers.synthetic.httpx.post")
    def test_call_synthetic_api_empty_response(self, mock_post):
        """Test Synthetic API call handles empty response."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": ""}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"SYNTHETIC_API_KEY": "test-key"}):
            result = call_synthetic_api(
                model="gpt-4",
                messages=_DUMMY_MESSAGES,
                temperature=0.7,
                max_tokens=100,
            )

        assert result == ""  # Empty string should be returned
