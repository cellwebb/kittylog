"""Tests for changelog/io module."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from kittylog.changelog.io import (
    _ensure_spacing_between_entries,
    backup_changelog,
    create_changelog_header,
    ensure_changelog_exists,
    get_changelog_stats,
    prepare_release,
    read_changelog,
    validate_changelog_format,
    write_changelog,
)
from kittylog.errors import ChangelogError


class TestCreateChangelogHeader:
    """Test create_changelog_header function."""

    def test_create_changelog_header_default(self):
        """Test basic changelog header creation."""
        header = create_changelog_header()
        assert header == "# Changelog\n\n"


class TestReadChangelog:
    """Test read_changelog function."""

    def test_read_changelog_existing_file(self):
        """Test reading existing changelog file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            f.write("# Changelog\n\n## [1.0.0]\n### Added\n- Feature 1")
            f.flush()

            content = read_changelog(f.name)
            assert "# Changelog" in content
            assert "## [1.0.0]" in content
            assert "Feature 1" in content

            Path(f.name).unlink()

    def test_read_changelog_file_not_found(self):
        """Test reading non-existent file returns empty string."""
        content = read_changelog("/nonexistent/file.md")
        assert content == ""

    def test_read_changelog_permission_error(self):
        """Test reading file with permission error."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            f.flush()

            with (
                patch("pathlib.Path.read_text", side_effect=PermissionError("Permission denied")),
                pytest.raises(PermissionError),
            ):
                read_changelog(f.name)

            Path(f.name).unlink()

    def test_read_changelog_unicode_error(self):
        """Test reading file with unicode decode error."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Write some binary data that will cause decode error
            f.write(b"\xff\xfe")
            f.flush()

            with (
                patch("pathlib.Path.read_text", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")),
                pytest.raises(UnicodeDecodeError),
            ):
                read_changelog(f.name)

            Path(f.name).unlink()


class TestWriteChangelog:
    """Test write_changelog function."""

    def test_write_changelog_new_file(self):
        """Test writing to a new file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_changelog.md"
            content = "# Changelog\n\n## [1.0.0]\n### Added\n- Feature 1"

            write_changelog(str(file_path), content)

            assert file_path.exists()
            read_content = file_path.read_text(encoding="utf-8")
            assert read_content == content

    def test_write_changelog_existing_file(self):
        """Test overwriting existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_changelog.md"
            file_path.write_text("Old content", encoding="utf-8")

            new_content = "# Changelog\n\n## [1.0.0]\n### Added\n- Feature 1"
            write_changelog(str(file_path), new_content)

            read_content = file_path.read_text(encoding="utf-8")
            assert read_content == new_content

    def test_write_changelog_creates_directory(self):
        """Test that write_changelog creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "nested" / "dir" / "changelog.md"
            content = "# Changelog\n\n"

            write_changelog(str(nested_path), content)

            assert nested_path.exists()
            assert nested_path.parent.exists()
            read_content = nested_path.read_text(encoding="utf-8")
            assert read_content == content

    def test_write_changelog_permission_error(self):
        """Test handling permission error during write."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "changelog.md"
            content = "# Changelog\n\n"

            with patch("pathlib.Path.write_text", side_effect=PermissionError("Permission denied")):
                with pytest.raises(ChangelogError) as exc_info:
                    write_changelog(str(file_path), content)

                assert "Failed to write changelog file" in str(exc_info.value)
                assert exc_info.value.file_path == str(file_path)

    def test_write_changelog_file_not_found_error(self):
        """Test handling file not found error during write."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "changelog.md"
            content = "# Changelog\n\n"

            with patch("pathlib.Path.write_text", side_effect=FileNotFoundError("File not found")):
                with pytest.raises(ChangelogError) as exc_info:
                    write_changelog(str(file_path), content)

                assert "Failed to write changelog file" in str(exc_info.value)

    def test_write_changelog_os_error(self):
        """Test handling OS error during write."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "changelog.md"
            content = "# Changelog\n\n"

            with patch("pathlib.Path.write_text", side_effect=OSError("Disk full")):
                with pytest.raises(ChangelogError) as exc_info:
                    write_changelog(str(file_path), content)

                assert "Failed to write changelog file" in str(exc_info.value)


class TestEnsureChangelogExists:
    """Test ensure_changelog_exists function."""

    def test_ensure_changelog_exists_nonexistent(self):
        """Test creating new changelog when none exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "CHANGELOG.md"

            content = ensure_changelog_exists(str(file_path))

            assert file_path.exists()
            assert content == "# Changelog\n\n"

            read_content = file_path.read_text(encoding="utf-8")
            assert read_content == "# Changelog\n\n"

    def test_ensure_changelog_exists_empty_file(self):
        """Test handling existing but empty changelog file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "CHANGELOG.md"
            file_path.write_text("", encoding="utf-8")

            content = ensure_changelog_exists(str(file_path))

            assert content == "# Changelog\n\n"

            read_content = file_path.read_text(encoding="utf-8")
            assert read_content == "# Changelog\n\n"

    def test_ensure_changelog_exists_whitespace_only(self):
        """Test handling existing changelog with only whitespace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "CHANGELOG.md"
            file_path.write_text("   \n\n  ", encoding="utf-8")

            content = ensure_changelog_exists(str(file_path))

            assert content == "# Changelog\n\n"

    def test_ensure_changelog_exists_existing_content(self):
        """Test returning existing content when file exists and has content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "CHANGELOG.md"
            existing_content = "# Changelog\n\n## [1.0.0]\n### Added\n- Feature"
            file_path.write_text(existing_content, encoding="utf-8")

            content = ensure_changelog_exists(str(file_path))

            assert content == existing_content


class TestBackupChangelog:
    """Test backup_changelog function."""

    def test_backup_changelog_existing_file(self):
        """Test creating backup of existing changelog."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "CHANGELOG.md"
            content = "# Changelog\n\n## [1.0.0]\n### Added\n- Feature"
            file_path.write_text(content, encoding="utf-8")

            backup_path = backup_changelog(str(file_path))

            assert backup_path  # Should return a path string
            assert backup_path != ""  # Should not be empty for existing file
            assert backup_path.endswith(".md")
            assert Path(backup_path).exists()

            backup_content = Path(backup_path).read_text(encoding="utf-8")
            assert backup_content == content

    def test_backup_changelog_nonexistent_file(self):
        """Test handling backup of non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nonexistent.md"

            backup_path = backup_changelog(str(file_path))

            assert backup_path == ""
            assert not Path(backup_path).exists() if backup_path else True

    def test_backup_changelog_os_error(self):
        """Test handling OS error during backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "CHANGELOG.md"
            file_path.write_text("content", encoding="utf-8")

            with patch("shutil.copy2", side_effect=OSError("Permission denied")), pytest.raises(OSError):
                backup_changelog(str(file_path))

    def test_backup_changelog_shutil_error(self):
        """Test handling shutil error during backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "CHANGELOG.md"
            file_path.write_text("content", encoding="utf-8")

            with patch("shutil.copy2", side_effect=shutil.Error("Copy error")), pytest.raises(shutil.Error):
                backup_changelog(str(file_path))


class TestValidateChangelogFormat:
    """Test validate_changelog_format function."""

    def test_validate_changelog_format_empty(self):
        """Test validation of empty content."""
        warnings = validate_changelog_format("")
        assert warnings == []

    def test_validate_changelog_format_whitespace_only(self):
        """Test validation of whitespace-only content."""
        warnings = validate_changelog_format("   \n\n  ")
        assert warnings == []

    def test_validate_changelog_format_missing_header(self):
        """Test validation of content without header."""
        content = "## [1.0.0]\n### Added\n- Feature"
        warnings = validate_changelog_format(content)

        assert len(warnings) == 1
        assert "Missing changelog header" in warnings[0]

    def test_validate_changelog_format_no_version_sections(self):
        """Test validation of content without version sections."""
        content = "# Changelog\n\nSome random content"
        warnings = validate_changelog_format(content)

        assert len(warnings) == 2  # Both version and section warnings
        assert any("version sections" in w for w in warnings)
        assert any("standard sections" in w for w in warnings)

    def test_validate_changelog_format_has_unreleased_section(self):
        """Test validation with unreleased section passes version check."""
        content = "# Changelog\n\n## [Unreleased]\n### Added\n- Feature"
        warnings = validate_changelog_format(content)

        # Should not warn about missing versions if unreleased exists
        version_warnings = [w for w in warnings if "version sections" in w]
        assert len(version_warnings) == 0

    def test_validate_changelog_format_no_standard_sections(self):
        """Test validation of content without standard sections."""
        content = "# Changelog\n\n## [1.0.0]\n- Random bullet point"
        warnings = validate_changelog_format(content)

        assert len(warnings) == 1
        assert "No standard sections found" in warnings[0]

    def test_validate_changelog_format_valid_content(self):
        """Test validation of properly formatted content."""
        content = """# Changelog

## [1.0.0]
### Added
- Feature 1

### Fixed
- Bug fix 1
"""
        warnings = validate_changelog_format(content)

        assert warnings == []


class TestGetChangelogStats:
    """Test get_changelog_stats function."""

    def test_get_changelog_stats_existing_file(self):
        """Test getting stats from existing changelog."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "CHANGELOG.md"
            content = """# Changelog

## [1.0.0]
### Added
- Feature 1

### Fixed
- Bug 1

## [1.1.0]
### Added
- Feature 2
"""
            file_path.write_text(content, encoding="utf-8")

            stats = get_changelog_stats(str(file_path))

            assert stats["file_path"] == str(file_path)
            assert stats["exists"] is True
            assert stats["line_count"] == 13
            assert stats["size_bytes"] > 0
            assert stats["version_count"] == 2
            assert stats["has_unreleased"] is False
            assert stats["section_counts"]["added"] == 2
            assert stats["section_counts"]["fixed"] == 1

    def test_get_changelog_stats_with_unreleased(self):
        """Test getting stats with unreleased section."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "CHANGELOG.md"
            content = """# Changelog

## [Unreleased]
### Added
- Feature 1
"""
            file_path.write_text(content, encoding="utf-8")

            stats = get_changelog_stats(str(file_path))

            assert stats["has_unreleased"] is True
            assert stats["version_count"] == 0  # Unreleased doesn't count

    def test_get_changelog_stats_nonexistent_file(self):
        """Test getting stats from non-existent file."""
        stats = get_changelog_stats("/nonexistent/file.md")

        assert stats["exists"] is False
        assert stats["file_path"] == "/nonexistent/file.md"
        assert stats["line_count"] == 1  # Empty string split gives 1 line
        assert stats["size_bytes"] == 0  # Empty content has 0 bytes

    def test_get_changelog_stats_unicode_error(self):
        """Test handling unicode decode error."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"\xff\xfe")
            f.flush()

            stats = get_changelog_stats(f.name)

            assert "error" in stats

            Path(f.name).unlink()


class TestPrepareRelease:
    """Test prepare_release function."""

    def test_prepare_release_with_unreleased_section(self):
        """Test preparing release with unreleased section."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "CHANGELOG.md"
            content = """# Changelog

## [Unreleased]
### Added
- Feature 1
- Feature 2

### Fixed
- Bug 1
"""
            file_path.write_text(content, encoding="utf-8")

            # Test that it works without mocking date format
            updated_content = prepare_release(str(file_path), "1.0.0")

            assert "## [1.0.0]" in updated_content
            assert "## [Unreleased]" not in updated_content
            assert "Feature 1" in updated_content
            assert "Feature 2" in updated_content
            assert "Bug 1" in updated_content

            # File should be updated
            read_content = file_path.read_text(encoding="utf-8")
            assert "## [1.0.0]" in read_content

    def test_prepare_release_no_unreleased_section(self):
        """Test preparing release without unreleased section."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "CHANGELOG.md"
            content = """# Changelog

## [0.9.0]
### Added
- Old feature
"""
            file_path.write_text(content, encoding="utf-8")

            updated_content = prepare_release(str(file_path), "1.0.0")

            # Should not add new version if no unreleased section
            assert content == updated_content
            # File should still be updated (written back)
            read_content = file_path.read_text(encoding="utf-8")
            assert read_content == content

    def test_prepare_release_with_version_links(self):
        """Test preparing release adds version link references."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "CHANGELOG.md"
            content = """# Changelog

## [Unreleased]
### Added
- Feature 1

[0.9.0]: https://github.com/repo/releases/tag/v0.9.0
[1.0.0]: https://github.com/repo/releases/tag/v1.0.0
"""
            file_path.write_text(content, encoding="utf-8")

            updated_content = prepare_release(str(file_path), "1.1.0")

            assert "## [1.1.0]" in updated_content
            assert "[1.1.0]: https://github.com/repo/releases/tag/v1.1.0" in updated_content

    def test_prepare_release_version_with_v_prefix(self):
        """Test preparing release with version that has 'v' prefix."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "CHANGELOG.md"
            content = """# Changelog

## [Unreleased]
### Added
- Feature 1
"""
            file_path.write_text(content, encoding="utf-8")

            updated_content = prepare_release(str(file_path), "v1.0.0")

            # Version should be present (with or without v prefix removed depending on implementation)
            assert "[1.0.0]" in updated_content

    def test_prepare_release_empty_file(self):
        """Test preparing release with empty changelog file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "CHANGELOG.md"
            file_path.write_text("", encoding="utf-8")

            with pytest.raises(ChangelogError) as exc_info:
                prepare_release(str(file_path), "1.0.0")

            assert "is empty or does not exist" in str(exc_info.value)
            assert exc_info.value.file_path == str(file_path)


class TestEnsureSpacingBetweenEntries:
    """Test _ensure_spacing_between_entries function."""

    def test_ensure_spacing_after_header(self):
        """Test proper spacing after changelog header."""
        content = "# Changelog\n\n\n\n## [1.0.0]\n### Added\n- Feature"
        result = _ensure_spacing_between_entries(content)

        # Should normalize to exactly 1 blank line
        assert "# Changelog\n\n## [1.0.0]" in result
        assert result.count("\n\n") == 1  # Just one blank line between header and version

    def test_ensure_spacing_between_versions(self):
        """Test proper spacing between version entries."""
        content = """# Changelog

## [1.0.0]
### Added
- Feature 1



## [1.1.0]
### Added
- Feature 2
"""
        result = _ensure_spacing_between_entries(content)

        # Should normalize to exactly 1 blank line between versions
        lines = result.split("\n")
        version_lines = [i for i, line in enumerate(lines) if line.startswith("## [")]

        if len(version_lines) >= 2:
            _, line2_idx = version_lines[:2]
            # Check there's exactly 1 blank line between versions
            assert lines[line2_idx - 1] == ""  # One blank line
            assert not (lines[line2_idx - 2] == "" and lines[line2_idx - 3] == "")  # Not multiple

    def test_ensure_spacing_unchanged_content(self):
        """Test that properly spaced content remains unchanged."""
        content = """# Changelog

## [1.0.0]
### Added
- Feature 1

## [1.1.0]
### Added
- Feature 2
"""
        result = _ensure_spacing_between_entries(content)

        # Should be unchanged
        assert content == result

    def test_ensure_spacing_bullet_points_before_version(self):
        """Test spacing when bullet points precede version."""
        content = """# Changelog

- Last item from previous version

- Another item



## [1.0.0]
### Added
- New feature
"""
        result = _ensure_spacing_between_entries(content)

        # Should normalize to 1 blank line between bullets and next version
        assert "- Another item\n\n## [1.0.0]" in result
        assert "\n\n\n## [" not in result  # No multiple blank lines
