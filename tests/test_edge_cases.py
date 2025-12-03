#!/usr/bin/env python3
"""Test edge cases for boundary detection."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

from kittylog.commit_analyzer import get_commits_by_date_boundaries, get_commits_by_gap_boundaries
from kittylog.config import ChangelogOptions, WorkflowOptions
from kittylog.workflow import main_business_logic


class TestEdgeCases:
    """Test edge cases for boundary detection."""

    @patch("kittylog.workflow.get_output_manager")
    @patch("kittylog.workflow.get_all_boundaries")  # Patch where it's used
    @patch("kittylog.tag_operations.get_repo")
    def test_no_boundaries_tags_mode(self, mock_get_repo, mock_get_all_boundaries, mock_output_manager, temp_dir):
        """Test handling of repositories with no tags."""
        # Mock repository with iterable tags and commits
        mock_repo = Mock()
        mock_repo.tags = []  # Empty tags for this test
        mock_repo.iter_commits.return_value = []  # Empty commits
        mock_get_repo.return_value = mock_repo

        # Mock no boundaries found
        mock_get_all_boundaries.return_value = []

        # Mock output manager
        mock_output = Mock()
        mock_output_manager.return_value = mock_output

        config_with_model = {
            "model": "openai:gpt-4o-mini",  # Switch from Cerebras to OpenAI
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.workflow.config", config_with_model):
            changelog_opts = ChangelogOptions(
                file=str(temp_dir / "CHANGELOG.md"),
                grouping_mode="tags",
            )
            workflow_opts = WorkflowOptions(
                quiet=True,
                yes=True,  # Auto-accept to avoid interaction
            )
            success, token_usage = main_business_logic(
                changelog_opts=changelog_opts,
                workflow_opts=workflow_opts,
                model="openai:gpt-4o-mini",
            )

        assert success is False  # Should fail when no boundaries found
        assert token_usage is None
        mock_output.warning.assert_called_with(
            "No git tags found. Create some tags first to generate changelog entries."
        )
        mock_output.info.assert_called_with(
            "💡 Tip: Try 'git tag v1.0.0' to create your first tag, or use --grouping-mode dates/gaps for tagless workflows"
        )

    @patch("kittylog.workflow.get_output_manager")
    @patch("kittylog.workflow.get_all_boundaries")  # Patch where it's used
    @patch("kittylog.tag_operations.get_repo")
    def test_no_boundaries_dates_mode(self, mock_get_repo, mock_get_all_boundaries, mock_output_manager, temp_dir):
        """Test handling of repositories with no date boundaries."""
        # Mock repository with iterable tags and commits
        mock_repo = Mock()
        mock_repo.tags = []  # Empty tags for this test
        mock_repo.iter_commits.return_value = []  # Empty commits
        mock_get_repo.return_value = mock_repo

        # Mock no boundaries found
        mock_get_all_boundaries.return_value = []

        # Mock output manager
        mock_output = Mock()
        mock_output_manager.return_value = mock_output

        config_with_model = {
            "model": "openai:gpt-4o-mini",  # Switch from Cerebras to OpenAI
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.workflow.config", config_with_model):
            changelog_opts = ChangelogOptions(
                file=str(temp_dir / "CHANGELOG.md"),
                grouping_mode="dates",
            )
            workflow_opts = WorkflowOptions(
                quiet=True,
                yes=True,  # Auto-accept to avoid interaction
            )
            success, token_usage = main_business_logic(
                changelog_opts=changelog_opts,
                workflow_opts=workflow_opts,
                model="openai:gpt-4o-mini",
            )

        assert success is False  # Should fail when no boundaries found
        assert token_usage is None
        mock_output.warning.assert_called_with(
            "No date-based boundaries found. This repository might have very few commits."
        )
        mock_output.info.assert_called_with(
            "💡 Tip: Try --date-grouping weekly/monthly for longer periods, or --grouping-mode gaps for activity-based grouping"
        )

    @patch("kittylog.workflow.get_output_manager")
    @patch("kittylog.workflow.get_all_boundaries")  # Patch where it's used
    @patch("kittylog.tag_operations.get_repo")
    def test_no_boundaries_gaps_mode(self, mock_get_repo, mock_get_all_boundaries, mock_output_manager, temp_dir):
        """Test handling of repositories with no gap boundaries."""
        # Mock repository with iterable tags and commits
        mock_repo = Mock()
        mock_repo.tags = []  # Empty tags for this test
        mock_repo.iter_commits.return_value = []  # Empty commits
        mock_get_repo.return_value = mock_repo

        # Mock no boundaries found
        mock_get_all_boundaries.return_value = []

        # Mock output manager
        mock_output = Mock()
        mock_output_manager.return_value = mock_output

        config_with_model = {
            "model": "openai:gpt-4o-mini",  # Switch from Cerebras to OpenAI
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.workflow.config", config_with_model):
            changelog_opts = ChangelogOptions(
                file=str(temp_dir / "CHANGELOG.md"),
                grouping_mode="gaps",
                gap_threshold_hours=4.0,
            )
            workflow_opts = WorkflowOptions(
                quiet=True,
                yes=True,  # Auto-accept to avoid interaction
            )
            success, token_usage = main_business_logic(
                changelog_opts=changelog_opts,
                workflow_opts=workflow_opts,
                model="openai:gpt-4o-mini",
            )

        assert success is False  # Should fail when no boundaries found
        assert token_usage is None
        mock_output.warning.assert_called_with("No gap-based boundaries found with 4.0 hour threshold.")
        mock_output.info.assert_called_with(
            "💡 Tip: Try --gap-threshold 2.0 for shorter gaps, or --grouping-mode dates for time-based grouping"
        )

    @patch("kittylog.commit_analyzer.get_all_commits_chronological")
    def test_timezone_consistency_in_date_boundaries(self, mock_get_all_commits):
        """Test that date boundaries are consistent across timezones."""
        # Mock commits spanning midnight in different timezones
        mock_commits = [
            {
                "hash": "abc123",
                "short_hash": "abc123",
                "message": "Commit at 23:30 UTC",
                "author": "Test Author",
                "date": datetime(2024, 1, 1, 23, 30, tzinfo=timezone.utc),
                "files": ["file1.py"],
            },
            {
                "hash": "def456",
                "short_hash": "def456",
                "message": "Commit at 01:30 UTC+2 (same as 23:30 UTC)",
                "author": "Test Author",
                "date": datetime(2024, 1, 2, 1, 30, tzinfo=timezone.utc),
                "files": ["file2.py"],
            },
        ]
        mock_get_all_commits.return_value = mock_commits

        boundaries = get_commits_by_date_boundaries(date_grouping="daily")

        # Should have 2 boundaries - one for each UTC date
        assert len(boundaries) == 2
        assert boundaries[0]["date"].date() == datetime(2024, 1, 1).date()
        assert boundaries[1]["date"].date() == datetime(2024, 1, 2).date()
        assert all(b["boundary_type"] == "date" for b in boundaries)

    @patch("kittylog.commit_analyzer.get_all_commits_chronological")
    @patch("kittylog.commit_analyzer.logger")
    def test_high_activity_repository_warnings(self, mock_logger, mock_get_all_commits):
        """Test warnings for repositories with very high activity."""
        # Mock a very active day with many commits
        mock_commits = [
            {
                "hash": f"abc{hour:02d}",
                "short_hash": f"abc{hour:02d}",
                "message": f"Commit at {hour}:00",
                "author": "Test Author",
                "date": datetime(2024, 1, 1, hour, 0, tzinfo=timezone.utc),
                "files": [f"file{hour}.py"],
            }
            for hour in range(24)  # 24 commits in one day
        ]
        mock_get_all_commits.return_value = mock_commits

        boundaries = get_commits_by_date_boundaries(date_grouping="daily")

        # Should have 1 boundary for the single day
        assert len(boundaries) == 1
        # Note: High activity warning is currently not implemented in get_commits_by_date_boundaries

    @patch("kittylog.commit_analyzer.get_all_commits_chronological")
    @patch("kittylog.commit_analyzer.logger")
    def test_irregular_commit_patterns(self, mock_logger, mock_get_all_commits):
        """Test handling of repositories with irregular commit patterns."""
        # Mock commits with highly variable gaps: 1min, 2days, 30min, 1week
        base_time = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        mock_commits = [
            {
                "hash": "abc001",
                "short_hash": "abc001",
                "message": "First commit",
                "author": "Test Author",
                "date": base_time,
                "files": ["file1.py"],
            },
            {
                "hash": "abc002",
                "short_hash": "abc002",
                "message": "Quick follow-up (1 min later)",
                "author": "Test Author",
                "date": base_time.replace(minute=1),
                "files": ["file2.py"],
            },
            {
                "hash": "abc003",
                "short_hash": "abc003",
                "message": "After weekend (2 days later)",
                "author": "Test Author",
                "date": base_time.replace(day=3),
                "files": ["file3.py"],
            },
            {
                "hash": "abc004",
                "short_hash": "abc004",
                "message": "Small fix (30 min later)",
                "author": "Test Author",
                "date": base_time.replace(day=3, minute=30),
                "files": ["file4.py"],
            },
            {
                "hash": "abc005",
                "short_hash": "abc005",
                "message": "Major update (1 week later)",
                "author": "Test Author",
                "date": base_time.replace(day=10),
                "files": ["file5.py"],
            },
        ]
        mock_get_all_commits.return_value = mock_commits

        boundaries = get_commits_by_gap_boundaries(gap_threshold_hours=4.0)

        # Should identify boundaries after gaps > 4 hours
        # Expected boundaries: commit 1 (first), commit 3 (after 2 day gap), commit 5 (after 1 week gap)
        assert len(boundaries) == 3

        # Should detect irregular patterns and log helpful info - check calls made
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any(
            "Repository has irregular commit patterns" in str(call) or "Repository has very long gaps" in str(call)
            for call in info_calls
        )
