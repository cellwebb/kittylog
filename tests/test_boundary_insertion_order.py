"""Tests for boundary insertion order in changelog generation.

These tests are regression tests to ensure that changelog entries are always
inserted in the correct order (newest first) for all boundary modes.

The bug: When inserting at a fixed position, each new insert pushes existing
content down. If we iterate newest→oldest (reversed), the oldest entry ends up
on top. We must iterate oldest→newest so the newest entry ends up on top.

This affects:
- handle_update_all_mode in boundary.py (dates and gaps modes)
- handle_missing_entries_mode in missing.py (dates and gaps modes)
"""

from datetime import datetime, timezone
from unittest.mock import patch

from kittylog.mode_handlers.boundary import handle_update_all_mode
from kittylog.mode_handlers.missing import handle_missing_entries_mode

# Common mock path prefixes
BOUNDARY_MODULE = "kittylog.mode_handlers.boundary"
MISSING_MODULE = "kittylog.mode_handlers.missing"
CHANGELOG_IO_MODULE = "kittylog.changelog.io"


class TestUpdateAllModeDateBoundaryOrder:
    """Tests for handle_update_all_mode with dates mode insertion order."""

    def test_date_boundaries_inserted_newest_first(self, temp_dir):
        """Test that date boundaries are inserted with newest at top.

        This is the core regression test for the insertion order bug.
        When processing boundaries [Sept, Oct, Nov, Dec] (chronological),
        the resulting changelog should have [Dec, Nov, Oct, Sept] order.
        """
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [Unreleased]

""")

        def mock_generate_entry(commits, tag, from_boundary=None, **kwargs):
            return f"### Added\n\n- Changes for {tag}"

        with (
            patch(f"{BOUNDARY_MODULE}.get_all_boundaries") as mock_get_boundaries,
            patch(f"{BOUNDARY_MODULE}.get_commits_between_boundaries") as mock_get_commits,
            patch(f"{CHANGELOG_IO_MODULE}.write_changelog"),
        ):
            # Boundaries returned in chronological order (oldest first)
            mock_get_boundaries.return_value = [
                {
                    "identifier": "2024-09-30",
                    "date": datetime(2024, 9, 30, tzinfo=timezone.utc),
                    "hash": "abc123",
                    "mode": "dates",
                },
                {
                    "identifier": "2024-10-31",
                    "date": datetime(2024, 10, 31, tzinfo=timezone.utc),
                    "hash": "def456",
                    "mode": "dates",
                },
                {
                    "identifier": "2024-11-30",
                    "date": datetime(2024, 11, 30, tzinfo=timezone.utc),
                    "hash": "ghi789",
                    "mode": "dates",
                },
                {
                    "identifier": "2024-12-31",
                    "date": datetime(2024, 12, 31, tzinfo=timezone.utc),
                    "hash": "jkl012",
                    "mode": "dates",
                },
            ]
            mock_get_commits.return_value = [{"hash": "abc", "message": "test commit"}]

            success, content = handle_update_all_mode(
                changelog_file=str(changelog_file),
                generate_entry_func=mock_generate_entry,
                mode="dates",
                quiet=True,
                dry_run=True,  # Don't actually write
            )

            assert success

            # Verify order: December should appear BEFORE November, etc.
            pos_dec = content.find("## [2024-12-31]")
            pos_nov = content.find("## [2024-11-30]")
            pos_oct = content.find("## [2024-10-31]")
            pos_sep = content.find("## [2024-09-30]")

            assert pos_dec != -1, "December entry not found"
            assert pos_nov != -1, "November entry not found"
            assert pos_oct != -1, "October entry not found"
            assert pos_sep != -1, "September entry not found"

            assert pos_dec < pos_nov < pos_oct < pos_sep, (
                f"Wrong order! Expected newest first.\n"
                f"Dec at {pos_dec}, Nov at {pos_nov}, Oct at {pos_oct}, Sep at {pos_sep}\n"
                f"Expected: Dec < Nov < Oct < Sep"
            )

    def test_date_boundaries_with_existing_versions(self, temp_dir):
        """Test date boundaries are inserted correctly when changelog has existing content."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [Unreleased]

## [1.0.0] - 2024-01-01

### Added

- Existing feature
""")

        def mock_generate_entry(commits, tag, from_boundary=None, **kwargs):
            return f"### Added\n\n- Changes for {tag}"

        with (
            patch(f"{BOUNDARY_MODULE}.get_all_boundaries") as mock_get_boundaries,
            patch(f"{BOUNDARY_MODULE}.get_commits_between_boundaries") as mock_get_commits,
            patch(f"{CHANGELOG_IO_MODULE}.write_changelog"),
        ):
            mock_get_boundaries.return_value = [
                {
                    "identifier": "2024-06-15",
                    "date": datetime(2024, 6, 15, tzinfo=timezone.utc),
                    "hash": "abc123",
                    "mode": "dates",
                },
                {
                    "identifier": "2024-06-30",
                    "date": datetime(2024, 6, 30, tzinfo=timezone.utc),
                    "hash": "def456",
                    "mode": "dates",
                },
            ]
            mock_get_commits.return_value = [{"hash": "abc", "message": "test"}]

            success, content = handle_update_all_mode(
                changelog_file=str(changelog_file),
                generate_entry_func=mock_generate_entry,
                mode="dates",
                quiet=True,
                dry_run=True,
            )

            assert success

            # New entries should be between Unreleased and existing 1.0.0
            pos_unreleased = content.find("## [Unreleased]")
            pos_jun30 = content.find("## [2024-06-30]")
            pos_jun15 = content.find("## [2024-06-15]")
            pos_v1 = content.find("## [1.0.0]")

            assert pos_unreleased < pos_jun30 < pos_jun15 < pos_v1, (
                f"Wrong order! Expected: Unreleased < 2024-06-30 < 2024-06-15 < 1.0.0\n"
                f"Got: Unreleased at {pos_unreleased}, Jun30 at {pos_jun30}, "
                f"Jun15 at {pos_jun15}, 1.0.0 at {pos_v1}"
            )


class TestUpdateAllModeGapBoundaryOrder:
    """Tests for handle_update_all_mode with gaps mode insertion order."""

    def test_gap_boundaries_inserted_newest_first(self, temp_dir):
        """Test that gap-based boundaries are inserted with newest at top."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [Unreleased]

""")

        def mock_generate_entry(commits, tag, from_boundary=None, **kwargs):
            return f"### Added\n\n- Changes for session {tag}"

        with (
            patch(f"{BOUNDARY_MODULE}.get_all_boundaries") as mock_get_boundaries,
            patch(f"{BOUNDARY_MODULE}.get_commits_between_boundaries") as mock_get_commits,
            patch(f"{CHANGELOG_IO_MODULE}.write_changelog"),
        ):
            # Gap boundaries - represent development sessions
            mock_get_boundaries.return_value = [
                {
                    "identifier": "2024-03-01",
                    "date": datetime(2024, 3, 1, 10, 0, tzinfo=timezone.utc),
                    "hash": "session1",
                    "mode": "gaps",
                },
                {
                    "identifier": "2024-03-05",
                    "date": datetime(2024, 3, 5, 14, 0, tzinfo=timezone.utc),
                    "hash": "session2",
                    "mode": "gaps",
                },
                {
                    "identifier": "2024-03-10",
                    "date": datetime(2024, 3, 10, 9, 0, tzinfo=timezone.utc),
                    "hash": "session3",
                    "mode": "gaps",
                },
            ]
            mock_get_commits.return_value = [{"hash": "abc", "message": "test"}]

            success, content = handle_update_all_mode(
                changelog_file=str(changelog_file),
                generate_entry_func=mock_generate_entry,
                mode="gaps",
                quiet=True,
                dry_run=True,
            )

            assert success

            # Newest session should be first
            pos_mar10 = content.find("## [2024-03-10]")
            pos_mar05 = content.find("## [2024-03-05]")
            pos_mar01 = content.find("## [2024-03-01]")

            assert pos_mar10 != -1, "March 10 session not found"
            assert pos_mar05 != -1, "March 5 session not found"
            assert pos_mar01 != -1, "March 1 session not found"

            assert pos_mar10 < pos_mar05 < pos_mar01, (
                f"Wrong order! Expected newest first.\nMar10 at {pos_mar10}, Mar05 at {pos_mar05}, Mar01 at {pos_mar01}"
            )


class TestMissingEntriesModeDateBoundaryOrder:
    """Tests for handle_missing_entries_mode with dates mode insertion order."""

    def test_missing_date_entries_inserted_newest_first(self, temp_dir):
        """Test that missing date entries are inserted with newest at top."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [Unreleased]

""")

        def mock_generate_entry(commits, tag, from_boundary=None, **kwargs):
            return f"### Added\n\n- Changes for {tag}"

        with (
            patch(f"{MISSING_MODULE}.get_all_boundaries") as mock_get_boundaries,
            patch(f"{MISSING_MODULE}.get_commits_between_boundaries") as mock_get_commits,
            patch(f"{CHANGELOG_IO_MODULE}.read_changelog") as mock_read,
            patch(f"{CHANGELOG_IO_MODULE}.write_changelog"),
        ):
            mock_get_boundaries.return_value = [
                {
                    "identifier": "2024-07-15",
                    "date": datetime(2024, 7, 15, tzinfo=timezone.utc),
                    "hash": "abc123",
                    "mode": "dates",
                },
                {
                    "identifier": "2024-08-15",
                    "date": datetime(2024, 8, 15, tzinfo=timezone.utc),
                    "hash": "def456",
                    "mode": "dates",
                },
                {
                    "identifier": "2024-09-15",
                    "date": datetime(2024, 9, 15, tzinfo=timezone.utc),
                    "hash": "ghi789",
                    "mode": "dates",
                },
            ]
            mock_get_commits.return_value = [{"hash": "abc", "message": "test"}]
            mock_read.return_value = changelog_file.read_text()

            success, content = handle_missing_entries_mode(
                changelog_file=str(changelog_file),
                generate_entry_func=mock_generate_entry,
                mode="dates",
                date_grouping="monthly",
                quiet=True,
                dry_run=True,
            )

            assert success

            # Verify order: September should appear BEFORE August, etc.
            pos_sep = content.find("## [2024-09-15]")
            pos_aug = content.find("## [2024-08-15]")
            pos_jul = content.find("## [2024-07-15]")

            assert pos_sep != -1, "September entry not found"
            assert pos_aug != -1, "August entry not found"
            assert pos_jul != -1, "July entry not found"

            assert pos_sep < pos_aug < pos_jul, (
                f"Wrong order! Expected newest first.\n"
                f"Sep at {pos_sep}, Aug at {pos_aug}, Jul at {pos_jul}\n"
                f"Expected: Sep < Aug < Jul"
            )


class TestMissingEntriesModeGapBoundaryOrder:
    """Tests for handle_missing_entries_mode with gaps mode insertion order."""

    def test_missing_gap_entries_inserted_newest_first(self, temp_dir):
        """Test that missing gap-based entries are inserted with newest at top."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [Unreleased]

""")

        def mock_generate_entry(commits, tag, from_boundary=None, **kwargs):
            return f"### Added\n\n- Session {tag}"

        with (
            patch(f"{MISSING_MODULE}.get_all_boundaries") as mock_get_boundaries,
            patch(f"{MISSING_MODULE}.get_commits_between_boundaries") as mock_get_commits,
            patch(f"{CHANGELOG_IO_MODULE}.read_changelog") as mock_read,
            patch(f"{CHANGELOG_IO_MODULE}.write_changelog"),
        ):
            mock_get_boundaries.return_value = [
                {
                    "identifier": "2024-04-01",
                    "date": datetime(2024, 4, 1, 10, 0, tzinfo=timezone.utc),
                    "hash": "gap1",
                    "mode": "gaps",
                },
                {
                    "identifier": "2024-04-10",
                    "date": datetime(2024, 4, 10, 14, 0, tzinfo=timezone.utc),
                    "hash": "gap2",
                    "mode": "gaps",
                },
                {
                    "identifier": "2024-04-20",
                    "date": datetime(2024, 4, 20, 9, 0, tzinfo=timezone.utc),
                    "hash": "gap3",
                    "mode": "gaps",
                },
            ]
            mock_get_commits.return_value = [{"hash": "abc", "message": "test"}]
            mock_read.return_value = changelog_file.read_text()

            success, content = handle_missing_entries_mode(
                changelog_file=str(changelog_file),
                generate_entry_func=mock_generate_entry,
                mode="gaps",
                gap_threshold=4.0,
                quiet=True,
                dry_run=True,
            )

            assert success

            pos_apr20 = content.find("## [2024-04-20]")
            pos_apr10 = content.find("## [2024-04-10]")
            pos_apr01 = content.find("## [2024-04-01]")

            assert pos_apr20 != -1, "April 20 entry not found"
            assert pos_apr10 != -1, "April 10 entry not found"
            assert pos_apr01 != -1, "April 1 entry not found"

            assert pos_apr20 < pos_apr10 < pos_apr01, (
                f"Wrong order! Expected newest first.\nApr20 at {pos_apr20}, Apr10 at {pos_apr10}, Apr01 at {pos_apr01}"
            )


class TestInsertionOrderWithManyBoundaries:
    """Tests with many boundaries to ensure order is correct at scale."""

    def test_twelve_monthly_boundaries_correct_order(self, temp_dir):
        """Test that a full year of monthly boundaries is ordered correctly."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [Unreleased]

""")

        def mock_generate_entry(commits, tag, from_boundary=None, **kwargs):
            return f"### Added\n\n- Monthly update for {tag}"

        with (
            patch(f"{BOUNDARY_MODULE}.get_all_boundaries") as mock_get_boundaries,
            patch(f"{BOUNDARY_MODULE}.get_commits_between_boundaries") as mock_get_commits,
            patch(f"{CHANGELOG_IO_MODULE}.write_changelog"),
        ):
            # Full year of monthly boundaries
            mock_get_boundaries.return_value = [
                {
                    "identifier": f"2024-{month:02d}-28",
                    "date": datetime(2024, month, 28, tzinfo=timezone.utc),
                    "hash": f"month{month}",
                    "mode": "dates",
                }
                for month in range(1, 13)  # Jan through Dec
            ]
            mock_get_commits.return_value = [{"hash": "abc", "message": "test"}]

            success, content = handle_update_all_mode(
                changelog_file=str(changelog_file),
                generate_entry_func=mock_generate_entry,
                mode="dates",
                quiet=True,
                dry_run=True,
            )

            assert success

            # Find positions of all months
            positions = []
            for month in range(1, 13):
                pos = content.find(f"## [2024-{month:02d}-28]")
                assert pos != -1, f"Month {month} entry not found"
                positions.append((month, pos))

            # Verify December is first, January is last
            positions_sorted_by_pos = sorted(positions, key=lambda x: x[1])
            months_in_order = [m for m, _ in positions_sorted_by_pos]

            # Expected order: 12, 11, 10, ..., 2, 1 (newest first)
            expected_order = list(range(12, 0, -1))

            assert months_in_order == expected_order, (
                f"Wrong order! Expected months in reverse chronological order.\n"
                f"Got: {months_in_order}\n"
                f"Expected: {expected_order}"
            )


class TestInsertionOrderEdgeCases:
    """Edge case tests for insertion order."""

    def test_single_boundary_still_works(self, temp_dir):
        """Test that a single boundary is handled correctly."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [Unreleased]

""")

        def mock_generate_entry(commits, tag, from_boundary=None, **kwargs):
            return "### Added\n\n- Single entry"

        with (
            patch(f"{BOUNDARY_MODULE}.get_all_boundaries") as mock_get_boundaries,
            patch(f"{BOUNDARY_MODULE}.get_commits_between_boundaries") as mock_get_commits,
            patch(f"{CHANGELOG_IO_MODULE}.write_changelog"),
        ):
            mock_get_boundaries.return_value = [
                {
                    "identifier": "2024-05-15",
                    "date": datetime(2024, 5, 15, tzinfo=timezone.utc),
                    "hash": "single",
                    "mode": "dates",
                }
            ]
            mock_get_commits.return_value = [{"hash": "abc", "message": "test"}]

            success, content = handle_update_all_mode(
                changelog_file=str(changelog_file),
                generate_entry_func=mock_generate_entry,
                mode="dates",
                quiet=True,
                dry_run=True,
            )

            assert success
            assert "## [2024-05-15]" in content

    def test_two_boundaries_correct_order(self, temp_dir):
        """Test the minimal case of two boundaries for correct order."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [Unreleased]

""")

        def mock_generate_entry(commits, tag, from_boundary=None, **kwargs):
            return f"### Added\n\n- Entry for {tag}"

        with (
            patch(f"{BOUNDARY_MODULE}.get_all_boundaries") as mock_get_boundaries,
            patch(f"{BOUNDARY_MODULE}.get_commits_between_boundaries") as mock_get_commits,
            patch(f"{CHANGELOG_IO_MODULE}.write_changelog"),
        ):
            mock_get_boundaries.return_value = [
                {
                    "identifier": "2024-01-01",
                    "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "hash": "first",
                    "mode": "dates",
                },
                {
                    "identifier": "2024-12-31",
                    "date": datetime(2024, 12, 31, tzinfo=timezone.utc),
                    "hash": "last",
                    "mode": "dates",
                },
            ]
            mock_get_commits.return_value = [{"hash": "abc", "message": "test"}]

            success, content = handle_update_all_mode(
                changelog_file=str(changelog_file),
                generate_entry_func=mock_generate_entry,
                mode="dates",
                quiet=True,
                dry_run=True,
            )

            assert success

            pos_dec = content.find("## [2024-12-31]")
            pos_jan = content.find("## [2024-01-01]")

            assert pos_dec < pos_jan, (
                f"Two boundary test failed! December ({pos_dec}) should be before January ({pos_jan})"
            )


class TestInsertionAlgorithmDirectly:
    """Direct tests of the insertion algorithm logic.

    These tests verify the specific algorithm used for inserting entries,
    independent of the full handler functions.
    """

    def test_fixed_position_insert_produces_correct_order(self):
        """Verify that inserting at fixed position produces newest-first order.

        This directly tests the algorithm:
        - Start with entries in chronological order (oldest first)
        - Insert each at the same fixed position
        - Result should be reverse chronological (newest first)
        """
        lines = ["# Header", "", "## [Unreleased]", "", "## [Old] - old content"]

        # Entries in chronological order (oldest first)
        entries = ["Entry A (oldest)", "Entry B (middle)", "Entry C (newest)"]

        insert_point = 4  # After Unreleased section

        # Simulate the insertion algorithm (from boundary.py)
        for entry in entries:  # NOT reversed - this is the fix!
            lines.insert(insert_point, f"## [{entry}]")

        # After all insertions:
        # - Entry C was inserted last at position 4, so it's at position 4
        # - Entry B was inserted second at position 4, pushed down to 5
        # - Entry A was inserted first at position 4, pushed down to 6

        result = "\n".join(lines)

        pos_a = result.find("Entry A")
        pos_b = result.find("Entry B")
        pos_c = result.find("Entry C")

        assert pos_c < pos_b < pos_a, (
            f"Algorithm test failed!\n"
            f"Entry C (newest) at {pos_c}, Entry B at {pos_b}, Entry A (oldest) at {pos_a}\n"
            f"Expected: C < B < A (newest first)"
        )

    def test_reversed_insert_produces_wrong_order(self):
        """Demonstrate that reversed insertion produces wrong order.

        This shows why the bug occurred when using reversed().
        """
        lines = ["# Header", "", "## [Unreleased]", "", "## [Old] - old content"]

        # Entries in chronological order (oldest first)
        entries = ["Entry A (oldest)", "Entry B (middle)", "Entry C (newest)"]

        insert_point = 4

        # WRONG: Using reversed (the bug)
        for entry in reversed(entries):
            lines.insert(insert_point, f"## [{entry}]")

        result = "\n".join(lines)

        pos_a = result.find("Entry A")
        pos_b = result.find("Entry B")
        pos_c = result.find("Entry C")

        # This produces WRONG order: oldest first
        assert pos_a < pos_b < pos_c, (
            f"This test verifies the bug behavior - reversed produces wrong order.\n"
            f"Entry A (oldest) at {pos_a}, Entry B at {pos_b}, Entry C (newest) at {pos_c}\n"
            f"With reversed(): oldest ends up first (wrong!)"
        )
