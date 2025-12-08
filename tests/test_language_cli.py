"""Comprehensive tests for language_cli.py module."""

from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

# Import the actual functions from the module
from kittylog.language_cli import (
    _run_language_selection_flow,
    configure_language_init_workflow,
    language,
)


def _load_existing_env():
    """Mock implementation for loading existing environment variables."""
    from dotenv import dotenv_values

    from kittylog.language_cli import KITTYLOG_ENV_PATH

    return dotenv_values(str(KITTYLOG_ENV_PATH)) or {}


class TestLoadExistingEnv:
    """Test the _load_existing_env function."""

    def test_filters_none_values_from_env(self, tmp_path):
        """Test that None values are filtered out from environment variables."""
        temp_path = tmp_path / ".kittylog.env"
        temp_path.write_text("KITTYLOG_LANGUAGE=en\nKITTYLOG_TRANSLATE_HEADINGS=true\n")

        with (
            mock.patch("kittylog.language_cli.KITTYLOG_ENV_PATH", temp_path),
            mock.patch("dotenv.dotenv_values") as mock_dotenv,
        ):
            mock_dotenv.return_value = {"KITTYLOG_LANGUAGE": "en", "KITTYLOG_TRANSLATE_HEADINGS": "true"}
            result = _load_existing_env()

        assert result == {"KITTYLOG_LANGUAGE": "en", "KITTYLOG_TRANSLATE_HEADINGS": "true"}


class TestConfigureLanguageInitWorkflow:
    """Test the configure_language_init_workflow function."""

    def test_preserves_existing_language_when_user_chooses_to_keep(self, tmp_path):
        """Test that existing language is preserved when user chooses to keep it."""
        env_file = tmp_path / ".kittylog.env"
        env_file.write_text("KITTYLOG_LANGUAGE=Spanish")

        with (
            mock.patch("kittylog.language_cli.load_dotenv"),
            mock.patch("kittylog.language_cli.os.getenv", return_value="Spanish"),
            mock.patch("kittylog.language_cli.questionary") as mock_q,
        ):
            mock_q.select.return_value.ask.return_value = "Keep existing language (Spanish)"

            with mock.patch("kittylog.language_cli.click.echo"):
                result = configure_language_init_workflow(env_file)

                # Should preserve existing language
                assert result is True


class TestRunLanguageSelectionFlow:
    """Test the _run_language_selection_flow function."""

    def test_handles_custom_language_input(self, tmp_path):
        """Test handling of custom language input."""
        fake_env_path = Path("/fake/.env")

        with (
            mock.patch("kittylog.language_cli.questionary") as mock_q,
            mock.patch("kittylog.language_cli.set_key"),
        ):
            mock_q.select.return_value.ask.return_value = "Custom"
            mock_q.text.return_value.ask.return_value = "custom"

            result = _run_language_selection_flow(fake_env_path)

        assert result == "custom"

    def test_cancels_heading_selection_returns_false(self, tmp_path):
        """Test that cancellation during heading selection returns False."""
        fake_env_path = Path("/fake/.env")

        with mock.patch("kittylog.language_cli.questionary") as mock_q:
            mock_q.select.return_value.ask.return_value = "English"
            mock_q.select.return_value.ask.return_value = None  # Cancel

            result = _run_language_selection_flow(fake_env_path)

        assert result is None

    def test_sets_translate_headings_true(self, tmp_path):
        """Test that translate headings is set to true when selected."""
        fake_env_path = Path("/fake/.env")

        # Mock questionary with side_effect to handle multiple calls
        with mock.patch("kittylog.language_cli.questionary") as mock_q:
            # First select call - language selection
            # Second text call - custom language name
            # Third select call - translate headings choice
            mock_q.select.return_value.ask.side_effect = [
                "Custom",  # First select - language
                "Translate section headings into TestLang",  # Third select - heading choice
            ]
            mock_q.text.return_value.ask.return_value = "TestLang"  # Second call - text input

            with mock.patch("kittylog.language_cli.set_key") as mock_set:
                result = _run_language_selection_flow(fake_env_path)

        assert result == "TestLang"
        # Should have set translate headings to true
        translate_calls = [call for call in mock_set.call_args_list if "KITTYLOG_TRANSLATE_HEADINGS" in str(call)]
        assert len(translate_calls) > 0

    def test_handles_predefined_language_selection(self, tmp_path):
        """Test handling of predefined language selection."""
        fake_env_path = Path("/fake/.env")

        # Mock questionary with side_effect to handle multiple calls
        with mock.patch("kittylog.language_cli.questionary") as mock_q:
            # First select call - language selection (Deutsch)
            # Second select call - heading choice (Keep in English)
            mock_q.select.return_value.ask.side_effect = [
                "Deutsch",  # First select - German language
                "Keep section headings in English",  # Second select - heading choice
            ]

            with mock.patch("kittylog.language_cli.set_key") as mock_set:
                result = _run_language_selection_flow(fake_env_path)

        assert result == "German"
        # Should have set language to German
        language_calls = [call for call in mock_set.call_args_list if "KITTYLOG_LANGUAGE" in str(call)]
        assert len(language_calls) > 0


class TestLanguageCommand:
    """Test the main language command function."""

    def test_cancels_language_selection(self):
        """Test cancellation of language selection."""
        env_path = Path("/fake/.kittylog.env")

        with (
            mock.patch("kittylog.language_cli.KITTYLOG_ENV_PATH", env_path),
            mock.patch("kittylog.language_cli.questionary") as mock_q,
            mock.patch.object(Path, "touch"),
        ):
            mock_q.select.return_value.ask.return_value = None  # Cancels selection

            runner = CliRunner()
            result = runner.invoke(language, [])

            assert result.exit_code == 0
            # Check that the cancelled message was printed
            assert "Language selection cancelled" in result.output

    def test_handles_english_selection(self):
        """Test handling of English language selection."""
        env_path = Path("/fake/.kittylog.env")

        with (
            mock.patch("kittylog.language_cli.KITTYLOG_ENV_PATH", env_path),
            mock.patch("kittylog.language_cli.questionary") as mock_q,
            mock.patch("kittylog.language_cli.click.echo"),
            mock.patch("dotenv.unset_key"),
            mock.patch.object(Path, "touch"),
        ):
            mock_q.select.return_value.ask.return_value = "English"

            runner = CliRunner()
            result = runner.invoke(language, [])

            assert result.exit_code == 0

    def test_handles_custom_language_input(self):
        """Test handling of custom language input."""
        env_path = Path("/fake/.kittylog.env")

        with (
            mock.patch("kittylog.language_cli.KITTYLOG_ENV_PATH", env_path),
            mock.patch("kittylog.language_cli.questionary") as mock_q,
            mock.patch("kittylog.language_cli.click.echo"),
            mock.patch("kittylog.language_cli.set_key"),
            mock.patch("kittylog.language_cli.Path.exists", return_value=False),
            mock.patch("kittylog.language_cli.Path.touch"),
        ):
            # Mock questionary with side_effect to handle multiple calls
            mock_q.select.return_value.ask.side_effect = [
                "Custom",  # First select - language selection
                "Keep section headings in English",  # Third select - heading choice
            ]
            mock_q.text.return_value.ask.return_value = "TestLanguage"  # Second call - text input

            runner = CliRunner()
            result = runner.invoke(language, [])

            assert result.exit_code == 0

    def test_handles_predefined_language_selection(self):
        """Test handling of predefined language selection."""
        env_path = Path("/fake/.kittylog.env")

        with (
            mock.patch("kittylog.language_cli.KITTYLOG_ENV_PATH", env_path),
            mock.patch("kittylog.language_cli.questionary") as mock_q,
            mock.patch("kittylog.language_cli.click.echo"),
            mock.patch("kittylog.language_cli.set_key"),
            mock.patch("kittylog.language_cli.Path.exists", return_value=False),
            mock.patch("kittylog.language_cli.Path.touch"),
        ):
            # Mock questionary with side_effect to handle multiple calls
            mock_q.select.return_value.ask.side_effect = [
                "Español",  # First select - language selection
                "Keep section headings in English",  # Second select - heading choice
            ]

            runner = CliRunner()
            result = runner.invoke(language, [])

            assert result.exit_code == 0

    def test_handles_cancellation_of_heading_selection(self):
        """Test handling of cancellation during heading selection."""
        env_path = Path("/fake/.kittylog.env")

        with (
            mock.patch("kittylog.language_cli.KITTYLOG_ENV_PATH", env_path),
            mock.patch("kittylog.language_cli.questionary") as mock_q,
            mock.patch("kittylog.language_cli.click.echo"),
            mock.patch.object(Path, "touch"),
        ):
            mock_q.select.return_value.ask.return_value = "English"
            mock_q.select.return_value.ask.return_value = None  # Cancel heading selection

            runner = CliRunner()
            result = runner.invoke(language, [])

            assert result.exit_code == 0

    def test_handles_empty_custom_language_input(self):
        """Test handling of empty custom language input."""
        env_path = Path("/fake/.kittylog.env")

        with (
            mock.patch("kittylog.language_cli.KITTYLOG_ENV_PATH", env_path),
            mock.patch("kittylog.language_cli.questionary") as mock_q,
            mock.patch("kittylog.language_cli.click.echo"),
            mock.patch.object(Path, "touch"),
        ):
            mock_q.select.return_value.ask.return_value = "Custom"
            mock_q.text.return_value.ask.return_value = ""  # Empty input

            runner = CliRunner()
            result = runner.invoke(language, [])

            assert result.exit_code == 0


class TestLanguageCliIntegration:
    """Integration tests for language CLI module."""

    def test_complete_language_configuration_workflow(self):
        """Test complete language configuration workflow."""
        env_path = Path("/fake/.kittylog.env")

        with (
            mock.patch("kittylog.language_cli.KITTYLOG_ENV_PATH", env_path),
            mock.patch("kittylog.language_cli.questionary") as mock_q,
            mock.patch("kittylog.language_cli.set_key"),
            mock.patch("kittylog.language_cli.click.echo"),
            mock.patch("kittylog.language_cli.Path.exists", return_value=False),
            mock.patch("kittylog.language_cli.Path.touch"),
        ):
            # Mock questionary with side_effect to handle multiple calls
            mock_q.select.return_value.ask.side_effect = [
                "English",  # First select - language selection
                "Keep section headings in English",  # Second select - heading choice
            ]

            runner = CliRunner()
            result = runner.invoke(language, [])

            assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
