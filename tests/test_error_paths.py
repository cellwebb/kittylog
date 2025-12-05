"""Tests for error handling paths.

This module tests error scenarios that should be properly handled:
- Provider authentication failures
- Rate limiting
- Timeout handling
- Invalid config values
- Git operation failures
"""

from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest

from kittylog.errors import AIError, ConfigError, GitError


class TestProviderAuthenticationErrors:
    """Test provider authentication error handling."""

    def test_missing_api_key_raises_ai_error(self):
        """Test that missing API key raises AIError."""
        from kittylog.providers.anthropic import call_anthropic_api

        with (
            patch.dict("os.environ", {}, clear=True),
            patch("os.getenv", return_value=None),
            pytest.raises(AIError),
        ):
            call_anthropic_api(
                model="claude-3-haiku",
                messages=[{"role": "user", "content": "test"}],
                temperature=0.7,
                max_tokens=100,
            )

    def test_http_401_raises_auth_error(self):
        """Test that 401 HTTP response raises authentication error."""
        from kittylog.errors import AIError
        from kittylog.providers.error_handler import handle_provider_errors

        # Create a test function with the decorator
        @handle_provider_errors("TestProvider")
        def mock_api_call():
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            raise httpx.HTTPStatusError(
                "401 Unauthorized",
                request=Mock(),
                response=mock_response,
            )

        with pytest.raises(AIError) as exc_info:
            mock_api_call()
        assert exc_info.value.error_type == "authentication"


class TestRateLimitErrors:
    """Test rate limit error handling."""

    def test_http_429_raises_rate_limit_error(self):
        """Test that 429 HTTP response raises rate_limit error type."""
        from kittylog.providers.error_handler import handle_provider_errors

        @handle_provider_errors("TestProvider")
        def mock_api_call():
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            raise httpx.HTTPStatusError(
                "429 Too Many Requests",
                request=Mock(),
                response=mock_response,
            )

        with pytest.raises(AIError) as exc_info:
            mock_api_call()
        assert exc_info.value.error_type == "rate_limit"

    def test_rate_limit_error_includes_retry_info(self):
        """Test that rate limit errors include helpful retry information."""
        error = AIError.rate_limit_error("Rate limit exceeded. Retry after 60 seconds.")
        assert "rate limit" in str(error).lower() or "retry" in str(error).lower()


class TestTimeoutErrors:
    """Test timeout error handling."""

    def test_timeout_exception_raises_timeout_error(self):
        """Test that httpx TimeoutException raises timeout error type."""
        from kittylog.providers.error_handler import handle_provider_errors

        @handle_provider_errors("TestProvider")
        def mock_api_call():
            raise httpx.TimeoutException("Request timed out")

        with pytest.raises(AIError) as exc_info:
            mock_api_call()
        assert exc_info.value.error_type == "timeout"

    def test_connect_error_raises_connection_error(self):
        """Test that httpx ConnectError raises connection error."""
        from kittylog.providers.error_handler import handle_provider_errors

        @handle_provider_errors("TestProvider")
        def mock_api_call():
            raise httpx.ConnectError("Connection refused")

        with pytest.raises(AIError) as exc_info:
            mock_api_call()
        assert exc_info.value.error_type == "connection"


class TestConfigErrors:
    """Test configuration error handling."""

    def test_provider_registry_has_expected_providers(self):
        """Test that provider registry contains expected providers."""
        from kittylog.providers import PROVIDER_REGISTRY

        # Verify key providers exist
        assert "openai" in PROVIDER_REGISTRY
        assert "anthropic" in PROVIDER_REGISTRY
        assert "groq" in PROVIDER_REGISTRY

    def test_unknown_provider_not_in_registry(self):
        """Test that unknown provider name is not in registry."""
        from kittylog.providers import PROVIDER_REGISTRY

        # Verify unknown provider is not in registry
        assert "nonexistent-provider" not in PROVIDER_REGISTRY

    def test_empty_model_string_handled(self):
        """Test that empty model string is handled gracefully."""
        from kittylog.config.data import KittylogConfigData

        # Empty model should be allowed (will use defaults)
        config = KittylogConfigData(model="")
        assert config.model == ""

    def test_negative_temperature_allowed_in_config(self):
        """Test that temperature can be set to any float in config."""
        from kittylog.config.data import KittylogConfigData

        # Temperature can be set to any float - validation happens at provider level
        config = KittylogConfigData(temperature=-0.5)
        assert config.temperature == -0.5


class TestGitOperationErrors:
    """Test git operation error handling."""

    def test_not_git_repo_raises_git_error(self):
        """Test that operations outside git repo raise GitError."""
        import os
        import tempfile

        from kittylog.tag_operations import get_all_tags

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = str(Path.cwd())
            try:
                os.chdir(tmpdir)
                # Clear any cached repo
                from kittylog.tag_operations import clear_git_cache

                clear_git_cache()

                with pytest.raises(GitError):
                    get_all_tags()
            finally:
                os.chdir(original_cwd)

    def test_get_tag_date_returns_none_for_nonexistent(self):
        """Test that get_tag_date returns None for non-existent tags."""
        from kittylog.tag_operations import clear_git_cache, get_tag_date

        # Clear cache first
        clear_git_cache()

        with patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_repo = Mock()
            # Mock tags as a dict-like object that raises KeyError for missing tags
            mock_tags = Mock()
            mock_tags.__getitem__ = Mock(side_effect=KeyError("nonexistent-tag"))
            mock_repo.tags = mock_tags
            mock_get_repo.return_value = mock_repo

            # Should return None for non-existent tag, not raise
            result = get_tag_date("nonexistent-tag")
            assert result is None

    def test_get_commits_handles_invalid_range(self):
        """Test that get_commits handles invalid tag ranges gracefully."""
        from kittylog.commit_analyzer import clear_commit_analyzer_cache, get_commits_between_tags
        from kittylog.tag_operations import clear_git_cache

        # Clear all caches first
        clear_git_cache()
        clear_commit_analyzer_cache()

        # Mock at the source (tag_operations.get_repo is used by commit_analyzer)
        with patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_repo = Mock()
            mock_repo.tags = []
            # Also mock iter_commits to handle the case where we call it
            mock_repo.iter_commits.return_value = []
            mock_get_repo.return_value = mock_repo

            # Should handle gracefully - either return empty or raise GitError
            try:
                result = get_commits_between_tags("v1.0.0", "v2.0.0")
                # If it doesn't raise, it should return a list
                assert isinstance(result, list)
            except GitError:
                # GitError is acceptable for invalid range
                pass


class TestErrorFormatting:
    """Test error message formatting."""

    def test_ai_error_includes_error_type(self):
        """Test that AIError includes error_type attribute."""
        error = AIError.authentication_error("Invalid API key")
        assert hasattr(error, "error_type")
        assert error.error_type == "authentication"

    def test_ai_error_types(self):
        """Test all AIError factory methods produce correct types."""
        error_types = [
            ("authentication", AIError.authentication_error),
            ("connection", AIError.connection_error),
            ("rate_limit", AIError.rate_limit_error),
            ("timeout", AIError.timeout_error),
            ("model", AIError.model_error),
            ("generation", AIError.generation_error),
        ]

        for expected_type, factory in error_types:
            error = factory("Test message")
            assert error.error_type == expected_type, f"Expected {expected_type}, got {error.error_type}"

    def test_git_error_includes_command(self):
        """Test that GitError can include command information."""
        error = GitError("Git operation failed", command="git status")
        assert error.command == "git status"

    def test_config_error_includes_key(self):
        """Test that ConfigError can include config key."""
        error = ConfigError("Invalid value", config_key="model")
        assert error.config_key == "model"

    def test_error_string_representation(self):
        """Test that errors have useful string representations."""
        error = AIError.rate_limit_error("Too many requests")
        error_str = str(error)
        assert "Too many requests" in error_str


class TestErrorRecovery:
    """Test error recovery and retry behavior."""

    def test_classify_error_identifies_retryable(self):
        """Test that error classification identifies retryable errors."""
        from kittylog.errors import classify_error

        # Rate limit should be classified
        rate_limit_error = Exception("Rate limit exceeded")
        assert classify_error(rate_limit_error) == "rate_limit"

        # Timeout should be classified
        timeout_error = Exception("Request timeout")
        assert classify_error(timeout_error) == "timeout"

        # Auth error should be classified (not retryable)
        auth_error = Exception("API key invalid, unauthorized")
        assert classify_error(auth_error) == "authentication"

    def test_unknown_errors_classified_as_unknown(self):
        """Test that unknown errors are classified as unknown."""
        from kittylog.errors import classify_error

        unknown_error = Exception("Something weird happened")
        assert classify_error(unknown_error) == "unknown"
