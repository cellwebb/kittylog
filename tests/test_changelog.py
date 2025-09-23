"""Tests for changelog module."""

import re
import tempfile
from datetime import datetime
from unittest.mock import patch

import pytest

from kittylog.changelog import (
    create_changelog_header,
    find_end_of_unreleased_section,
    find_existing_tags,
    find_insertion_point,
    read_changelog,
    remove_unreleased_sections,
    update_changelog,
    write_changelog,
)


class TestChangelogHeader:
    """Test changelog header creation."""

    def test_create_changelog_header_default(self):
        """Test default changelog header creation."""
        header = create_changelog_header()
        assert "# Changelog" in header
        assert "All notable changes" in header
        assert "Keep a Changelog" in header
        assert "Unreleased" in header

    def test_create_changelog_header_no_unreleased(self):
        """Test changelog header creation without unreleased section."""
        header = create_changelog_header(include_unreleased=False)
        assert "# Changelog" in header
        assert "All notable changes" in header
        assert "Keep a Changelog" in header
        assert "[Unreleased]" not in header


class TestFindEndOfUnreleasedSection:
    """Test find_end_of_unreleased_section function."""

    def test_find_end_of_unreleased_section(self):
        """Test finding the end of an unreleased section."""
        lines = [
            "# Changelog",
            "",
            "## [Unreleased]",
            "",
            "### Added",
            "- Feature 1",
            "",
            "## [0.1.0]",
            "",
            "### Added",
            "- Initial feature",
        ]
        result = find_end_of_unreleased_section(lines, 2)  # Unreleased starts at line 2
        assert result == 6  # Should point to the start of the next section

    def test_find_end_of_unreleased_section_custom_sections(self):
        """Test finding end with custom sections."""
        lines = [
            "# Changelog",
            "",
            "## [Unreleased]",
            "",
            "### Added",
            "- Feature 1",
            "",
            "## [Security Policy]",
            "",
            "- Details about security",
        ]
        result = find_end_of_unreleased_section(lines, 2)  # Unreleased starts at line 2
        assert result == 6  # Should point to the custom section

    def test_find_end_of_unreleased_section_single(self):
        """Test finding end with single unreleased section."""
        lines = [
            "# Changelog",
            "",
            "## [Unreleased]",
            "",
            "### Added",
            "- Feature 1",
            "- Feature 2",
            "",
        ]
        result = find_end_of_unreleased_section(lines, 2)  # Unreleased starts at line 2
        assert result == 8  # Should point to the end of the file

    def test_find_end_of_unreleased_section_no_content(self):
        """Test finding end with empty unreleased section."""
        lines = [
            "# Changelog",
            "",
            "## [Unreleased]",
            "",
            "## [0.1.0]",
            "",
            "### Added",
            "- Initial feature",
        ]
        result = find_end_of_unreleased_section(lines, 2)  # Unreleased starts at line 2
        assert result == 3  # Should point to the next section (0.1.0)

    def test_find_end_of_unreleased_section_with_diff(self):
        """Test finding end with diff content."""
        lines = [
            "# Changelog",
            "",
            "## [Unreleased]",
            "",
            "### Added",
            "- Feature 1",
            "",
            "...",  # Diff ellipsis
        ]
        result = find_end_of_unreleased_section(lines, 2)
        assert result == 8  # Should point to the end of the file


class TestFindInsertionPoint:
    """Test find_insertion_point function."""

    def test_find_insertion_point_with_version(self):
        """Test finding insertion point when version sections exist."""
        content = """# Changelog

## [Unreleased]

## [0.2.0] - 2024-01-15

### Added
- Feature 2

## [0.1.0] - 2024-01-01

### Added
- Feature 1
"""
        result = find_insertion_point(content)
        # Should insert at the first version section
        assert result == 4  # Line where [0.2.0] section starts

    def test_find_insertion_point_no_existing_versions(self):
        """Test finding insertion point when no version sections exist."""
        content = """# Changelog

## [Unreleased]
"""
        result = find_insertion_point(content)
        # Should insert after the first non-empty line
        assert result == 1

    def test_find_insertion_point_exact_match(self):
        """Test finding insertion point at exact version match."""
        content = """# Changelog

## [Unreleased]

## [0.2.0] - 2024-01-15

### Added
- Feature 2
"""
        result = find_insertion_point(content)
        # Should point to the existing version line
        assert result == 4


class TestFindExistingTags:
    """Test find_existing_tags function."""

    def test_find_existing_tags_basic(self):
        """Test finding existing tags in changelog."""
        content = """# Changelog

## [Unreleased]

## [0.2.0] - 2024-01-15
## [v0.1.5] - 2024-01-10
## [0.1.0] - 2024-01-01
"""
        result = find_existing_tags(content)
        assert set(result) == {"0.2.0", "0.1.5", "0.1.0"}

    def test_find_existing_tags_no_versions(self):
        """Test finding existing tags when no versions exist."""
        content = """# Changelog

## [Unreleased]

### Added
- Feature 1
"""
        result = find_existing_tags(content)
        assert result == set()  # Should be empty set


class TestRemoveUnreleasedSections:
    """Test remove_unreleased_sections function."""

    def test_remove_unreleased_sections(self):
        """Test removing unreleased sections from content."""
        lines = [
            "# Changelog",
            "",
            "## [Unreleased]",
            "",
            "### Added",
            "- Feature 1",
            "",
            "## [0.1.0]",
            "",
            "### Added",
            "- Initial feature",
        ]
        result = remove_unreleased_sections(lines)

        # Should remove the Unreleased section and its content
        expected = [
            "# Changelog",
            "",
            "## [0.1.0]",
            "",
            "### Added",
            "- Initial feature",
        ]
        assert result == expected

    def test_remove_unreleased_sections_multiple(self):
        """Test removing multiple unreleased sections."""
        lines = [
            "# Changelog",
            "",
            "## [Unreleased]",
            "",
            "### Added",
            "- Feature 1",
            "",
            "## [Unreleased]",
            "",
            "### Fixed",
            "- Bug 1",
            "",
            "## [0.1.0]",
            "",
            "### Added",
            "- Initial feature",
        ]
        result = remove_unreleased_sections(lines)

        # Should remove all Unreleased sections
        expected = [
            "# Changelog",
            "",
            "## [0.1.0]",
            "",
            "### Added",
            "- Initial feature",
        ]
        assert result == expected


class TestUpdateChangelog:
    """Test update_changelog function."""

    @patch("kittylog.changelog.get_commits_between_tags")
    @patch("kittylog.changelog.generate_changelog_entry")
    @patch("kittylog.changelog.get_tag_date")
    def test_update_changelog_success(self, mock_get_date, mock_generate, mock_get_commits, temp_dir, sample_commits):
        """Test successful changelog update."""
        # Setup mocks
        mock_get_commits.return_value = sample_commits
        mock_generate.return_value = (
            "### Added\n- New feature\n\n### Fixed\n- Bug fix",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )
        mock_get_date.return_value = datetime(2024, 1, 20)

        # Create existing changelog
        changelog_file = temp_dir / "CHANGELOG.md"
        existing_content = """# Changelog

## [Unreleased]

## [0.1.0] - 2024-01-01

### Added
- Initial release
"""
        changelog_file.write_text(existing_content)

        # Update changelog
        result, token_usage = update_changelog(
            file_path=str(changelog_file),
            from_tag="v0.1.0",
            to_tag="v0.2.0",
            model="test:model",
            hint="",
            show_prompt=False,
            quiet=True,
            no_unreleased=False,
        )

        assert "## [0.2.0] - 2024-01-20" in result
        assert "### Added" in result
        assert "New feature" in result
        assert "### Fixed" in result
        assert "Bug fix" in result

    @patch("kittylog.changelog.get_commits_between_tags")
    def test_update_changelog_no_commits(self, mock_get_commits, temp_dir):
        """Test update when no commits found."""
        mock_get_commits.return_value = []

        changelog_file = temp_dir / "CHANGELOG.md"
        existing_content = "# Changelog\n"
        changelog_file.write_text(existing_content)

        result, token_usage = update_changelog(
            file_path=str(changelog_file),
            from_tag="v0.1.0",
            to_tag="v0.2.0",
            model="test:model",
            quiet=True,
            no_unreleased=False,
        )

        assert result == existing_content  # Content should be unchanged
        assert token_usage is None

    @patch("kittylog.changelog.get_commits_between_tags")
    @patch("kittylog.changelog.generate_changelog_entry")
    def test_update_changelog_tagged_version(self, mock_generate, mock_get_commits, temp_dir):
        """Test updating changelog when current commit is tagged."""
        mock_get_commits.return_value = [
            {"hash": "abc123", "message": "Add feature", "files": ["feature.py"]},
        ]
        mock_generate.return_value = (
            "### Added\n- New feature",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

        # Create existing changelog
        changelog_file = temp_dir / "CHANGELOG.md"
        existing_content = """# Changelog

## [Unreleased]

## [0.1.0]

### Added
- Initial release
"""
        changelog_file.write_text(existing_content)

        result, token_usage = update_changelog(
            file_path=str(changelog_file),
            from_tag=None,
            to_tag="v0.1.0",
            model="test:model",
            quiet=True,
            no_unreleased=False,
        )

        # Should process from beginning to the tag
        assert "## [0.1.0]" in result
        assert "### Added" in result
        assert "New feature" in result

    @patch("kittylog.changelog.get_commits_between_tags")
    @patch("kittylog.changelog.generate_changelog_entry")
    def test_update_changelog_intelligent_unreleased(self, mock_generate, mock_get_commits, temp_dir):
        """Test intelligent unreleased content replacement."""
        mock_get_commits.return_value = [
            {"hash": "def456", "message": "Fix bug", "files": ["bug.py"]},
        ]
        mock_generate.return_value = (
            "### Fixed\n- Bug fix",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

        changelog_file = temp_dir / "CHANGELOG.md"
        existing_content = """# Changelog

## [Unreleased]

### Added
- User authentication system with OAuth2 support
- Dashboard widgets for real-time monitoring
- API endpoints for user management

## [0.1.0] - 2024-01-01

### Added
- Initial release
"""
        changelog_file.write_text(existing_content)

        result, token_usage = update_changelog(
            file_path=str(changelog_file),
            from_tag="v0.1.0",
            to_tag=None,
            model="test:model",
            quiet=True,
            no_unreleased=False,
        )

        # Existing Added section should be replaced with new content
        added_sections = re.findall(r"### Added\n(?:- .*\n)*", result)
        assert len(added_sections) == 1  # Should only have one Added section now
        assert "User authentication" not in result  # Old bullets should be gone
        assert "### Fixed" in result
        assert "Bug fix" in result


class TestChangelogIO:
    """Test changelog file I/O operations."""

    def test_read_changelog_existing_file(self, temp_dir):
        """Test reading existing changelog file."""
        changelog_file = temp_dir / "CHANGELOG.md"
        content = "# Changelog\n\n## [Unreleased]\n"
        changelog_file.write_text(content)

        result = read_changelog(str(changelog_file))
        assert result == content

    def test_read_changelog_nonexistent_file(self, temp_dir):
        """Test reading non-existent changelog file."""
        changelog_file = temp_dir / "NONEXISTENT.md"
        result = read_changelog(str(changelog_file))
        assert result == ""

    def test_write_changelog_success(self, temp_dir):
        """Test writing changelog file successfully."""
        changelog_file = temp_dir / "CHANGELOG.md"
        content = "# Changelog\n\n## [Unreleased]\n"

        write_changelog(str(changelog_file), content)
        assert changelog_file.read_text() == content

    def test_write_changelog_directory_error(self):
        """Test writing changelog file when path is a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(OSError):
                write_changelog(tmpdir, "content")
