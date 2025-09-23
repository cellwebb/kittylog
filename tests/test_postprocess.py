"""Tests for changelog postprocessing module."""

from kittylog.postprocess import (
    clean_duplicate_sections,
    ensure_newlines_around_section_headers,
    postprocess_changelog_content,
    remove_unreleased_sections,
)


class TestEnsureNewlinesAroundSectionHeaders:
    """Test ensure_newlines_around_section_headers function."""

    def test_adds_newlines_around_version_headers(self):
        """Test that proper newlines are added around version section headers."""
        lines = [
            "# Changelog",
            "",
            "All notable changes to this project will be documented in this file.",
            "## [1.0.0]",
            "### Added",
            "- New feature",
            "## [0.1.0]",
        ]

        result = ensure_newlines_around_section_headers(lines)

        # Check that blank lines are added around version headers
        assert result[3] == ""  # Blank line before first version header
        assert result[5] == ""  # Blank line after first version header
        assert result[9] == ""  # Blank line before second version header

    def test_adds_newlines_around_category_headers(self):
        """Test that proper newlines are added around category section headers."""
        lines = ["## [1.0.0]", "### Added", "- New feature", "### Changed", "- Improvement"]

        result = ensure_newlines_around_section_headers(lines)

        # Check that blank lines are added around category headers
        assert result[1] == ""  # Blank line before first category header
        assert result[3] == ""  # Blank line after first category header
        assert result[5] == ""  # Blank line after second category header

    def test_handles_empty_lines_correctly(self):
        """Test that existing empty lines are handled properly."""
        lines = [
            "# Changelog",
            "",  # Already has blank line
            "## [1.0.0]",
            "",  # Already has blank line
            "### Added",
            "- New feature",
        ]

        result = ensure_newlines_around_section_headers(lines)

        # Should not add duplicate blank lines
        assert result[:3] == ["# Changelog", "", ""]  # Header + blank line + version header
        assert result[4] == ""  # Still has blank line after version header


class TestCleanDuplicateSections:
    """Test clean_duplicate_sections function."""

    def test_removes_duplicate_section_headers(self):
        """Test that duplicate section headers are removed."""
        lines = [
            "## [1.0.0]",
            "### Added",
            "- Feature 1",
            "### Added",  # Duplicate
            "- Feature 2",
            "### Changed",
            "- Change 1",
            "### Changed",  # Duplicate
            "- Change 2",
        ]

        result = clean_duplicate_sections(lines)

        # Should only keep first occurrence of each section
        expected = ["## [1.0.0]", "### Added", "- Feature 1", "- Feature 2", "### Changed", "- Change 1", "- Change 2"]
        assert result == expected

    def test_preserves_non_duplicate_headers(self):
        """Test that non-duplicate headers are preserved."""
        lines = ["## [1.0.0]", "### Added", "- Feature 1", "### Changed", "- Change 1", "### Fixed", "- Fix 1"]

        result = clean_duplicate_sections(lines)

        # Should preserve all unique headers
        assert result == lines


class TestRemoveUnreleasedSections:
    """Test remove_unreleased_sections function."""

    def test_removes_unreleased_section_and_content(self):
        """Test that unreleased sections and their content are completely removed."""
        lines = [
            "# Changelog",
            "",
            "## [Unreleased]",
            "### Added",
            "- Unreleased feature",
            "### Changed",
            "- Unreleased change",
            "",
            "## [1.0.0]",
            "### Added",
            "- Released feature",
        ]

        result = remove_unreleased_sections(lines)

        # Should remove the Unreleased section and all its content
        expected = ["# Changelog", "", "## [1.0.0]", "### Added", "- Released feature"]
        assert result == expected

    def test_removes_unreleased_with_different_casing(self):
        """Test that unreleased sections are removed regardless of casing."""
        lines = [
            "# Changelog",
            "",
            "## [UNRELEASED]",  # All caps
            "### Added",
            "- Feature",
            "",
            "## [1.0.0]",
            "### Added",
            "- Released feature",
        ]

        result = remove_unreleased_sections(lines)

        # Should remove the UNRELEASED section and all its content
        expected = ["# Changelog", "", "## [1.0.0]", "### Added", "- Released feature"]
        assert result == expected

    def test_preserves_other_sections(self):
        """Test that non-Unreleased sections are preserved."""
        lines = ["# Changelog", "", "## [1.0.0]", "### Added", "- Feature", "", "## [0.1.0]", "### Changed", "- Change"]

        result = remove_unreleased_sections(lines)

        # Should preserve all sections when no Unreleased section exists
        assert result == lines


class TestPostprocessChangelogContent:
    """Test postprocess_changelog_content function."""

    def test_complete_postprocessing_pipeline(self):
        """Test the complete postprocessing pipeline with all steps."""
        content = """# Changelog

## [1.0.0]
### Added
- Feature 1
- Feature 2

### Added
- Duplicate feature section
## [0.1.0]"""

        result = postprocess_changelog_content(content)

        # Should apply all postprocessing steps
        assert "### Added" in result
        # Should remove duplicates and ensure proper spacing
        lines = result.split("\n")
        assert lines.count("### Added") == 1  # Only one occurrence

    def test_removes_unreleased_when_tagged(self):
        """Test that unreleased sections are removed when current commit is tagged."""
        content = """# Changelog

## [Unreleased]
### Added
- Unreleased feature

## [1.0.0]
### Added
- Released feature"""

        result = postprocess_changelog_content(content, is_current_commit_tagged=True)

        # Should remove Unreleased section entirely
        assert "## [Unreleased]" not in result
        assert "Unreleased feature" not in result
        assert "## [1.0.0]" in result
        assert "Released feature" in result

    def test_preserves_unreleased_when_untagged(self):
        """Test that unreleased sections are preserved when current commit is not tagged."""
        content = """# Changelog

## [Unreleased]
### Added
- Unreleased feature

## [1.0.0]"""

        result = postprocess_changelog_content(content, is_current_commit_tagged=False)

        # Should preserve Unreleased section
        assert "## [Unreleased]" in result
        assert "Unreleased feature" in result
