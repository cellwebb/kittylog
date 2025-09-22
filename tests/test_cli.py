"""Tests for CLI module."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from clog.cli import cli, update


class TestMainCLI:
    """Test main CLI command."""

    def test_main_help(self):
        """Test main command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Changelog Updater" in result.output
        assert "update" in result.output
        assert "config" in result.output
        assert "init" in result.output

    def test_main_version(self):
        """Test main command version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "changelog-updater" in result.output


class TestUpdateCommand:
    """Test update CLI command."""

    @patch("clog.cli.main_business_logic")
    def test_update_basic(self, mock_main_logic):
        """Test basic update command."""
        mock_main_logic.return_value = True

        runner = CliRunner()
        result = runner.invoke(update)

        assert result.exit_code == 0
        mock_main_logic.assert_called_once()

        # Check default arguments
        call_args = mock_main_logic.call_args[1]
        assert call_args["changelog_file"] == "CHANGELOG.md"
        assert call_args["from_tag"] is None
        assert call_args["to_tag"] is None
        assert call_args["model"] is None
        assert call_args["hint"] == ""
        assert call_args["dry_run"] is False
        assert call_args["require_confirmation"] is True
        assert call_args["show_prompt"] is False
        assert call_args["quiet"] is False

    @patch("clog.cli.main_business_logic")
    def test_update_with_all_options(self, mock_main_logic):
        """Test update command with all options."""
        mock_main_logic.return_value = True

        runner = CliRunner()
        result = runner.invoke(
            update,
            [
                "--file",
                "CHANGES.md",
                "--from-tag",
                "v1.0.0",
                "--to-tag",
                "v1.1.0",
                "--model",
                "openai:gpt-4",
                "--hint",
                "Focus on breaking changes",
                "--dry-run",
                "--yes",
                "--show-prompt",
                "--quiet",
            ],
        )

        assert result.exit_code == 0
        mock_main_logic.assert_called_once()

        # Check arguments
        call_args = mock_main_logic.call_args[1]
        assert call_args["changelog_file"] == "CHANGES.md"  # Changed from file_path to changelog_file
        assert call_args["from_tag"] == "v1.0.0"
        assert call_args["to_tag"] == "v1.1.0"
        assert call_args["model"] == "openai:gpt-4"
        assert call_args["hint"] == "Focus on breaking changes"
        assert call_args["dry_run"] is True
        assert call_args["require_confirmation"] is False
        assert call_args["show_prompt"] is True
        assert call_args["quiet"] is True

    @patch("clog.cli.main_business_logic")
    def test_update_short_options(self, mock_main_logic):
        """Test update command with short options."""
        mock_main_logic.return_value = True

        runner = CliRunner()
        result = runner.invoke(
            update,
            [
                "-f",
                "CHANGES.md",
                "-m",
                "anthropic:claude-3-5-haiku-latest",
                "-h",
                "Test hint",
                "-y",
                "-q",
            ],
        )

        assert result.exit_code == 0

        call_args = mock_main_logic.call_args[1]
        assert call_args["changelog_file"] == "CHANGES.md"
        assert call_args["model"] == "anthropic:claude-3-5-haiku-latest"
        assert call_args["hint"] == "Test hint"
        assert call_args["require_confirmation"] is False  # --yes flag sets this to False
        assert call_args["quiet"] is True

    @patch("clog.cli.main_business_logic")
    def test_update_failure_exit_code(self, mock_main_logic):
        """Test update command exit code on failure."""
        mock_main_logic.return_value = False

        runner = CliRunner()
        result = runner.invoke(update)

        assert result.exit_code == 1

    @patch("clog.cli.main_business_logic")
    def test_update_exception_handling(self, mock_main_logic):
        """Test update command exception handling."""
        from clog.errors import ChangelogUpdaterError

        mock_main_logic.side_effect = ChangelogUpdaterError("Test error")

        runner = CliRunner()
        result = runner.invoke(update)

        assert result.exit_code == 1
        assert "Test error" in result.output

    @patch("clog.cli.main_business_logic")
    def test_update_keyboard_interrupt(self, mock_main_logic):
        """Test update command handling of keyboard interrupt."""
        mock_main_logic.side_effect = KeyboardInterrupt()

        runner = CliRunner()
        result = runner.invoke(update)

        assert result.exit_code == 1
        assert "cancelled" in result.output.lower()


class TestConfigCommand:
    """Test config CLI command."""

    def test_config_help(self):
        """Test config command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "--help"])

        assert result.exit_code == 0
        assert "config" in result.output
        assert "show" in result.output
        assert "set" in result.output
        assert "get" in result.output
        assert "unset" in result.output

    @patch("clog.config_cli.CLOG_ENV_PATH")
    def test_config_show_no_file(self, mock_path):
        """Test config show when no config file exists."""
        mock_path.exists.return_value = False

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "show"])

        assert result.exit_code == 0
        assert "No $HOME/.clog.env found" in result.output

    @patch("clog.config_cli.CLOG_ENV_PATH")
    @patch("clog.config_cli.load_dotenv")
    @patch("builtins.open")
    def test_config_show_with_file(self, mock_open, mock_load_dotenv, mock_path):
        """Test config show with existing config file."""
        mock_path.exists.return_value = True
        mock_file_content = "CLOG_MODEL=anthropic:claude-3-5-haiku-latest\nANTHROPIC_API_KEY=sk-ant-test123\n"
        mock_open.return_value.__enter__.return_value.read.return_value = mock_file_content
        mock_open.return_value.__enter__.return_value.__iter__ = Mock(
            return_value=iter(mock_file_content.splitlines(True))
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "show"])

        assert result.exit_code == 0
        assert "CLOG_MODEL=anthropic:claude-3-5-haiku-latest" in result.output
        assert "ANTHROPIC_API_KEY=sk-ant-test123" in result.output

    @patch("clog.config_cli.set_key")
    @patch("clog.config_cli.CLOG_ENV_PATH")
    def test_config_set(self, mock_path, mock_set_key):
        """Test config set command."""
        mock_path.touch = Mock()

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "set", "TEST_KEY", "test_value"])

        assert result.exit_code == 0
        mock_path.touch.assert_called_once_with(exist_ok=True)
        mock_set_key.assert_called_once()
        assert "Set TEST_KEY" in result.output

    @patch("clog.config_cli.load_dotenv")
    @patch("clog.config_cli.CLOG_ENV_PATH")
    @patch("os.getenv")
    def test_config_get_existing_key(self, mock_getenv, mock_path, mock_load_dotenv):
        """Test config get for existing key."""
        mock_getenv.return_value = "test_value"

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "get", "TEST_KEY"])

        assert result.exit_code == 0
        assert "test_value" in result.output

    @patch("clog.config_cli.load_dotenv")
    @patch("clog.config_cli.CLOG_ENV_PATH")
    @patch("os.getenv")
    def test_config_get_nonexistent_key(self, mock_getenv, mock_path, mock_load_dotenv):
        """Test config get for non-existent key."""
        mock_getenv.return_value = None

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "get", "NONEXISTENT"])

        assert result.exit_code == 0
        assert "NONEXISTENT not set" in result.output

    @patch("clog.config_cli.CLOG_ENV_PATH")
    def test_config_unset_no_file(self, mock_path):
        """Test config unset when no config file exists."""
        mock_path.exists.return_value = False

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "unset", "TEST_KEY"])

        assert result.exit_code == 0
        assert "No $HOME/.clog.env found" in result.output


class TestInitCommand:
    """Test init CLI command."""

    @patch("clog.init_cli.questionary")
    @patch("clog.init_cli.set_key")
    @patch("clog.init_cli.CLOG_ENV_PATH")
    def test_init_new_config(self, mock_path, mock_set_key, mock_questionary):
        """Test init command creating new config."""
        mock_path.exists.return_value = False
        mock_path.touch = Mock()

        # Mock questionary responses
        mock_questionary.select.return_value.ask.return_value = "Anthropic"
        mock_questionary.text.return_value.ask.return_value = "claude-3-5-haiku-latest"
        mock_questionary.password.return_value.ask.return_value = "sk-ant-test123"

        runner = CliRunner()
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        assert "Welcome to clog initialization" in result.output
        assert "Created $HOME/.clog.env" in result.output

        # Verify file operations
        mock_path.touch.assert_called_once()
        assert mock_set_key.call_count == 2  # model + API key

    @patch("clog.init_cli.questionary")
    @patch("clog.init_cli.set_key")
    @patch("clog.init_cli.CLOG_ENV_PATH")
    def test_init_existing_config(self, mock_path, mock_set_key, mock_questionary):
        """Test init command with existing config."""
        mock_path.exists.return_value = True

        mock_questionary.select.return_value.ask.return_value = "OpenAI"
        mock_questionary.text.return_value.ask.return_value = "gpt-4"
        mock_questionary.password.return_value.ask.return_value = "sk-test123"

        runner = CliRunner()
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        assert "$HOME/.clog.env already exists" in result.output

    @patch("clog.init_cli.questionary")
    @patch("clog.init_cli.CLOG_ENV_PATH")
    def test_init_cancelled(self, mock_path, mock_questionary):
        """Test init command when user cancels."""
        mock_path.exists.return_value = False
        mock_questionary.select.return_value.ask.return_value = None  # User cancelled

        runner = CliRunner()
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        assert "cancelled" in result.output

    @patch("clog.init_cli.questionary")
    @patch("clog.init_cli.set_key")
    @patch("clog.init_cli.CLOG_ENV_PATH")
    def test_init_no_api_key(self, mock_path, mock_set_key, mock_questionary):
        """Test init command without providing API key."""
        mock_path.exists.return_value = False
        mock_path.touch = Mock()

        mock_questionary.select.return_value.ask.return_value = "Groq"
        mock_questionary.text.return_value.ask.return_value = "llama-4"
        mock_questionary.password.return_value.ask.return_value = ""  # No API key

        runner = CliRunner()
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        # Should only set model, not API key
        assert mock_set_key.call_count == 1


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def test_cli_workflow_dry_run(self, temp_dir, git_repo_with_tags):
        """Test complete CLI workflow with dry run."""
        with patch("clog.cli.main_business_logic") as mock_logic:
            mock_logic.return_value = True

            runner = CliRunner()
            result = runner.invoke(
                update,
                [
                    "--file",
                    str(temp_dir / "CHANGELOG.md"),
                    "--from-tag",
                    "v0.1.0",
                    "--to-tag",
                    "v0.2.0",
                    "--dry-run",
                    "--quiet",
                ],
            )

            assert result.exit_code == 0
            mock_logic.assert_called_once()

            call_args = mock_logic.call_args[1]
            assert call_args["dry_run"] is True
            assert call_args["quiet"] is True

    def test_cli_error_handling(self):
        """Test CLI error handling."""
        with patch("clog.cli.main_business_logic") as mock_logic:
            from clog.errors import GitError

            mock_logic.side_effect = GitError("Not a git repository")

            runner = CliRunner()
            result = runner.invoke(update)

            assert result.exit_code == 1
            assert "Not a git repository" in result.output

    def test_cli_with_relative_paths(self, temp_dir):
        """Test CLI with relative file paths."""
        with patch("clog.cli.main_business_logic") as mock_logic:
            mock_logic.return_value = True

            runner = CliRunner()
            result = runner.invoke(
                update,
                [
                    "--file",
                    "docs/CHANGELOG.md",
                ],
            )

            assert result.exit_code == 0
            call_args = mock_logic.call_args[1]
            assert call_args["changelog_file"] == "docs/CHANGELOG.md"


class TestCLIValidation:
    """Test CLI argument validation."""

    def test_invalid_model_format(self):
        """Test handling of invalid model format."""
        with patch("clog.cli.main_business_logic") as mock_logic:
            from clog.errors import ConfigError

            mock_logic.side_effect = ConfigError("Invalid model format")

            runner = CliRunner()
            result = runner.invoke(update, ["--model", "invalid"])

            assert result.exit_code == 1
            assert "Invalid model format" in result.output

    def test_nonexistent_changelog_file(self):
        """Test handling of non-existent changelog file."""
        with patch("clog.cli.main_business_logic") as mock_logic:
            mock_logic.return_value = True  # Business logic should handle this gracefully

            runner = CliRunner()
            result = runner.invoke(
                update,
                [
                    "--file",
                    "nonexistent/CHANGELOG.md",
                ],
            )

            # CLI should not fail, let business logic handle it
            assert result.exit_code == 0
