#!/usr/bin/env python3
"""Tests for confirmation functionality added to handler functions."""

import os
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner
from git import Repo

from kittylog.cli import cli


class TestConfirmationFunctionality:
    """Test confirmation prompts in CLI workflow."""

    def test_dry_run_works_without_yes_flag(self, temp_dir):
        """Test that dry-run mode works without --yes flag (removed functionality)."""
        # Create git repo with tags
        repo = Repo.init(temp_dir)
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # Create commit and tag
        test_file = temp_dir / "file.py"
        test_file.write_text("# Test file")
        repo.index.add(["file.py"])
        commit = repo.index.commit("Initial commit")
        repo.create_tag("v0.1.0", commit)

        # Create second commit for range
        test_file2 = temp_dir / "file2.py"
        test_file2.write_text("# Test file 2")
        repo.index.add(["file2.py"])
        commit2 = repo.index.commit("Second commit")
        repo.create_tag("v0.2.0", commit2)

        # Create config
        config_file = temp_dir / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=test\n")

        # Create changelog file to avoid prompt
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("# Changelog\n\nAll notable changes will be documented in this file.\n")

        original_cwd = str(Path.cwd())
        try:
            os.chdir(temp_dir)
            # Clear git cache to ensure we're working with the right repo
            from kittylog.tag_operations import clear_git_cache

            clear_git_cache()
            runner = CliRunner()

            # Test update command with --dry-run flag
            result = runner.invoke(
                cli,
                [
                    "update",
                    "--from-tag",
                    "v0.1.0",
                    "--to-tag",
                    "v0.2.0",
                    "--dry-run",  # Should show preview but not save
                ],
            )

            # Should succeed and show preview
            assert result.exit_code == 0
            # Verify --yes flag is not available in help output
            help_result = runner.invoke(cli, ["update", "--help"])
            assert "--yes" not in help_result.output
            assert "--dry-run" in help_result.output

        finally:
            os.chdir(original_cwd)

    def test_no_yes_flag_in_commands(self, temp_dir):
        """Test that --yes flag has been removed from all commands."""
        runner = CliRunner()

        # Check that --yes flag is removed from main commands
        commands_to_check = [
            ["add-cli", "--help"],
            ["update", "--help"],
            ["release", "--help"],
        ]

        for command in commands_to_check:
            result = runner.invoke(cli, command)
            assert result.exit_code == 0
            # --yes flag should not be in help (except for init-changelog which keeps it)
            assert "Skip confirmation" not in result.output
            assert "Auto-accept" not in result.output

        # init-changelog should still have --yes but for different purpose
        result = runner.invoke(cli, ["init-changelog", "--help"])
        assert result.exit_code == 0
        assert "--yes" in result.output  # Should be there for changelog creation

    def test_incremental_save_no_confirmation(self, temp_dir):
        """Test that changelog is saved incrementally without confirmation."""
        # Create git repo with tags
        repo = Repo.init(temp_dir)
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # Create commits and tags
        test_file = temp_dir / "file.py"
        test_file.write_text("# Test file")
        repo.index.add(["file.py"])
        commit = repo.index.commit("Initial commit")
        repo.create_tag("v0.1.0", commit)

        test_file2 = temp_dir / "file2.py"
        test_file2.write_text("# Test file 2")
        repo.index.add(["file2.py"])
        commit2 = repo.index.commit("Second commit")
        repo.create_tag("v0.2.0", commit2)

        # Create changelog file with only the first version entry
        changelog_file = temp_dir / "CHANGELOG.md"
        original_content = """# Changelog

All notable changes will be documented in this file.

## [v0.1.0] - 2024-01-01

### Added
- Initial release
"""
        changelog_file.write_text(original_content)

        # Create config
        config_file = temp_dir / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=openai:gpt-4o-mini\n")

        original_cwd = str(Path.cwd())
        try:
            os.chdir(temp_dir)
            # Clear git cache to ensure we're working with the right repo
            from kittylog.tag_operations import clear_git_cache

            clear_git_cache()
            runner = CliRunner()

            # Test update command (no confirmation needed for incremental save)
            result = runner.invoke(
                cli,
                [
                    "update",
                    "--from-tag",
                    "v0.1.0",
                    "--to-tag",
                    "v0.2.0",
                ],
            )

            # Should succeed (exit code 0)
            assert result.exit_code == 0
            # Should not show save confirmation prompt
            assert "Save the updated changelog?" not in result.output
            # Should show success message about incremental update
            assert (
                "Changelog updated incrementally:" in result.output
                or "Successfully updated changelog:" in result.output
            )
            # Verify changelog was actually updated
            updated_content = changelog_file.read_text()
            assert updated_content != original_content
            assert "v0.2.0" in updated_content

        finally:
            os.chdir(original_cwd)

    @patch("os.getenv", return_value="")
    @patch("httpx.post")
    @patch(
        "kittylog.ai.load_config",
    )
    def test_quiet_mode_bypasses_confirmation(self, mock_ai_load_config, mock_post, mock_getenv, temp_dir):
        """Test that quiet mode bypasses confirmation prompts."""
        original_cwd = str(Path.cwd())
        try:
            # Change to temp_dir BEFORE git operations
            os.chdir(temp_dir)

            # Create git repo with tags
            repo = Repo.init(temp_dir)
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@example.com").release()

            # Create commits and tags
            test_file = temp_dir / "file.py"
            test_file.write_text("# Test file")
            repo.index.add(["file.py"])
            commit = repo.index.commit("Initial commit")
            repo.create_tag("v0.1.0", commit)

            test_file2 = temp_dir / "file2.py"
            test_file2.write_text("# Test file 2")
            repo.index.add(["file2.py"])
            commit2 = repo.index.commit("Second commit")
            repo.create_tag("v0.2.0", commit2)

            # Create third commit and tag for range processing
            test_file3 = temp_dir / "file3.py"
            test_file3.write_text("# Test file 3")
            repo.index.add(["file3.py"])
            commit3 = repo.index.commit("Third commit")
            repo.create_tag("v0.3.0", commit3)

            # Configure mock_getenv using proper side_effect
            def mock_getenv_side_effect(key, default=""):
                env_vars = {
                    "ANTHROPIC_API_KEY": "sk-ant-test123",
                    "KITTYLOG_MODEL": "anthropic:claude-3-haiku",
                    "KITTYLOG_TEMPERATURE": "0.7",
                    "KITTYLOG_MAX_OUTPUT_TOKENS": "1024",
                    "KITTYLOG_RETRIES": "3",
                    "KITTYLOG_GAP_THRESHOLD_HOURS": "4.0",
                    "KITTYLOG_GROUPING_MODE": "tags",
                    "KITTYLOG_DATE_GROUPING": "daily",
                    "KITTYLOG_TRANSLATE_HEADINGS": "false",
                    "KITTYLOG_LANGUAGE": "en",
                    "KITTYLOG_AUDIENCE": "stakeholders",
                    "KITTYLOG_LOG_LEVEL": "INFO",
                    "KITTYLOG_WARNING_LIMIT_TOKENS": "8192",
                }
                return env_vars.get(key, default or "")

            mock_getenv.side_effect = mock_getenv_side_effect

            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"content": [{"text": "### Added\n- Quiet feature"}]}
            mock_post.return_value = mock_response

            # Mock config to return proper KittylogConfigData object
            from kittylog.config.data import KittylogConfigData

            mock_ai_load_config.return_value = KittylogConfigData(
                model="anthropic:claude-3-haiku",
                temperature=0.7,
                max_output_tokens=1024,
                max_retries=3,
            )

            # Create config
            config_file = temp_dir / ".kittylog.env"
            config_file.write_text("KITTYLOG_MODEL=anthropic:claude-3-haiku\n")

            # Create changelog file to avoid prompt
            changelog_file = temp_dir / "CHANGELOG.md"
            changelog_file.write_text("# Changelog\n\nAll notable changes will be documented in this file.\n")

            # Clear git cache to ensure we're working with the right repo
            from kittylog.tag_operations import clear_git_cache

            clear_git_cache()
            runner = CliRunner()

            # Test update command with --quiet flag (should bypass confirmation)
            result = runner.invoke(
                cli,
                [
                    "update",
                    "--from-tag",
                    "v0.1.0",
                    "--to-tag",
                    "v0.3.0",
                    "--quiet",  # Should bypass confirmation
                ],
            )

            # Should succeed without requiring interaction
            assert result.exit_code == 0
            # Should not ask for save confirmation (auto-saved incrementally)
            assert "Save the updated changelog?" not in result.output

        finally:
            os.chdir(original_cwd)

    @patch("kittylog.providers.base.os.getenv", return_value="gsk_test123")
    def test_auto_mode_shows_entry_count(self, mock_getenv, temp_dir):
        """Test that auto mode shows correct entry count in confirmation."""
        # Note: httpx.post is mocked by the autouse fixture in conftest.py

        # Create git repo with multiple tags to process
        repo = Repo.init(temp_dir)
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # Create multiple commits and tags
        for i in range(4):
            test_file = temp_dir / f"file{i}.py"
            test_file.write_text(f"# File {i}")
            repo.index.add([f"file{i}.py"])
            commit = repo.index.commit(f"Add file {i}")
            repo.create_tag(f"v0.{i + 1}.0", commit)

        # Create changelog with only first entry to simulate missing entries
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [0.1.0] - 2024-01-01
- Initial release
""")

        # Create config
        config_file = temp_dir / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=groq:llama-3.3-70b-versatile\nGROQ_API_KEY=gsk_test123\n")

        original_cwd = str(Path.cwd())
        try:
            os.chdir(temp_dir)
            # Clear git cache to ensure we're working with the right repo
            from kittylog.tag_operations import clear_git_cache

            clear_git_cache()
            runner = CliRunner()

            # Test add-cli command (auto mode) with confirmation "y"
            # Use --no-interactive to skip the interactive wizard
            result = runner.invoke(
                cli,
                ["add-cli", "--no-interactive"],  # Skip interactive wizard
                input="y\n",  # Confirm the prompt
            )

            # Should show information about missing entries being processed
            # Actual output shows "Found X missing changelog entries" and "Processing missing tag"
            assert (
                "missing changelog entries" in result.output
                or "Processing missing tag" in result.output
                or "Updated changelog preview:" in result.output
            )

        finally:
            os.chdir(original_cwd)
