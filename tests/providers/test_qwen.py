"""Tests for Qwen provider."""

from unittest import mock
from unittest.mock import MagicMock, patch

import httpx
import pytest

from kittylog.errors import AIError
from kittylog.providers import PROVIDER_REGISTRY


class TestQwenImports:
    """Test that Qwen provider can be imported."""

    def test_import_provider(self):
        """Test that Qwen provider module can be imported."""
        from kittylog.providers import qwen  # noqa: F401

    def test_import_api_function(self):
        """Test that Qwen API function is registered and callable."""
        from kittylog.providers import PROVIDER_REGISTRY

        assert "qwen" in PROVIDER_REGISTRY
        assert callable(PROVIDER_REGISTRY["qwen"])


class TestQwenOAuthValidation:
    """Test Qwen OAuth validation."""

    def test_missing_oauth_token_error(self):
        """Test that Qwen raises error when no OAuth token is available."""
        with patch("kittylog.providers.qwen.QwenOAuthProvider") as mock_provider_class:
            mock_provider = mock.Mock()
            mock_provider.get_token.return_value = None
            mock_provider_class.return_value = mock_provider

            with pytest.raises(AIError) as exc_info:
                PROVIDER_REGISTRY["qwen"]("qwen3-coder-plus", [], 0.7, 1000)

            assert exc_info.value.error_type == "authentication"


class TestCallQwenApi:
    """Tests for call_qwen_api function."""

    def test_successful_api_call(self):
        """Test successful API call with OAuth."""
        with (
            patch("kittylog.providers.qwen.QwenOAuthProvider") as mock_provider_class,
            patch("kittylog.providers.base.httpx.post") as mock_post,
        ):
            mock_oauth_provider = mock.Mock()
            mock_oauth_provider.get_token.return_value = {
                "access_token": "oauth_token_123",
                "resource_url": "portal.qwen.ai",
            }
            mock_provider_class.return_value = mock_oauth_provider

            mock_response = MagicMock()
            mock_response.json.return_value = {"choices": [{"message": {"content": "Test response"}}]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            result = PROVIDER_REGISTRY["qwen"](
                model="qwen3-coder-plus",
                messages=[{"role": "user", "content": "Hello"}],
                temperature=0.7,
                max_tokens=100,
            )

            assert result == "Test response"
            mock_post.assert_called_once()

            # Verify OAuth token was used
            call_args = mock_post.call_args
            headers = call_args.kwargs["headers"]
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer oauth_token_123"

    def test_dynamic_resource_url(self):
        """Test Qwen OAuth with dynamic resource URL."""
        with (
            patch("kittylog.providers.qwen.QwenOAuthProvider") as mock_provider_class,
            patch("kittylog.providers.base.httpx.post") as mock_post,
        ):
            mock_oauth_provider = mock.Mock()
            mock_oauth_provider.get_token.return_value = {
                "access_token": "oauth_token",
                "resource_url": "custom.qwen.ai",
            }
            mock_provider_class.return_value = mock_oauth_provider

            mock_response = MagicMock()
            mock_response.json.return_value = {"choices": [{"message": {"content": "test response"}}]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            result = PROVIDER_REGISTRY["qwen"]("qwen3-coder-plus", [], 0.7, 1000)

            # Verify custom URL was used
            call_args = mock_post.call_args
            url = call_args[0][0]
            assert url == "https://custom.qwen.ai/v1/chat/completions"
            assert result == "test response"

    def test_missing_choices_error(self):
        """Test handling of response without choices field."""
        with (
            patch("kittylog.providers.qwen.QwenOAuthProvider") as mock_provider_class,
            patch("kittylog.providers.base.httpx.post") as mock_post,
        ):
            mock_oauth_provider = mock.Mock()
            mock_oauth_provider.get_token.return_value = {
                "access_token": "test-oauth-token",
                "resource_url": "chat.qwen.ai",
            }
            mock_provider_class.return_value = mock_oauth_provider

            mock_response = MagicMock()
            mock_response.json.return_value = {"some_other_field": "value"}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with pytest.raises(AIError) as exc_info:
                PROVIDER_REGISTRY["qwen"]("qwen3-coder-plus", [], 0.7, 1000)

            assert "invalid response" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()

    def test_null_content_error(self):
        """Test error when API returns null content."""
        with (
            patch("kittylog.providers.qwen.QwenOAuthProvider") as mock_provider_class,
            patch("kittylog.providers.base.httpx.post") as mock_post,
        ):
            mock_oauth_provider = mock.Mock()
            mock_oauth_provider.get_token.return_value = {
                "access_token": "test-oauth-token",
                "resource_url": "chat.qwen.ai",
            }
            mock_provider_class.return_value = mock_oauth_provider

            mock_response = MagicMock()
            mock_response.json.return_value = {"choices": [{"message": {"content": None}}]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with pytest.raises(AIError) as exc_info:
                PROVIDER_REGISTRY["qwen"](
                    model="qwen3-coder-plus",
                    messages=[{"role": "user", "content": "Hello"}],
                    temperature=0.7,
                    max_tokens=100,
                )

            assert "missing" in str(exc_info.value).lower() or "content" in str(exc_info.value).lower()

    def test_empty_content_raises_error(self):
        """Test that API returning empty content raises an error."""
        with (
            patch("kittylog.providers.qwen.QwenOAuthProvider") as mock_provider_class,
            patch("kittylog.providers.base.httpx.post") as mock_post,
        ):
            mock_oauth_provider = mock.Mock()
            mock_oauth_provider.get_token.return_value = {
                "access_token": "test-oauth-token",
                "resource_url": "chat.qwen.ai",
            }
            mock_provider_class.return_value = mock_oauth_provider

            mock_response = MagicMock()
            mock_response.json.return_value = {"choices": [{"message": {"content": ""}}]}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            # Empty content should raise an error
            with pytest.raises(AIError) as exc_info:
                PROVIDER_REGISTRY["qwen"](
                    model="qwen3-coder-plus",
                    messages=[{"role": "user", "content": "Hello"}],
                    temperature=0.7,
                    max_tokens=100,
                )
            assert "empty content" in str(exc_info.value).lower()

    def test_authentication_error(self):
        """Test 401 authentication error."""
        with (
            patch("kittylog.providers.qwen.QwenOAuthProvider") as mock_provider_class,
            patch("kittylog.providers.base.httpx.post") as mock_post,
        ):
            mock_oauth_provider = mock.Mock()
            mock_oauth_provider.get_token.return_value = {
                "access_token": "test-oauth-token",
                "resource_url": "chat.qwen.ai",
            }
            mock_provider_class.return_value = mock_oauth_provider

            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized",
                request=mock.Mock(),
                response=mock_response,
            )
            mock_post.return_value = mock_response

            with pytest.raises(AIError):
                PROVIDER_REGISTRY["qwen"](
                    model="qwen3-coder-plus",
                    messages=[{"role": "user", "content": "Hello"}],
                    temperature=0.7,
                    max_tokens=100,
                )

    def test_rate_limit_error(self):
        """Test 429 rate limit error."""
        with (
            patch("kittylog.providers.qwen.QwenOAuthProvider") as mock_provider_class,
            patch("kittylog.providers.base.httpx.post") as mock_post,
        ):
            mock_oauth_provider = mock.Mock()
            mock_oauth_provider.get_token.return_value = {
                "access_token": "test-oauth-token",
                "resource_url": "chat.qwen.ai",
            }
            mock_provider_class.return_value = mock_oauth_provider

            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "429 Too Many Requests",
                request=mock.Mock(),
                response=mock_response,
            )
            mock_post.return_value = mock_response

            with pytest.raises(AIError) as exc_info:
                PROVIDER_REGISTRY["qwen"](
                    model="qwen3-coder-plus",
                    messages=[{"role": "user", "content": "Hello"}],
                    temperature=0.7,
                    max_tokens=100,
                )

            assert exc_info.value.error_type == "rate_limit"

    def test_timeout_error(self):
        """Test timeout error."""
        with (
            patch("kittylog.providers.qwen.QwenOAuthProvider") as mock_provider_class,
            patch("kittylog.providers.base.httpx.post") as mock_post,
        ):
            mock_oauth_provider = mock.Mock()
            mock_oauth_provider.get_token.return_value = {
                "access_token": "test-oauth-token",
                "resource_url": "chat.qwen.ai",
            }
            mock_provider_class.return_value = mock_oauth_provider

            mock_post.side_effect = httpx.TimeoutException("Request timed out")

            with pytest.raises(AIError) as exc_info:
                PROVIDER_REGISTRY["qwen"](
                    model="qwen3-coder-plus",
                    messages=[{"role": "user", "content": "Hello"}],
                    temperature=0.7,
                    max_tokens=100,
                )

            assert exc_info.value.error_type == "timeout"
