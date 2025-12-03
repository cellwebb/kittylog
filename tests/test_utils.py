"""Tests for utility functions."""

from datetime import datetime
from unittest.mock import patch

from kittylog.utils import (
    clean_changelog_content,
    count_tokens,
    format_commit_for_display,
    is_semantic_version,
    normalize_tag,
    setup_logging,
    truncate_text,
)


class TestCountTokens:
    """Test count_tokens function with character-based estimation."""

    def test_count_tokens_success(self):
        """Test token counting with GPT model."""
        # Implementation uses len(text) // chars_per_token, max(1, ...)
        # For GPT models, chars_per_token = 4
        text = "test text here"  # 14 characters -> 14 // 4 = 3
        count = count_tokens(text, "gpt-4")
        assert count == max(1, len(text) // 4)

    def test_count_tokens_fallback_encoding(self):
        """Test token counting with different model types."""
        text = "test text here"  # 14 characters
        # Claude model uses chars_per_token = 3.5 -> 14 // 3.5 = 4
        count_claude = count_tokens(text, "claude-3-opus")
        count_gpt = count_tokens(text, "gpt-4")

        # Claude should have slightly higher count due to smaller chars_per_token
        assert count_claude >= count_gpt

    def test_count_tokens_error_handling(self):
        """Test token counting returns minimum of 1."""
        # Short text should return at least 1
        count = count_tokens("hi", "gpt-4")  # 2 chars // 4 = 0, but min is 1
        assert count >= 1

    def test_count_tokens_empty_text(self):
        """Test token counting with empty text returns 1 (minimum)."""
        count = count_tokens("", "gpt-4")
        # max(1, 0 // 4) = max(1, 0) = 1
        assert count == 1


class TestFormatCommitForDisplay:
    """Test format_commit_for_display function."""

    def test_format_commit_basic(self):
        """Test basic commit formatting."""
        commit = {
            "short_hash": "abc123d",
            "message": "feat: add new feature",
            "author": "John Doe <john@example.com>",
            "date": datetime(2024, 1, 15, 10, 30),
            "files": ["src/feature.py", "tests/test_feature.py"],
        }

        formatted = format_commit_for_display(commit)

        assert "abc123d" in formatted
        assert "feat: add new feature" in formatted
        assert "John Doe" in formatted
        assert "2024-01-15" in formatted
        assert "src/feature.py" in formatted
        assert "tests/test_feature.py" in formatted

    def test_format_commit_long_message(self):
        """Test formatting with long commit message."""
        commit = {
            "short_hash": "abc123d",
            "message": "feat: add a very long feature description that exceeds normal length",
            "author": "John Doe <john@example.com>",
            "date": datetime(2024, 1, 15),
            "files": ["file.py"],
        }

        formatted = format_commit_for_display(commit, max_message_length=30)

        # Message should be truncated
        assert "..." in formatted
        # Full line includes hash, truncated message, files, author, date
        assert "abc123d" in formatted

    def test_format_commit_many_files(self):
        """Test formatting with many changed files."""
        files = [f"file{i}.py" for i in range(10)]
        commit = {
            "short_hash": "abc123d",
            "message": "feat: update many files",
            "author": "John Doe <john@example.com>",
            "date": datetime(2024, 1, 15),
            "files": files,
        }

        formatted = format_commit_for_display(commit, max_files=5)

        # Should show limited files
        assert "file0.py" in formatted
        assert "file4.py" in formatted
        assert "... and 5 more" in formatted

    def test_format_commit_minimal_data(self):
        """Test formatting with minimal commit data."""
        commit = {
            "short_hash": "abc123d",
            "message": "fix bug",
        }

        formatted = format_commit_for_display(commit)

        assert "abc123d" in formatted
        assert "fix bug" in formatted
        # Should handle missing fields gracefully


class TestCleanChangelogContent:
    """Test clean_changelog_content function."""

    def test_clean_changelog_basic(self):
        """Test basic changelog content cleaning."""
        content = """Here's the changelog:

### Added

- New feature A
- New feature B

### Fixed

- Bug fix A
- Bug fix B

Let me know if you need anything else!"""

        cleaned = clean_changelog_content(content)

        assert "Here's the changelog:" not in cleaned
        assert "Let me know if you need anything else!" not in cleaned
        assert "### Added" in cleaned
        assert "### Fixed" in cleaned
        assert "- New feature A" in cleaned

    def test_clean_changelog_with_markdown_blocks(self):
        """Test cleaning content with markdown code blocks."""
        # Content ends with ``` and no trailing text (clean extraction)
        content = """```markdown
### Added

- New feature
```"""

        cleaned = clean_changelog_content(content)

        assert "```markdown" not in cleaned
        assert "```" not in cleaned
        assert "### Added" in cleaned
        assert "- New feature" in cleaned

    def test_clean_changelog_preserve_structure(self):
        """Test that cleaning preserves changelog structure."""
        content = """### Added

- Feature 1
- Feature 2

### Changed

- Modified behavior

### Fixed

- Bug fix"""

        cleaned = clean_changelog_content(content)

        # Should preserve the exact structure
        assert cleaned.strip() == content.strip()

    def test_clean_changelog_remove_ai_chatter(self):
        """Test removal of common AI response patterns."""
        content = """I'll help you create a changelog entry.

### Added

- New authentication system

### Fixed

- Login validation errors

Is there anything else you'd like me to adjust?"""

        cleaned = clean_changelog_content(content)

        assert "I'll help you" not in cleaned
        assert "Is there anything else" not in cleaned
        assert "### Added" in cleaned
        assert "### Fixed" in cleaned

    def test_clean_changelog_empty_content(self):
        """Test cleaning empty or whitespace-only content."""
        assert clean_changelog_content("") == ""
        assert clean_changelog_content("   \n\n  ") == ""
        assert clean_changelog_content("No changes found.") == ""


class TestSetupLogging:
    """Test setup_logging function."""

    @patch("kittylog.utils.logging.logging")
    def test_setup_logging_debug(self, mock_logging):
        """Test setting up debug logging."""
        setup_logging("DEBUG")

        mock_logging.basicConfig.assert_called_once()
        call_args = mock_logging.basicConfig.call_args[1]
        assert call_args["level"] == mock_logging.DEBUG

    @patch("kittylog.utils.logging.logging")
    def test_setup_logging_info(self, mock_logging):
        """Test setting up info logging."""
        setup_logging("INFO")

        call_args = mock_logging.basicConfig.call_args[1]
        assert call_args["level"] == mock_logging.INFO

    @patch("kittylog.utils.logging.logging")
    def test_setup_logging_warning(self, mock_logging):
        """Test setting up warning logging (default)."""
        setup_logging("WARNING")

        call_args = mock_logging.basicConfig.call_args[1]
        assert call_args["level"] == mock_logging.WARNING

    @patch("kittylog.utils.logging.logging")
    def test_setup_logging_invalid_level(self, mock_logging):
        """Test handling of invalid log level."""
        import logging

        # Set up real logging level values and make INVALID not exist
        mock_logging.WARNING = logging.WARNING
        mock_logging.ERROR = logging.ERROR
        mock_logging.INFO = logging.INFO
        mock_logging.DEBUG = logging.DEBUG

        # Configure mock to raise AttributeError for unknown attributes
        mock_logging.configure_mock(**{"INVALID": logging.WARNING})

        setup_logging("INVALID")

        # Should have been called
        mock_logging.basicConfig.assert_called_once()
        call_args = mock_logging.basicConfig.call_args[1]
        # Level should be WARNING since we configured INVALID to return WARNING
        assert call_args["level"] == logging.WARNING


class TestTruncateText:
    """Test truncate_text function."""

    def test_truncate_text_short(self):
        """Test truncating text shorter than limit."""
        text = "Short text"
        result = truncate_text(text, 20)
        assert result == "Short text"

    def test_truncate_text_exact_limit(self):
        """Test text exactly at limit."""
        text = "Exactly twenty chars"
        result = truncate_text(text, 20)
        assert result == "Exactly twenty chars"

    def test_truncate_text_over_limit(self):
        """Test truncating text over limit."""
        text = "This is a very long text that exceeds the limit"
        result = truncate_text(text, 20)
        assert len(result) <= 23  # 20 + "..."
        assert result.endswith("...")
        assert result.startswith("This is a very")

    def test_truncate_text_custom_suffix(self):
        """Test truncating with custom suffix."""
        text = "This is a long text"
        result = truncate_text(text, 10, suffix=" [...]")
        assert result.endswith(" [...]")
        assert len(result) <= 16  # 10 + " [...]"

    def test_truncate_text_empty(self):
        """Test truncating empty text."""
        result = truncate_text("", 10)
        assert result == ""


class TestIsSemanticVersion:
    """Test is_semantic_version function."""

    def test_is_semantic_version_valid(self):
        """Test valid semantic versions."""
        valid_versions = [
            "1.0.0",
            "0.1.0",
            "10.20.30",
            "1.1.2-alpha",
            "1.0.0-beta.1",
            "2.0.0-rc.1",
            "1.2.3-alpha.1+build.1",
        ]

        for version in valid_versions:
            assert is_semantic_version(version), f"{version} should be valid"

    def test_is_semantic_version_with_v_prefix(self):
        """Test semantic versions with v prefix."""
        versions_with_v = [
            "v1.0.0",
            "v0.1.0",
            "v2.1.3-alpha",
        ]

        for version in versions_with_v:
            assert is_semantic_version(version), f"{version} should be valid"

    def test_is_semantic_version_invalid(self):
        """Test invalid semantic versions."""
        invalid_versions = [
            "1.0",
            "1",
            "1.0.0.0",
            "a.b.c",
            "1.0.0-",
            "",
            "release-1",
            "stable",
        ]

        for version in invalid_versions:
            assert not is_semantic_version(version), f"{version} should be invalid"


class TestNormalizeTag:
    """Test normalize_tag function."""

    def test_normalize_tag_with_v_prefix(self):
        """Test normalizing tags with v prefix."""
        assert normalize_tag("v1.0.0") == "1.0.0"
        assert normalize_tag("v0.1.0") == "0.1.0"
        assert normalize_tag("v2.1.3-alpha") == "2.1.3-alpha"

    def test_normalize_tag_without_v_prefix(self):
        """Test normalizing tags without v prefix."""
        assert normalize_tag("1.0.0") == "1.0.0"
        assert normalize_tag("0.1.0") == "0.1.0"
        assert normalize_tag("2.1.3-alpha") == "2.1.3-alpha"

    def test_normalize_tag_edge_cases(self):
        """Test normalizing edge cases."""
        assert normalize_tag("V1.0.0") == "1.0.0"  # Capital V
        assert normalize_tag("") == ""
        assert normalize_tag("v") == ""
        assert normalize_tag("release-1.0") == "release-1.0"  # Non-standard format


class TestUtilsIntegration:
    """Integration tests for utility functions."""

    def test_commit_formatting_pipeline(self):
        """Test complete commit formatting pipeline."""
        commit = {
            "hash": "abcdef123456789",
            "short_hash": "abcdef1",
            "message": "feat: implement user authentication with OAuth2 support and session management",
            "author": "Jane Developer <jane@example.com>",
            "date": datetime(2024, 1, 15, 14, 30, 45),
            "files": [
                "src/auth/oauth.py",
                "src/auth/session.py",
                "src/auth/__init__.py",
                "tests/test_oauth.py",
                "tests/test_session.py",
                "docs/auth.md",
                "requirements.txt",
            ],
        }

        # Format with different constraints
        short_format = format_commit_for_display(commit, max_message_length=50, max_files=3)

        assert "abcdef1" in short_format
        assert "..." in short_format  # Message truncated
        assert "and 4 more" in short_format  # Files truncated
        assert "2024-01-15" in short_format

    def test_token_counting_with_changelog_content(self):
        """Test token counting with realistic changelog content."""
        changelog_content = """### Added

- User authentication system with OAuth2 support
- Dashboard widgets for real-time monitoring
- Export functionality for reports

### Changed

- Updated UI components for better accessibility
- Improved performance of database queries

### Fixed

- Fixed issue where users couldn't save preferences
- Resolved login validation errors"""

        token_count = count_tokens(changelog_content, "gpt-4")

        # Simple character-based estimation: len(text) // 4 for GPT models
        expected_count = max(1, len(changelog_content) // 4)
        assert token_count == expected_count

    def test_version_handling_pipeline(self):
        """Test complete version handling pipeline."""
        test_tags = [
            "v1.0.0",
            "v1.1.0-alpha",
            "v2.0.0-beta.1",
            "1.2.3",
            "release-1.0",  # Non-semantic
        ]

        semantic_tags = []
        normalized_tags = []

        for tag in test_tags:
            if is_semantic_version(tag):
                semantic_tags.append(tag)
                normalized_tags.append(normalize_tag(tag))

        assert len(semantic_tags) == 4  # All except "release-1.0"
        assert "1.0.0" in normalized_tags
        assert "1.1.0-alpha" in normalized_tags
        assert "2.0.0-beta.1" in normalized_tags
        assert "1.2.3" in normalized_tags
