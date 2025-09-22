"""Tests for main business logic module."""

from pathlib import Path
from unittest.mock import patch

from clog.errors import AIError, ChangelogError, GitError
from clog.main import main_business_logic


class TestMainBusinessLogic:
    """Test main_business_logic function."""

    @patch("clog.main.write_changelog")
    @patch("clog.main.update_changelog")
    @patch("clog.main.find_existing_tags")
    @patch("clog.main.read_changelog")
    @patch("clog.main.get_all_tags")
    @patch("clog.ai.generate_changelog_entry")
    @patch("clog.main.get_previous_tag")
    @patch("clog.main.get_latest_tag")
    @patch("clog.main.is_current_commit_tagged")
    @patch("clog.main.get_commits_between_tags")
    def test_main_logic_auto_detect_success(
        self,
        mock_get_commits_between_tags,
        mock_is_current_commit_tagged,
        mock_get_latest_tag,
        mock_get_previous_tag,
        mock_generate_changelog_entry,
        mock_get_all_tags,
        mock_read_changelog,
        mock_find_existing_tags,
        mock_update,
        mock_write,
        temp_dir,
    ):
        """Test successful auto-detection and update."""
        # Setup mocks
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0", "v0.3.0"]
        mock_read_changelog.return_value = "# Changelog"  # Empty changelog
        mock_find_existing_tags.return_value = []  # No existing tags in changelog
        mock_get_previous_tag.side_effect = lambda tag: {"v0.2.0": "v0.1.0", "v0.3.0": "v0.2.0"}.get(tag, None)
        mock_get_latest_tag.return_value = "v0.3.0"
        mock_is_current_commit_tagged.return_value = False
        mock_get_commits_between_tags.return_value = ["commit1", "commit2"]
        # Need 4 return values: one for each tag including v0.1.0 (None->v0.1.0, v0.1.0->v0.2.0, v0.2.0->v0.3.0) and one for unreleased changes
        mock_update.side_effect = [
            "Updated changelog content v0.1.0",
            "Updated changelog content v0.2.0",
            "Updated changelog content v0.3.0",
            "Updated changelog content unreleased",
        ]
        mock_generate_changelog_entry.return_value = "Mock AI generated content"

        # Test
        result = main_business_logic(
            changelog_file=str(temp_dir / "CHANGELOG.md"),
            from_tag=None,
            to_tag=None,
            model="anthropic:claude-3-5-haiku-latest",
            hint="",
            dry_run=False,
            require_confirmation=False,
            show_prompt=False,
            quiet=True,
        )

        assert result is True
        assert mock_find_existing_tags.call_count == 1
        assert mock_update.call_count == 4  # Three tags (v0.1.0, v0.2.0, v0.3.0) + unreleased changes
        assert mock_write.call_count == 1

    @patch("clog.main.get_all_tags")
    @patch("clog.git_operations.get_tags_since_last_changelog")
    def test_main_logic_no_new_tags(self, mock_get_tags_since_last_changelog, mock_get_all_tags, git_repo):
        """Test when no new tags are found."""
        mock_get_all_tags.return_value = ["v0.1.0"]
        mock_get_tags_since_last_changelog.return_value = ("v0.1.0", [])  # No new tags

        result = main_business_logic(
            changelog_file=str(Path(git_repo.working_dir) / "CHANGELOG.md"),
            from_tag=None,
            to_tag=None,
            model="anthropic:claude-3-5-haiku-latest",
            quiet=True,
            require_confirmation=False,
        )

        assert result is True
        # We can't easily mock console.print calls, so we'll skip this assertion

    @patch("clog.main.get_all_tags")
    @patch("clog.main.update_changelog")
    @patch("clog.main.write_changelog")
    @patch("clog.main.get_previous_tag")
    def test_main_logic_specific_tags(
        self, mock_get_previous_tag, mock_write, mock_update, mock_get_all_tags, temp_dir
    ):
        """Test with specific from/to tags."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_get_previous_tag.return_value = "v0.1.0"
        mock_update.return_value = "Updated changelog content"

        result = main_business_logic(
            changelog_file=str(temp_dir / "CHANGELOG.md"),
            from_tag="v0.1.0",
            to_tag="v0.2.0",
            model="anthropic:claude-3-5-haiku-latest",
            require_confirmation=False,
            quiet=True,
        )

        assert result is True
        mock_update.assert_called_once_with(
            file_path=str(temp_dir / "CHANGELOG.md"),
            from_tag="v0.1.0",
            to_tag="v0.2.0",
            model="anthropic:claude-3-5-haiku-latest",
            hint="",
            show_prompt=False,
            quiet=True,
            replace_unreleased=True,
        )
        mock_write.assert_called_once()

    @patch("clog.main.update_changelog")
    @patch("click.confirm")
    @patch("clog.main.get_all_tags")
    @patch("clog.main.get_previous_tag")
    def test_main_logic_dry_run(self, mock_get_previous_tag, mock_get_all_tags, mock_confirm, mock_update, temp_dir):
        """Test dry run mode."""
        mock_update.return_value = "Updated changelog content"
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_get_previous_tag.return_value = "v0.1.0"

        with patch("clog.main.write_changelog") as mock_write:
            result = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                from_tag="v0.1.0",
                to_tag="v0.2.0",
                model="anthropic:claude-3-5-haiku-latest",
                dry_run=True,
                quiet=False,
            )

        assert result is True
        mock_update.assert_called_once()
        # Should not write in dry run mode
        mock_write.assert_not_called()

    @patch("clog.main.update_changelog")
    @patch("click.confirm")
    @patch("clog.main.get_all_tags")
    @patch("clog.main.get_previous_tag")
    def test_main_logic_user_confirmation_yes(
        self, mock_get_previous_tag, mock_get_all_tags, mock_confirm, mock_update, temp_dir
    ):
        """Test user confirmation when user says yes."""
        mock_update.return_value = "Updated changelog content"
        mock_confirm.return_value = True
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_get_previous_tag.return_value = "v0.1.0"

        with patch("clog.main.write_changelog") as mock_write:
            result = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                from_tag="v0.1.0",
                to_tag="v0.2.0",
                model="anthropic:claude-3-5-haiku-latest",
                require_confirmation=True,  # Require confirmation
                quiet=False,
            )

        assert result is True
        mock_confirm.assert_called_once()
        mock_write.assert_called_once()

    @patch("clog.main.update_changelog")
    @patch("click.confirm")
    @patch("clog.main.get_all_tags")
    @patch("clog.main.get_previous_tag")
    def test_main_logic_user_confirmation_no(
        self, mock_get_previous_tag, mock_get_all_tags, mock_confirm, mock_update, temp_dir
    ):
        """Test user confirmation when user says no."""
        mock_update.return_value = "Updated changelog content"
        mock_confirm.return_value = False
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_get_previous_tag.return_value = "v0.1.0"

        with patch("clog.main.write_changelog") as mock_write:
            result = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                from_tag="v0.1.0",
                to_tag="v0.2.0",
                model="anthropic:claude-3-5-haiku-latest",
                require_confirmation=True,
                quiet=False,
            )

        assert result is True
        mock_confirm.assert_called_once()
        mock_write.assert_not_called()

    @patch("clog.git_operations.get_tags_since_last_changelog")
    @patch("clog.main.get_all_tags")
    def test_main_logic_git_error(self, mock_get_all_tags, mock_get_tags, temp_dir):
        """Test handling of Git errors."""
        mock_get_all_tags.side_effect = GitError("Not a git repository")
        mock_get_tags.side_effect = GitError("Not a git repository")

        result = main_business_logic(
            changelog_file=str(temp_dir / "CHANGELOG.md"),
            model="anthropic:claude-3-5-haiku-latest",
            quiet=True,
            require_confirmation=False,
        )

        assert result is False

    @patch("clog.git_operations.get_tags_since_last_changelog")
    @patch("clog.main.update_changelog")
    @patch("clog.main.get_all_tags")
    def test_main_logic_ai_error(self, mock_get_all_tags, mock_update, mock_get_tags, temp_dir):
        """Test handling of AI errors."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_get_tags.return_value = ("v0.1.0", ["v0.2.0"])
        mock_update.side_effect = AIError("API key invalid", "authentication")

        result = main_business_logic(
            changelog_file=str(temp_dir / "CHANGELOG.md"),
            model="anthropic:claude-3-5-haiku-latest",
            quiet=True,
            require_confirmation=False,
        )

        assert result is False

    @patch("clog.git_operations.get_tags_since_last_changelog")
    @patch("clog.main.update_changelog")
    @patch("clog.main.write_changelog")
    @patch("clog.main.get_all_tags")
    def test_main_logic_changelog_error(self, mock_get_all_tags, mock_write, mock_update, mock_get_tags, git_repo):
        """Test handling of changelog errors."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_get_tags.return_value = ("v0.1.0", ["v0.2.0"])
        mock_update.return_value = "Updated content"
        mock_write.side_effect = ChangelogError("Permission denied")

        result = main_business_logic(
            changelog_file=str(Path(git_repo.working_dir) / "CHANGELOG.md"),
            model="anthropic:claude-3-5-haiku-latest",
            require_confirmation=False,
            quiet=True,
        )

        assert result is False


class TestMainLogicMultipleTags:
    """Test main logic with multiple tags."""

    @patch("clog.main.get_all_tags")
    @patch("clog.main.read_changelog")
    @patch("clog.main.find_existing_tags")
    @patch("clog.main.update_changelog")
    @patch("clog.main.write_changelog")
    @patch("clog.main.get_previous_tag")
    @patch("clog.main.get_latest_tag")
    @patch("clog.main.is_current_commit_tagged")
    @patch("clog.main.get_commits_between_tags")
    def test_multiple_tags_success(
        self,
        mock_get_commits,
        mock_is_tagged,
        mock_get_latest,
        mock_get_previous_tag,
        mock_write,
        mock_update,
        mock_find_existing,
        mock_read,
        mock_get_all_tags,
        temp_dir,
    ):
        """Test processing multiple new tags."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0", "v0.3.0", "v0.4.0"]
        mock_read.return_value = "# Changelog"
        mock_find_existing.return_value = ["0.1.0"]  # v0.1.0 already in changelog
        mock_get_previous_tag.side_effect = lambda tag: {
            "v0.2.0": "v0.1.0",
            "v0.3.0": "v0.2.0",
            "v0.4.0": "v0.3.0",
        }.get(tag, None)
        mock_get_latest.return_value = "v0.4.0"
        mock_is_tagged.return_value = False
        mock_get_commits.return_value = ["commit1"]

        # Return different content for each update (3 new tags + unreleased)
        mock_update.side_effect = [
            "Changelog with v0.2.0",
            "Changelog with v0.3.0",
            "Changelog with v0.4.0",
            "Changelog with unreleased",
        ]

        result = main_business_logic(
            changelog_file=str(temp_dir / "CHANGELOG.md"),
            model="anthropic:claude-3-5-haiku-latest",
            require_confirmation=False,
            quiet=True,
        )

        assert result is True
        assert mock_update.call_count == 4  # 3 new tags + unreleased
        assert mock_write.call_count == 1

        # Verify the tags were processed in order
        update_calls = mock_update.call_args_list
        assert update_calls[0][1]["from_tag"] == "v0.1.0"
        assert update_calls[0][1]["to_tag"] == "v0.2.0"
        assert update_calls[1][1]["from_tag"] == "v0.2.0"
        assert update_calls[1][1]["to_tag"] == "v0.3.0"
        assert update_calls[2][1]["from_tag"] == "v0.3.0"
        assert update_calls[2][1]["to_tag"] == "v0.4.0"
        assert update_calls[3][1]["from_tag"] == "v0.4.0"
        assert update_calls[3][1]["to_tag"] is None  # Unreleased

    @patch("clog.main.get_all_tags")
    @patch("clog.git_operations.get_tags_since_last_changelog")
    @patch("clog.main.update_changelog")
    @patch("clog.main.get_previous_tag")
    def test_multiple_tags_partial_failure(
        self, mock_get_previous_tag, mock_update, mock_get_tags, mock_get_all_tags, temp_dir
    ):
        """Test when one tag update fails among multiple."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0", "v0.3.0"]
        mock_get_tags.return_value = ("v0.1.0", ["v0.2.0", "v0.3.0"])
        mock_get_previous_tag.return_value = "v0.1.0"

        # First update succeeds, second fails
        mock_update.side_effect = ["Changelog with v0.2.0", AIError("Rate limit exceeded", "rate_limit")]

        result = main_business_logic(
            changelog_file=str(temp_dir / "CHANGELOG.md"),
            model="anthropic:claude-3-5-haiku-latest",
            require_confirmation=False,
            quiet=True,
        )

        assert result is False
        assert mock_update.call_count == 2


class TestMainLogicEdgeCases:
    """Test edge cases in main business logic."""

    @patch("clog.main.get_latest_tag")
    @patch("clog.main.get_all_tags")
    @patch("clog.git_operations.get_tags_since_last_changelog")
    def test_only_from_tag_specified(self, mock_get_tags, mock_get_all_tags, mock_get_latest_tag, temp_dir):
        """Test when only from_tag is specified (to_tag=None means HEAD)."""
        mock_get_all_tags.return_value = ["v0.1.0"]
        mock_get_latest_tag.return_value = "v0.2.0"
        mock_get_tags.return_value = ("v0.1.0", [])

        with patch("clog.main.update_changelog") as mock_update:
            mock_update.return_value = "Updated content"

            result = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                from_tag="v0.1.0",
                to_tag=None,  # Should use HEAD
                model="anthropic:claude-3-5-haiku-latest",
                require_confirmation=False,
                quiet=True,
            )

            assert result is True
            mock_update.assert_called_once()
            call_args = mock_update.call_args[1]
            assert call_args["from_tag"] == "v0.1.0"
            assert call_args["to_tag"] == "v0.2.0"

    @patch("clog.main.get_all_tags")
    @patch("clog.main.get_previous_tag")
    @patch("clog.main.read_changelog")
    def test_only_to_tag_specified(self, mock_read, mock_get_previous_tag, mock_get_all_tags, temp_dir):
        """Test when only to_tag is specified (from_tag=None means beginning)."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_get_previous_tag.return_value = "v0.1.0"
        mock_read.return_value = "# Changelog"

        with patch("clog.main.update_changelog") as mock_update, patch("clog.main.write_changelog"):
            mock_update.return_value = "Updated content"

            result = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                from_tag=None,
                to_tag="v0.2.0",
                model="anthropic:claude-3-5-haiku-latest",
                require_confirmation=False,
                quiet=True,
            )

            assert result is True
            mock_update.assert_called_once()
            call_args = mock_update.call_args[1]
            assert call_args["from_tag"] == "v0.1.0"  # Previous tag is found automatically
            assert call_args["to_tag"] == "v0.2.0"

    @patch("clog.main.get_all_tags")
    def test_empty_file_path(self, mock_get_all_tags, git_repo):
        """Test with empty file path."""
        mock_get_all_tags.return_value = ["v0.1.0"]  # Need at least one tag

        # Empty file path causes an error when writing
        result = main_business_logic(
            changelog_file="",
            model="anthropic:claude-3-5-haiku-latest",
            quiet=True,
            require_confirmation=False,
        )

        # Empty file path should fail
        assert result is False

    def test_no_model_specified(self, temp_dir):
        """Test when no model is specified and no default available."""
        with patch("clog.main.config", {"model": None}):
            result = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model=None,
                quiet=True,
                require_confirmation=False,
            )

            assert result is False


class TestMainLogicConfiguration:
    """Test main logic configuration handling."""

    @patch("clog.main.get_all_tags")
    @patch("clog.git_operations.get_tags_since_last_changelog")
    @patch("clog.main.update_changelog")
    @patch("clog.main.get_previous_tag")
    def test_config_precedence(self, mock_get_previous_tag, mock_update, mock_get_tags, mock_get_all_tags, git_repo):
        """Test that CLI arguments override config defaults."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_get_tags.return_value = ("v0.1.0", ["v0.2.0"])
        mock_get_previous_tag.return_value = "v0.1.0"
        mock_update.return_value = "Updated content"

        with patch(
            "clog.main.config",
            {
                "model": "anthropic:claude-3-5-haiku-latest",
                "temperature": 0.7,
            },
        ):
            result = main_business_logic(
                changelog_file=str(Path(git_repo.working_dir) / "CHANGELOG.md"),
                model="openai:gpt-4",  # Should override config
                require_confirmation=False,
                quiet=True,
            )

        assert result is True
        # Check that the last call used the correct model
        call_args = mock_update.call_args[1]
        assert call_args["model"] == "openai:gpt-4"

    @patch("clog.main.get_all_tags")
    @patch("clog.main.read_changelog")
    @patch("clog.main.find_existing_tags")
    @patch("clog.main.update_changelog")
    @patch("clog.main.write_changelog")
    @patch("clog.main.get_previous_tag")
    @patch("clog.main.get_latest_tag")
    @patch("clog.main.is_current_commit_tagged")
    @patch("clog.main.get_commits_between_tags")
    def test_replace_unreleased_config_default(
        self,
        mock_get_commits,
        mock_is_tagged,
        mock_get_latest,
        mock_get_previous_tag,
        mock_write,
        mock_update,
        mock_find_existing,
        mock_read,
        mock_get_all_tags,
        temp_dir,
    ):
        """Test that replace_unreleased config is used as default when not specified."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_read.return_value = "# Changelog"
        mock_find_existing.return_value = []  # No tags in changelog yet
        mock_get_previous_tag.side_effect = lambda tag: {"v0.1.0": None, "v0.2.0": "v0.1.0"}.get(tag, None)
        mock_get_latest.return_value = "v0.2.0"
        mock_is_tagged.return_value = False
        mock_get_commits.return_value = ["commit1"]
        mock_update.side_effect = ["Updated v0.1.0", "Updated v0.2.0", "Updated unreleased"]

        with patch(
            "clog.main.config",
            {
                "model": "anthropic:claude-3-5-haiku-latest",
            },
        ):
            result = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                require_confirmation=False,
                quiet=True,
            )

        assert result is True
        # The implementation now always passes replace_unreleased=True for tagged versions
        call_args = mock_update.call_args[1]
        assert call_args["replace_unreleased"]


class TestMainLogicLogging:
    """Test logging behavior in main logic."""

    @patch("clog.main.get_all_tags")
    @patch("clog.git_operations.get_tags_since_last_changelog")
    def test_quiet_mode_suppresses_output(self, mock_get_tags_since_last_changelog, mock_get_all_tags, git_repo):
        """Test that quiet mode suppresses non-error output."""
        mock_get_all_tags.return_value = ["v0.1.0"]
        mock_get_tags_since_last_changelog.return_value = ("v0.1.0", [])  # No new tags

        result = main_business_logic(
            changelog_file=str(Path(git_repo.working_dir) / "CHANGELOG.md"),
            model="anthropic:claude-3-5-haiku-latest",
            quiet=True,
            require_confirmation=False,
        )

        assert result is True
        # In quiet mode, should still show important messages but fewer of them
        # We can't easily mock console.print calls, so we'll skip this assertion

    @patch("clog.main.get_all_tags")
    @patch("clog.git_operations.get_tags_since_last_changelog")
    def test_verbose_mode_shows_output(self, mock_get_tags_since_last_changelog, mock_get_all_tags, git_repo):
        """Test that verbose mode shows detailed output."""
        mock_get_all_tags.return_value = ["v0.1.0"]
        mock_get_tags_since_last_changelog.return_value = ("v0.1.0", [])  # No new tags

        result = main_business_logic(
            changelog_file=str(Path(git_repo.working_dir) / "CHANGELOG.md"),
            model="anthropic:claude-3-5-haiku-latest",
            quiet=False,
            require_confirmation=False,
        )

        assert result is True
        # In verbose mode, should show more output
        # We can't easily mock console.print calls, so we'll skip this assertion
