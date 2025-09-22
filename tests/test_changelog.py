"""Tests for changelog operations module."""

from datetime import datetime
from unittest.mock import patch

import pytest

from clog.changelog import (
    create_changelog_header,
    find_end_of_unreleased_section,
    find_insertion_point,
    find_unreleased_section,
    format_changelog_entry,
    preview_changelog_entry,
    read_changelog,
    update_changelog,
    write_changelog,
)


class TestReadChangelog:
    """Test read_changelog function."""

    def test_read_existing_file(self, temp_dir):
        """Test reading an existing changelog file."""
        changelog_file = temp_dir / "CHANGELOG.md"
        content = "# Changelog\n\n## [1.0.0]\n\n### Added\n- Feature"
        changelog_file.write_text(content)

        result = read_changelog(str(changelog_file))
        assert result == content

    def test_read_nonexistent_file(self, temp_dir):
        """Test reading a non-existent changelog file."""
        result = read_changelog(str(temp_dir / "NONEXISTENT.md"))
        assert result == ""

    def test_read_file_with_encoding(self, temp_dir):
        """Test reading file with different encoding."""
        changelog_file = temp_dir / "CHANGELOG.md"
        content = "# Changelog\n\n## [1.0.0]\n\n### Added\n- Feature with émojis "
        changelog_file.write_text(content, encoding="utf-8")

        result = read_changelog(str(changelog_file))
        assert "émojis " in result


class TestFindUnreleasedSection:
    """Test find_unreleased_section function."""

    def test_find_unreleased_section_exists(self):
        """Test finding existing unreleased section."""
        content = """# Changelog

## [Unreleased]

### Added
- New feature

## [1.0.0]
"""
        result = find_unreleased_section(content)
        assert result == 2  # Line index where [Unreleased] is found

    def test_find_unreleased_section_case_insensitive(self):
        """Test finding unreleased section with different casing."""
        content = """# Changelog

## [UNRELEASED]

### Added
- New feature
"""
        result = find_unreleased_section(content)
        assert result == 2

    def test_find_unreleased_section_not_exists(self):
        """Test when unreleased section doesn't exist."""
        content = """# Changelog

## [1.0.0]

### Added
- Feature
"""
        result = find_unreleased_section(content)
        assert result is None


class TestFindEndOfUnreleasedSection:
    """Test find_end_of_unreleased_section function."""

    def test_find_end_of_unreleased_section_with_next_version(self):
        """Test finding end when there's a next version section."""
        lines = [
            "# Changelog",
            "",
            "## [Unreleased]",
            "",
            "### Added",
            "- Feature 1",
            "- Feature 2",
            "",
            "## [1.0.0] - 2024-01-01",
            "",
            "### Added",
            "- Initial release",
        ]
        result = find_end_of_unreleased_section(lines, 2)  # Unreleased starts at line 2
        assert result == 8  # Should point to the next version section

    def test_find_end_of_unreleased_section_without_next_version(self):
        """Test finding end when there's no next version section."""
        lines = [
            "# Changelog",
            "",
            "## [Unreleased]",
            "",
            "### Added",
            "- Feature 1",
            "",
        ]
        result = find_end_of_unreleased_section(lines, 2)  # Unreleased starts at line 2
        assert result == 7  # Should point to end of file (len(lines))

    def test_find_end_of_unreleased_section_with_custom_section(self):
        """Test finding end when there's a custom section after unreleased."""
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
        assert result == 7  # Should point to the custom section


class TestFindInsertionPoint:
    """Test find_insertion_point function."""

    def test_find_insertion_point_with_version(self):
        """Test finding insertion point when version sections exist."""
        content = """# Changelog

## [Unreleased]

## [1.0.0]

### Added
- Feature
"""
        result = find_insertion_point(content)
        assert result == 4  # Before the first version section

    def test_find_insertion_point_no_versions(self):
        """Test finding insertion point when no version sections exist."""
        content = """# Changelog

All notable changes documented here.
"""
        result = find_insertion_point(content)
        assert result == 2  # After the description

    def test_find_insertion_point_empty_file(self):
        """Test finding insertion point in empty file."""
        content = ""
        result = find_insertion_point(content)
        assert result == 0


class TestCreateChangelogHeader:
    """Test create_changelog_header function."""

    def test_create_changelog_header(self):
        """Test creating a standard changelog header."""
        header = create_changelog_header()
        assert "# Changelog" in header
        assert "Keep a Changelog" in header
        assert "Semantic Versioning" in header
        assert "[Unreleased]" in header


class TestFormatChangelogEntry:
    """Test format_changelog_entry function."""

    def test_format_changelog_entry_with_ai_content(self, sample_commits):
        """Test formatting changelog entry with AI-generated content."""
        ai_content = """### Added

- New user authentication system
- Dashboard widgets

### Fixed

- Login validation errors"""

        tag_date = datetime(2024, 1, 20)
        entry = format_changelog_entry("v1.0.0", sample_commits, ai_content, tag_date)

        assert "## [1.0.0] - 2024-01-20" in entry
        assert "### Added" in entry
        assert "New user authentication system" in entry
        assert "### Fixed" in entry

    def test_format_changelog_entry_without_ai_content(self, sample_commits):
        """Test formatting changelog entry without AI content (fallback)."""
        entry = format_changelog_entry("v1.0.0", sample_commits, "", None)

        assert "## [1.0.0]" in entry
        assert "### Changed" in entry
        # Should include commit messages as fallback
        assert any(commit["message"].split("\n")[0] in entry for commit in sample_commits)

    def test_format_changelog_entry_strips_v_prefix(self, sample_commits):
        """Test that v prefix is stripped from tag in display."""
        entry = format_changelog_entry("v1.0.0", sample_commits, "### Added\n- Feature", None)
        assert "## [1.0.0]" in entry
        assert "## [v1.0.0]" not in entry


class TestUpdateChangelog:
    """Test update_changelog function."""

    @patch("clog.changelog.get_commits_between_tags")
    @patch("clog.changelog.generate_changelog_entry")
    @patch("clog.changelog.get_tag_date")
    def test_update_changelog_success(self, mock_get_date, mock_generate, mock_get_commits, temp_dir, sample_commits):
        """Test successful changelog update."""
        # Setup mocks
        mock_get_commits.return_value = sample_commits
        mock_generate.return_value = "### Added\n- New feature\n\n### Fixed\n- Bug fix"
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
        result = update_changelog(
            file_path=str(changelog_file),
            from_tag="v0.1.0",
            to_tag="v0.2.0",
            model="test:model",
            hint="",
            show_prompt=False,
            quiet=True,
        )

        assert "## [0.2.0] - 2024-01-20" in result
        assert "### Added" in result
        assert "New feature" in result
        assert "### Fixed" in result
        assert "Bug fix" in result

    @patch("clog.changelog.get_commits_between_tags")
    def test_update_changelog_no_commits(self, mock_get_commits, temp_dir):
        """Test update when no commits found."""
        mock_get_commits.return_value = []

        changelog_file = temp_dir / "CHANGELOG.md"
        existing_content = "# Changelog\n"
        changelog_file.write_text(existing_content)

        result = update_changelog(
            file_path=str(changelog_file),
            from_tag="v0.1.0",
            to_tag="v0.2.0",
            model="test:model",
        )

        # Should add header if content is too short
        expected_content = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

"""
        assert result == expected_content

    @patch("clog.changelog.get_commits_between_tags")
    @patch("clog.changelog.generate_changelog_entry")
    def test_update_changelog_empty_file(self, mock_generate, mock_get_commits, temp_dir, sample_commits):
        """Test update with empty/new changelog file."""
        mock_get_commits.return_value = sample_commits
        mock_generate.return_value = "### Added\n- New feature"

    @patch("clog.changelog.get_commits_between_tags")
    @patch("clog.changelog.generate_changelog_entry")
    def test_update_changelog_append_unreleased(self, mock_generate, mock_get_commits, temp_dir, sample_commits):
        """Test that unreleased changes are appended by default."""
        mock_get_commits.return_value = sample_commits
        mock_generate.return_value = "### Added\n- New feature\n\n### Fixed\n- Bug fix"

        # Create existing changelog with unreleased content
        changelog_file = temp_dir / "CHANGELOG.md"
        existing_content = """# Changelog

## [Unreleased]

### Changed
- Existing change

## [0.1.0] - 2024-01-01

### Added
- Initial release
"""
        changelog_file.write_text(existing_content)

        # Update with unreleased changes in append mode
        result = update_changelog(
            existing_content=existing_content,
            from_tag="v0.1.0",
            to_tag=None,  # Unreleased changes
            model="test:model",
            quiet=True,
            replace_unreleased=False,
        )

        # Should have both existing and new content in unreleased section
        assert result.count("## [Unreleased]") == 1
        assert "Existing change" in result
        assert "New feature" in result
        assert "Bug fix" in result

    @patch("clog.changelog.get_commits_between_tags")
    @patch("clog.changelog.generate_changelog_entry")
    def test_update_changelog_replace_unreleased(self, mock_generate, mock_get_commits, temp_dir, sample_commits):
        """Test that unreleased changes replace existing content when replace_unreleased=True."""
        mock_get_commits.return_value = sample_commits
        mock_generate.return_value = "### Added\n- New feature\n\n### Fixed\n- Bug fix"

        # Create existing changelog with unreleased content
        changelog_file = temp_dir / "CHANGELOG.md"
        existing_content = """# Changelog

## [Unreleased]

### Changed
- Existing change

## [0.1.0] - 2024-01-01

### Added
- Initial release
"""
        changelog_file.write_text(existing_content)

        # Update with unreleased changes in replace mode
        result = update_changelog(
            existing_content=existing_content,
            from_tag="v0.1.0",
            to_tag=None,  # Unreleased changes
            model="test:model",
            quiet=True,
        )

        # Should have only new content in unreleased section (existing content removed)
        assert result.count("## [Unreleased]") == 1
        assert "Existing change" not in result
        assert "New feature" in result
        assert "Bug fix" in result
        # Non-existent file
        changelog_file = temp_dir / "NEW_CHANGELOG.md"

        result = update_changelog(
            file_path=str(changelog_file),
            from_tag=None,
            to_tag="v1.0.0",
            model="test:model",
            quiet=True,
        )

        # Should create header for new file
        assert "# Changelog" in result
        assert "Keep a Changelog" in result
        assert "## [1.0.0]" in result


class TestWriteChangelog:
    """Test write_changelog function."""

    def test_write_changelog_success(self, temp_dir):
        """Test successful changelog writing."""
        changelog_file = temp_dir / "CHANGELOG.md"
        content = "# Changelog\n\n## [1.0.0]\n\n### Added\n- Feature"

        write_changelog(str(changelog_file), content)

        assert changelog_file.exists()
        assert changelog_file.read_text() == content

    def test_write_changelog_create_directory(self, temp_dir):
        """Test writing changelog with directory creation."""
        changelog_file = temp_dir / "docs" / "CHANGELOG.md"
        content = "# Changelog\n"

        write_changelog(str(changelog_file), content)

        assert changelog_file.exists()
        assert changelog_file.read_text() == content

    def test_write_changelog_permission_error(self, temp_dir):
        """Test handling permission errors when writing."""
        # Create a read-only directory
        readonly_dir = temp_dir / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)

        changelog_file = readonly_dir / "CHANGELOG.md"

        with pytest.raises((PermissionError, OSError)):  # Should raise some form of permission error\n
            write_changelog(str(changelog_file), "content")


class TestPreviewChangelogEntry:
    """Test preview_changelog_entry function."""

    @patch("clog.changelog.get_tag_date")
    def test_preview_changelog_entry(self, mock_get_date, sample_commits):
        """Test generating a preview of changelog entry."""
        mock_get_date.return_value = datetime(2024, 1, 20)
        ai_content = "### Added\n- New feature"

        preview = preview_changelog_entry("v1.0.0", sample_commits, ai_content)

        assert "## [1.0.0] - 2024-01-20" in preview
        assert "### Added" in preview
        assert "New feature" in preview


class TestChangelogIntegration:
    """Integration tests for changelog operations."""

    @patch("clog.changelog.get_commits_between_tags")
    @patch("clog.changelog.generate_changelog_entry")
    @patch("clog.changelog.get_tag_date")
    def test_full_changelog_workflow(self, mock_get_date, mock_generate, mock_get_commits, temp_dir, sample_commits):
        """Test complete changelog update workflow."""
        # Setup mocks
        mock_get_commits.return_value = sample_commits
        mock_generate.return_value = """### Added

- User authentication system with OAuth2 support
- Dashboard widgets for monitoring

### Fixed

- Login validation errors
- Session timeout issues"""
        mock_get_date.return_value = datetime(2024, 1, 20)

        # Create initial changelog WITH content in Unreleased section
        changelog_file = temp_dir / "CHANGELOG.md"
        initial_content = """# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Placeholder for unreleased changes

## [0.1.0] - 2024-01-01

### Added
- Initial project setup
"""
        changelog_file.write_text(initial_content)

        # Update changelog
        updated_content = update_changelog(
            file_path=str(changelog_file),
            from_tag="v0.1.0",
            to_tag="v0.2.0",
            model="anthropic:claude-3-5-haiku-latest",
            hint="Focus on user-facing features",
            show_prompt=False,
            quiet=True,
        )

        # Verify structure
        assert "# Changelog" in updated_content
        assert "## [Unreleased]" in updated_content
        assert "## [0.2.0] - 2024-01-20" in updated_content
        assert "## [0.1.0] - 2024-01-01" in updated_content

        # Verify new content
        assert "User authentication system" in updated_content
        assert "Dashboard widgets" in updated_content
        assert "Login validation errors" in updated_content

        # Verify ordering (newest first)
        unreleased_pos = updated_content.find("## [Unreleased]")
        new_version_pos = updated_content.find("## [0.2.0]")
        old_version_pos = updated_content.find("## [0.1.0]")

        assert unreleased_pos < new_version_pos < old_version_pos

        # Write and verify file
        write_changelog(str(changelog_file), updated_content)
        assert changelog_file.read_text() == updated_content

    def test_changelog_insertion_points(self, temp_dir):
        """Test various changelog insertion scenarios."""
        scenarios = [
            # Scenario 1: Standard changelog with unreleased section
            {
                "content": """# Changelog

## [Unreleased]

### Added
- Some unreleased feature

## [0.1.0] - 2024-01-01

### Added
- Initial release
""",
                "expected_sections": ["## [Unreleased]", "## [0.1.0]"],
            },
            # Scenario 2: Changelog without unreleased section
            {
                "content": """# Changelog

## [0.1.0] - 2024-01-01

### Added
- Initial release
""",
                "expected_sections": ["## [0.1.0]"],
            },
            # Scenario 3: Minimal changelog
            {
                "content": """# Changelog

All changes documented here.
""",
                "expected_sections": [],
            },
        ]

        for _i, scenario in enumerate(scenarios):
            # Test finding unreleased section
            unreleased_line = find_unreleased_section(scenario["content"])
            has_unreleased = any("Unreleased" in section for section in scenario["expected_sections"])

            if has_unreleased:
                assert unreleased_line is not None
            else:
                assert unreleased_line is None

            # Test finding insertion point
            insertion_point = find_insertion_point(scenario["content"])
            assert isinstance(insertion_point, int)
            assert insertion_point >= 0
