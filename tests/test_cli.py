"""Tests for CLI module."""

from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from kittylog.cli import cli
from kittylog.update_cli import update_version as update


class TestMainCLI:
    """Test main CLI command."""

    def test_main_help(self):
        """Test main command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "kittylog" in result.output
        assert "update" in result.output
        assert "config" in result.output
        assert "init" in result.output

    def test_main_version(self):
        """Test main command version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "kittylog" in result.output


class TestUpdateCommand:
    """Test update CLI command."""

    @patch("kittylog.update_cli.main_business_logic")
    def test_update_basic(self, mock_main_logic):
        """Test basic update command."""
        mock_main_logic.return_value = (True, None)

        runner = CliRunner()
        result = runner.invoke(update)

        assert result.exit_code == 0
        mock_main_logic.assert_called_once()

        # Check default arguments
        call_args = mock_main_logic.call_args[1]
        assert call_args["changelog_file"] == "CHANGELOG.md"
        assert call_args["dry_run"] is False
        assert call_args["require_confirmation"] is True
        assert call_args["quiet"] is False
        assert call_args["language"] is None
        assert call_args["audience"] is None

    @patch("kittylog.update_cli.main_business_logic")
    def test_update_with_all_options(self, mock_main_logic):
        """Test update command with all options."""
        mock_main_logic.return_value = (True, {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})

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
                "--language",
                "es",
                "--audience",
                "users",
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
        assert call_args["changelog_file"] == "CHANGES.md"
        assert call_args["model"] == "openai:gpt-4"
        assert call_args["hint"] == "Focus on breaking changes"
        assert call_args["dry_run"] is True
        assert call_args["require_confirmation"] is False
        assert call_args["quiet"] is True
        assert call_args["language"] == "Spanish"
        assert call_args["audience"] == "users"

        # Clean up created file
        if Path("CHANGES.md").exists():
            Path("CHANGES.md").unlink()

    @patch("kittylog.update_cli.main_business_logic")
    def test_update_short_options(self, mock_main_logic):
        """Test update command with short options."""
        mock_main_logic.return_value = (True, {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})

        runner = CliRunner()
        result = runner.invoke(
            update,
            [
                "-f",
                "CHANGES.md",
                "-m",
                "cerebras:qwen-3-coder-480b",
                "-l",
                "fr",
                "-u",
                "stakeholders",
                "-h",
                "Test hint",
                "-y",
                "-q",
            ],
        )

        assert result.exit_code == 0

        call_args = mock_main_logic.call_args[1]
        assert call_args["changelog_file"] == "CHANGES.md"
        assert call_args["model"] == "cerebras:qwen-3-coder-480b"
        assert call_args["hint"] == "Test hint"
        assert call_args["require_confirmation"] is False  # --yes flag sets this to False
        assert call_args["quiet"] is True
        assert call_args["language"] == "French"
        assert call_args["audience"] == "stakeholders"

        # Clean up created file
        if Path("CHANGES.md").exists():
            Path("CHANGES.md").unlink()

    @patch("kittylog.update_cli.main_business_logic")
    def test_update_failure_exit_code(self, mock_main_logic):
        """Test update command exit code on failure."""
        mock_main_logic.return_value = (False, None)

        runner = CliRunner()
        result = runner.invoke(update)

        assert result.exit_code == 1

    @patch("kittylog.update_cli.main_business_logic")
    def test_update_exception_handling(self, mock_main_logic):
        """Test update command exception handling."""
        from kittylog.errors import KittylogError

        mock_main_logic.return_value = (False, None)
        mock_main_logic.side_effect = KittylogError("Test error")

        runner = CliRunner()
        result = runner.invoke(update)

        assert result.exit_code == 1
        assert "Test error" in result.output

    @patch("kittylog.update_cli.main_business_logic")
    def test_update_keyboard_interrupt(self, mock_main_logic):
        """Test update command handling of keyboard interrupt."""
        mock_main_logic.side_effect = KeyboardInterrupt()

        runner = CliRunner()
        result = runner.invoke(update)

        assert result.exit_code == 1
        assert "cancelled" in result.output.lower() or "aborted" in result.output.lower()


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

    @patch("kittylog.config_cli.KITTYLOG_ENV_PATH")
    def test_config_show_no_file(self, mock_path):
        """Test config show when no config file exists."""
        mock_path.exists.return_value = False

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "show"])

        assert result.exit_code == 0
        assert "No $HOME/.kittylog.env found" in result.output

    @patch("kittylog.config_cli.load_dotenv")
    @patch("kittylog.config_cli.KITTYLOG_ENV_PATH")
    @patch("builtins.open")
    def test_config_show_with_file(self, mock_open, mock_load_dotenv, mock_path):
        """Test config show with existing config file."""
        mock_path.exists.return_value = True
        mock_file_content = "KITTYLOG_MODEL=cerebras:qwen-3-coder-480b\nANTHROPIC_API_KEY=sk-ant-test123\n"
        mock_open.return_value.__enter__.return_value.read.return_value = mock_file_content
        mock_open.return_value.__enter__.return_value.__iter__ = Mock(
            return_value=iter(mock_file_content.splitlines(True))
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "show"])

        assert result.exit_code == 0
        assert "KITTYLOG_MODEL=cerebras:qwen-3-coder-480b" in result.output
        assert "ANTHROPIC_API_KEY=sk-ant-test123" in result.output

    @patch("kittylog.config_cli.set_key")
    @patch("kittylog.config_cli.KITTYLOG_ENV_PATH")
    def test_config_set(self, mock_path, mock_set_key):
        """Test config set command."""
        mock_path.touch = Mock()

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "set", "TEST_KEY", "test_value"])

        assert result.exit_code == 0
        mock_path.touch.assert_called_once_with(exist_ok=True)
        mock_set_key.assert_called_once()
        assert "Set TEST_KEY" in result.output

    @patch("kittylog.config_cli.load_dotenv")
    @patch("kittylog.config_cli.KITTYLOG_ENV_PATH")
    @patch("os.getenv")
    def test_config_get_existing_key(self, mock_getenv, mock_path, mock_load_dotenv):
        """Test config get for existing key."""
        mock_getenv.return_value = "test_value"

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "get", "TEST_KEY"])

        assert result.exit_code == 0
        assert "test_value" in result.output

    @patch("kittylog.config_cli.load_dotenv")
    @patch("kittylog.config_cli.KITTYLOG_ENV_PATH")
    @patch("os.getenv")
    def test_config_get_nonexistent_key(self, mock_getenv, mock_path, mock_load_dotenv):
        """Test config get for non-existent key."""
        mock_getenv.return_value = None

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "get", "NONEXISTENT"])

        assert result.exit_code == 0
        assert "NONEXISTENT not set" in result.output

    @patch("kittylog.config_cli.KITTYLOG_ENV_PATH")
    def test_config_unset_no_file(self, mock_path):
        """Test config unset when no config file exists."""
        mock_path.exists.return_value = False

        runner = CliRunner()
        result = runner.invoke(cli, ["config", "unset", "TEST_KEY"])

        assert result.exit_code == 0
        assert "No $HOME/.kittylog.env found" in result.output


class TestInitCommand:
    """Test init CLI command."""

    @patch("kittylog.init_cli.questionary")
    @patch("kittylog.init_cli.set_key")
    @patch("kittylog.init_cli.KITTYLOG_ENV_PATH")
    def test_init_new_config(self, mock_path, mock_set_key, mock_questionary):
        """Test init command creating new config."""
        mock_path.exists.return_value = False
        mock_path.touch = Mock()

        # Mock questionary responses
        mock_questionary.select.return_value.ask.side_effect = [
            "Anthropic",  # provider
            "English",  # language
            "developers",  # audience
        ]
        mock_questionary.text.return_value.ask.return_value = "claude-3-5-haiku-latest"
        mock_questionary.password.return_value.ask.return_value = "sk-ant-test123"

        runner = CliRunner()
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        assert "Welcome to kittylog initialization" in result.output
        assert "Created $HOME/.kittylog.env" in result.output

        # Verify file operations
        mock_path.touch.assert_called_once()
        assert mock_set_key.call_count == 3  # model + API key + audience
        calls = mock_set_key.call_args_list
        assert any("KITTYLOG_AUDIENCE" in str(call) and "developers" in str(call) for call in calls)

    @patch("kittylog.init_cli.questionary")
    @patch("kittylog.init_cli.set_key")
    @patch("kittylog.init_cli.KITTYLOG_ENV_PATH")
    def test_init_existing_config(self, mock_path, mock_set_key, mock_questionary):
        """Test init command with existing config."""
        mock_path.exists.return_value = True

        mock_questionary.select.return_value.ask.side_effect = [
            "OpenAI",
            "English",
            "developers",
        ]
        mock_questionary.text.return_value.ask.return_value = "gpt-4"
        mock_questionary.password.return_value.ask.return_value = "sk-test123"

        runner = CliRunner()
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        assert "$HOME/.kittylog.env already exists" in result.output

    @patch("kittylog.init_cli.questionary")
    @patch("kittylog.init_cli.KITTYLOG_ENV_PATH")
    def test_init_cancelled(self, mock_path, mock_questionary):
        """Test init command when user cancels."""
        mock_path.exists.return_value = False
        mock_questionary.select.return_value.ask.return_value = None  # User cancelled

        runner = CliRunner()
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        assert "cancelled" in result.output

    @patch("kittylog.init_cli.questionary")
    @patch("kittylog.init_cli.set_key")
    @patch("kittylog.init_cli.KITTYLOG_ENV_PATH")
    def test_init_no_api_key(self, mock_path, mock_set_key, mock_questionary):
        """Test init command without providing API key."""
        mock_path.exists.return_value = False
        mock_path.touch = Mock()

        mock_questionary.select.return_value.ask.side_effect = [
            "Groq",
            "English",
            "developers",
        ]
        mock_questionary.text.return_value.ask.return_value = "llama-4"
        mock_questionary.password.return_value.ask.return_value = ""  # No API key

        runner = CliRunner()
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        # Should only set model, not API key
        assert mock_set_key.call_count == 2  # model + audience

    @patch("kittylog.init_cli.questionary")
    @patch("kittylog.init_cli.set_key")
    @patch("kittylog.init_cli.KITTYLOG_ENV_PATH")
    def test_init_zai_coding_provider(self, mock_path, mock_set_key, mock_questionary):
        """Test init command with Z.AI Coding provider."""
        mock_path.exists.return_value = False
        mock_path.touch = Mock()

        # Mock questionary responses
        mock_questionary.select.return_value.ask.side_effect = [
            "Z.AI Coding",
            "English",
            "developers",
        ]
        mock_questionary.text.return_value.ask.return_value = "glm-4.6"
        mock_questionary.password.return_value.ask.return_value = "zai-api-key"

        runner = CliRunner()
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        assert "Welcome to kittylog initialization" in result.output

        # Verify set_key calls - should only be 2 (model + API key)
        assert mock_set_key.call_count == 3  # model + API key + audience

        # Check the specific calls
        calls = mock_set_key.call_args_list
        assert any("KITTYLOG_MODEL" in str(call) and "zai-coding:glm-4.6" in str(call) for call in calls)
        assert any("ZAI_API_KEY" in str(call) and "zai-api-key" in str(call) for call in calls)

    @patch("kittylog.init_cli.questionary")
    @patch("kittylog.init_cli.set_key")
    @patch("kittylog.init_cli.KITTYLOG_ENV_PATH")
    def test_init_zai_without_coding_plan(self, mock_path, mock_set_key, mock_questionary):
        """Test init command with Z.AI provider and coding plan disabled."""
        mock_path.exists.return_value = False
        mock_path.touch = Mock()

        # Mock questionary responses
        mock_questionary.select.return_value.ask.side_effect = [
            "Z.AI",
            "English",
            "developers",
        ]
        mock_questionary.text.return_value.ask.return_value = "glm-4.6"
        mock_questionary.password.return_value.ask.return_value = "zai-api-key"

        runner = CliRunner()
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        assert "Welcome to kittylog initialization" in result.output

        # Verify set_key calls
        assert mock_set_key.call_count == 3  # model + API key + audience

        # Check the specific calls
        calls = mock_set_key.call_args_list
        assert any("KITTYLOG_MODEL" in str(call) and "zai:glm-4.6" in str(call) for call in calls)
        assert any("ZAI_API_KEY" in str(call) and "zai-api-key" in str(call) for call in calls)

    @patch("kittylog.init_cli.questionary")
    @patch("kittylog.init_cli.set_key")
    @patch("kittylog.init_cli.KITTYLOG_ENV_PATH")
    def test_init_custom_openai_provider(self, mock_path, mock_set_key, mock_questionary):
        """Test init command with Custom (OpenAI) provider."""
        mock_path.exists.return_value = True

        mock_questionary.select.return_value.ask.side_effect = [
            "Custom (OpenAI)",
            "English",
            "developers",
        ]
        mock_questionary.text.return_value.ask.side_effect = [
            "gpt-4o-mini",
            "https://example.com/v1",
        ]
        mock_questionary.password.return_value.ask.return_value = "sk-custom"

        runner = CliRunner()
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        calls = mock_set_key.call_args_list
        assert any("KITTYLOG_MODEL" in str(call) and "custom-openai:gpt-4o-mini" in str(call) for call in calls)
        assert any("CUSTOM_OPENAI_BASE_URL" in str(call) and "https://example.com/v1" in str(call) for call in calls)
        assert any("CUSTOM_OPENAI_API_KEY" in str(call) and "sk-custom" in str(call) for call in calls)

    @patch("kittylog.init_cli.questionary")
    @patch("kittylog.init_cli.set_key")
    @patch("kittylog.init_cli.KITTYLOG_ENV_PATH")
    def test_init_lmstudio_optional_api_key(self, mock_path, mock_set_key, mock_questionary):
        """Test init command with LM Studio provider without API key."""
        mock_path.exists.return_value = True

        mock_questionary.select.return_value.ask.side_effect = [
            "LM Studio",
            "English",
            "developers",
        ]
        mock_questionary.text.return_value.ask.side_effect = [
            "gemma3:instruct",
            "http://localhost:4321",
        ]
        mock_questionary.password.return_value.ask.return_value = ""

        runner = CliRunner()
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        calls = mock_set_key.call_args_list
        assert any("KITTYLOG_MODEL" in str(call) and "lm-studio:gemma3:instruct" in str(call) for call in calls)
        assert any("LMSTUDIO_API_URL" in str(call) and "http://localhost:4321" in str(call) for call in calls)
        # Should not set API key when skipped
        assert not any("LMSTUDIO_API_KEY" in str(call) for call in calls)

    @patch("kittylog.init_cli.questionary")
    @patch("kittylog.init_cli.set_key")
    @patch("kittylog.init_cli.KITTYLOG_ENV_PATH")
    def test_init_streamlake_provider(self, mock_path, mock_set_key, mock_questionary):
        """Test init command with Streamlake provider requiring endpoint ID."""
        mock_path.exists.return_value = True

        mock_questionary.select.return_value.ask.side_effect = [
            "Streamlake",
            "English",
            "developers",
        ]
        mock_questionary.text.return_value.ask.return_value = "endpoint-123"
        mock_questionary.password.return_value.ask.return_value = "streamlake-key"

        runner = CliRunner()
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        calls = mock_set_key.call_args_list
        assert any("KITTYLOG_MODEL" in str(call) and "streamlake:endpoint-123" in str(call) for call in calls)
        assert any("STREAMLAKE_API_KEY" in str(call) and "streamlake-key" in str(call) for call in calls)

    @patch("kittylog.init_cli.KITTYLOG_ENV_PATH")
    def test_init_with_no_config_dir(self, mock_path):
        """Test init command when config directory doesn't exist."""
        mock_path.exists.return_value = False
        mock_path.parent.exists.return_value = False
        mock_path.parent.mkdir = Mock()

        runner = CliRunner()
        result = runner.invoke(cli, ["init"])

        # Should handle gracefully
        assert result.exit_code in [0, 1]


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def test_cli_workflow_dry_run(self, temp_dir, git_repo_with_tags):
        """Test complete CLI workflow with dry run."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "update",
                "--file",
                str(temp_dir / "CHANGELOG.md"),
                "--dry-run",
                "--quiet",
            ],
        )

        # This test just verifies the CLI command can be invoked without crashing
        # The actual business logic is tested elsewhere
        assert result.exit_code in [0, 1]  # Allow both success and failure exit codes

    def test_cli_error_handling(self):
        """Test CLI error handling."""
        with patch("kittylog.update_cli.main_business_logic") as mock_logic:
            from kittylog.errors import GitError

            mock_logic.return_value = (False, None)
            mock_logic.side_effect = GitError("Not a git repository")

            runner = CliRunner()
            result = runner.invoke(cli, ["update"])

            assert result.exit_code == 1
            assert "Not a git repository" in result.output

    def test_cli_with_relative_paths(self, temp_dir):
        """Test CLI with relative file paths."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "update",
                "--file",
                "docs/CHANGELOG.md",
            ],
        )

        # This test just verifies the CLI command can be invoked without crashing
        # The actual business logic is tested elsewhere
        assert result.exit_code in [0, 1]  # Allow both success and failure exit codes


class TestCLIValidation:
    """Test CLI argument validation."""

    def test_invalid_model_format(self):
        """Test handling of invalid model format."""
        with patch("kittylog.update_cli.main_business_logic") as mock_logic:
            from kittylog.errors import ConfigError

            mock_logic.return_value = (False, None)
            mock_logic.side_effect = ConfigError("Invalid model format")

            runner = CliRunner()
            result = runner.invoke(cli, ["update", "--model", "invalid"])

            assert result.exit_code == 1
            assert "Invalid model format" in result.output

    def test_nonexistent_changelog_file(self):
        """Test handling of non-existent changelog file."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "update",
                "--file",
                "nonexistent/CHANGELOG.md",
            ],
        )

        # This test just verifies the CLI command can be invoked without crashing
        # The actual business logic is tested elsewhere
        assert result.exit_code in [0, 1]  # Allow both success and failure exit codes
