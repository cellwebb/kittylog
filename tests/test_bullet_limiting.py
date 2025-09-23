"""Tests for bullet limiting functionality in changelog processing."""

from datetime import datetime
from unittest.mock import patch

from kittylog.changelog import update_changelog


class TestBulletLimiting:
    """Test bullet limiting functionality in changelog processing."""

    @patch("kittylog.git_operations.is_current_commit_tagged")
    @patch("kittylog.git_operations.get_latest_tag")
    @patch("kittylog.changelog.get_commits_between_tags")
    @patch("kittylog.changelog.generate_changelog_entry")
    def test_bullet_limiting_per_section(
        self, mock_generate, mock_get_commits, mock_get_latest_tag, mock_is_tagged, temp_dir
    ):
        """Test that bullet points are limited to 6 per section."""
        # Setup mocks
        mock_get_commits.return_value = [
            {"hash": "abc123", "message": "Add new feature", "files": ["feature.py"]},
        ]
        mock_get_latest_tag.return_value = "v0.1.0"
        mock_is_tagged.return_value = False  # Simulate unreleased commits

        # AI generated content with more than 6 bullets per section
        ai_content = """### Added
- New feature 1
- New feature 2
- New feature 3
- New feature 4
- New feature 5
- New feature 6
- New feature 7 (should be dropped)
- New feature 8 (should be dropped)

### Fixed
- New fix 1
- New fix 2
- New fix 3
- New fix 4
- New fix 5
- New fix 6
- New fix 7 (should be dropped)

### Changed
- New change 1
- New change 2
- New change 3
- New change 4
- New change 5
- New change 6
- New change 7 (should be dropped)
- New change 8 (should be dropped)
- New change 9 (should be dropped)"""
        mock_generate.return_value = ai_content

        # Create a changelog file with existing content
        changelog_content = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Existing feature 1
- Existing feature 2

### Fixed
- Existing fix 1
"""

        # Update the changelog
        updated_content = update_changelog(
            existing_content=changelog_content, from_tag="v0.1.0", to_tag=None, model="test:model", quiet=True
        )

        # Count bullets in each section
        lines = updated_content.split("\n")

        # Count all bullets in the unreleased section
        added_count = 0
        fixed_count = 0
        changed_count = 0

        in_unreleased_section = False
        in_added_section = False
        in_fixed_section = False
        in_changed_section = False

        for line in lines:
            if "## [Unreleased]" in line:
                in_unreleased_section = True
            elif in_unreleased_section and line.startswith("### Added"):
                in_added_section = True
                in_fixed_section = False
                in_changed_section = False
            elif in_unreleased_section and line.startswith("### Fixed"):
                in_added_section = False
                in_fixed_section = True
                in_changed_section = False
            elif in_unreleased_section and line.startswith("### Changed"):
                in_added_section = False
                in_fixed_section = False
                in_changed_section = True
            elif in_unreleased_section and line.startswith("## [") and not line.startswith("## [Unreleased]"):
                # Next version section - stop processing
                break
            elif (
                in_unreleased_section
                and line.startswith("- ")
                and (in_added_section or in_fixed_section or in_changed_section)
            ):
                if in_added_section:
                    added_count += 1
                elif in_fixed_section:
                    fixed_count += 1
                elif in_changed_section:
                    changed_count += 1

        # Verify that each section has at most 6 bullets (total, not just new ones)
        # Since we're working with unreleased content, we limit the total bullets per section
        assert added_count <= 6
        assert fixed_count <= 6
        assert changed_count <= 6

        # Verify that the content has our new features but limited to 6 total
        assert "New feature 1" in updated_content
        assert "New feature 6" in updated_content
        # This one should be dropped due to the limit
        assert "New feature 7" not in updated_content

        # Verify that the content has our new fixes but limited to 6 total
        assert "New fix 1" in updated_content
        assert "New fix 6" in updated_content
        # This one should be dropped due to the limit
        assert "New fix 7" not in updated_content

        # Verify that the content has our new changes but limited to 6 total
        assert "New change 1" in updated_content
        assert "New change 6" in updated_content
        # These ones should be dropped due to the limit
        assert "New change 7" not in updated_content
        assert "New change 8" not in updated_content
        assert "New change 9" not in updated_content

    @patch("kittylog.git_operations.is_current_commit_tagged")
    @patch("kittylog.git_operations.get_latest_tag")
    @patch("kittylog.changelog.get_commits_between_tags")
    @patch("kittylog.changelog.generate_changelog_entry")
    def test_bullet_limiting_replace_mode(
        self, mock_generate, mock_get_commits, mock_get_latest_tag, mock_is_tagged, temp_dir
    ):
        """Test that bullet points are limited to 6 per section in replace mode."""
        # Setup mocks
        mock_get_commits.return_value = [
            {"hash": "abc123", "message": "Add features and fixes", "files": ["feature.py", "fix.py"]},
        ]
        mock_get_latest_tag.return_value = "v0.1.0"
        mock_is_tagged.return_value = False  # Simulate unreleased commits

        # AI generated content with more than 6 bullets per section
        ai_content = """### Added
- Feature 1
- Feature 2
- Feature 3
- Feature 4
- Feature 5
- Feature 6
- Feature 7 (should be dropped)

### Fixed
- Fix 1
- Fix 2
- Fix 3
- Fix 4
- Fix 5
- Fix 6
- Fix 7 (should be dropped)
- Fix 8 (should be dropped)"""
        mock_generate.return_value = ai_content

        # Create a changelog file with an Unreleased section
        changelog_content = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Existing feature 1

### Fixed
- Existing fix 1
"""

        # Update the changelog in replace mode
        updated_content = update_changelog(
            existing_content=changelog_content, from_tag="v0.1.0", to_tag=None, model="test:model", quiet=True
        )

        # Count bullets in each section
        lines = updated_content.split("\n")

        # Find the unreleased section and count bullets within it
        added_count = 0
        fixed_count = 0

        in_unreleased_section = False
        in_added_section = False
        in_fixed_section = False

        for line in lines:
            if "## [Unreleased]" in line:
                in_unreleased_section = True
            elif in_unreleased_section and line.startswith("### Added"):
                in_added_section = True
                in_fixed_section = False
            elif in_unreleased_section and line.startswith("### Fixed"):
                in_added_section = False
                in_fixed_section = True
            elif in_unreleased_section and line.startswith("## [") and not line.startswith("## [Unreleased]"):
                # Next version section - stop processing
                break
            elif in_unreleased_section and line.startswith("- ") and (in_added_section or in_fixed_section):
                if in_added_section:
                    added_count += 1
                elif in_fixed_section:
                    fixed_count += 1

        # Verify that each section has at most 6 bullets
        assert added_count <= 6
        assert fixed_count <= 6

        # Verify that we replaced the existing content with the new AI content
        assert "Existing feature 1" not in updated_content
        assert "Existing fix 1" not in updated_content

        # Verify that the content includes the new items but not the ones that should be dropped
        assert "Feature 1" in updated_content
        assert "Feature 6" in updated_content
        assert "Feature 7" not in updated_content

        assert "Fix 1" in updated_content
        assert "Fix 6" in updated_content
        assert "Fix 7" not in updated_content
        assert "Fix 8" not in updated_content

    @patch("kittylog.changelog.get_commits_between_tags")
    @patch("kittylog.changelog.generate_changelog_entry")
    @patch("kittylog.changelog.get_tag_date")
    def test_bullet_limiting_standard_mode(self, mock_get_date, mock_generate, mock_get_commits, temp_dir):
        """Test that bullet points are limited to 6 per section in standard mode."""
        # Setup mocks
        mock_get_commits.return_value = [
            {"hash": "abc123", "message": "Add features and fixes", "files": ["feature.py", "fix.py"]},
        ]
        mock_get_date.return_value = datetime(2024, 1, 20)

        # AI generated content with more than 6 bullets per section
        ai_content = """### Added
- Feature 1
- Feature 2
- Feature 3
- Feature 4
- Feature 5
- Feature 6
- Feature 7 (should be dropped)

### Fixed
- Fix 1
- Fix 2
- Fix 3
- Fix 4
- Fix 5
- Fix 6
- Fix 7 (should be dropped)
- Fix 8 (should be dropped)

### Changed
- Change 1
- Change 2
- Change 3
- Change 4
- Change 5
- Change 6
- Change 7 (should be dropped)
- Change 8 (should be dropped)
- Change 9 (should be dropped)
- Change 10 (should be dropped)"""
        mock_generate.return_value = ai_content

        # Create a minimal changelog file
        changelog_content = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
"""

        # Update the changelog in standard mode (tag to tag)
        updated_content = update_changelog(
            existing_content=changelog_content, from_tag="v0.1.0", to_tag="v0.2.0", model="test:model", quiet=True
        )

        # Count bullets in each section
        lines = updated_content.split("\n")
        added_count = 0
        fixed_count = 0
        changed_count = 0

        in_added_section = False
        in_fixed_section = False
        in_changed_section = False

        for line in lines:
            if line.startswith("### Added"):
                in_added_section = True
                in_fixed_section = False
                in_changed_section = False
            elif line.startswith("### Fixed"):
                in_added_section = False
                in_fixed_section = True
                in_changed_section = False
            elif line.startswith("### Changed"):
                in_added_section = False
                in_fixed_section = False
                in_changed_section = True
            elif line.startswith("- ") and (in_added_section or in_fixed_section or in_changed_section):
                if in_added_section:
                    added_count += 1
                elif in_fixed_section:
                    fixed_count += 1
                elif in_changed_section:
                    changed_count += 1

        # Verify that each section has at most 6 bullets
        assert added_count <= 6
        assert fixed_count <= 6
        assert changed_count <= 6

        # Verify that the content includes the new items but not the ones that should be dropped
        assert "Feature 1" in updated_content
        assert "Feature 6" in updated_content
        assert "Feature 7" not in updated_content

        assert "Fix 1" in updated_content
        assert "Fix 6" in updated_content
        assert "Fix 7" not in updated_content
        assert "Fix 8" not in updated_content

        assert "Change 1" in updated_content
        assert "Change 6" in updated_content
        assert "Change 7" not in updated_content
        assert "Change 8" not in updated_content
        assert "Change 9" not in updated_content
        assert "Change 10" not in updated_content
