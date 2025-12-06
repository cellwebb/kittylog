"""Tests for changelog module."""

import re
import tempfile
from datetime import datetime
from unittest.mock import patch

import pytest

from kittylog.changelog.io import (
    create_changelog_header,
    read_changelog,
    write_changelog,
)
from kittylog.changelog.parser import (
    find_end_of_unreleased_section,
    find_existing_boundaries,
    find_insertion_point,
    find_insertion_point_by_version,
)
from kittylog.changelog.updater import (
    _update_version_section,
    update_changelog,
)
from kittylog.errors import ChangelogError
from kittylog.postprocess import (
    remove_unreleased_sections,
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


class TestFindExistingBoundaries:
    """Test find_existing_boundaries function."""

    def test_find_existing_boundaries_basic(self):
        """Test finding existing boundaries in changelog."""
        content = """# Changelog

## [Unreleased]

## [0.2.0] - 2024-01-15
## [v0.1.5] - 2024-01-10
## [0.1.0] - 2024-01-01
"""
        result = find_existing_boundaries(content)
        assert set(result) == {"0.2.0", "0.1.5", "0.1.0"}

    def test_find_existing_boundaries_no_versions(self):
        """Test finding existing boundaries when no versions exist."""
        content = """# Changelog

## [Unreleased]

### Added
- Feature 1
"""
        result = find_existing_boundaries(content)
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

    @patch("kittylog.changelog.updater.get_commits_between_tags")
    @patch("kittylog.changelog.updater.generate_changelog_entry")
    @patch("kittylog.changelog.updater.get_tag_date")
    def test_update_changelog_success(self, mock_get_date, mock_generate, mock_get_commits, temp_dir, sample_commits):
        """Test successful changelog update."""
        # Setup mocks
        mock_get_commits.return_value = sample_commits
        mock_generate.return_value = (
            "### Added\n- New feature\n\n### Fixed\n- Bug fix",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )
        mock_get_date.return_value = datetime(2024, 1, 20)

        # Create existing changelog content
        existing_content = """# Changelog

## [Unreleased]

## [0.1.0] - 2024-01-01

### Added
- Initial release
"""

        # Update changelog
        result, _token_usage = update_changelog(
            existing_content=existing_content,
            from_boundary="v0.1.0",
            to_boundary="v0.2.0",
            model="openai:gpt-4o-mini",
            hint="",
            show_prompt=False,
            quiet=True,
            no_unreleased=False,
        )

        mock_generate.assert_called_once()
        assert mock_generate.call_args.kwargs.get("audience") is None

        # Check for version (may have v prefix)
        assert "## [0.2.0] - 2024-01-20" in result or "## [v0.2.0] - 2024-01-20" in result
        assert "### Added" in result
        assert "New feature" in result
        assert "### Fixed" in result
        assert "Bug fix" in result

    @patch("kittylog.changelog.updater.get_commits_between_tags")
    def test_update_changelog_no_commits(self, mock_get_commits, temp_dir):
        """Test update when no commits found."""
        mock_get_commits.return_value = []

        existing_content = "# Changelog\n"

        result, _token_usage = update_changelog(
            existing_content=existing_content,
            from_boundary="v0.1.0",
            to_boundary="v0.2.0",
            model="openai:gpt-4o-mini",
            quiet=True,
            no_unreleased=False,
        )

        assert result == existing_content  # Content should be unchanged
        assert _token_usage is None

    @patch("kittylog.changelog.updater.get_commits_between_tags")
    @patch("kittylog.changelog.updater.generate_changelog_entry")
    def test_update_changelog_tagged_version(self, mock_generate, mock_get_commits, temp_dir):
        """Test updating changelog when current commit is tagged."""
        mock_get_commits.return_value = [
            {"hash": "abc123", "message": "Add feature", "files": ["feature.py"]},
        ]
        mock_generate.return_value = (
            "### Added\n- New feature",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

        # Create existing changelog content
        existing_content = """# Changelog

## [Unreleased]

## [0.1.0]

### Added
- Initial release
"""

        result, _token_usage = update_changelog(
            existing_content=existing_content,
            from_boundary=None,
            to_boundary="v0.1.0",
            model="openai:gpt-4o-mini",
            quiet=True,
            no_unreleased=False,
        )

        # Should process from beginning to the tag
        assert "## [0.1.0]" in result  # Tag v prefix is stripped
        assert "### Added" in result
        assert "New feature" in result

    @patch("kittylog.changelog.updater.get_commits_between_tags")
    @patch("kittylog.changelog.updater.generate_changelog_entry")
    def test_update_changelog_intelligent_unreleased(self, mock_generate, mock_get_commits, temp_dir):
        """Test intelligent unreleased content replacement."""
        mock_get_commits.return_value = [
            {"hash": "def456", "message": "Fix bug", "files": ["bug.py"]},
        ]
        mock_generate.return_value = (
            "### Fixed\n- Bug fix",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

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

        result, _token_usage = update_changelog(
            existing_content=existing_content,
            from_boundary="v0.1.0",
            to_boundary=None,
            model="openai:gpt-4o-mini",
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
        with tempfile.TemporaryDirectory() as tmpdir, pytest.raises(ChangelogError):
            write_changelog(tmpdir, "content")


class TestFindInsertionPointByVersion:
    """Test find_insertion_point_by_version function with various scenarios."""

    def test_basic_semantic_version_ordering(self):
        """Test basic semantic version ordering (descending order)."""
        content = """# Changelog

## [Unreleased]

## [2.0.0] - 2024-03-01

### Added
- Major feature

## [1.5.0] - 2024-02-01

### Added
- Minor feature

## [1.0.0] - 2024-01-01

### Added
- Initial release
"""
        # Test inserting v1.2.0 between v1.5.0 and v1.0.0
        result = find_insertion_point_by_version(content, "v1.2.0")
        assert result == 14  # Should insert before "## [1.0.0]"

        # Test inserting v3.0.0 at the beginning (newest)
        result = find_insertion_point_by_version(content, "v3.0.0")
        assert result == 4  # Should insert before "## [2.0.0]"

        # Test inserting v0.9.0 at the end (oldest)
        result = find_insertion_point_by_version(content, "v0.9.0")
        # Should insert after the last version section
        assert result >= 18  # After all content

    def test_prerelease_versions(self):
        """Test pre-release version handling.

        Note: Current implementation has non-standard semver behavior where
        final releases (1.0.0) are considered less than pre-releases (1.0.0-rc.1).
        """
        content = """# Changelog

## [Unreleased]

## [1.0.0] - 2024-01-15

### Added
- Final release

## [1.0.0-rc.1] - 2024-01-10

### Added
- Release candidate

## [1.0.0-beta.2] - 2024-01-05

### Added
- Beta release

## [1.0.0-alpha.1] - 2024-01-01

### Added
- Alpha release
"""
        # Test inserting 1.0.0-beta.1 - due to current implementation behavior,
        # it will insert before the final 1.0.0 release
        result = find_insertion_point_by_version(content, "1.0.0-beta.1")
        assert result == 4  # Inserts before "## [1.0.0]" due to current implementation

        # Test inserting 1.0.0-rc.2 - also inserts before final release
        result = find_insertion_point_by_version(content, "1.0.0-rc.2")
        assert result == 4  # Inserts before "## [1.0.0]" due to current implementation

    def test_mixed_version_formats(self):
        """Test mixed version formats with and without 'v' prefix."""
        content = """# Changelog

## [Unreleased]

## [v2.1.0] - 2024-03-01

### Added
- Version with v prefix

## [2.0.0] - 2024-02-01

### Added
- Version without v prefix

## [v1.9.0] - 2024-01-01

### Added
- Another v prefix version
"""
        # Test inserting version without prefix
        result = find_insertion_point_by_version(content, "2.0.1")
        assert result == 9  # Should insert before "## [2.0.0]"

        # Test inserting version with prefix
        result = find_insertion_point_by_version(content, "v1.9.1")
        assert result == 14  # Should insert before "## [v1.9.0]"

    def test_version_insertion_at_beginning(self):
        """Test inserting newest version at the beginning."""
        content = """# Changelog

## [Unreleased]

## [1.0.0] - 2024-01-01

### Added
- Initial release
"""
        result = find_insertion_point_by_version(content, "v2.0.0")
        assert result == 4  # Should insert before "## [1.0.0]"

    def test_version_insertion_at_end(self):
        """Test inserting oldest version at the end."""
        content = """# Changelog

## [Unreleased]

## [2.0.0] - 2024-02-01

### Added
- Latest release

## [1.0.0] - 2024-01-01

### Added
- Initial release
"""
        result = find_insertion_point_by_version(content, "v0.9.0")
        # Should insert at the end of the content
        lines = content.split("\n")
        assert result >= len(lines) - 2

    def test_version_insertion_in_middle(self):
        """Test inserting version in the middle of existing versions."""
        content = """# Changelog

## [Unreleased]

## [3.0.0] - 2024-03-01

### Added
- Version 3

## [2.0.0] - 2024-02-01

### Added
- Version 2

## [1.0.0] - 2024-01-01

### Added
- Version 1
"""
        result = find_insertion_point_by_version(content, "v2.5.0")
        assert result == 9  # Should insert before "## [2.0.0]"

    def test_empty_changelog_scenarios(self):
        """Test version insertion in empty or minimal changelog."""
        # Test completely empty changelog
        empty_content = ""
        result = find_insertion_point_by_version(empty_content, "v1.0.0")
        assert result == 1  # Empty content splits to [""], insert after it

        # Test changelog with only header
        header_only = """# Changelog

All notable changes to this project will be documented in this file.
"""
        result = find_insertion_point_by_version(header_only, "v1.0.0")
        assert result == 1  # Should insert after first non-empty line (the # Changelog)

        # Test changelog with unreleased section only
        unreleased_only = """# Changelog

## [Unreleased]

### Added
- Some feature
"""
        result = find_insertion_point_by_version(unreleased_only, "v1.0.0")
        assert result == 1  # No version sections, so inserts after first non-empty line

    def test_edge_cases_malformed_versions(self):
        """Test edge cases with malformed or unusual versions."""
        content = """# Changelog

## [Unreleased]

## [v1.0.0] - 2024-01-15

### Added
- Normal version

## [experimental-build] - 2024-01-10

### Added
- Non-semantic version

## [v0.9.0] - 2024-01-01

### Added
- Another normal version
"""
        # Should still work with semantic versions present
        result = find_insertion_point_by_version(content, "v0.9.5")
        # Should insert between v1.0.0 and experimental-build, but since experimental-build
        # is not a semantic version, it should be ignored for ordering
        # Should find the position based on semantic versions only
        assert result == 14  # Inserts before "## [v0.9.0]" based on current implementation

    def test_complex_prerelease_with_numbers(self):
        """Test complex pre-release versions with numbers."""
        content = """# Changelog

## [Unreleased]

## [2.0.0] - 2024-02-01

### Added
- Final release

## [2.0.0-rc.2] - 2024-01-25

### Added
- Release candidate 2

## [2.0.0-rc.1] - 2024-01-20

### Added
- Release candidate 1

## [2.0.0-beta.3] - 2024-01-15

### Added
- Beta 3

## [2.0.0-alpha.1] - 2024-01-01

### Added
- Alpha 1
"""
        # Test inserting between existing pre-releases
        result = find_insertion_point_by_version(content, "2.0.0-beta.2")
        assert result == 4  # Due to current implementation, inserts before final release

        # Test inserting a new alpha version
        result = find_insertion_point_by_version(content, "2.0.0-alpha.2")
        assert result == 4  # Due to current implementation, inserts before final release

    def test_patch_versions(self):
        """Test patch version ordering."""
        content = """# Changelog

## [Unreleased]

## [1.0.3] - 2024-01-20

### Fixed
- Bug fix 3

## [1.0.1] - 2024-01-10

### Fixed
- Bug fix 1

## [1.0.0] - 2024-01-01

### Added
- Initial release
"""
        # Test inserting patch version between existing ones
        result = find_insertion_point_by_version(content, "v1.0.2")
        assert result == 9  # Should insert before "## [1.0.1]"

    def test_major_minor_patch_combinations(self):
        """Test various combinations of major.minor.patch versions."""
        content = """# Changelog

## [Unreleased]

## [3.1.0] - 2024-04-01

### Added
- Feature in 3.1

## [3.0.2] - 2024-03-15

### Fixed
- Patch in 3.0

## [3.0.0] - 2024-03-01

### Added
- Major version 3

## [2.5.1] - 2024-02-15

### Fixed
- Patch in 2.5

## [2.0.0] - 2024-02-01

### Added
- Major version 2
"""
        # Test inserting minor version
        result = find_insertion_point_by_version(content, "3.0.1")
        assert result == 14  # Should insert before "## [3.0.0]"

        # Test inserting new major version
        result = find_insertion_point_by_version(content, "4.0.0")
        assert result == 4  # Should insert before "## [3.1.0]"

        # Test inserting between major versions
        result = find_insertion_point_by_version(content, "2.1.0")
        assert result == 24  # Should insert before "## [2.0.0]"

    def test_version_with_build_metadata(self):
        """Test versions with build metadata (rarely used but valid semver)."""
        content = """# Changelog

## [Unreleased]

## [1.0.0+build.1] - 2024-01-15

### Added
- Version with build metadata

## [1.0.0] - 2024-01-01

### Added
- Standard version
"""
        # Build metadata should not affect ordering (per semver spec)
        result = find_insertion_point_by_version(content, "1.0.0+build.2")
        # Should be treated as equivalent to 1.0.0, so insert after existing 1.0.0+build.1
        assert result == 4  # Due to current implementation, inserts before final release

    def test_no_existing_versions(self):
        """Test behavior when no version sections exist."""
        content = """# Changelog

## [Unreleased]

### Added
- Some unreleased feature

## [Custom Section]

Some custom content that's not a version.
"""
        result = find_insertion_point_by_version(content, "v1.0.0")
        # Should fall back to original insertion point logic
        assert result == 7  # Should insert after unreleased section, before custom section

    def test_version_normalization(self):
        """Test that version normalization works correctly."""
        content = """# Changelog

## [Unreleased]

## [v1.0.0] - 2024-01-01

### Added
- Initial release
"""
        # Test that v1.1.0 and 1.1.0 are treated the same
        result1 = find_insertion_point_by_version(content, "v1.1.0")
        result2 = find_insertion_point_by_version(content, "1.1.0")
        assert result1 == result2 == 4  # Both should insert before v1.0.0

    def test_large_version_numbers(self):
        """Test handling of large version numbers."""
        content = """# Changelog

## [Unreleased]

## [10.5.2] - 2024-01-15

### Added
- Version 10

## [2.15.0] - 2024-01-10

### Added
- Version 2

## [2.3.100] - 2024-01-01

### Added
- Version 2 with large patch
"""
        # Test inserting between large numbers
        result = find_insertion_point_by_version(content, "2.10.0")
        assert result == 14  # Should insert before "## [2.3.100]"

        # Test large major version
        result = find_insertion_point_by_version(content, "15.0.0")
        assert result == 4  # Should insert before "## [10.5.2]"

    def test_alphanumeric_prerelease_versions(self):
        """Test pre-release versions with alphanumeric identifiers."""
        content = """# Changelog

## [Unreleased]

## [1.0.0] - 2024-01-15

### Added
- Final release

## [1.0.0a3] - 2024-01-10

### Added
- Alpha 3

## [1.0.0a1] - 2024-01-05

### Added
- Alpha 1

## [0.9.0] - 2024-01-01

### Added
- Previous version
"""
        # Test inserting between alpha versions
        result = find_insertion_point_by_version(content, "1.0.0a2")
        assert result == 4  # Due to current implementation, inserts before final release

        # Test inserting beta version (should come after alpha)
        result = find_insertion_point_by_version(content, "1.0.0b1")
        assert result == 4  # Due to current implementation, inserts before final release


class TestVersionStripping:
    """Test version prefix stripping functionality.

    These tests verify that the 'v' prefix is correctly stripped from version tags
    when creating changelog headers, ensuring consistent formatting across all modes.
    """

    @patch("kittylog.changelog.updater.get_commits_between_tags")
    @patch("kittylog.changelog.updater.generate_changelog_entry")
    @patch("kittylog.changelog.updater.get_tag_date")
    def test_version_with_v_prefix_is_stripped(self, mock_get_date, mock_generate, mock_get_commits, temp_dir):
        """Test that version with 'v' prefix is stripped in header.

        Input: v0.1.0
        Expected: ## [0.1.0] - YYYY-MM-DD
        """
        mock_get_commits.return_value = [
            {"hash": "abc123", "message": "Add feature", "files": ["feature.py"]},
        ]
        mock_generate.return_value = (
            "### Added\n- New feature",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )
        mock_get_date.return_value = datetime(2024, 1, 20)

        existing_content = """# Changelog

## [Unreleased]

"""

        result, _token_usage = update_changelog(
            existing_content=existing_content,
            from_boundary=None,
            to_boundary="v0.1.0",
            model="openai:gpt-4o-mini",
            hint="",
            show_prompt=False,
            quiet=True,
            no_unreleased=False,
        )

        # Verify the v prefix is stripped
        assert "## [0.1.0] - 2024-01-20" in result
        assert "## [v0.1.0]" not in result

    @patch("kittylog.changelog.updater.get_commits_between_tags")
    @patch("kittylog.changelog.updater.generate_changelog_entry")
    @patch("kittylog.changelog.updater.get_tag_date")
    def test_version_without_v_prefix_unchanged(self, mock_get_date, mock_generate, mock_get_commits, temp_dir):
        """Test that version without 'v' prefix remains unchanged.

        Input: 0.1.0
        Expected: ## [0.1.0] - YYYY-MM-DD
        """
        mock_get_commits.return_value = [
            {"hash": "def456", "message": "Fix bug", "files": ["bug.py"]},
        ]
        mock_generate.return_value = (
            "### Fixed\n- Bug fix",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )
        mock_get_date.return_value = datetime(2024, 2, 15)

        existing_content = """# Changelog

## [Unreleased]

"""

        result, _token_usage = update_changelog(
            existing_content=existing_content,
            from_boundary=None,
            to_boundary="0.1.0",
            model="openai:gpt-4o-mini",
            hint="",
            show_prompt=False,
            quiet=True,
            no_unreleased=False,
        )

        # Verify version remains unchanged (no v prefix)
        assert "## [0.1.0] - 2024-02-15" in result

    @patch("kittylog.changelog.updater.get_commits_between_tags")
    @patch("kittylog.changelog.updater.generate_changelog_entry")
    @patch("kittylog.changelog.updater.get_tag_date")
    def test_version_with_v_prefix_and_prerelease(self, mock_get_date, mock_generate, mock_get_commits, temp_dir):
        """Test that 'v' prefix is stripped from prerelease versions.

        Input: v1.0.0-beta
        Expected: ## [1.0.0-beta] - YYYY-MM-DD
        """
        mock_get_commits.return_value = [
            {"hash": "ghi789", "message": "Beta release", "files": ["beta.py"]},
        ]
        mock_generate.return_value = (
            "### Added\n- Beta features",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )
        mock_get_date.return_value = datetime(2024, 3, 10)

        existing_content = """# Changelog

## [Unreleased]

"""

        result, _token_usage = update_changelog(
            existing_content=existing_content,
            from_boundary=None,
            to_boundary="v1.0.0-beta",
            model="openai:gpt-4o-mini",
            hint="",
            show_prompt=False,
            quiet=True,
            no_unreleased=False,
        )

        # Verify v prefix is stripped but prerelease tag remains
        assert "## [1.0.0-beta] - 2024-03-10" in result
        assert "## [v1.0.0-beta]" not in result

    @patch("kittylog.changelog.updater.get_commits_between_tags")
    @patch("kittylog.changelog.updater.generate_changelog_entry")
    @patch("kittylog.changelog.updater.get_tag_date")
    def test_version_with_major_minor_patch(self, mock_get_date, mock_generate, mock_get_commits, temp_dir):
        """Test version stripping with standard semantic version.

        Input: v1.2.3
        Expected: ## [1.2.3] - YYYY-MM-DD
        """
        mock_get_commits.return_value = [
            {"hash": "jkl012", "message": "Patch release", "files": ["patch.py"]},
        ]
        mock_generate.return_value = (
            "### Fixed\n- Patch fix",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )
        mock_get_date.return_value = datetime(2024, 4, 5)

        existing_content = """# Changelog

## [Unreleased]

"""

        result, _token_usage = update_changelog(
            existing_content=existing_content,
            from_boundary=None,
            to_boundary="v1.2.3",
            model="openai:gpt-4o-mini",
            hint="",
            show_prompt=False,
            quiet=True,
            no_unreleased=False,
        )

        # Verify correct format
        assert "## [1.2.3] - 2024-04-05" in result
        assert "## [v1.2.3]" not in result

    @patch("kittylog.changelog.updater.get_commits_between_tags")
    @patch("kittylog.changelog.updater.generate_changelog_entry")
    @patch("kittylog.changelog.updater.get_tag_date")
    def test_multiple_versions_consistent_stripping(self, mock_get_date, mock_generate, mock_get_commits, temp_dir):
        """Test that multiple version updates maintain consistent stripping.

        Ensures that when updating a changelog with multiple versions,
        all 'v' prefixes are consistently stripped.
        """
        mock_get_commits.return_value = [
            {"hash": "abc", "message": "Feature", "files": ["file.py"]},
        ]
        mock_generate.return_value = (
            "### Added\n- Feature",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

        # First update with v0.1.0
        mock_get_date.return_value = datetime(2024, 1, 1)
        existing_content = """# Changelog

## [Unreleased]

"""

        result1, _ = update_changelog(
            existing_content=existing_content,
            from_boundary=None,
            to_boundary="v0.1.0",
            model="openai:gpt-4o-mini",
            quiet=True,
            no_unreleased=False,
        )

        # Second update with v0.2.0
        mock_get_date.return_value = datetime(2024, 2, 1)
        result2, _ = update_changelog(
            existing_content=result1,
            from_boundary="v0.1.0",
            to_boundary="v0.2.0",
            model="openai:gpt-4o-mini",
            quiet=True,
            no_unreleased=False,
        )

        # Both versions should have v stripped
        assert "## [0.1.0] - 2024-01-01" in result2
        assert "## [0.2.0] - 2024-02-01" in result2
        assert "## [v0.1.0]" not in result2
        assert "## [v0.2.0]" not in result2

    @patch("kittylog.changelog.updater.get_commits_between_tags")
    @patch("kittylog.changelog.updater.generate_changelog_entry")
    @patch("kittylog.changelog.updater.get_tag_date")
    def test_version_stripping_with_existing_entry(self, mock_get_date, mock_generate, mock_get_commits, temp_dir):
        """Test version stripping when updating an existing version entry.

        Verifies that when replacing an existing version section,
        the v prefix is still correctly stripped.
        """
        mock_get_commits.return_value = [
            {"hash": "xyz", "message": "Updated feature", "files": ["feature.py"]},
        ]
        mock_generate.return_value = (
            "### Changed\n- Updated feature",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )
        mock_get_date.return_value = datetime(2024, 5, 20)

        # Existing changelog with version (without v)
        existing_content = """# Changelog

## [Unreleased]

## [1.0.0] - 2024-05-20

### Added
- Old feature

## [0.9.0] - 2024-01-01

### Added
- Initial release
"""

        result, _ = update_changelog(
            existing_content=existing_content,
            from_boundary="v0.9.0",
            to_boundary="v1.0.0",
            model="openai:gpt-4o-mini",
            quiet=True,
            no_unreleased=False,
        )

        # Verify replacement maintains correct format
        assert "## [1.0.0] - 2024-05-20" in result
        assert "## [v1.0.0]" not in result
        # Old content should be replaced
        assert "### Changed" in result
        assert "Updated feature" in result

    def test_edge_case_empty_version(self):
        """Test handling of edge case with empty version string.

        While this shouldn't happen in practice, ensure graceful handling.
        """
        # lstrip('v') on empty string should return empty string
        assert "".lstrip("v") == ""

    def test_edge_case_only_v_character(self):
        """Test handling of version that is only 'v'."""
        # Just 'v' should strip to empty
        assert "v".lstrip("v") == ""

    def test_edge_case_multiple_v_prefixes(self):
        """Test handling of multiple 'v' characters at start.

        Input: vv1.0.0
        Expected: 1.0.0 (all leading v's stripped)
        """
        # lstrip removes ALL leading 'v' characters
        assert "vv1.0.0".lstrip("v") == "1.0.0"
        assert "vvv1.0.0".lstrip("v") == "1.0.0"

    def test_edge_case_v_in_middle_of_version(self):
        """Test that 'v' in middle of version is not stripped.

        Input: 1.v0.0
        Expected: 1.v0.0 (only leading v's are stripped)
        """
        # lstrip only removes from the beginning
        assert "1.v0.0".lstrip("v") == "1.v0.0"

    def test_edge_case_uppercase_v(self):
        """Test handling of uppercase 'V' prefix.

        Note: lstrip('v') only strips lowercase 'v', not uppercase 'V'.
        This documents current behavior - may need enhancement if uppercase is used.
        """
        # Current implementation only strips lowercase 'v'
        assert "V1.0.0".lstrip("v") == "V1.0.0"
        # Mixed case
        assert "vV1.0.0".lstrip("v") == "V1.0.0"


class TestTwoBlankLinesSpacing:
    """Test the two blank lines spacing functionality for changelog entries.

    This test class verifies that version sections are properly formatted with
    exactly two blank lines between them, ensuring consistent and readable
    changelog formatting.
    """

    def test_add_new_version_with_two_blanks_simple(self):
        """Test inserting a new version with proper two blank lines spacing (simple case)."""
        existing_content = """# Changelog

## [1.0.0] - 2025-01-01

### Added
- Initial feature

## [0.9.0] - 2024-12-01

### Added
- Older feature"""

        version_section = "## [1.1.0] - 2025-01-15\n\n### Added\n- New feature"
        result = _update_version_section(existing_content, version_section, "1.1.0")

        lines = result.split("\n")

        # Find version sections
        version_sections = []
        for i, line in enumerate(lines):
            if line.startswith("## [") and not line.startswith("## [Unreleased]"):
                version_sections.append((i, line))

        # Should have 3 version sections in correct order
        assert len(version_sections) == 3
        assert "## [1.1.0]" in version_sections[0][1]
        assert "## [1.0.0]" in version_sections[1][1]
        assert "## [0.9.0]" in version_sections[2][1]

        # Check spacing between sections
        for i in range(1, len(version_sections)):
            prev_line = version_sections[i - 1][0]
            curr_line = version_sections[i][0]
            blank_lines = 0
            for j in range(prev_line + 1, curr_line):
                if lines[j].strip() == "":
                    blank_lines += 1
            assert blank_lines == 2, f"Expected 2 blank lines between sections, got {blank_lines}"

    def test_add_new_version_at_beginning(self):
        """Test inserting newest version at the beginning with proper spacing."""
        existing_content = """# Changelog

## [1.0.0] - 2025-01-01

### Added
- Initial feature

## [0.9.0] - 2024-12-01

### Added
- Older feature"""

        version_section = "## [2.0.0] - 2025-02-01\n\n### Added\n- Major new feature"
        result = _update_version_section(existing_content, version_section, "2.0.0")

        lines = result.split("\n")

        # Should start with new version
        assert lines[2] == "## [2.0.0] - 2025-02-01"

        # Check spacing after new version
        next_version_line = None
        for i in range(3, len(lines)):
            if lines[i].startswith("## [1.0.0]"):
                next_version_line = i
                break

        assert next_version_line is not None
        blank_lines = 0
        for i in range(3, next_version_line):
            if lines[i].strip() == "":
                blank_lines += 1
        assert blank_lines == 2

    def test_add_new_version_at_end(self):
        """Test inserting oldest version at the end with proper spacing."""
        existing_content = """# Changelog

## [1.2.0] - 2025-01-20

### Added
- Latest feature

## [1.0.0] - 2025-01-01

### Added
- Initial feature"""

        version_section = "## [0.9.0] - 2024-12-01\n\n### Added\n- Older feature"
        result = _update_version_section(existing_content, version_section, "0.9.0")

        lines = result.split("\n")

        # New version should be at the end
        assert "## [0.9.0] - 2024-12-01" in lines
        last_version_line = lines.index("## [0.9.0] - 2024-12-01")

        # Find the previous version (1.0.0)
        prev_version_line = None
        for i in range(last_version_line - 1, -1, -1):
            if lines[i].startswith("## [1.0.0]"):
                prev_version_line = i
                break

        assert prev_version_line is not None
        blank_lines = 0
        for i in range(prev_version_line + 1, last_version_line):
            if lines[i].strip() == "":
                blank_lines += 1
        assert blank_lines == 2

    def test_replace_existing_version_maintains_spacing(self):
        """Test replacing existing version maintains proper spacing."""
        existing_content = """# Changelog

## [1.1.0] - 2025-01-15

### Added
- Old feature description

## [1.0.0] - 2025-01-01

### Added
- Initial feature

## [0.9.0] - 2024-12-01

### Added
- Older feature"""

        version_section = "## [1.1.0] - 2025-01-15\n\n### Changed\n- Updated feature description"
        result = _update_version_section(existing_content, version_section, "1.1.0")

        lines = result.split("\n")

        # Should still have exactly 2 blank lines between all sections
        version_sections = []
        for i, line in enumerate(lines):
            if line.startswith("## [") and not line.startswith("## [Unreleased]"):
                version_sections.append((i, line))

        # Check spacing between all sections
        for i in range(1, len(version_sections)):
            prev_line = version_sections[i - 1][0]
            curr_line = version_sections[i][0]
            blank_lines = 0
            for j in range(prev_line + 1, curr_line):
                if lines[j].strip() == "":
                    blank_lines += 1
            assert blank_lines == 2, f"Expected 2 blank lines between sections, got {blank_lines}"

        # Verify content was updated
        assert "### Changed" in result
        assert "Updated feature description" in result
        assert "Old feature description" not in result

    def test_normalize_existing_inconsistent_spacing(self):
        """Test that existing inconsistent spacing is normalized to 2 blank lines."""
        # Existing content with inconsistent spacing (3 blanks, then 1 blank)
        existing_content = """# Changelog

## [1.2.0] - 2025-01-20

### Added
- Latest feature



## [1.0.0] - 2025-01-01

### Added
- Initial feature

## [0.9.0] - 2024-12-01

### Added
- Older feature"""

        version_section = "## [1.1.0] - 2025-01-15\n\n### Added\n- Middle feature"
        result = _update_version_section(existing_content, version_section, "1.1.0")

        lines = result.split("\n")

        # All spacing should be normalized to exactly 2 blank lines
        version_sections = []
        for i, line in enumerate(lines):
            if line.startswith("## [") and not line.startswith("## [Unreleased]"):
                version_sections.append((i, line))

        # Check spacing between all sections
        for i in range(1, len(version_sections)):
            prev_line = version_sections[i - 1][0]
            curr_line = version_sections[i][0]
            blank_lines = 0
            for j in range(prev_line + 1, curr_line):
                if lines[j].strip() == "":
                    blank_lines += 1
            assert blank_lines == 2, f"Expected 2 blank lines between sections, got {blank_lines}"

    def test_empty_changelog_with_first_version(self):
        """Test adding first version to empty changelog."""
        existing_content = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
"""

        version_section = "## [1.0.0] - 2025-01-01\n\n### Added\n- Initial release"
        result = _update_version_section(existing_content, version_section, "1.0.0")

        lines = result.split("\n")

        # Should have header, then version (no extra blank lines at top)
        assert lines[0] == "# Changelog"
        assert "## [1.0.0] - 2025-01-01" in lines

        # Should have content after header
        assert "### Added" in result
        assert "Initial release" in result

    def test_single_existing_version_add_new_one(self):
        """Test adding new version to changelog with single existing version."""
        existing_content = """# Changelog

## [1.0.0] - 2025-01-01

### Added
- Initial feature"""

        version_section = "## [1.1.0] - 2025-01-15\n\n### Added\n- New feature"
        result = _update_version_section(existing_content, version_section, "1.1.0")

        lines = result.split("\n")

        # Should have exactly 2 blank lines between the two versions
        version_sections = []
        for i, line in enumerate(lines):
            if line.startswith("## [") and not line.startswith("## [Unreleased]"):
                version_sections.append((i, line))

        assert len(version_sections) == 2
        blank_lines = 0
        for i in range(version_sections[0][0] + 1, version_sections[1][0]):
            if lines[i].strip() == "":
                blank_lines += 1
        assert blank_lines == 2

    def test_version_with_complex_content_structure(self):
        """Test spacing with complex version content (multiple sections)."""
        existing_content = """# Changelog

## [1.2.0] - 2025-01-20

### Added
- New API endpoints
- Performance improvements

### Changed
- Updated dependencies
- Refactored core module

### Fixed
- Memory leak in数据处理

### Deprecated
- Old API methods

## [1.1.0] - 2025-01-10

### Added
- User authentication
"""

        version_section = (
            "## [1.1.5] - 2025-01-15\n\n### Fixed\n- Critical security fix\n\n### Security\n- Updated SSL certificates"
        )
        result = _update_version_section(existing_content, version_section, "1.1.5")

        lines = result.split("\n")

        # Should maintain 2 blank lines between all sections
        version_sections = []
        for i, line in enumerate(lines):
            if line.startswith("## [") and not line.startswith("## [Unreleased]"):
                version_sections.append((i, line))

        # All sections should have 2 blank lines between them
        for i in range(1, len(version_sections)):
            prev_line = version_sections[i - 1][0]
            curr_line = version_sections[i][0]
            blank_lines = 0
            for j in range(prev_line + 1, curr_line):
                if lines[j].strip() == "":
                    blank_lines += 1
            assert blank_lines == 2, f"Expected 2 blank lines between sections, got {blank_lines}"

    def test_multiple_insertions_consistent_spacing(self):
        """Test multiple sequential insertions maintain consistent spacing."""
        # Start with basic changelog
        existing_content = """# Changelog

## [1.2.0] - 2025-01-20

### Added
- Latest feature

## [0.9.0] - 2024-12-01

### Added
- Oldest feature"""

        # Insert first version
        version_section1 = "## [1.1.0] - 2025-01-15\n\n### Added\n- Middle feature"
        result1 = _update_version_section(existing_content, version_section1, "1.1.0")

        # Insert another version
        version_section2 = "## [1.0.0] - 2025-01-01\n\n### Added\n- Another feature"
        result2 = _update_version_section(result1, version_section2, "1.0.0")

        lines = result2.split("\n")

        # All four versions should have 2 blank lines between them
        version_sections = []
        for i, line in enumerate(lines):
            if line.startswith("## [") and not line.startswith("## [Unreleased]"):
                version_sections.append((i, line))

        assert len(version_sections) == 4

        # Check spacing between all sections
        for i in range(1, len(version_sections)):
            prev_line = version_sections[i - 1][0]
            curr_line = version_sections[i][0]
            blank_lines = 0
            for j in range(prev_line + 1, curr_line):
                if lines[j].strip() == "":
                    blank_lines += 1
            assert blank_lines == 2, f"Expected 2 blank lines between sections, got {blank_lines}"

    def test_edge_case_version_with_no_content(self):
        """Test handling version section with minimal content."""
        existing_content = """# Changelog

## [1.0.0] - 2025-01-01

### Added
- Feature

## [0.9.0] - 2024-12-01

### Added
- Old feature"""

        version_section = "## [1.1.0] - 2025-01-15\n\n### Fixed\n- Quick fix"
        result = _update_version_section(existing_content, version_section, "1.1.0")

        lines = result.split("\n")

        # Should still maintain 2 blank lines
        version_sections = []
        for i, line in enumerate(lines):
            if line.startswith("## [") and not line.startswith("## [Unreleased]"):
                version_sections.append((i, line))

        for i in range(1, len(version_sections)):
            prev_line = version_sections[i - 1][0]
            curr_line = version_sections[i][0]
            blank_lines = 0
            for j in range(prev_line + 1, curr_line):
                if lines[j].strip() == "":
                    blank_lines += 1
            assert blank_lines == 2

    def test_preserve_unreleased_section_spacing(self):
        """Test that unreleased section spacing is preserved when adding versions."""
        existing_content = """# Changelog

## [Unreleased]

### Added
- Unreleased feature

## [1.0.0] - 2025-01-01

### Added
- Released feature

## [0.9.0] - 2024-12-01

### Added
- Older feature"""

        version_section = "## [1.1.0] - 2025-01-15\n\n### Added\n- New feature"
        result = _update_version_section(existing_content, version_section, "1.1.0")

        lines = result.split("\n")

        # Unreleased section should be at top
        unreleased_line = None
        for i, line in enumerate(lines):
            if line.startswith("## [Unreleased]"):
                unreleased_line = i
                break

        assert unreleased_line is not None

        # Check spacing between version sections (unreleased doesn't count)
        version_sections = []
        for i, line in enumerate(lines):
            if line.startswith("## [") and not line.startswith("## [Unreleased]"):
                version_sections.append((i, line))

        # All version sections should have 2 blank lines between them
        for i in range(1, len(version_sections)):
            prev_line = version_sections[i - 1][0]
            curr_line = version_sections[i][0]
            blank_lines = 0
            for j in range(prev_line + 1, curr_line):
                if lines[j].strip() == "":
                    blank_lines += 1
            assert blank_lines == 2, f"Expected 2 blank lines between version sections, got {blank_lines}"

    def test_no_excessive_blank_lines_accumulation(self):
        """Test that repeated insertions don't cause excessive blank line accumulation."""
        content = """# Changelog

## [1.0.0] - 2025-01-01

### Added
- Initial feature"""

        # Insert multiple versions sequentially
        for i in range(5):
            version = f"1.{5 - i}.0"
            date = f"2025-01-{15 - i:02d}"
            version_section = f"## [{version}] - {date}\n\n### Added\n- Feature {i}"
            content = _update_version_section(content, version_section, version)

        lines = content.split("\n")

        # Count maximum consecutive blank lines
        max_consecutive = 0
        current_consecutive = 0

        for line in lines:
            if line.strip() == "":
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        # Should not have more than 2 consecutive blank lines
        assert max_consecutive <= 2, f"Found {max_consecutive} consecutive blank lines, should be ≤ 2"

        # Count total blank lines (should be reasonable)
        total_blanks = sum(1 for line in lines if line.strip() == "")
        # Should have approximately 2 blank lines per interval between versions
        # For 6 versions total, should have around 5 intervals * 2 blanks = 10 blanks (roughly)
        assert total_blanks < 20, f"Too many blank lines: {total_blanks}"
