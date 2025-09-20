"""Tests for error classes and error handling."""

import pytest

from clog.errors import (
    AIError,
    ChangelogError,
    ChangelogUpdaterError,
    ConfigError,
    GitError,
)


class TestChangelogUpdaterError:
    """Test base ChangelogUpdaterError class."""

    def test_base_error_creation(self):
        """Test creating base error."""
        error = ChangelogUpdaterError("Base error message")
        assert str(error) == "Base error message"
        assert isinstance(error, Exception)

    def test_base_error_inheritance(self):
        """Test that base error is properly inherited."""
        error = ChangelogUpdaterError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, ChangelogUpdaterError)


class TestGitError:
    """Test GitError class."""

    def test_git_error_creation(self):
        """Test creating git error."""
        error = GitError("Not a git repository")
        assert str(error) == "Not a git repository"
        assert isinstance(error, ChangelogUpdaterError)
        assert isinstance(error, GitError)

    def test_git_error_with_details(self):
        """Test git error with additional details."""
        error = GitError("Git command failed", command="git status")
        assert str(error) == "Git command failed"
        assert error.command == "git status"

    def test_git_error_inheritance(self):
        """Test git error inheritance chain."""
        error = GitError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, ChangelogUpdaterError)
        assert isinstance(error, GitError)


class TestAIError:
    """Test AIError class."""

    def test_ai_error_basic(self):
        """Test creating basic AI error."""
        error = AIError("API key invalid")
        assert str(error) == "API key invalid"
        assert error.error_type == "unknown"
        assert isinstance(error, ChangelogUpdaterError)

    def test_ai_error_with_type(self):
        """Test creating AI error with error type."""
        error = AIError("Authentication failed", error_type="authentication")
        assert str(error) == "Authentication failed"
        assert error.error_type == "authentication"

    def test_ai_error_with_details(self):
        """Test AI error with additional details."""
        error = AIError("Rate limit exceeded", error_type="rate_limit", model="gpt-4", retry_after=60)
        assert str(error) == "Rate limit exceeded"
        assert error.error_type == "rate_limit"
        assert error.model == "gpt-4"
        assert error.retry_after == 60

    def test_ai_error_types(self):
        """Test different AI error types."""
        error_types = [
            "authentication",
            "rate_limit",
            "model_not_found",
            "context_length",
            "timeout",
            "unknown",
        ]

        for error_type in error_types:
            error = AIError("Test error", error_type=error_type)
            assert error.error_type == error_type

    def test_ai_error_inheritance(self):
        """Test AI error inheritance chain."""
        error = AIError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, ChangelogUpdaterError)
        assert isinstance(error, AIError)


class TestChangelogError:
    """Test ChangelogError class."""

    def test_changelog_error_creation(self):
        """Test creating changelog error."""
        error = ChangelogError("Failed to parse changelog")
        assert str(error) == "Failed to parse changelog"
        assert isinstance(error, ChangelogUpdaterError)

    def test_changelog_error_with_file_path(self):
        """Test changelog error with file path."""
        error = ChangelogError("Permission denied", file_path="/path/to/CHANGELOG.md")
        assert str(error) == "Permission denied"
        assert error.file_path == "/path/to/CHANGELOG.md"

    def test_changelog_error_with_line_number(self):
        """Test changelog error with line number."""
        error = ChangelogError("Invalid format", file_path="CHANGELOG.md", line_number=42)
        assert str(error) == "Invalid format"
        assert error.file_path == "CHANGELOG.md"
        assert error.line_number == 42

    def test_changelog_error_inheritance(self):
        """Test changelog error inheritance chain."""
        error = ChangelogError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, ChangelogUpdaterError)
        assert isinstance(error, ChangelogError)


class TestConfigError:
    """Test ConfigError class."""

    def test_config_error_creation(self):
        """Test creating config error."""
        error = ConfigError("Invalid configuration")
        assert str(error) == "Invalid configuration"
        assert isinstance(error, ChangelogUpdaterError)

    def test_config_error_with_key(self):
        """Test config error with configuration key."""
        error = ConfigError("Invalid temperature value", config_key="temperature")
        assert str(error) == "Invalid temperature value"
        assert error.config_key == "temperature"

    def test_config_error_with_value(self):
        """Test config error with configuration value."""
        error = ConfigError("Temperature must be between 0 and 2", config_key="temperature", config_value=5.0)
        assert str(error) == "Temperature must be between 0 and 2"
        assert error.config_key == "temperature"
        assert error.config_value == 5.0

    def test_config_error_inheritance(self):
        """Test config error inheritance chain."""
        error = ConfigError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, ChangelogUpdaterError)
        assert isinstance(error, ConfigError)


class TestErrorChaining:
    """Test error chaining and cause tracking."""

    def test_error_with_cause(self):
        """Test creating error with underlying cause."""
        original_error = ValueError("Original error")

        try:
            raise original_error
        except ValueError as e:
            git_error = GitError("Git operation failed")
            git_error.__cause__ = e
            git_error.__cause__ = original_error

        assert str(git_error) == "Git operation failed"
        assert git_error.__cause__ is original_error

    def test_nested_error_chain(self):
        """Test nested error chain."""
        original = FileNotFoundError("File not found")

        try:
            raise original
        except FileNotFoundError as e:
            changelog_error = ChangelogError("Cannot read changelog")
            changelog_error.__cause__ = e

        try:
            raise changelog_error
        except ChangelogError as e:
            git_error = GitError("Git status failed")
            git_error.__cause__ = e

        assert git_error.__cause__ is changelog_error
        assert changelog_error.__cause__ is original


class TestErrorAttributes:
    """Test error attributes and properties."""

    def test_ai_error_attributes(self):
        """Test AI error attributes are properly stored."""
        error = AIError(
            "Complex AI error",
            error_type="rate_limit",
            model="gpt-4",
            retry_after=120,
            tokens_used=1500,
            max_tokens=2000,
        )

        assert error.error_type == "rate_limit"
        assert error.model == "gpt-4"
        assert error.retry_after == 120
        assert error.tokens_used == 1500
        assert error.max_tokens == 2000

    def test_git_error_attributes(self):
        """Test Git error attributes are properly stored."""
        error = GitError(
            "Git command failed",
            command="git log --oneline",
            exit_code=128,
            stdout="",
            stderr="fatal: not a git repository",
        )

        assert error.command == "git log --oneline"
        assert error.exit_code == 128
        assert error.stdout == ""
        assert error.stderr == "fatal: not a git repository"

    def test_changelog_error_attributes(self):
        """Test Changelog error attributes are properly stored."""
        error = ChangelogError(
            "Parse error",
            file_path="/path/to/CHANGELOG.md",
            line_number=15,
            line_content="## [Invalid Version Format",
            expected_format="## [X.Y.Z] - YYYY-MM-DD",
        )

        assert error.file_path == "/path/to/CHANGELOG.md"
        assert error.line_number == 15
        assert error.line_content == "## [Invalid Version Format"
        assert error.expected_format == "## [X.Y.Z] - YYYY-MM-DD"


class TestErrorStringRepresentation:
    """Test error string representation."""

    def test_error_str_basic(self):
        """Test basic error string representation."""
        error = GitError("Simple error message")
        assert str(error) == "Simple error message"

    def test_error_repr(self):
        """Test error repr representation."""
        error = GitError("Simple error message")
        repr_str = repr(error)
        assert "GitError" in repr_str
        assert "Simple error message" in repr_str

    def test_ai_error_detailed_str(self):
        """Test AI error with detailed information."""
        error = AIError("Rate limit exceeded", error_type="rate_limit", model="gpt-4")

        # Basic string should be clean
        assert str(error) == "Rate limit exceeded"

        # But attributes should be accessible
        assert error.error_type == "rate_limit"
        assert error.model == "gpt-4"


class TestErrorUsagePatterns:
    """Test common error usage patterns."""

    def test_catch_specific_error(self):
        """Test catching specific error types."""

        def raise_git_error():
            raise GitError("Not a git repository")

        def raise_ai_error():
            raise AIError("API key invalid", "authentication")

        # Test catching GitError specifically
        with pytest.raises(GitError) as exc_info:
            raise_git_error()
        assert "Not a git repository" in str(exc_info.value)

        # Test catching AIError specifically
        with pytest.raises(AIError) as exc_info:
            raise_ai_error()
        assert exc_info.value.error_type == "authentication"

    def test_catch_base_error(self):
        """Test catching base ChangelogUpdaterError."""

        def raise_various_errors(error_type):
            if error_type == "git":
                raise GitError("Git error")
            elif error_type == "ai":
                raise AIError("AI error")
            elif error_type == "changelog":
                raise ChangelogError("Changelog error")
            elif error_type == "config":
                raise ConfigError("Config error")

        for error_type in ["git", "ai", "changelog", "config"]:
            with pytest.raises(ChangelogUpdaterError):
                raise_various_errors(error_type)

    def test_error_handling_in_try_except(self):
        """Test error handling in try-except blocks."""

        def problematic_function():
            raise AIError("Rate limit", "rate_limit")

        try:
            problematic_function()
        except AIError as e:
            assert e.error_type == "rate_limit"
            assert str(e) == "Rate limit"
        except ChangelogUpdaterError:
            pytest.fail("Should have caught AIError specifically")
        except Exception:
            pytest.fail("Should have caught ChangelogUpdaterError family")
