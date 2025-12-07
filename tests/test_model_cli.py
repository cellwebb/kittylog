"""Tests for kittylog model_cli module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from kittylog.model_cli import model


def test_prompt_required_text_valid_input():
    """Test _prompt_required_text with valid input."""
    from kittylog.model_cli import _prompt_required_text

    with patch("questionary.text") as mock_text:
        mock_text.return_value.ask.return_value = "valid input"
        result = _prompt_required_text("Test prompt:")
        assert result == "valid input"
        mock_text.assert_called_once_with("Test prompt:")


def test_prompt_required_text_empty_then_valid():
    """Test _prompt_required_text when empty input is given first, then valid input."""
    from kittylog.model_cli import _prompt_required_text

    with patch("questionary.text") as mock_text, patch("click.echo") as mock_echo:
        mock_text.return_value.ask.side_effect = ["", "  ", "valid input"]
        result = _prompt_required_text("Test prompt:")

        assert result == "valid input"
        assert mock_echo.call_count == 2  # Two echo calls for empty inputs
        assert mock_text.call_count == 3


def test_prompt_required_text_cancelled():
    """Test _prompt_required_text when user cancels."""
    from kittylog.model_cli import _prompt_required_text

    with patch("questionary.text") as mock_text:
        mock_text.return_value.ask.return_value = None
        result = _prompt_required_text("Test prompt:")
        assert result is None


def test_load_existing_env_creates_new_file():
    """Test _load_existing_env creates new file when it doesn't exist."""
    from kittylog.model_cli import _load_existing_env

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".kittylog.env"

        with patch("kittylog.model_cli.KITTYLOG_ENV_PATH", fake_path), patch("click.echo") as mock_echo:
            result = _load_existing_env()

            assert result == {}
            assert fake_path.exists()
            mock_echo.assert_any_call(f"Created $HOME/.kittylog.env at {fake_path}.")


def test_load_existing_env_updates_existing():
    """Test _load_existing_env loads existing file."""
    from kittylog.model_cli import _load_existing_env

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".kittylog.env"
        fake_path.write_text("EXISTING_KEY=value\nANOTHER_KEY=another_value\nEMPTY_KEY=\n")

        with patch("kittylog.model_cli.KITTYLOG_ENV_PATH", fake_path), patch("click.echo") as mock_echo:
            result = _load_existing_env()

            assert result == {"EXISTING_KEY": "value", "ANOTHER_KEY": "another_value", "EMPTY_KEY": ""}
            mock_echo.assert_any_call(f"$HOME/.kittylog.env already exists at {fake_path}. Values will be updated.")


def test_model_command_success():
    """Test the model command with successful configuration."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".kittylog.env"

        with (
            patch("kittylog.model_cli.KITTYLOG_ENV_PATH", fake_path),
            patch("kittylog.model_cli._load_existing_env") as mock_load_env,
            patch("kittylog.model_cli._configure_model") as mock_configure,
            patch("click.echo") as mock_echo,
        ):
            mock_load_env.return_value = {}
            mock_configure.return_value = True

            result = runner.invoke(model)

            assert result.exit_code == 0
            mock_echo.assert_any_call("Welcome to kittylog model configuration!\n")
            mock_echo.assert_any_call(
                f"\nModel configuration complete. You can edit {fake_path} to update values later."
            )


def test_model_command_configuration_fails():
    """Test the model command when configuration fails."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".kittylog.env"

        with (
            patch("kittylog.model_cli.KITTYLOG_ENV_PATH", fake_path),
            patch("kittylog.model_cli._load_existing_env") as mock_load_env,
            patch("kittylog.model_cli._configure_model") as mock_configure,
            patch("click.echo") as mock_echo,
        ):
            mock_load_env.return_value = {}
            mock_configure.return_value = False  # Configuration failed

            result = runner.invoke(model)

            assert result.exit_code == 0
            # Should not show completion message when configuration fails
            completion_call = any("Model configuration complete" in str(call) for call in mock_echo.call_args_list)
            assert not completion_call


def test_configure_model_cancelled_provider_selection():
    """Test _configure_model when provider selection is cancelled."""
    from kittylog.model_cli import _configure_model

    with patch("questionary.select") as mock_select, patch("click.echo") as mock_echo:
        mock_select.return_value.ask.return_value = None
        result = _configure_model({})

        assert result is False
        mock_echo.assert_any_call("Provider selection cancelled. Exiting.")


def test_configure_model_cancelled_model_entry():
    """Test _configure_model when model entry is cancelled."""
    from kittylog.model_cli import _configure_model

    with (
        patch("questionary.select") as mock_select,
        patch("questionary.text") as mock_text,
        patch("click.echo") as mock_echo,
    ):
        mock_select.return_value.ask.return_value = "OpenAI"
        mock_text.return_value.ask.return_value = None

        result = _configure_model({})

        assert result is False
        mock_echo.assert_any_call("Model entry cancelled. Exiting.")


def test_configure_model_new_api_key_empty():
    """Test _configure_model when new API key entry is empty."""
    from kittylog.model_cli import _configure_model

    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".kittylog.env"

        with (
            patch("kittylog.model_cli.KITTYLOG_ENV_PATH", fake_path),
            patch("questionary.select") as mock_select,
            patch("questionary.text") as mock_text,
            patch("questionary.password") as mock_password,
            patch("dotenv.set_key"),
            patch("click.echo") as mock_echo,
        ):
            mock_select.return_value.ask.return_value = "OpenAI"
            mock_text.return_value.ask.return_value = "gpt-4"
            mock_password.return_value.ask.return_value = ""  # Empty API key

            result = _configure_model({})

            assert result is True
            mock_echo.assert_any_call("No API key entered. You can add one later by editing ~/.kittylog.env")
