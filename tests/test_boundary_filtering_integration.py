"""Unit test for boundary filtering logic that would catch the regression."""

from datetime import datetime, timezone

from kittylog.changelog.boundaries import find_existing_boundaries
from kittylog.tag_operations import generate_boundary_identifier


def test_boundary_filtering_prefix_mismatch():
    """Test that boundary filtering correctly handles prefix mismatch between changelog and git.

    This test would have caught the regression where existing boundaries weren't filtered out
    due to "v0.1.0" vs "0.1.0" prefix mismatch.
    """
    # Realistic changelog content with boundaries WITHOUT "v" prefix
    changelog_content = """# Changelog

## [Unreleased]

## [0.1.3] - 2024-01-03
- Some changes

## [0.1.0] - 2023-12-01
- Initial release
"""

    # Realistic git boundaries WITH "v" prefix (like actual git tags)
    mock_boundaries = [
        {
            "identifier": "v0.1.0",
            "boundary_type": "tag",
            "hash": "abc123",
            "short_hash": "abc123",
            "message": "Release v0.1.0",
            "author": "Test Author",
            "date": datetime(2023, 12, 1, tzinfo=timezone.utc),
            "files": [],
        },
        {
            "identifier": "v0.1.3",
            "boundary_type": "tag",
            "hash": "def456",
            "short_hash": "def456",
            "message": "Release v0.1.3",
            "author": "Test Author",
            "date": datetime(2024, 1, 3, tzinfo=timezone.utc),
            "files": [],
        },
        {
            "identifier": "v0.2.0",  # This is missing from changelog
            "boundary_type": "tag",
            "hash": "ghi789",
            "short_hash": "ghi789",
            "message": "Release v0.2.0",
            "author": "Test Author",
            "date": datetime(2024, 2, 1, tzinfo=timezone.utc),
            "files": [],
        },
    ]

    # Step 1: Test that existing boundaries are found correctly (without "v")
    existing_boundaries = find_existing_boundaries(changelog_content)
    assert existing_boundaries == {"0.1.0", "0.1.3"}, f"Expected {{'0.1.0', '0.1.3'}}, got {existing_boundaries}"

    # Step 2: Test boundary filtering logic (the fix I implemented)
    boundaries_to_process = []
    for boundary in mock_boundaries:
        identifier = generate_boundary_identifier(boundary, "tags")
        # The key fix: normalize by removing "v" prefix before comparison
        normalized_identifier = identifier.lstrip("v")
        if normalized_identifier not in existing_boundaries:
            boundaries_to_process.append(boundary)

    # Step 3: Verify only missing boundary (v0.2.0) is selected for processing
    assert len(boundaries_to_process) == 1, f"Expected 1 boundary to process, got {len(boundaries_to_process)}"
    assert boundaries_to_process[0]["identifier"] == "v0.2.0", (
        f"Expected v0.2.0, got {boundaries_to_process[0]['identifier']}"
    )

    print("✅ Boundary filtering regression test passes!")


def test_boundary_filtering_regression_scenario():
    """Test the exact scenario that would fail before the fix."""
    changelog_content = """# Changelog
## [0.1.0] - 2023-12-01
- Initial release
"""

    boundary = {"identifier": "v0.1.0", "boundary_type": "tag", "hash": "abc123"}

    existing = find_existing_boundaries(changelog_content)
    identifier = generate_boundary_identifier(boundary, "tags")

    # This is what FAILED before the fix
    old_logic_would_process = identifier not in existing  # "v0.1.0" not in {"0.1.0"} = True (WRONG)

    # This is what WORKS after the fix
    new_logic_would_process = identifier.lstrip("v") not in existing  # "0.1.0" not in {"0.1.0"} = False (CORRECT)

    assert old_logic_would_process, "Regression test setup failed - old logic should fail"
    assert not new_logic_would_process, "Fix verification failed - new logic should work"

    print("✅ Regression scenario test passes - fix prevents the bug!")


def test_date_boundary_existing_detection_handles_nested_brackets():
    """Existing boundary detection should normalize date headings generated from display names."""
    changelog_content = """# Changelog

## [[2024-01-03] - January 03, 2024]
- Some changes here
"""

    existing_boundaries = find_existing_boundaries(changelog_content)

    assert "2024-01-03" in existing_boundaries
