"""Test suite for changelog boundaries module."""

from kittylog.changelog.boundaries import (
    extract_version_boundaries,
    find_existing_boundaries,
    get_latest_version_in_changelog,
    is_version_in_changelog,
)


class TestFindExistingBoundaries:
    """Test the find_existing_boundaries function."""

    def test_finds_version_boundaries(self):
        """Test finding version boundaries."""
        content = """
# Changelog

## [1.0.0] - 2024-01-15

### Added
- New feature

## [0.5.0] - 2024-01-01

### Fixed
- Bug fix

## [Unreleased]
### Added
- Future feature
"""
        boundaries = find_existing_boundaries(content)
        assert "1.0.0" in boundaries
        assert "0.5.0" in boundaries
        assert "unreleased" not in boundaries  # Should be excluded

    def test_finds_version_boundaries_with_v_prefix(self):
        """Test finding version boundaries with 'v' prefix."""
        content = """
# Changelog

## [v1.0.0] - 2024-01-15

### Added
- New feature

## [v0.5.0] - 2024-01-01"""
        boundaries = find_existing_boundaries(content)
        assert "1.0.0" in boundaries  # 'v' should be stripped
        assert "0.5.0" in boundaries  # 'v' should be stripped
        assert "v1.0.0" not in boundaries  # Original with 'v' should not be included

    def test_finds_date_boundaries(self):
        """Test finding date-based boundaries."""
        content = """
# Changelog

## [2024-01-15]
### Added
- Feature

## [2024-01-01]
### Fixed
- Bug fix

## [Unreleased]
### Added
- Future feature
"""
        boundaries = find_existing_boundaries(content)
        assert "2024-01-15" in boundaries
        assert "2024-01-01" in boundaries
        assert "unreleased" not in boundaries

    def test_finds_gap_boundaries(self):
        """Test finding gap-based boundaries."""
        content = """
# Changelog

## [Gap-2024-01-15]

### Added
- Gap feature

## [Gap-2024-01-01]"""
        boundaries = find_existing_boundaries(content)
        assert "Gap-2024-01-15" in boundaries
        assert "Gap-2024-01-01" in boundaries

    def test_finds_nested_bracket_boundaries(self):
        """Test finding boundaries with nested brackets."""
        content = """
# Changelog

## [[2024-01-15] - January 15, 2024]

### Added
- Feature

## [[v1.0.0]]
### Added
- Version feature
"""
        boundaries = find_existing_boundaries(content)
        # Date boundaries in nested brackets are normalized to just the date
        assert "2024-01-15" in boundaries
        # Version boundaries in double brackets preserve the brackets
        assert "[v1.0.0]" in boundaries

    def test_handles_empty_content(self):
        """Test handling empty content."""
        boundaries = find_existing_boundaries("")
        assert boundaries == set()

    def test_handles_no_boundaries(self):
        """Test handling content with no boundaries."""
        content = """
# Changelog

This is just some regular content
without any version headers
"""
        boundaries = find_existing_boundaries(content)
        assert boundaries == set()

    def test_handles_unreleased_case_insensitive(self):
        """Test that unreleased is excluded case-insensitively."""
        content = """
# Changelog

## [Unreleased]
### Added
- Feature

## [UNRELEASED]
### Fixed
- Bug fix

## [unreleased]
### Changed
- Change
"""
        boundaries = find_existing_boundaries(content)
        assert boundaries == set()  # All should be excluded

    def test_handles_mixed_boundaries(self):
        """Test handling mixed types of boundaries."""
        content = """
# Changelog

## [1.0.0] - 2024-01-15
### Added
- Version feature

## [2024-01-15]
### Added
- Date feature

## [Gap-2024-01-15]
### Added
- Gap feature

## [Unreleased]
### Added
- Future feature
"""
        boundaries = find_existing_boundaries(content)
        assert "1.0.0" in boundaries
        assert "2024-01-15" in boundaries
        assert "Gap-2024-01-15" in boundaries
        assert "unreleased" not in boundaries

    def test_handles_invalid_version_patterns(self):
        """Test that invalid version patterns are not included."""
        content = """
# Changelog

## [1.0] - Invalid version (missing patch)
### Added
- Feature

## [not-a-version]
### Added
- Not a version

## [v1.0.0.0] - Too many parts
### Added
- Too many parts

## [v1.0] - Missing patch version
### Added
- Missing patch
"""
        boundaries = find_existing_boundaries(content)
        assert "1.0.0.0" not in boundaries  # Should be excluded
        assert "not-a-version" not in boundaries  # Should be excluded
        assert "1.0" not in boundaries  # Should be excluded (missing patch)
        assert "v1.0" not in boundaries  # Should be excluded (missing patch)


class TestExtractVersionBoundaries:
    """Test the extract_version_boundaries function."""

    def test_extracts_version_boundaries(self):
        """Test extracting version boundaries."""
        content = """
# Changelog

## [1.0.0] - 2024-01-15
### Added
- New feature

## [0.5.0] - 2024-01-01
### Fixed
- Bug fix

## [Unreleased]
### Added
- Future feature
"""
        boundaries = extract_version_boundaries(content)

        assert len(boundaries) == 2

        # Check first boundary
        assert boundaries[0]["identifier"] == "1.0.0"
        assert boundaries[0]["line"] == 4  # 0-indexed line number
        assert "## [1.0.0] - 2024-01-15" in boundaries[0]["raw_line"]

        # Check second boundary
        assert boundaries[1]["identifier"] == "0.5.0"
        assert boundaries[1]["line"] == 9  # 0-indexed line number
        assert "## [0.5.0] - 2024-01-01" in boundaries[1]["raw_line"]

    def test_extracts_version_boundaries_with_v_prefix(self):
        """Test extracting version boundaries with 'v' prefix."""
        content = """
# Changelog

## [v1.0.0] - 2024-01-15
### Added
- New feature

## [v0.5.0]
### Fixed
- Bug fix
"""
        boundaries = extract_version_boundaries(content)

        assert len(boundaries) == 2
        assert boundaries[0]["identifier"] == "v1.0.0"  # Keep 'v' prefix
        assert boundaries[1]["identifier"] == "v0.5.0"  # Keep 'v' prefix

    def test_excludes_unreleased(self):
        """Test that unreleased is excluded."""
        content = """
# Changelog

## [1.0.0] - 2024-01-15
### Added
- New feature

## [Unreleased]
### Added
- Future feature

## [0.5.0]
### Fixed
- Bug fix
"""
        boundaries = extract_version_boundaries(content)

        assert len(boundaries) == 2  # Only versions, not unreleased
        identifiers = [b["identifier"] for b in boundaries]
        assert "1.0.0" in identifiers
        assert "0.5.0" in identifiers
        assert "Unreleased" not in identifiers

    def test_excludes_non_version_boundaries(self):
        """Test that non-version boundaries are excluded."""
        content = """
# Changelog

## [1.0.0] - 2024-01-15
### Added
- Version

## [2024-01-15]
### Added
- Date (not a version)

## [Gap-2024-01-15]
### Added
- Gap (not a version)
"""
        boundaries = extract_version_boundaries(content)

        assert len(boundaries) == 1  # Only version boundaries
        assert boundaries[0]["identifier"] == "1.0.0"
        assert boundaries[0]["line"] == 4

    def test_handles_empty_content(self):
        """Test handling empty content."""
        boundaries = extract_version_boundaries("")
        assert boundaries == []

    def test_handles_no_version_boundaries(self):
        """Test handling content with no version boundaries."""
        content = """
# Changelog

## [Unreleased]
### Added
- Future feature

## [2024-01-15]
### Added
- Date feature
"""
        boundaries = extract_version_boundaries(content)
        assert boundaries == []


class TestGetLatestVersionInChangelog:
    """Test the get_latest_version_in_changelog function."""

    def test_returns_latest_version(self):
        """Test returning the latest version."""
        content = """
# Changelog

## [1.0.0] - 2024-01-15
### Added
- New feature

## [0.5.0] - 2024-01-01
### Fixed
- Bug fix
"""
        latest = get_latest_version_in_changelog(content)
        assert latest == "1.0.0"

    def test_returns_latest_with_v_prefix(self):
        """Test returning latest version with 'v' prefix."""
        content = """
# Changelog

## [v1.0.0] - 2024-01-15
### Added
- New feature

## [v0.5.0] - 2024-01-01
### Fixed
- Bug fix
"""
        latest = get_latest_version_in_changelog(content)
        assert latest == "v1.0.0"

    def test_returns_none_when_no_versions(self):
        """Test returning None when no version boundaries exist."""
        content = """
# Changelog

## [Unreleased]
### Added
- Future feature

## [2024-01-15]
### Added
- Date feature
"""
        latest = get_latest_version_in_changelog(content)
        assert latest is None

    def test_returns_none_for_empty_content(self):
        """Test returning None for empty content."""
        latest = get_latest_version_in_changelog("")
        assert latest is None


class TestIsVersionInChangelog:
    """Test the is_version_in_changelog function."""

    def test_finds_exact_version(self):
        """Test finding exact version match."""
        content = """
# Changelog

## [1.0.0] - 2024-01-15
### Added
- New feature

## [0.5.0] - 2024-01-01
### Fixed
- Bug fix
"""
        assert is_version_in_changelog(content, "1.0.0") is True
        assert is_version_in_changelog(content, "0.5.0") is True

    def test_finds_version_with_v_prefix(self):
        """Test finding version when changelog has 'v' prefix."""
        content = """
# Changelog

## [v1.0.0] - 2024-01-15
### Added
- New feature
"""
        # Should find regardless of 'v' prefix
        assert is_version_in_changelog(content, "1.0.0") is True
        assert is_version_in_changelog(content, "v1.0.0") is True

    def test_finds_version_without_v_prefix(self):
        """Test finding version when changelog doesn't have 'v' prefix."""
        content = """
# Changelog

## [1.0.0] - 2024-01-15
### Added
- New feature
"""
        # Should find regardless of 'v' prefix
        assert is_version_in_changelog(content, "1.0.0") is True
        assert is_version_in_changelog(content, "v1.0.0") is True

    def test_returns_false_for_nonexistent_version(self):
        """Test returning False for version that doesn't exist."""
        content = """
# Changelog

## [1.0.0] - 2024-01-15
### Added
- New feature
"""
        assert is_version_in_changelog(content, "2.0.0") is False
        assert is_version_in_changelog(content, "0.1.0") is False
        assert is_version_in_changelog(content, "not-a-version") is False

    def test_handles_empty_content(self):
        """Test handling empty content."""
        assert is_version_in_changelog("", "1.0.0") is False

    def test_handles_non_version_boundaries(self):
        """Test handling non-version boundaries."""
        content = """
# Changelog

## [Unreleased]
### Added
- Future feature

## [2024-01-15]
### Added
- Date feature
"""
        assert is_version_in_changelog(content, "1.0.0") is False
        assert is_version_in_changelog(content, "Unreleased") is False
        assert is_version_in_changelog(content, "2024-01-15") is False
