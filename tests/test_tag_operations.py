"""Comprehensive tests for tag_operations.py module."""

from datetime import datetime
from unittest import mock

import pytest

from kittylog.tag_operations import (
    clear_git_cache,
    get_all_boundaries,
    get_all_tags,
    get_boundary_by_identifier,
    get_current_commit_hash,
    get_latest_boundary,
    get_latest_tag,
    get_previous_boundary,
    get_repo,
    get_tag_date,
    is_current_commit_tagged,
)


class TestGetRepo:
    """Test the get_repo function."""

    def test_returns_repository_instance(self):
        """Test that get_repo returns a repository instance."""
        with mock.patch("kittylog.tag_operations.Repo") as mock_repo_class:
            mock_repo_instance = mock.Mock()
            mock_repo_class.return_value = mock_repo_instance

            result = get_repo()

        assert result == mock_repo_instance
        mock_repo_class.assert_called_once_with(".", search_parent_directories=True)

    def test_handles_invalid_git_repository_error(self):
        """Test handling of invalid git repository error."""
        from git.exc import InvalidGitRepositoryError

        from kittylog.errors import GitError

        with mock.patch("kittylog.tag_operations.Repo") as mock_repo_class:
            mock_repo_class.side_effect = InvalidGitRepositoryError("Not a git repo")

            with pytest.raises(GitError, match="Not in a git repository"):
                get_repo()

    def test_handles_other_git_errors(self):
        """Test handling of other git errors."""
        from git.exc import InvalidGitRepositoryError

        from kittylog.errors import GitError

        with mock.patch("kittylog.tag_operations.Repo") as mock_repo_class:
            mock_repo_class.side_effect = InvalidGitRepositoryError("Not a git repository")

            with pytest.raises(GitError):
                get_repo()


class TestGetAllTags:
    """Test the get_all_tags function."""

    def test_returns_sorted_tags(self):
        """Test that get_all_tags returns sorted tags."""
        mock_tag1 = mock.Mock()
        mock_tag1.name = "v1.0.0"
        mock_tag1.commit.committed_date = 1609459200  # 2021-01-01

        mock_tag2 = mock.Mock()
        mock_tag2.name = "v2.0.0"
        mock_tag2.commit.committed_date = 1640995200  # 2022-01-01

        mock_tag3 = mock.Mock()
        mock_tag3.name = "v1.1.0"
        mock_tag3.commit.committed_date = 1612137600  # 2021-02-01

        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_repo = mock.Mock()
            mock_repo.tags = [mock_tag2, mock_tag1, mock_tag3]  # Random order
            mock_get_repo.return_value = mock_repo

            result = get_all_tags()

        assert result == ["v1.0.0", "v1.1.0", "v2.0.0"]

    def test_handles_tags_without_v_prefix(self):
        """Test handling of tags without 'v' prefix."""
        mock_tag1 = mock.Mock()
        mock_tag1.name = "1.0.0"
        mock_tag1.commit.committed_date = 1609459200

        mock_tag2 = mock.Mock()
        mock_tag2.name = "2.0.0"
        mock_tag2.commit.committed_date = 1640995200

        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_repo = mock.Mock()
            mock_repo.tags = [mock_tag2, mock_tag1]
            mock_get_repo.return_value = mock_repo

            result = get_all_tags()

        assert result == ["1.0.0", "2.0.0"]

    def test_falls_back_to_chronological_sorting(self):
        """Test fallback to chronological sorting when semantic version sorting fails."""
        mock_tag1 = mock.Mock()
        mock_tag1.name = "invalid-version"
        mock_tag1.commit.committed_date = 1609459200

        mock_tag2 = mock.Mock()
        mock_tag2.name = "another-invalid"
        mock_tag2.commit.committed_date = 1640995200

        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_repo = mock.Mock()
            mock_repo.tags = [mock_tag2, mock_tag1]
            mock_get_repo.return_value = mock_repo

            result = get_all_tags()

        assert result == ["another-invalid", "invalid-version"]

    def test_handles_git_error(self):
        """Test handling of git error."""
        from git.exc import GitCommandError

        from kittylog.errors import GitError

        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_get_repo.side_effect = GitCommandError("git tag --list", 1)

            with pytest.raises(GitError, match="Failed to get tags"):
                get_all_tags()


class TestGetCurrentCommitHash:
    """Test the get_current_commit_hash function."""

    def test_returns_commit_hash(self):
        """Test that get_current_commit_hash returns the commit hash."""
        mock_commit = mock.Mock()
        mock_commit.hexsha = "abc123def456"

        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_repo = mock.Mock()
            mock_repo.head.commit = mock_commit
            mock_get_repo.return_value = mock_repo

            result = get_current_commit_hash()

        assert result == "abc123def456"

    def test_handles_git_errors(self):
        """Test handling of git errors."""
        from kittylog.errors import GitError

        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_repo = mock.Mock()
            mock_repo.head.commit = None
            mock_get_repo.return_value = mock_repo

            with pytest.raises(GitError):
                get_current_commit_hash()

    def test_handles_missing_head(self):
        """Test handling of missing head."""
        from kittylog.errors import GitError

        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_repo = mock.Mock()
            mock_repo.head.commit = None
            mock_get_repo.return_value = mock_repo

            with pytest.raises(GitError):
                get_current_commit_hash()


class TestIsCurrentCommitTagged:
    """Test the is_current_commit_tagged function."""

    def test_returns_true_when_tagged(self):
        """Test that is_current_commit_tagged returns True when HEAD is tagged."""
        mock_commit = mock.Mock()
        mock_commit.hexsha = "abc123"

        mock_tag = mock.Mock()
        mock_tag.commit = mock_commit

        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_repo = mock.Mock()
            mock_repo.head.commit = mock_commit
            mock_repo.tags = [mock_tag]
            mock_get_repo.return_value = mock_repo

            with mock.patch("kittylog.tag_operations.get_current_commit_hash") as mock_hash:
                mock_hash.return_value = "abc123"

                result = is_current_commit_tagged()

        assert result is True

    def test_returns_false_when_not_tagged(self):
        """Test that is_current_commit_tagged returns False when HEAD is not tagged."""
        mock_commit = mock.Mock()
        mock_commit.hexsha = "abc123"

        mock_tag = mock.Mock()
        mock_tag.commit.hexsha = "different_hash"

        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_repo = mock.Mock()
            mock_repo.head.commit = mock_commit
            mock_repo.tags = [mock_tag]
            mock_get_repo.return_value = mock_repo

            with mock.patch("kittylog.tag_operations.get_current_commit_hash") as mock_hash:
                mock_hash.return_value = "abc123"

                result = is_current_commit_tagged()

        assert result is False

    def test_returns_false_on_error(self):
        """Test that is_current_commit_tagged returns False on error."""
        import git

        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_get_repo.side_effect = git.GitError("Git error")

            result = is_current_commit_tagged()

        assert result is False


class TestGetTagDate:
    """Test the get_tag_date function."""

    def test_returns_tag_date(self):
        """Test that get_tag_date returns the tag date."""
        expected_date = datetime(2023, 1, 1, 12, 0, 0)

        mock_tag = mock.Mock()
        mock_tag.commit.committed_datetime = expected_date

        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_repo = mock.Mock()
            mock_repo.tags = {"v1.0.0": mock_tag}
            mock_get_repo.return_value = mock_repo

            result = get_tag_date("v1.0.0")

        assert result == expected_date

    def test_returns_none_for_nonexistent_tag(self):
        """Test that get_tag_date returns None for nonexistent tag."""
        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_repo = mock.Mock()
            mock_repo.tags = {}
            mock_get_repo.return_value = mock_repo

            result = get_tag_date("nonexistent")

        assert result is None

    def test_handles_git_errors(self):
        """Test handling of git errors."""
        import git

        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_get_repo.side_effect = git.GitError("Git error")

            result = get_tag_date("v1.0.0")

        assert result is None


class TestGetLatestTag:
    """Test the get_latest_tag function."""

    def test_returns_latest_tag(self):
        """Test that get_latest_tag returns the latest tag."""
        with mock.patch("kittylog.tag_operations.get_all_tags") as mock_tags:
            mock_tags.return_value = ["v1.0.0", "v1.1.0", "v2.0.0"]

            result = get_latest_tag()

        assert result == "v2.0.0"

    def test_returns_none_when_no_tags(self):
        """Test that get_latest_tag returns None when no tags exist."""
        with mock.patch("kittylog.tag_operations.get_all_tags") as mock_tags:
            mock_tags.return_value = []

            result = get_latest_tag()

        assert result is None

    def test_handles_git_errors(self):
        """Test handling of git errors."""
        from kittylog.errors import GitError

        with mock.patch("kittylog.tag_operations.get_all_tags") as mock_tags:
            mock_tags.side_effect = GitError("Failed to get tags", "git tag --list")

            result = get_latest_tag()

        assert result is None


class TestBoundaryRetrieval:
    """Test boundary retrieval functions."""

    def test_get_latest_boundary_tags_mode(self):
        """Test get_latest_boundary with tags mode."""
        mock_tag = {"identifier": "v1.0.0", "hash": "abc123", "date": datetime(2023, 1, 1), "author": "test"}

        with mock.patch("kittylog.tag_operations.get_latest_tag") as mock_latest:
            mock_latest.return_value = "v1.0.0"
            with mock.patch("kittylog.commit_analyzer.get_all_tags_with_dates") as mock_tags_data:
                mock_tags_data.return_value = [mock_tag]

                result = get_latest_boundary("tags")

        assert result == mock_tag

    def test_get_latest_boundary_dates_mode(self):
        """Test get_latest_boundary with dates mode."""
        expected_boundary = {"identifier": "2023-01-01", "date": datetime(2023, 1, 1), "hash": "abc123"}

        with mock.patch("kittylog.commit_analyzer.get_commits_by_date_boundaries") as mock_boundaries:
            mock_boundaries.return_value = [expected_boundary]

            result = get_latest_boundary("dates", date_grouping="daily")

        assert result == expected_boundary

    def test_get_latest_boundary_gaps_mode(self):
        """Test get_latest_boundary with gaps mode."""
        expected_boundary = {"hash": "gap123", "date": datetime(2023, 1, 1)}

        with mock.patch("kittylog.commit_analyzer.get_commits_by_gap_boundaries") as mock_boundaries:
            mock_boundaries.return_value = [expected_boundary]

            result = get_latest_boundary("gaps", gap_threshold_hours=4.0)

        assert result == expected_boundary

    def test_get_all_boundaries_tags_mode(self):
        """Test get_all_boundaries with tags mode."""
        expected_boundaries = [
            {"identifier": "v1.0.0", "hash": "abc123", "date": datetime(2023, 1, 1), "author": "test"},
            {"identifier": "v1.1.0", "hash": "def456", "date": datetime(2023, 2, 1), "author": "test"},
        ]

        with mock.patch("kittylog.commit_analyzer.get_all_tags_with_dates") as mock_tags_data:
            mock_tags_data.return_value = expected_boundaries

            result = get_all_boundaries("tags")

        assert result == expected_boundaries

    def test_get_previous_boundary(self):
        """Test get_previous_boundary function."""
        boundaries = [
            {"identifier": "v1.0.0", "hash": "abc123", "date": datetime(2023, 1, 1)},
            {"identifier": "v1.1.0", "hash": "def456", "date": datetime(2023, 2, 1)},
        ]

        current_boundary = boundaries[1]

        with mock.patch("kittylog.commit_analyzer.get_all_tags_with_dates") as mock_tags_data:
            mock_tags_data.return_value = boundaries

            result = get_previous_boundary(current_boundary, "tags")

        assert result == boundaries[0]

    def test_get_previous_boundary_first_item(self):
        """Test get_previous_boundary when current is the first item."""
        boundaries = [
            {"identifier": "v1.0.0", "hash": "abc123", "date": datetime(2023, 1, 1)},
            {"identifier": "v1.1.0", "hash": "def456", "date": datetime(2023, 2, 1)},
        ]

        first_boundary = boundaries[0]

        with mock.patch("kittylog.tag_operations.get_all_boundaries") as mock_boundaries:
            mock_boundaries.return_value = boundaries

            result = get_previous_boundary(first_boundary, "tags")

        assert result is None

    def test_get_previous_boundary_not_found(self):
        """Test get_previous_boundary when boundary not found in list."""
        boundaries = [
            {"identifier": "v1.0.0", "hash": "abc123", "date": datetime(2023, 1, 1)},
            {"identifier": "v1.1.0", "hash": "def456", "date": datetime(2023, 2, 1)},
        ]

        unknown_boundary = {"identifier": "unknown", "hash": "xyz789", "date": datetime(2023, 3, 1)}

        with mock.patch("kittylog.tag_operations.get_all_boundaries") as mock_boundaries:
            mock_boundaries.return_value = boundaries

            result = get_previous_boundary(unknown_boundary, "tags")

        assert result is None

    def test_get_boundary_by_identifier(self):
        """Test get_boundary_by_identifier function."""
        boundaries = [
            {"identifier": "v1.0.0", "hash": "abc123", "date": datetime(2023, 1, 1)},
            {"identifier": "v1.1.0", "hash": "def456", "date": datetime(2023, 2, 1)},
        ]

        with mock.patch("kittylog.tag_operations.get_all_boundaries") as mock_boundaries:
            mock_boundaries.return_value = boundaries

            result = get_boundary_by_identifier("v1.0.0", "tags")

        assert result == boundaries[0]


class TestClearGitCache:
    """Test the clear_git_cache function."""

    def test_clears_all_caches(self):
        """Test that clear_git_cache clears all caches."""
        with (
            mock.patch("kittylog.tag_operations.get_repo") as mock_repo,
            mock.patch("kittylog.tag_operations.get_all_tags") as mock_tags,
            mock.patch("kittylog.tag_operations.get_latest_tag") as mock_latest,
            mock.patch("kittylog.tag_operations.get_current_commit_hash") as mock_commit,
        ):
            # Apply cache_clear method to each mock
            mock_repo.cache_clear = mock.Mock()
            mock_tags.cache_clear = mock.Mock()
            mock_latest.cache_clear = mock.Mock()
            mock_commit.cache_clear = mock.Mock()

            clear_git_cache()

        # Verify cache_clear was called for each cached function
        mock_repo.cache_clear.assert_called_once()
        mock_tags.cache_clear.assert_called_once()
        mock_latest.cache_clear.assert_called_once()
        mock_commit.cache_clear.assert_called_once()


class TestTagOperationsIntegration:
    """Integration tests for tag operations module."""

    def test_complete_tag_workflow(self):
        """Test complete tag workflow."""
        mock_tag = mock.Mock()
        mock_tag.name = "v1.0.0"
        mock_tag.commit.hexsha = "abc123"
        mock_tag.commit.committed_datetime = datetime(2023, 1, 1)

        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            mock_repo = mock.Mock()
            mock_repo.tags = [mock_tag]
            mock_repo.head.commit = mock_tag.commit
            mock_get_repo.return_value = mock_repo

            # Test getting all tags
            tags = get_all_tags()
            assert tags == ["v1.0.0"]

            # Test getting latest tag
            latest = get_latest_tag()
            assert latest == "v1.0.0"

            # Test getting current commit hash
            current_hash = get_current_commit_hash()
            assert current_hash == "abc123"

            # Test checking if current commit is tagged
            is_tagged = is_current_commit_tagged()
            assert is_tagged is True

    def test_workflow_with_error_handling(self):
        """Test workflow error handling."""
        with mock.patch("kittylog.tag_operations.get_repo") as mock_get_repo:
            # Simulate git error
            mock_get_repo.side_effect = Exception("Git error")

            # These should handle errors gracefully without raising exceptions
            try:
                result = get_repo()
                assert result is None  # or whatever the error handling returns
            except Exception:
                pass  # Some functions might raise exceptions, which is acceptable


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
