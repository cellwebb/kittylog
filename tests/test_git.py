"""Tests for git operations module."""

import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from clog.errors import GitError
from clog.git_operations import (
    get_all_tags,
    get_commits_between_tags,
    get_latest_tag,
    get_tag_date,
    get_tags_since_last_changelog,
    is_current_commit_tagged,
    run_git_command,
)


class TestGetAllTags:
    """Test get_all_tags function."""

    def test_get_all_tags_success(self, git_repo_with_tags):
        """Test getting all tags from a repository."""
        tags = get_all_tags()
        assert "v0.1.0" in tags
        assert "v0.2.0" in tags
        assert "v0.2.1" in tags
        assert len(tags) == 3

    def test_get_all_tags_empty_repo(self, git_repo):
        """Test getting tags from repository with no tags."""
        tags = get_all_tags()
        assert tags == []

    def test_get_all_tags_sorting(self, git_repo):
        """Test that tags are sorted correctly."""
        repo = git_repo

        # Create tags in non-sequential order
        test_file = repo.working_dir + "/test.py"
        for version in ["v0.10.0", "v0.2.0", "v0.1.0"]:
            with open(test_file, "w") as f:
                f.write(f"# Version {version}\n")
            repo.index.add([test_file])
            commit = repo.index.commit(f"Version {version}")
            repo.create_tag(version, commit)

        tags = get_all_tags()
        assert tags == ["v0.1.0", "v0.2.0", "v0.10.0"]


class TestGetLatestTag:
    """Test get_latest_tag function."""

    def test_get_latest_tag_success(self, git_repo_with_tags):
        """Test getting the latest tag."""
        latest = get_latest_tag()
        assert latest == "v0.2.1"

    def test_get_latest_tag_no_tags(self, git_repo):
        """Test getting latest tag when no tags exist."""
        latest = get_latest_tag()
        assert latest is None


class TestGetCommitsBetweenTags:
    """Test get_commits_between_tags function."""

    def test_get_commits_between_tags_success(self, git_repo_with_tags):
        """Test getting commits between two tags."""
        commits = get_commits_between_tags("v0.1.0", "v0.2.0")
        assert len(commits) > 0

        # Check commit structure
        commit = commits[0]
        assert "hash" in commit
        assert "short_hash" in commit
        assert "message" in commit
        assert "author" in commit
        assert "date" in commit
        assert "files" in commit
        assert isinstance(commit["date"], datetime)

    def test_get_commits_from_tag_to_head(self, git_repo_with_tags):
        """Test getting commits from tag to HEAD."""
        commits = get_commits_between_tags("v0.2.0", None)
        assert len(commits) > 0

    def test_get_commits_all_history(self, git_repo_with_tags):
        """Test getting all commits when no tags specified."""
        commits = get_commits_between_tags(None, None)
        assert len(commits) >= 5  # We created 5 commits in fixture

    def test_get_commits_invalid_tag(self, git_repo_with_tags):
        """Test handling of invalid tag."""
        # Should gracefully handle invalid from_tag
        commits = get_commits_between_tags("invalid-tag", "v0.1.0")
        assert isinstance(commits, list)  # Should not crash


class TestGetTagsSinceLastChangelog:
    """Test get_tags_since_last_changelog function."""

    def test_no_changelog_file(self, git_repo_with_tags, temp_dir):
        """Test when no changelog file exists."""
        os.chdir(temp_dir)
        last_tag, new_tags = get_tags_since_last_changelog("NONEXISTENT.md")
        assert last_tag is None
        assert len(new_tags) == 3  # All tags are new

    def test_changelog_with_version(self, git_repo_with_tags, temp_dir):
        """Test when changelog contains a version."""
        changelog_content = """# Changelog

## [0.1.0] - 2024-01-01

### Added
- Initial release
"""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text(changelog_content)

        last_tag, new_tags = get_tags_since_last_changelog("CHANGELOG.md")
        assert last_tag == "v0.1.0"
        assert "v0.2.0" in new_tags
        assert "v0.2.1" in new_tags
        assert len(new_tags) == 2

    def test_changelog_with_v_prefix(self, git_repo_with_tags, temp_dir):
        """Test when changelog version has v prefix."""
        changelog_content = """# Changelog

## [v0.1.0] - 2024-01-01

### Added
- Initial release
"""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text(changelog_content)

        last_tag, new_tags = get_tags_since_last_changelog("CHANGELOG.md")
        assert last_tag == "v0.1.0"
        assert len(new_tags) == 2

    def test_empty_changelog(self, git_repo_with_tags, temp_dir):
        """Test with empty changelog file."""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("# Changelog\n")

        last_tag, new_tags = get_tags_since_last_changelog("CHANGELOG.md")
        assert last_tag is None
        assert len(new_tags) == 3


class TestGetTagDate:
    """Test get_tag_date function."""

    def test_get_tag_date_success(self, git_repo_with_tags):
        """Test getting tag date."""
        date = get_tag_date("v0.1.0")
        assert isinstance(date, datetime)

    def test_get_tag_date_invalid_tag(self, git_repo_with_tags):
        """Test getting date for invalid tag."""
        date = get_tag_date("invalid-tag")
        assert date is None


class TestRunGitCommand:
    """Test run_git_command function."""

    def test_run_git_command_success(self, git_repo):
        """Test running a successful git command."""
        result = run_git_command(["status", "--porcelain"])
        assert isinstance(result, str)

    def test_run_git_command_failure(self, git_repo):
        """Test running a failing git command."""
        # This should not raise an exception due to raise_on_error=False
        result = run_git_command(["invalid-command"])
        assert result == ""


class TestIsCurrentCommitTagged:
    """Test is_current_commit_tagged function."""

    def test_is_current_commit_tagged_false(self, git_repo_with_tags):
        """Test that current commit is not tagged in a repo with existing tags."""
        # In our test repo, HEAD should not have a tag pointing to it
        # Add a new commit without a tag to ensure HEAD is not tagged
        repo = git_repo_with_tags
        test_file = Path(repo.working_dir) / "uncommitted_file.py"
        test_file.write_text("# This file is not tagged\nprint('uncommitted')\n")
        repo.index.add([str(test_file)])
        repo.index.commit("Add file without tag")
        
        result = is_current_commit_tagged()
        assert result is False

    def test_is_current_commit_tagged_true(self, git_repo):
        """Test that current commit is tagged when we create a tag on HEAD."""
        repo = git_repo
        # Create a tag on the current commit
        current_commit = repo.head.commit
        repo.create_tag("test-tag", current_commit)

        # Now the current commit should be tagged
        result = is_current_commit_tagged()
        assert result is True


class TestGitErrorHandling:
    """Test git error handling."""

    @patch("clog.git_operations.Repo")
    def test_git_error_not_in_repo(self, mock_repo):
        """Test error when not in a git repository."""
        from git import InvalidGitRepositoryError

        mock_repo.side_effect = InvalidGitRepositoryError

        with pytest.raises(GitError):
            get_all_tags()

    @patch("clog.git_operations.get_repo")
    def test_git_error_general_exception(self, mock_get_repo):
        """Test handling of general git exceptions."""
        mock_get_repo.side_effect = Exception("Git error")

        with pytest.raises(GitError):
            get_all_tags()


class TestIntegration:
    """Integration tests for git operations."""

    def test_full_workflow(self, git_repo_with_tags, temp_dir):
        """Test a complete workflow with git operations."""
        # Create a changelog
        changelog_content = """# Changelog

## [0.1.0] - 2024-01-01

### Added
- Initial release
"""
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text(changelog_content)

        # Get new tags
        last_tag, new_tags = get_tags_since_last_changelog("CHANGELOG.md")
        assert last_tag == "v0.1.0"
        assert len(new_tags) >= 1

        # Get commits for the first new tag
        if new_tags:
            commits = get_commits_between_tags(last_tag, new_tags[0])
            assert isinstance(commits, list)

            # Verify commit structure
            if commits:
                commit = commits[0]
                assert all(key in commit for key in ["hash", "message", "author", "date", "files"])
                assert isinstance(commit["date"], datetime)
                assert isinstance(commit["files"], list)
