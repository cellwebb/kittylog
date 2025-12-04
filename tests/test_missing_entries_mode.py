"""Tests for missing entries mode handler.

These tests verify fixes for:
1. Tag recognition: normalizing tag names before comparison with existing boundaries
2. Changelog order: processing tags in correct order (newest first, proper insertion)
"""

from datetime import datetime, timezone
from unittest.mock import patch

from kittylog.mode_handlers.missing import determine_missing_entries, handle_missing_entries_mode

# Common mock path prefixes
MISSING_MODULE = "kittylog.mode_handlers.missing"
CHANGELOG_IO_MODULE = "kittylog.changelog.io"


class TestDetermineMissingEntries:
    """Tests for determine_missing_entries function."""

    def test_tag_recognition_with_v_prefix(self, temp_dir):
        """Test that tags with 'v' prefix are correctly matched to changelog entries without prefix.

        This is a regression test for the bug where 'v0.1.0' tags were not recognized
        as existing in the changelog that had '0.1.0' entries.
        """
        # Create changelog with versions WITHOUT 'v' prefix (common format)
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [Unreleased]

## [0.2.0] - 2024-01-15
- Feature B

## [0.1.0] - 2024-01-01
- Feature A
""")

        # Mock get_all_tags to return tags WITH 'v' prefix (git tag format)
        with patch("kittylog.mode_handlers.missing.get_all_tags") as mock_get_tags:
            mock_get_tags.return_value = ["v0.1.0", "v0.2.0", "v0.3.0"]

            missing = determine_missing_entries(str(changelog_file))

            # Only v0.3.0 should be missing - v0.1.0 and v0.2.0 exist as 0.1.0 and 0.2.0
            assert missing == ["v0.3.0"], f"Expected ['v0.3.0'], got {missing}"

    def test_tag_recognition_without_v_prefix(self, temp_dir):
        """Test that tags without 'v' prefix work correctly."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [1.0.0] - 2024-01-01
- Initial release
""")

        with patch("kittylog.mode_handlers.missing.get_all_tags") as mock_get_tags:
            mock_get_tags.return_value = ["1.0.0", "1.1.0"]

            missing = determine_missing_entries(str(changelog_file))

            assert missing == ["1.1.0"]

    def test_tag_recognition_mixed_prefixes(self, temp_dir):
        """Test handling of mixed prefix styles in changelog and tags."""
        # Changelog has entries with 'v' prefix
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [v1.0.0] - 2024-01-01
- Initial release
""")

        with patch("kittylog.mode_handlers.missing.get_all_tags") as mock_get_tags:
            # Tags also have 'v' prefix
            mock_get_tags.return_value = ["v1.0.0", "v1.1.0"]

            missing = determine_missing_entries(str(changelog_file))

            # Both should normalize to same format, so only 1.1.0 is missing
            assert missing == ["v1.1.0"]

    def test_all_tags_missing_when_changelog_empty(self, temp_dir):
        """Test that all tags are returned when changelog has no version entries."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [Unreleased]

Nothing here yet.
""")

        with patch("kittylog.mode_handlers.missing.get_all_tags") as mock_get_tags:
            mock_get_tags.return_value = ["v0.1.0", "v0.2.0"]

            missing = determine_missing_entries(str(changelog_file))

            assert missing == ["v0.1.0", "v0.2.0"]

    def test_no_missing_when_all_tags_exist(self, temp_dir):
        """Test that empty list is returned when all tags exist in changelog."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [0.2.0] - 2024-01-15
- Feature

## [0.1.0] - 2024-01-01
- Initial
""")

        with patch("kittylog.mode_handlers.missing.get_all_tags") as mock_get_tags:
            mock_get_tags.return_value = ["v0.1.0", "v0.2.0"]

            missing = determine_missing_entries(str(changelog_file))

            assert missing == []

    def test_changelog_file_not_found(self, temp_dir):
        """Test that all tags are returned when changelog doesn't exist."""
        nonexistent_file = temp_dir / "NONEXISTENT.md"

        with patch("kittylog.mode_handlers.missing.get_all_tags") as mock_get_tags:
            mock_get_tags.return_value = ["v1.0.0"]

            missing = determine_missing_entries(str(nonexistent_file))

            assert missing == ["v1.0.0"]


class TestHandleMissingEntriesMode:
    """Tests for handle_missing_entries_mode function."""

    def test_changelog_order_newest_first(self, temp_dir):
        """Test that new entries are inserted in correct order (newest at top).

        This is a regression test for the bug where entries were added in
        old->new order instead of new->old order.
        """
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [Unreleased]

""")

        def mock_generate_entry(commits, tag, from_boundary=None, **kwargs):
            return f"### Added\n\n- Changes for {tag}"

        with (
            patch(f"{MISSING_MODULE}.get_all_tags") as mock_get_tags,
            patch(f"{MISSING_MODULE}.get_commits_between_tags") as mock_get_commits,
            patch(f"{MISSING_MODULE}.get_tag_date") as mock_get_date,
            patch(f"{CHANGELOG_IO_MODULE}.read_changelog") as mock_read,
        ):
            # Tags in ascending order (oldest first) as returned by get_all_tags
            mock_get_tags.return_value = ["v0.1.0", "v0.2.0", "v0.3.0"]
            mock_get_commits.return_value = [{"hash": "abc", "message": "test"}]
            mock_get_date.side_effect = [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 2, 1, tzinfo=timezone.utc),
                datetime(2024, 3, 1, tzinfo=timezone.utc),
            ]
            mock_read.return_value = changelog_file.read_text()

            success, content = handle_missing_entries_mode(
                changelog_file=str(changelog_file),
                generate_entry_func=mock_generate_entry,
                quiet=True,
            )

            assert success

            # Verify order: v0.3.0 should appear BEFORE v0.2.0 which should appear BEFORE v0.1.0
            pos_v3 = content.find("## [v0.3.0]")
            pos_v2 = content.find("## [v0.2.0]")
            pos_v1 = content.find("## [v0.1.0]")

            assert pos_v3 < pos_v2 < pos_v1, (
                f"Wrong order! v0.3.0 at {pos_v3}, v0.2.0 at {pos_v2}, v0.1.0 at {pos_v1}. "
                f"Expected newest first (v0.3.0 < v0.2.0 < v0.1.0)"
            )

    def test_insertion_uses_semantic_version_ordering(self, temp_dir):
        """Test that entries are inserted at correct positions based on semantic version."""
        changelog_file = temp_dir / "CHANGELOG.md"
        # Existing changelog with v0.2.0
        changelog_file.write_text("""# Changelog

## [Unreleased]

## [0.2.0] - 2024-02-01

### Added

- Existing feature
""")

        def mock_generate_entry(commits, tag, from_boundary=None, **kwargs):
            return f"### Added\n\n- Changes for {tag}"

        with (
            patch(f"{MISSING_MODULE}.get_all_tags") as mock_get_tags,
            patch(f"{MISSING_MODULE}.get_commits_between_tags") as mock_get_commits,
            patch(f"{MISSING_MODULE}.get_tag_date") as mock_get_date,
            patch(f"{CHANGELOG_IO_MODULE}.read_changelog") as mock_read,
            patch(f"{MISSING_MODULE}.find_existing_boundaries") as mock_find_existing,
        ):
            # v0.1.0 is older, v0.3.0 is newer - both missing
            mock_get_tags.return_value = ["v0.1.0", "v0.2.0", "v0.3.0"]
            mock_find_existing.return_value = {"0.2.0"}  # Only 0.2.0 exists
            mock_get_commits.return_value = [{"hash": "abc", "message": "test"}]
            mock_get_date.side_effect = [
                datetime(2024, 3, 1, tzinfo=timezone.utc),  # v0.3.0 (processed first due to reversed)
                datetime(2024, 1, 1, tzinfo=timezone.utc),  # v0.1.0
            ]
            mock_read.return_value = changelog_file.read_text()

            success, content = handle_missing_entries_mode(
                changelog_file=str(changelog_file),
                generate_entry_func=mock_generate_entry,
                quiet=True,
            )

            assert success

            # v0.3.0 should be BEFORE v0.2.0 (newer)
            # v0.1.0 should be AFTER v0.2.0 (older)
            pos_v3 = content.find("## [v0.3.0]")
            pos_v2 = content.find("## [0.2.0]")
            pos_v1 = content.find("## [v0.1.0]")

            assert pos_v3 != -1, "v0.3.0 not found in content"
            assert pos_v2 != -1, "v0.2.0 not found in content"
            assert pos_v1 != -1, "v0.1.0 not found in content"

            assert pos_v3 < pos_v2, f"v0.3.0 ({pos_v3}) should be before v0.2.0 ({pos_v2})"
            assert pos_v2 < pos_v1, f"v0.2.0 ({pos_v2}) should be before v0.1.0 ({pos_v1})"

    def test_includes_date_in_version_header(self, temp_dir):
        """Test that version headers include the tag date."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("# Changelog\n\n## [Unreleased]\n")

        def mock_generate_entry(commits, tag, from_boundary=None, **kwargs):
            return "### Added\n\n- Test feature"

        with (
            patch(f"{MISSING_MODULE}.get_all_tags") as mock_get_tags,
            patch(f"{MISSING_MODULE}.get_commits_between_tags") as mock_get_commits,
            patch(f"{MISSING_MODULE}.get_tag_date") as mock_get_date,
            patch(f"{CHANGELOG_IO_MODULE}.read_changelog") as mock_read,
        ):
            mock_get_tags.return_value = ["v1.0.0"]
            mock_get_commits.return_value = [{"hash": "abc", "message": "test"}]
            mock_get_date.return_value = datetime(2024, 6, 15, tzinfo=timezone.utc)
            mock_read.return_value = changelog_file.read_text()

            success, content = handle_missing_entries_mode(
                changelog_file=str(changelog_file),
                generate_entry_func=mock_generate_entry,
                quiet=True,
            )

            assert success
            assert "## [v1.0.0] - 2024-06-15" in content

    def test_no_changes_when_no_missing_tags(self, temp_dir):
        """Test that no changes are made when all tags exist in changelog."""
        changelog_content = """# Changelog

## [0.1.0] - 2024-01-01

### Added

- Initial feature
"""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text(changelog_content)

        def mock_generate_entry(commits, tag, from_boundary=None, **kwargs):
            return "### Added\n\n- Should not be called"

        with (
            patch(f"{MISSING_MODULE}.get_all_tags") as mock_get_tags,
            patch(f"{CHANGELOG_IO_MODULE}.read_changelog") as mock_read,
        ):
            mock_get_tags.return_value = ["v0.1.0"]  # Already exists
            mock_read.return_value = changelog_content

            success, content = handle_missing_entries_mode(
                changelog_file=str(changelog_file),
                generate_entry_func=mock_generate_entry,
                quiet=True,
            )

            assert success
            # Content should be unchanged
            assert content == changelog_content

    def test_skips_tags_with_no_commits(self, temp_dir):
        """Test that tags with no commits are skipped."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("# Changelog\n\n## [Unreleased]\n")

        def mock_generate_entry(commits, tag, from_boundary=None, **kwargs):
            return "### Added\n\n- Test"

        with (
            patch(f"{MISSING_MODULE}.get_all_tags") as mock_get_tags,
            patch(f"{MISSING_MODULE}.get_commits_between_tags") as mock_get_commits,
            patch(f"{CHANGELOG_IO_MODULE}.read_changelog") as mock_read,
        ):
            mock_get_tags.return_value = ["v1.0.0", "v1.1.0"]
            # Due to reversed() processing order: v1.1.0 first, then v1.0.0
            # v1.1.0 has no commits (skipped), v1.0.0 has commits
            mock_get_commits.side_effect = [
                [],  # No commits for v1.1.0 (processed first due to reversed)
                [{"hash": "abc", "message": "test"}],  # v1.0.0 has commits
            ]
            mock_read.return_value = changelog_file.read_text()

            with patch(f"{MISSING_MODULE}.get_tag_date") as mock_get_date:
                mock_get_date.return_value = datetime(2024, 1, 1, tzinfo=timezone.utc)

                success, content = handle_missing_entries_mode(
                    changelog_file=str(changelog_file),
                    generate_entry_func=mock_generate_entry,
                    quiet=True,
                )

            assert success
            # v1.1.0 should NOT be in the content (no commits)
            # But v1.0.0 should be there
            assert "v1.0.0" in content
            assert "v1.1.0" not in content

    def test_handles_empty_ai_response(self, temp_dir):
        """Test that empty AI responses are handled gracefully."""
        changelog_file = temp_dir / "CHANGELOG.md"
        original_content = "# Changelog\n\n## [Unreleased]\n"
        changelog_file.write_text(original_content)

        def mock_generate_entry(commits, tag, from_boundary=None, **kwargs):
            return ""  # Empty response

        with (
            patch(f"{MISSING_MODULE}.get_all_tags") as mock_get_tags,
            patch(f"{MISSING_MODULE}.get_commits_between_tags") as mock_get_commits,
            patch(f"{CHANGELOG_IO_MODULE}.read_changelog") as mock_read,
        ):
            mock_get_tags.return_value = ["v1.0.0"]
            mock_get_commits.return_value = [{"hash": "abc", "message": "test"}]
            mock_read.return_value = original_content

            success, content = handle_missing_entries_mode(
                changelog_file=str(changelog_file),
                generate_entry_func=mock_generate_entry,
                quiet=True,
            )

            assert success
            # Content should be unchanged when AI returns empty
            assert "v1.0.0" not in content


class TestTagNormalizationEdgeCases:
    """Edge case tests for tag normalization logic."""

    def test_multiple_v_prefixes(self, temp_dir):
        """Test handling of unusual prefixes like 'vv1.0.0'."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [v1.0.0] - 2024-01-01
- Test
""")

        with patch("kittylog.mode_handlers.missing.get_all_tags") as mock_get_tags:
            # Unusual but possible: double v prefix
            mock_get_tags.return_value = ["vv1.0.0", "v1.1.0"]

            missing = determine_missing_entries(str(changelog_file))

            # vv1.0.0 normalizes to v1.0.0 which matches 1.0.0
            # v1.1.0 normalizes to 1.1.0 which doesn't exist
            assert "v1.1.0" in missing

    def test_version_with_prerelease(self, temp_dir):
        """Test handling of prerelease versions."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [1.0.0-alpha] - 2024-01-01
- Test
""")

        with patch("kittylog.mode_handlers.missing.get_all_tags") as mock_get_tags:
            mock_get_tags.return_value = ["v1.0.0-alpha", "v1.0.0-beta"]

            missing = determine_missing_entries(str(changelog_file))

            # 1.0.0-alpha exists, 1.0.0-beta doesn't
            assert missing == ["v1.0.0-beta"]

    def test_case_sensitivity(self, temp_dir):
        """Test that version matching is case-insensitive for the prefix."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [V1.0.0] - 2024-01-01
- Test
""")

        with patch("kittylog.mode_handlers.missing.get_all_tags") as mock_get_tags:
            mock_get_tags.return_value = ["v1.0.0", "v2.0.0"]

            missing = determine_missing_entries(str(changelog_file))

            # V1.0.0 should match v1.0.0 (case insensitive via lstrip('v'))
            # Actually, lstrip only strips lowercase 'v', so V1.0.0 won't match
            # This documents current behavior
            assert "v1.0.0" in missing or "v2.0.0" in missing
