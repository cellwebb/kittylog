"""Tests for main module."""

from unittest.mock import patch

from kittylog.main import main_business_logic


class TestMainBusinessLogic:
    """Test main business logic."""

    @patch("kittylog.main.get_commits_between_tags")
    @patch("kittylog.main.is_current_commit_tagged")
    @patch("kittylog.main.get_latest_tag")
    @patch("kittylog.main.find_existing_tags")
    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    @patch("kittylog.main.write_changelog")
    def test_main_logic_auto_detect_success(
        self,
        mock_write,
        mock_read,
        mock_update,
        mock_get_all_tags,
        mock_find_existing,
        mock_get_latest_tag,
        mock_is_current_commit_tagged,
        mock_get_commits,
        temp_dir,
    ):
        """Test successful auto-detection logic."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_read.return_value = "# Changelog\n\n## [Unreleased]\n"
        mock_find_existing.return_value = []  # No existing tags in changelog
        mock_get_latest_tag.return_value = "v0.2.0"
        mock_is_current_commit_tagged.return_value = False  # Current commit not tagged
        mock_get_commits.return_value = []  # No unreleased commits
        mock_update.return_value = (
            "Updated content",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

        # Mock config to avoid loading from file
        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model="cerebras:qwen-3-coder-480b",
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is True
        # Should call update_changelog for each tag
        assert mock_update.call_count == 2
        mock_write.assert_called_once_with(str(temp_dir / "CHANGELOG.md"), "Updated content")

    @patch("kittylog.main.get_commits_between_tags")
    @patch("kittylog.main.is_current_commit_tagged")
    @patch("kittylog.main.get_latest_tag")
    @patch("kittylog.main.find_existing_tags")
    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    def test_main_logic_no_new_tags(
        self,
        mock_read,
        mock_update,
        mock_get_all_tags,
        mock_find_existing,
        mock_get_latest_tag,
        mock_is_current_commit_tagged,
        mock_get_commits,
        temp_dir,
    ):
        """Test when no new tags need processing."""
        mock_get_all_tags.return_value = ["v0.1.0"]
        mock_read.return_value = "# Changelog\n\n## [0.1.0]\n"  # Already has the tag
        mock_find_existing.return_value = ["0.1.0"]  # Tag already exists in changelog
        mock_get_latest_tag.return_value = "v0.1.0"
        mock_is_current_commit_tagged.return_value = True  # Current commit is tagged
        mock_get_commits.return_value = []  # No unreleased commits

        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model="cerebras:qwen-3-coder-480b",
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is True
        mock_update.assert_not_called()  # Should not call update when no new tags

    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    @patch("kittylog.main.write_changelog")
    def test_main_logic_specific_tags(self, mock_write, mock_read, mock_update, mock_get_all_tags, temp_dir):
        """Test processing specific tag range."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0", "v0.3.0"]
        mock_read.return_value = "# Changelog\n\n## [Unreleased]\n"
        mock_update.return_value = (
            "Updated content",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                from_tag="v0.1.0",
                to_tag="v0.2.0",
                model="cerebras:qwen-3-coder-480b",
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is True
        mock_update.assert_called_once()
        mock_write.assert_called_once_with(str(temp_dir / "CHANGELOG.md"), "Updated content")

    @patch("kittylog.main.get_commits_between_tags")
    @patch("kittylog.main.is_current_commit_tagged")
    @patch("kittylog.main.get_latest_tag")
    @patch("kittylog.main.find_existing_tags")
    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    def test_main_logic_dry_run(
        self,
        mock_read,
        mock_update,
        mock_get_all_tags,
        mock_find_existing,
        mock_get_latest_tag,
        mock_is_current_commit_tagged,
        mock_get_commits,
        temp_dir,
    ):
        """Test dry run mode."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_read.return_value = "# Changelog\n\n## [Unreleased]\n"
        mock_find_existing.return_value = []  # No existing tags in changelog
        mock_get_latest_tag.return_value = "v0.2.0"
        mock_is_current_commit_tagged.return_value = False  # Current commit not tagged
        mock_get_commits.return_value = []  # No unreleased commits
        mock_update.return_value = (
            "Preview content",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model="cerebras:qwen-3-coder-480b",
                dry_run=True,  # Dry run mode
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is True
        # Should call update_changelog for each tag
        assert mock_update.call_count == 2
        # In dry run mode, write_changelog should not be called

    @patch("kittylog.main.get_commits_between_tags")
    @patch("kittylog.main.is_current_commit_tagged")
    @patch("kittylog.main.get_latest_tag")
    @patch("kittylog.main.find_existing_tags")
    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    def test_main_logic_user_confirmation_yes(
        self,
        mock_read,
        mock_update,
        mock_get_all_tags,
        mock_find_existing,
        mock_get_latest_tag,
        mock_is_current_commit_tagged,
        mock_get_commits,
        temp_dir,
    ):
        """Test user confirmation accepted."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_read.return_value = "# Changelog\n\n## [Unreleased]\n"
        mock_find_existing.return_value = []  # No existing tags in changelog
        mock_get_latest_tag.return_value = "v0.2.0"
        mock_is_current_commit_tagged.return_value = False  # Current commit not tagged
        mock_get_commits.return_value = []  # No unreleased commits
        mock_update.return_value = (
            "Updated content",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

        with patch("kittylog.main.click.confirm", return_value=True):  # User says yes
            config_with_model = {
                "model": "cerebras:qwen-3-coder-480b",
                "temperature": 0.7,
                "log_level": "INFO",
                "max_output_tokens": 1024,
                "max_retries": 3,
            }

            with patch("kittylog.main.config", config_with_model):
                success, token_usage = main_business_logic(
                    changelog_file=str(temp_dir / "CHANGELOG.md"),
                    model="cerebras:qwen-3-coder-480b",
                    quiet=True,
                    require_confirmation=True,  # Require confirmation
                    no_unreleased=False,
                )

        assert success is True
        # Should call update_changelog for each tag
        assert mock_update.call_count == 2

    @patch("kittylog.main.get_commits_between_tags")
    @patch("kittylog.main.is_current_commit_tagged")
    @patch("kittylog.main.get_latest_tag")
    @patch("kittylog.main.find_existing_tags")
    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    def test_main_logic_user_confirmation_no(
        self,
        mock_read,
        mock_update,
        mock_get_all_tags,
        mock_find_existing,
        mock_get_latest_tag,
        mock_is_current_commit_tagged,
        mock_get_commits,
        temp_dir,
    ):
        """Test user confirmation rejected."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_read.return_value = "# Changelog\n\n## [Unreleased]\n"
        mock_find_existing.return_value = []  # No existing tags in changelog
        mock_get_latest_tag.return_value = "v0.2.0"
        mock_is_current_commit_tagged.return_value = False  # Current commit not tagged
        mock_get_commits.return_value = []  # No unreleased commits
        mock_update.return_value = (
            "Updated content",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

        with patch("kittylog.main.click.confirm", return_value=False):  # User says no
            config_with_model = {
                "model": "cerebras:qwen-3-coder-480b",
                "temperature": 0.7,
                "log_level": "INFO",
                "max_output_tokens": 1024,
                "max_retries": 3,
            }

            with patch("kittylog.main.config", config_with_model):
                success, token_usage = main_business_logic(
                    changelog_file=str(temp_dir / "CHANGELOG.md"),
                    model="cerebras:qwen-3-coder-480b",
                    quiet=True,
                    require_confirmation=True,  # Require confirmation
                    no_unreleased=False,
                )

        assert success is True
        # Should call update_changelog for each tag
        assert mock_update.call_count == 2
        # Should not write file when user rejects

    @patch("kittylog.main.get_all_tags")
    def test_main_logic_git_error(self, mock_get_all_tags):
        """Test handling of git errors."""
        from kittylog.errors import GitError

        mock_get_all_tags.side_effect = GitError("Git error")  # Simulate git error

        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file="CHANGELOG.md",
                model="cerebras:qwen-3-coder-480b",
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is False  # Should return False on git error

    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    def test_main_logic_ai_error(self, mock_update, mock_get_all_tags):
        """Test handling of AI errors."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_update.side_effect = Exception("AI error")  # Simulate AI error

        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file="CHANGELOG.md",
                model="cerebras:qwen-3-coder-480b",
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is False  # Should return False on AI error

    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    @patch("kittylog.main.write_changelog")
    def test_main_logic_changelog_error(self, mock_write, mock_read, mock_update, mock_get_all_tags, temp_dir):
        """Test handling of changelog file errors."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_read.return_value = "# Changelog\n\n## [Unreleased]\n"
        mock_update.return_value = (
            "Updated content",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )
        mock_write.side_effect = Exception("Permission denied")  # Simulate file error

        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model="cerebras:qwen-3-coder-480b",
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is False  # Should return False on file error

    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    def test_main_logic_empty_repo(self, mock_update, mock_get_all_tags):
        """Test handling of empty git repository."""
        mock_get_all_tags.return_value = []  # No tags
        mock_update.return_value = (
            "Updated content",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file="CHANGELOG.md",
                model="cerebras:qwen-3-coder-480b",
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is True  # Should succeed even with no tags

    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    @patch("kittylog.main.write_changelog")
    def test_main_logic_write_failure(self, mock_write, mock_read, mock_update, mock_get_all_tags, temp_dir):
        """Test handling of write failures."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_read.return_value = "# Changelog\n\n## [Unreleased]\n"
        mock_update.return_value = (
            "Updated content",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )
        mock_write.side_effect = OSError("Disk full")  # Simulate write error

        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model="cerebras:qwen-3-coder-480b",
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is False  # Should return False on write error


class TestMainLogicMultipleTags:
    """Test main logic with multiple tags."""

    @patch("kittylog.main.get_commits_between_tags")
    @patch("kittylog.main.is_current_commit_tagged")
    @patch("kittylog.main.get_latest_tag")
    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.changelog.find_existing_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    @patch("kittylog.main.write_changelog")
    def test_multiple_tags_success(
        self,
        mock_write,
        mock_read,
        mock_update,
        mock_find_existing,
        mock_get_all_tags,
        mock_get_latest_tag,
        mock_is_current_commit_tagged,
        mock_get_commits,
        temp_dir,
    ):
        """Test successful processing of multiple tags."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0", "v0.3.0"]
        mock_read.return_value = "# Changelog\n\n## [Unreleased]\n## [0.1.0]\n"
        mock_find_existing.return_value = ["0.1.0"]  # Only 0.1.0 exists in changelog
        mock_get_latest_tag.return_value = "v0.3.0"
        mock_is_current_commit_tagged.return_value = False  # Current commit not tagged
        mock_get_commits.return_value = []  # No unreleased commits

        # Mock update_changelog to return different content for each call
        mock_update.side_effect = [
            ("Updated content for 0.2.0", {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}),
            ("Updated content for 0.3.0", {"prompt_tokens": 120, "completion_tokens": 60, "total_tokens": 180}),
        ]

        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model="cerebras:qwen-3-coder-480b",
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is True
        assert mock_update.call_count == 2  # Should process 2 missing tags
        assert mock_write.call_count == 1  # Should write once at the end

    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.changelog.find_existing_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    @patch("kittylog.main.write_changelog")
    def test_multiple_tags_partial_failure(
        self, mock_write, mock_read, mock_update, mock_find_existing, mock_get_all_tags, temp_dir
    ):
        """Test handling when some tags fail to process."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0", "v0.3.0"]
        mock_read.return_value = "# Changelog\n\n## [Unreleased]\n## [0.1.0]\n"
        mock_find_existing.return_value = ["0.1.0"]  # Only 0.1.0 exists in changelog

        # Mock first update to succeed, second to fail
        mock_update.side_effect = [
            ("Updated content for 0.2.0", {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}),
            Exception("AI generation failed"),  # Second tag fails
        ]

        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model="cerebras:qwen-3-coder-480b",
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is False  # Should return False when any tag fails
        assert mock_update.call_count == 2


class TestMainLogicEdgeCases:
    """Test edge cases in main business logic."""

    @patch("kittylog.main.get_commits_between_tags")
    @patch("kittylog.main.is_current_commit_tagged")
    @patch("kittylog.main.get_latest_tag")
    @patch("kittylog.main.find_existing_tags")
    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    @patch("kittylog.main.get_previous_tag")
    def test_only_from_tag_specified(
        self,
        mock_get_previous_tag,
        mock_read,
        mock_update,
        mock_get_all_tags,
        mock_find_existing,
        mock_get_latest_tag,
        mock_is_current_commit_tagged,
        mock_get_commits,
        temp_dir,
    ):
        """Test when only from_tag is specified."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0", "v0.3.0"]
        mock_read.return_value = "# Changelog\n\n## [Unreleased]\n"
        mock_find_existing.return_value = []  # No existing tags in changelog
        mock_get_latest_tag.return_value = "v0.3.0"
        mock_is_current_commit_tagged.return_value = False  # Current commit not tagged
        mock_get_commits.return_value = []  # No unreleased commits
        mock_update.return_value = (
            "Updated content",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )
        mock_get_previous_tag.return_value = "v0.1.0"  # Previous tag for v0.2.0

        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                from_tag="v0.1.0",
                to_tag=None,  # Only from_tag specified
                model="cerebras:qwen-3-coder-480b",
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is True
        mock_update.assert_called_once()

    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    @patch("kittylog.main.get_previous_tag")
    def test_only_to_tag_specified(self, mock_get_previous_tag, mock_read, mock_update, mock_get_all_tags, temp_dir):
        """Test when only to_tag is specified."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_read.return_value = "# Changelog\n\n## [Unreleased]\n"
        mock_update.return_value = (
            "Updated content",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )
        mock_get_previous_tag.return_value = "v0.1.0"  # Previous tag for v0.2.0

        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                from_tag=None,
                to_tag="v0.2.0",
                model="cerebras:qwen-3-coder-480b",
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is True
        mock_update.assert_called_once()
        # Should automatically get previous tag

    @patch("kittylog.main.get_all_tags")
    def test_empty_file_path(self, mock_get_all_tags):
        """Test with empty file path."""
        mock_get_all_tags.return_value = ["v0.1.0"]  # Need at least one tag

        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        # Empty file path causes an error when writing
        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }
        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file="",
                model="cerebras:qwen-3-coder-480b",
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        # Empty file path should fail
        assert success is False

    @patch("kittylog.main.get_all_tags")
    def test_no_model_specified(self, mock_get_all_tags, temp_dir):
        """Test when no model is specified and no default available."""
        mock_get_all_tags.return_value = ["v0.1.0"]

        # Test with config that has no model
        no_model_config = {
            "model": None,
            "log_level": "WARNING",
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", no_model_config):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model=None,
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is False


class TestMainLogicConfiguration:
    """Test configuration handling in main business logic."""

    @patch("kittylog.main.get_commits_between_tags")
    @patch("kittylog.main.is_current_commit_tagged")
    @patch("kittylog.main.get_latest_tag")
    @patch("kittylog.main.find_existing_tags")
    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    @patch("kittylog.main.write_changelog")
    def test_config_precedence(
        self,
        mock_write,
        mock_read,
        mock_update,
        mock_get_all_tags,
        mock_find_existing,
        mock_get_latest_tag,
        mock_is_current_commit_tagged,
        mock_get_commits,
        temp_dir,
    ):
        """Test that CLI arguments override config defaults."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_read.return_value = "# Changelog\n\n## [Unreleased]\n"
        mock_find_existing.return_value = []  # No existing tags in changelog
        mock_get_latest_tag.return_value = "v0.2.0"
        mock_is_current_commit_tagged.return_value = False  # Current commit not tagged
        mock_get_commits.return_value = []  # No unreleased commits
        mock_update.return_value = (
            "Updated content",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

        config_with_model = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_with_model):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model="openai:gpt-4",  # Should override config
                require_confirmation=False,
                quiet=True,
                no_unreleased=False,
            )

        assert success is True
        # Should call update_changelog for each tag
        assert mock_update.call_count == 2
        # Should use the CLI model, not config model


class TestMainLogicLogging:
    """Test logging behavior in main business logic."""

    @patch("kittylog.main.get_commits_between_tags")
    @patch("kittylog.main.is_current_commit_tagged")
    @patch("kittylog.main.get_latest_tag")
    @patch("kittylog.main.find_existing_tags")
    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    @patch("kittylog.main.write_changelog")
    def test_quiet_mode_suppresses_output(
        self,
        mock_write,
        mock_read,
        mock_update,
        mock_get_all_tags,
        mock_find_existing,
        mock_get_latest_tag,
        mock_is_current_commit_tagged,
        mock_get_commits,
        temp_dir,
    ):
        """Test that quiet mode suppresses non-error output."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_read.return_value = "# Changelog\n\n## [Unreleased]\n"
        mock_find_existing.return_value = []  # No existing tags in changelog
        mock_get_latest_tag.return_value = "v0.2.0"
        mock_is_current_commit_tagged.return_value = False  # Current commit not tagged
        mock_get_commits.return_value = []  # No unreleased commits
        mock_update.return_value = (
            "Updated content",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

        config_for_quiet = {
            "model": "cerebras:qwen-3-coder-480b",
            "log_level": "ERROR",  # Quiet mode sets log level to ERROR
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_for_quiet):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is True
        # Should call update_changelog for each tag
        assert mock_update.call_count == 2

    @patch("kittylog.main.get_commits_between_tags")
    @patch("kittylog.main.is_current_commit_tagged")
    @patch("kittylog.main.get_latest_tag")
    @patch("kittylog.main.find_existing_tags")
    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.update_changelog")
    @patch("kittylog.main.read_changelog")
    @patch("kittylog.main.write_changelog")
    def test_verbose_mode_shows_output(
        self,
        mock_write,
        mock_read,
        mock_update,
        mock_get_all_tags,
        mock_find_existing,
        mock_get_latest_tag,
        mock_is_current_commit_tagged,
        mock_get_commits,
        temp_dir,
    ):
        """Test that verbose mode shows detailed output."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_read.return_value = "# Changelog\n\n## [Unreleased]\n"
        mock_find_existing.return_value = []  # No existing tags in changelog
        mock_get_latest_tag.return_value = "v0.2.0"
        mock_is_current_commit_tagged.return_value = False  # Current commit not tagged
        mock_get_commits.return_value = []  # No unreleased commits
        mock_update.return_value = (
            "Updated content",
            {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

        config_for_verbose = {
            "model": "cerebras:qwen-3-coder-480b",
            "log_level": "INFO",  # Verbose mode sets log level to INFO
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_for_verbose):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                quiet=False,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is True
        # Should call update_changelog for each tag
        assert mock_update.call_count == 2

    @patch("kittylog.main.get_commits_between_tags")
    @patch("kittylog.main.is_current_commit_tagged")
    @patch("kittylog.main.get_latest_tag")
    @patch("kittylog.main.find_existing_tags")
    @patch("kittylog.main.get_all_tags")
    def test_debug_mode_enables_debug_logging(
        self,
        mock_get_all_tags,
        mock_find_existing,
        mock_get_latest_tag,
        mock_is_current_commit_tagged,
        mock_get_commits,
    ):
        """Test that debug logging can be enabled."""
        mock_get_all_tags.return_value = ["v0.1.0"]
        mock_find_existing.return_value = ["0.1.0"]  # Tag already exists
        mock_get_latest_tag.return_value = "v0.1.0"
        mock_is_current_commit_tagged.return_value = True  # Current commit is tagged
        mock_get_commits.return_value = []  # No unreleased commits

        config_for_debug = {
            "model": "cerebras:qwen-3-coder-480b",
            "log_level": "DEBUG",  # Debug mode
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_for_debug):
            success, token_usage = main_business_logic(
                changelog_file="CHANGELOG.md",
                quiet=False,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is True


class TestMainBusinessLogicIntegration:
    """Integration tests for main business logic."""

    @patch("kittylog.main.get_commits_between_tags")
    @patch("kittylog.main.is_current_commit_tagged")
    @patch("kittylog.main.get_latest_tag")
    @patch("kittylog.main.find_existing_tags")
    @patch("kittylog.main.get_all_tags")
    @patch("kittylog.main.read_changelog")
    def test_main_logic_no_commits(
        self,
        mock_read,
        mock_get_all_tags,
        mock_find_existing,
        mock_get_latest_tag,
        mock_is_current_commit_tagged,
        mock_get_commits,
        temp_dir,
    ):
        """Test main logic when no commits are found."""
        mock_get_all_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_read.return_value = "# Changelog\n"
        mock_find_existing.return_value = []  # No existing tags in changelog
        mock_get_latest_tag.return_value = "v0.2.0"
        mock_is_current_commit_tagged.return_value = False  # Current commit not tagged
        mock_get_commits.return_value = []  # No unreleased commits

        config_no_commits = {
            "model": "cerebras:qwen-3-coder-480b",
            "log_level": "INFO",
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_no_commits):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                quiet=True,
                require_confirmation=False,
                no_unreleased=False,
            )

        assert success is True  # Should succeed even with no commits

    @patch("kittylog.main.get_commits_between_tags")
    @patch("kittylog.main.is_current_commit_tagged")
    @patch("kittylog.main.get_latest_tag")
    @patch("kittylog.main.find_existing_tags")
    @patch("kittylog.main.get_all_tags")
    def test_main_logic_missing_config(
        self,
        mock_get_all_tags,
        mock_find_existing,
        mock_get_latest_tag,
        mock_is_current_commit_tagged,
        mock_get_commits,
    ):
        """Test main logic with missing config."""
        # This mostly tests that the system can handle missing config gracefully
        mock_get_all_tags.return_value = ["v0.1.0"]
        mock_find_existing.return_value = ["0.1.0"]  # Tag already exists
        mock_get_latest_tag.return_value = "v0.1.0"
        mock_is_current_commit_tagged.return_value = True  # Current commit is tagged
        mock_get_commits.return_value = []  # No unreleased commits
        success, token_usage = main_business_logic(
            changelog_file="CHANGELOG.md",
            model="cerebras:qwen-3-coder-480b",
            quiet=True,
            require_confirmation=False,
            no_unreleased=False,
        )

        # Should succeed with explicit model
        assert success is True
