#!/usr/bin/env python3
"""Tests for confirmation functionality added to handler functions."""

import os
from unittest.mock import Mock, patch

from click.testing import CliRunner
from git import Repo

from kittylog.cli import cli


class TestConfirmationFunctionality:
    """Test confirmation prompts in CLI workflow."""

    @patch("kittylog.main.config", {"model": "openai:gpt-4o-mini"})
    @patch("httpx.post")
    @patch("os.getenv")
    def test_yes_flag_bypasses_confirmation(self, mock_getenv, mock_post, temp_dir):
        """Test CLI workflow with --yes flag bypasses confirmation."""
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

        # Mock API key and response
        mock_getenv.return_value = "sk-test-key"
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": "### Added\n- New feature"}}]}
        mock_post.return_value = mock_response

        # Create config
        config_file = temp_dir / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=openai:gpt-4o-mini\n")

        # Create changelog file to avoid prompt
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("# Changelog\n\nAll notable changes will be documented in this file.\n")

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            # Clear git cache to ensure we're working with the right repo
            from kittylog.git_operations import clear_git_cache

            clear_git_cache()
            runner = CliRunner()

            # Test update command with --yes flag
            result = runner.invoke(
                cli,
                [
                    "update",
                    "--from-tag",
                    "v0.1.0",
                    "--to-tag",
                    "v0.2.0",
                    "--yes",  # Should bypass confirmation
                ],
            )

            # Should succeed without requiring interaction
            assert result.exit_code == 0
            # Should not contain confirmation prompts in output
            assert "Proceed with generating changelog entry? [Y/n]:" not in result.output

        finally:
            os.chdir(original_cwd)

    @patch("kittylog.main.config", {"model": "openai:gpt-4o-mini"})
    def test_confirmation_shows_when_yes_not_used(self, temp_dir):
        """Test that confirmation prompt appears when --yes flag is not used."""
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

        # Create changelog file to avoid prompt
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("# Changelog\n\nAll notable changes will be documented in this file.\n")

        # Create config
        config_file = temp_dir / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=openai:gpt-4o-mini\n")

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            # Clear git cache to ensure we're working with the right repo
            from kittylog.git_operations import clear_git_cache

            clear_git_cache()
            runner = CliRunner()

            # Test update command without --yes flag, provide "y" to confirmation
            result = runner.invoke(
                cli,
                [
                    "update",
                    "--from-tag",
                    "v0.1.0",
                    "--to-tag",
                    "v0.2.0",
                ],
                input="y\n",  # Confirm the prompt
            )

            # Should show confirmation prompt
            assert "About to generate 1 changelog entry using model: openai:gpt-4o-mini" in result.output
            assert "Range to process: v0.1.0 to v0.2.0" in result.output
            assert "Proceed with generating changelog entry? [Y/n]:" in result.output

        finally:
            os.chdir(original_cwd)

    @patch("kittylog.main.config", {"model": "openai:gpt-4o-mini"})
    def test_cancellation_no_save_prompt(self, temp_dir):
        """Test that canceling confirmation doesn't trigger save confirmation."""
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

        # Create config
        config_file = temp_dir / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=openai:gpt-4o-mini\n")

        # Create changelog file to avoid prompt
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("# Changelog\n\nAll notable changes will be documented in this file.\n")

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            # Clear git cache to ensure we're working with the right repo
            from kittylog.git_operations import clear_git_cache

            clear_git_cache()
            runner = CliRunner()

            # Test update command and provide "n" to confirmation
            result = runner.invoke(
                cli,
                [
                    "update",
                    "--from-tag",
                    "v0.1.0",
                    "--to-tag",
                    "v0.2.0",
                ],
                input="n\n",  # Cancel the confirmation
            )

            # Should succeed (exit code 0) even when cancelled
            assert result.exit_code == 0
            # Should not ask for save confirmation after cancelling
            assert "Save the updated changelog?" not in result.output
            # Should show cancellation message
            assert "Operation cancelled by user" in result.output
            # Should show no changes message
            assert "No changes made to changelog" in result.output

        finally:
            os.chdir(original_cwd)

    @patch("kittylog.main.config", {"model": "anthropic:claude-3-haiku"})
    @patch(
        "kittylog.ai.config",
        {"model": "anthropic:claude-3-haiku", "temperature": 0.7, "max_output_tokens": 1024, "retries": 3},
    )
    @patch("httpx.post")
    @patch("os.getenv")
    def test_quiet_mode_bypasses_confirmation(self, mock_getenv, mock_post, temp_dir):
        """Test that quiet mode bypasses confirmation prompts."""
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

        # Mock API key and response
        mock_getenv.return_value = "sk-ant-test123"
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"content": [{"text": "### Added\n- Quiet feature"}]}
        mock_post.return_value = mock_response

        # Create config
        config_file = temp_dir / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=anthropic:claude-3-haiku\n")

        # Create changelog file to avoid prompt
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("# Changelog\n\nAll notable changes will be documented in this file.\n")

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            # Clear git cache to ensure we're working with the right repo
            from kittylog.git_operations import clear_git_cache

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
            # Should not contain confirmation prompts in output
            assert "Proceed with generating changelog entry? [Y/n]:" not in result.output

        finally:
            os.chdir(original_cwd)

    @patch("kittylog.main.config", {"model": "groq:llama-3.3-70b-versatile"})
    @patch("httpx.post")
    @patch("os.getenv")
    def test_auto_mode_shows_entry_count(self, mock_getenv, mock_post, temp_dir):
        """Test that auto mode shows correct entry count in confirmation."""
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

        # Mock API key and response
        mock_getenv.return_value = "gsk_test123"
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": "### Added\n- Multiple features"}}]}
        mock_post.return_value = mock_response

        # Create config
        config_file = temp_dir / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=groq:llama-3.3-70b-versatile\n")

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            # Clear git cache to ensure we're working with the right repo
            from kittylog.git_operations import clear_git_cache

            clear_git_cache()
            runner = CliRunner()

            # Test default kittylog command (auto mode) with confirmation "y"
            result = runner.invoke(
                cli,
                [],  # Default auto mode
                input="y\n",  # Confirm the prompt
            )

            # Should show confirmation with entry count
            assert "About to generate" in result.output
            assert "changelog entries using model: groq:llama-3.3-70b-versatile" in result.output
            assert "Proceed with generating changelog entries?" in result.output

        finally:
            os.chdir(original_cwd)
