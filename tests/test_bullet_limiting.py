"""Tests for bullet point limiting functionality."""

import re
from unittest.mock import patch

from kittylog.changelog import update_changelog


class TestBulletLimiting:
    """Test bullet point limiting in changelog entries."""

    @patch("kittylog.git_operations.is_current_commit_tagged")
    @patch("kittylog.git_operations.get_latest_tag")
    @patch("kittylog.git_operations.get_commits_between_tags")
    @patch("kittylog.changelog.get_commits_between_tags")
    @patch("kittylog.changelog.get_git_diff")
    @patch("kittylog.changelog.generate_changelog_entry")
    def test_bullet_limiting_per_section(
        self,
        mock_generate,
        mock_get_git_diff,
        mock_get_commits_changelog,
        mock_get_commits_git_ops,
        mock_get_latest_tag,
        mock_is_tagged,
        temp_dir,
    ):
        """Test that bullet points are limited to 6 per section."""
        # Setup mocks
        mock_get_commits_changelog.return_value = [
            {"hash": "abc123", "message": "Add new feature", "files": ["feature.py"]},
        ]
        mock_get_commits_git_ops.return_value = [
            {"hash": "abc123", "message": "Add new feature", "files": ["feature.py"]},
        ]
        mock_get_latest_tag.return_value = "v0.1.0"
        mock_is_tagged.return_value = False  # Simulate unreleased commits
        mock_get_git_diff.return_value = "diff --git a/feature.py b/feature.py"

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
        mock_generate.return_value = (ai_content, {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})

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
        updated_content, token_usage = update_changelog(
            existing_content=changelog_content,
            from_tag="v0.1.0",
            to_tag=None,
            model="openai:gpt-4o-mini",
            quiet=True,
            no_unreleased=False,
        )

        # Debug: Print the actual updated content
        print("DEBUG: Updated content:")
        print(updated_content)
        print("DEBUG: End of updated content")

        # Verify that the content was updated
        assert updated_content is not None
        assert "## [Unreleased]" in updated_content

        # Check that new AI content is present (replace mode)
        assert "New feature 1" in updated_content
        assert "New fix 1" in updated_content
        assert "New change 1" in updated_content

        # Count bullet points in each section
        added_matches = re.findall(r"### Added\s*\n(?:\s*- .*\s*\n)+", updated_content)
        fixed_matches = re.findall(r"### Fixed\s*\n(?:\s*- .*\s*\n)+", updated_content)
        changed_matches = re.findall(r"### Changed\s*\n(?:\s*- .*\s*\n)+", updated_content)

        # Debug: Print the matches
        print(f"DEBUG: Added matches: {added_matches}")
        print(f"DEBUG: Fixed matches: {fixed_matches}")
        print(f"DEBUG: Changed matches: {changed_matches}")

        # Should find sections in the updated content
        assert len(added_matches) == 1
        assert len(fixed_matches) == 1

        # Extract bullet points from sections
        added_bullets = re.findall(r"- .+", added_matches[0])
        fixed_bullets = re.findall(r"- .+", fixed_matches[0])

        # Should have up to 6 new bullets only (replace mode)
        assert len(added_bullets) <= 6  # 6 new limit
        assert len(fixed_bullets) <= 6  # 6 new limit

    @patch("kittylog.git_operations.is_current_commit_tagged")
    @patch("kittylog.git_operations.get_latest_tag")
    @patch("kittylog.git_operations.get_commits_between_tags")
    @patch("kittylog.changelog.get_commits_between_tags")
    @patch("kittylog.changelog.get_git_diff")
    @patch("kittylog.changelog.generate_changelog_entry")
    def test_bullet_limiting_standard_mode(
        self,
        mock_generate,
        mock_get_git_diff,
        mock_get_commits_changelog,
        mock_get_commits_git_ops,
        mock_get_latest_tag,
        mock_is_tagged,
        temp_dir,
    ):
        """Test bullet limiting in standard mode (append to existing sections)."""
        # Setup mocks
        mock_get_commits_changelog.return_value = [
            {"hash": "abc123", "message": "Add new feature", "files": ["feature.py"]},
        ]
        mock_get_commits_git_ops.return_value = [
            {"hash": "abc123", "message": "Add new feature", "files": ["feature.py"]},
        ]
        mock_get_latest_tag.return_value = "v0.1.0"
        mock_is_tagged.return_value = False  # Simulate unreleased commits
        mock_get_git_diff.return_value = "diff --git a/feature.py b/feature.py"

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
- New fix 7 (should be dropped)"""
        mock_generate.return_value = (ai_content, {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})

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

        # Update the changelog in standard mode (append)
        updated_content, token_usage = update_changelog(
            existing_content=changelog_content,
            from_tag="v0.1.0",
            to_tag=None,
            model="openai:gpt-4o-mini",
            quiet=True,
            no_unreleased=False,
        )

        # Verify that the content was updated
        assert updated_content is not None
        assert "## [Unreleased]" in updated_content

        # Count bullet points in each section
        added_matches = re.findall(r"### Added\s*\n(?:\s*- .*\s*\n)+", updated_content)
        fixed_matches = re.findall(r"### Fixed\s*\n(?:\s*- .*\s*\n)+", updated_content)

        # Should find sections in the updated content
        assert len(added_matches) == 1
        assert len(fixed_matches) == 1

        # Extract bullet points from sections
        added_bullets = re.findall(r"- .+", added_matches[0])
        fixed_bullets = re.findall(r"- .+", fixed_matches[0])

        # Should have up to 6 new bullets only (replace mode)
        assert len(added_bullets) <= 6  # 6 new limit
        assert len(fixed_bullets) <= 6  # 6 new limit

        # Verify content was replaced (not preserved) with new content
        assert "New feature 1" in updated_content
        assert "New fix 1" in updated_content

    @patch("kittylog.git_operations.is_current_commit_tagged")
    @patch("kittylog.git_operations.get_latest_tag")
    @patch("kittylog.git_operations.get_commits_between_tags")
    @patch("kittylog.changelog.get_commits_between_tags")
    @patch("kittylog.changelog.get_git_diff")
    @patch("kittylog.changelog.generate_changelog_entry")
    def test_bullet_limiting_replace_mode(
        self,
        mock_generate,
        mock_get_git_diff,
        mock_get_commits_changelog,
        mock_get_commits_git_ops,
        mock_get_latest_tag,
        mock_is_tagged,
        temp_dir,
    ):
        """Test bullet limiting in replace mode (overwrite existing sections)."""
        # Setup mocks
        mock_get_commits_changelog.return_value = [
            {"hash": "abc123", "message": "Add new feature", "files": ["feature.py"]},
        ]
        mock_get_commits_git_ops.return_value = [
            {"hash": "abc123", "message": "Add new feature", "files": ["feature.py"]},
        ]
        mock_get_latest_tag.return_value = "v0.1.0"
        mock_is_tagged.return_value = False  # Simulate unreleased commits
        mock_get_git_diff.return_value = "diff --git a/feature.py b/feature.py"

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
- New fix 7 (should be dropped)"""
        mock_generate.return_value = (ai_content, {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})

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

        # Update the changelog in replace mode (overwrite sections)
        updated_content, token_usage = update_changelog(
            existing_content=changelog_content,
            from_tag="v0.1.0",
            to_tag=None,
            model="openai:gpt-4o-mini",
            quiet=True,
            no_unreleased=False,
        )

        # Verify that the content was updated
        assert updated_content is not None
        assert "## [Unreleased]" in updated_content

        # In replace mode, existing bullets should be dropped and only AI content should remain
        # Count bullet points in each section - use a more robust pattern
        # that handles the last bullet not having a trailing newline
        added_matches = re.findall(r"### Added\s*\n((?:\s*- .*(?:\n|$))+)", updated_content)
        fixed_matches = re.findall(r"### Fixed\s*\n((?:\s*- .*(?:\n|$))+)", updated_content)

        # Should find both sections in the updated content
        assert len(added_matches) == 1
        assert len(fixed_matches) == 1

        # Extract bullet points from sections
        added_bullets = re.findall(r"- .+", added_matches[0])
        fixed_bullets = re.findall(r"- .+", fixed_matches[0])

        # Should have exactly 6 bullet points per section (limit)
        assert len(added_bullets) == 6
        assert len(fixed_bullets) == 6

        # Verify old content is gone in replace mode
        assert "Existing feature 1" not in updated_content
        assert "Existing feature 2" not in updated_content
        assert "Existing fix 1" not in updated_content

        # Verify new content is present and limited
        assert "New feature 1" in updated_content
        assert "New feature 6" in updated_content
        assert "New fix 1" in updated_content
        assert "New fix 6" in updated_content
