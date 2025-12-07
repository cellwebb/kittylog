"""Tests for context entries feature.

These tests verify the functionality for extracting preceding changelog entries
and including them in AI prompts for style reference.
"""

from kittylog.changelog.parser import extract_preceding_entries
from kittylog.prompt import build_changelog_prompt


class TestExtractPrecedingEntries:
    """Tests for extract_preceding_entries function."""

    def test_extract_single_entry(self):
        """Test extracting a single entry from changelog."""
        changelog = """# Changelog

## [Unreleased]

### Added
- New feature

## [1.0.0] - 2024-01-01

### Added
- Initial release
"""
        result = extract_preceding_entries(changelog, 1)

        assert "## Previous 1 Changelog Entry" in result
        assert "## [1.0.0] - 2024-01-01" in result
        assert "Initial release" in result
        assert "Unreleased" not in result

    def test_extract_multiple_entries(self):
        """Test extracting multiple entries from changelog."""
        changelog = """# Changelog

## [Unreleased]

## [2.0.0] - 2024-02-01

### Changed
- Major update

## [1.1.0] - 2024-01-15

### Fixed
- Bug fix

## [1.0.0] - 2024-01-01

### Added
- Initial release
"""
        result = extract_preceding_entries(changelog, 2)

        assert "## Previous 2 Changelog Entries" in result
        assert "## [2.0.0] - 2024-02-01" in result
        assert "## [1.1.0] - 2024-01-15" in result
        assert "## [1.0.0]" not in result  # Only 2 entries requested
        assert "---" in result  # Separator between entries

    def test_extract_all_entries_when_n_exceeds_available(self):
        """Test that requesting more entries than available returns all available."""
        changelog = """# Changelog

## [1.0.0] - 2024-01-01

### Added
- Initial release
"""
        result = extract_preceding_entries(changelog, 5)

        assert "## Previous 1 Changelog Entry" in result
        assert "## [1.0.0]" in result

    def test_extract_zero_entries(self):
        """Test that requesting 0 entries returns empty string."""
        changelog = """# Changelog

## [1.0.0] - 2024-01-01

### Added
- Initial release
"""
        result = extract_preceding_entries(changelog, 0)

        assert result == ""

    def test_extract_negative_entries(self):
        """Test that requesting negative entries returns empty string."""
        changelog = """# Changelog

## [1.0.0] - 2024-01-01

### Added
- Initial release
"""
        result = extract_preceding_entries(changelog, -1)

        assert result == ""

    def test_extract_from_empty_changelog(self):
        """Test extracting from empty changelog."""
        result = extract_preceding_entries("", 3)

        assert result == ""

    def test_extract_from_changelog_without_versions(self):
        """Test extracting from changelog with only unreleased section."""
        changelog = """# Changelog

## [Unreleased]

### Added
- New feature
"""
        result = extract_preceding_entries(changelog, 3)

        assert result == ""

    def test_skips_unreleased_section(self):
        """Test that Unreleased section is not included in extracted entries."""
        changelog = """# Changelog

## [Unreleased]

### Added
- Upcoming feature

## [1.0.0] - 2024-01-01

### Added
- Initial release
"""
        result = extract_preceding_entries(changelog, 3)

        assert "Unreleased" not in result
        assert "Upcoming feature" not in result
        assert "## [1.0.0]" in result

    def test_preserves_full_entry_content(self):
        """Test that full entry content including all sections is preserved."""
        changelog = """# Changelog

## [1.0.0] - 2024-01-01

### Added
- Feature A
- Feature B

### Changed
- Update X

### Fixed
- Bug Y

### Removed
- Old code
"""
        result = extract_preceding_entries(changelog, 1)

        assert "### Added" in result
        assert "Feature A" in result
        assert "Feature B" in result
        assert "### Changed" in result
        assert "Update X" in result
        assert "### Fixed" in result
        assert "Bug Y" in result
        assert "### Removed" in result
        assert "Old code" in result

    def test_handles_various_version_formats(self):
        """Test extraction with different version header formats."""
        changelog = """# Changelog

## [v2.0.0] - 2024-02-01

### Added
- Version 2

## [1.0.0-beta] - 2024-01-15

### Added
- Beta

## [v0.1.0] - 2024-01-01

### Added
- Initial
"""
        result = extract_preceding_entries(changelog, 3)

        assert "## [v2.0.0]" in result
        assert "## [1.0.0-beta]" in result
        assert "## [v0.1.0]" in result

    def test_case_insensitive_unreleased_detection(self):
        """Test that Unreleased is detected case-insensitively."""
        changelog = """# Changelog

## [UNRELEASED]

### Added
- New

## [1.0.0] - 2024-01-01

### Added
- Initial
"""
        result = extract_preceding_entries(changelog, 1)

        assert "UNRELEASED" not in result
        assert "## [1.0.0]" in result


class TestPromptWithContextEntries:
    """Tests for prompt building with context entries."""

    def test_prompt_includes_context_when_provided(self):
        """Test that context entries are included in the prompt."""
        commits = [
            {
                "short_hash": "abc123",
                "author": "Test",
                "date": __import__("datetime").datetime.now(),
                "message": "Test commit",
                "files": [],
            }
        ]
        context = "## [1.0.0]\n\n### Added\n- Feature X"

        _, user_prompt = build_changelog_prompt(
            commits=commits,
            tag="1.1.0",
            context_entries=context,
        )

        # Prompt format changed in commit cf9255c - now uses "CRITICAL CONTEXT" instead of "STYLE REFERENCE"
        assert "CRITICAL CONTEXT" in user_prompt or "WHAT'S ALREADY IN THE CHANGELOG" in user_prompt
        assert "## [1.0.0]" in user_prompt
        assert "Feature X" in user_prompt
        assert "Maintain consistency with the existing changelog style" in user_prompt

    def test_prompt_without_context_entries(self):
        """Test that prompt works without context entries."""
        commits = [
            {
                "short_hash": "abc123",
                "author": "Test",
                "date": __import__("datetime").datetime.now(),
                "message": "Test commit",
                "files": [],
            }
        ]

        _, user_prompt = build_changelog_prompt(
            commits=commits,
            tag="1.1.0",
            context_entries="",
        )

        assert "STYLE REFERENCE" not in user_prompt
        assert "preceding entries" not in user_prompt.lower()

    def test_prompt_context_appears_before_commits(self):
        """Test that context entries appear before commits in the prompt."""
        commits = [
            {
                "short_hash": "abc123",
                "author": "Test",
                "date": __import__("datetime").datetime.now(),
                "message": "Test commit",
                "files": [],
            }
        ]
        context = "## [1.0.0]\n\n### Added\n- Previous feature"

        _, user_prompt = build_changelog_prompt(
            commits=commits,
            tag="1.1.0",
            context_entries=context,
        )

        context_pos = user_prompt.find("STYLE REFERENCE")
        commits_pos = user_prompt.find("## Commits to analyze")

        assert context_pos < commits_pos, "Context should appear before commits"

    def test_prompt_with_empty_whitespace_context(self):
        """Test that whitespace-only context is treated as empty."""
        commits = [
            {
                "short_hash": "abc123",
                "author": "Test",
                "date": __import__("datetime").datetime.now(),
                "message": "Test commit",
                "files": [],
            }
        ]

        _, user_prompt = build_changelog_prompt(
            commits=commits,
            tag="1.1.0",
            context_entries="   \n\n   ",
        )

        assert "STYLE REFERENCE" not in user_prompt
