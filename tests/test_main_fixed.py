#!/usr/bin/env python3
"""Fixed tests for main module using current function signatures."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

from kittylog.main import main_business_logic


class TestMainBusinessLogicFixed:
    """Test main business logic with proper mocks."""

    @patch("kittylog.main.get_output_manager")
    @patch("kittylog.git_operations.get_repo")
    @patch("kittylog.changelog.write_changelog")
    @patch("kittylog.changelog.read_changelog")
    @patch("kittylog.changelog.update_changelog")
    @patch("kittylog.git_operations.get_all_boundaries")
    @patch("kittylog.changelog.find_existing_boundaries")
    @patch("kittylog.git_operations.get_latest_boundary")
    @patch("kittylog.git_operations.is_current_commit_tagged")
    @patch("kittylog.git_operations.generate_boundary_identifier")
    @patch("kittylog.git_operations.generate_boundary_display_name")
    @patch("kittylog.git_operations.get_commits_between_tags")
    @patch("kittylog.git_operations.get_previous_boundary")
    def test_main_logic_tags_success(
        self,
        mock_get_previous_boundary,
        mock_get_commits_between_tags,
        mock_generate_display,
        mock_generate_identifier,
        mock_is_tagged,
        mock_get_latest_boundary,
        mock_find_existing,
        mock_get_all_boundaries,
        mock_update,
        mock_read,
        mock_write,
        mock_get_repo,
        mock_output_manager,
        temp_dir,
    ):
        """Test successful tags mode processing."""
        # Mock repository - since we're mocking get_all_boundaries, this doesn't need to be complex
        mock_repo = Mock()
        mock_repo.tags = []
        mock_repo.iter_commits.return_value = []
        mock_get_repo.return_value = mock_repo

        # Mock output manager
        mock_output = Mock()
        mock_output_manager.return_value = mock_output

        # Mock boundaries
        mock_boundaries = [
            {
                "hash": "abc123",
                "short_hash": "abc123",
                "message": "Release v1.0.0",
                "author": "Test Author",
                "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "files": [],
                "boundary_type": "tag",
                "identifier": "v1.0.0",
            }
        ]

        mock_get_all_boundaries.return_value = mock_boundaries
        mock_find_existing.return_value = set()  # No existing boundaries
        mock_get_latest_boundary.return_value = mock_boundaries[0]
        mock_get_previous_boundary.return_value = None  # No previous boundary for first tag
        mock_is_tagged.return_value = False
        mock_read.return_value = "# Changelog\n"

        # Mock commits to simulate unreleased changes
        mock_unreleased_commits = [
            {"hash": "def456", "message": "Unreleased change", "files": ["new_file.py"]}
        ]
        mock_get_commits_between_tags.return_value = mock_unreleased_commits

        # Mock identifier functions - ensure consistent identifier
        mock_generate_identifier.return_value = "v1.0.0"
        mock_generate_display.return_value = "[v1.0.0] - January 1, 2024"

        mock_update.return_value = ("Updated content", {"total_tokens": 100})

        config_with_model = {
            "model": "openai:gpt-4o-mini",  # Switch from Cerebras to OpenAI
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with (
            patch("kittylog.main.config", config_with_model),
            patch("kittylog.utils.find_changelog_file", return_value=str(temp_dir / "CHANGELOG.md")),
        ):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model="openai:gpt-4o-mini",
                quiet=True,
                require_confirmation=False,
                grouping_mode="tags",
                update_all_entries=True,  # Force processing of all boundaries
            )

        assert success is True
        assert token_usage is not None
        mock_update.assert_called_once()
        mock_write.assert_called_once()

    @patch("kittylog.main.get_output_manager")
    @patch("kittylog.git_operations.get_all_boundaries")
    @patch("kittylog.git_operations.get_repo")
    def test_main_logic_no_boundaries_warning(
        self, mock_get_repo, mock_get_all_boundaries, mock_output_manager, temp_dir
    ):
        """Test handling when no boundaries are found."""
        # Mock repository with iterable tags and commits
        mock_repo = Mock()
        mock_repo.tags = []  # Empty tags for this test
        mock_repo.iter_commits.return_value = []  # Empty commits
        mock_get_repo.return_value = mock_repo

        # Mock no boundaries
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

        with (
            patch("kittylog.main.config", config_with_model),
            patch("kittylog.utils.find_changelog_file", return_value=str(temp_dir / "CHANGELOG.md")),
        ):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model="openai:gpt-4o-mini",
                quiet=True,
                grouping_mode="tags",
            )

        assert success is True
        assert token_usage is None
        mock_output.warning.assert_called()
        mock_output.info.assert_called()

    @patch("kittylog.main.get_output_manager")
    @patch("kittylog.git_operations.get_repo")
    @patch("kittylog.changelog.write_changelog")
    @patch("kittylog.changelog.read_changelog")
    @patch("kittylog.changelog.update_changelog")
    @patch("kittylog.git_operations.get_all_boundaries")
    @patch("kittylog.changelog.find_existing_boundaries")
    @patch("kittylog.git_operations.get_latest_boundary")
    @patch("kittylog.git_operations.is_current_commit_tagged")
    @patch("kittylog.git_operations.generate_boundary_identifier")
    @patch("kittylog.git_operations.generate_boundary_display_name")
    def test_main_logic_dates_mode(
        self,
        mock_generate_display,
        mock_generate_identifier,
        mock_is_tagged,
        mock_get_latest_boundary,
        mock_find_existing,
        mock_get_all_boundaries,
        mock_update,
        mock_read,
        mock_write,
        mock_get_repo,
        mock_output_manager,
        temp_dir,
    ):
        """Test date-based boundary mode."""
        # Mock repository with iterable tags and commits
        mock_repo = Mock()
        mock_repo.tags = []  # Empty tags for this test
        mock_repo.iter_commits.return_value = []  # Empty commits
        mock_get_repo.return_value = mock_repo

        # Mock output manager
        mock_output = Mock()
        mock_output_manager.return_value = mock_output

        # Mock date boundaries
        mock_boundaries = [
            {
                "hash": "abc123",
                "short_hash": "abc123",
                "message": "Daily work",
                "author": "Test Author",
                "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "files": [],
                "boundary_type": "date",
                "identifier": "2024-01-01",
            }
        ]

        mock_get_all_boundaries.return_value = mock_boundaries
        mock_find_existing.return_value = set()
        mock_get_latest_boundary.return_value = mock_boundaries[0]
        mock_is_tagged.return_value = False
        mock_read.return_value = "# Changelog\n"

        mock_generate_identifier.return_value = "2024-01-01"
        mock_generate_display.return_value = "[2024-01-01] - January 1, 2024"

        mock_update.return_value = ("Updated content", {"total_tokens": 100})

        config_with_model = {
            "model": "openai:gpt-4o-mini",  # Switch from Cerebras to OpenAI
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with (
            patch("kittylog.main.config", config_with_model),
            patch("kittylog.utils.find_changelog_file", return_value=str(temp_dir / "CHANGELOG.md")),
        ):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model="openai:gpt-4o-mini",
                quiet=True,
                require_confirmation=False,
                grouping_mode="dates",
            )

        assert success is True
        assert token_usage is not None
        mock_update.assert_called_once()
        mock_write.assert_called_once()

    def test_main_logic_no_model_error(self, temp_dir):
        """Test error handling when no model is specified."""
        config_without_model = {
            "model": None,
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_without_model):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"), model=None, quiet=True
            )

        assert success is False
        assert token_usage is None

    @patch("kittylog.main.get_output_manager")
    @patch("kittylog.git_operations.get_repo")
    @patch("kittylog.changelog.write_changelog")
    @patch("kittylog.changelog.read_changelog")
    @patch("kittylog.changelog.update_changelog")
    @patch("kittylog.git_operations.get_all_boundaries")
    @patch("kittylog.changelog.find_existing_boundaries")
    @patch("kittylog.git_operations.get_latest_boundary")
    @patch("kittylog.git_operations.is_current_commit_tagged")
    @patch("kittylog.git_operations.generate_boundary_identifier")
    @patch("kittylog.git_operations.generate_boundary_display_name")
    def test_main_logic_dry_run_mode(
        self,
        mock_generate_display,
        mock_generate_identifier,
        mock_is_tagged,
        mock_get_latest_boundary,
        mock_find_existing,
        mock_get_all_boundaries,
        mock_update,
        mock_read,
        mock_write,
        mock_get_repo,
        mock_output_manager,
        temp_dir,
    ):
        """Test dry run mode doesn't write changes."""
        # Mock repository with iterable tags and commits
        mock_repo = Mock()
        mock_repo.tags = []  # Empty tags for this test
        mock_repo.iter_commits.return_value = []  # Empty commits
        mock_get_repo.return_value = mock_repo

        # Mock output manager
        mock_output = Mock()
        mock_output_manager.return_value = mock_output

        # Mock boundaries
        mock_boundaries = [
            {
                "hash": "abc123",
                "short_hash": "abc123",
                "message": "Release v1.0.0",
                "author": "Test Author",
                "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "files": [],
                "boundary_type": "tag",
                "identifier": "v1.0.0",
            }
        ]

        mock_get_all_boundaries.return_value = mock_boundaries
        mock_find_existing.return_value = set()
        mock_get_latest_boundary.return_value = mock_boundaries[0]
        mock_is_tagged.return_value = False
        mock_read.return_value = "# Changelog\n"

        mock_generate_identifier.return_value = "v1.0.0"
        mock_generate_display.return_value = "[v1.0.0] - January 1, 2024"

        mock_update.return_value = ("Updated content", {"total_tokens": 100})

        config_with_model = {
            "model": "openai:gpt-4o-mini",  # Switch from Cerebras to OpenAI
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with (
            patch("kittylog.main.config", config_with_model),
            patch("kittylog.utils.find_changelog_file", return_value=str(temp_dir / "CHANGELOG.md")),
        ):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model="openai:gpt-4o-mini",
                quiet=True,
                require_confirmation=False,
                dry_run=True,  # Enable dry run
                grouping_mode="tags",
            )

        assert success is True
        assert token_usage is not None
        mock_update.assert_called_once()
        # In dry run mode, write_changelog should NOT be called
        mock_write.assert_not_called()
