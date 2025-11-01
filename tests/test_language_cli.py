"""Tests for kittylog language_cli module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from kittylog.language_cli import language


def test_language_select_predefined_with_heading_translation():
    """Test selecting a predefined language with heading translation enabled."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".kittylog.env"
        with patch("kittylog.language_cli.KITTYLOG_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select:
                mock_select.return_value.ask.side_effect = [
                    "Español",
                    "Translate section headings into Spanish",
                ]
                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "✓ Set language to Español" in result.output
                assert "KITTYLOG_LANGUAGE=Spanish" in result.output
                assert "KITTYLOG_TRANSLATE_HEADINGS=true" in result.output
                assert fake_path.exists()

                content = fake_path.read_text()
                assert "KITTYLOG_LANGUAGE=Spanish" in content
                assert "KITTYLOG_TRANSLATE_HEADINGS=true" in content


def test_language_select_predefined_keep_english_headings():
    """Test selecting a predefined language without translating section headings."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".kittylog.env"
        with patch("kittylog.language_cli.KITTYLOG_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select:
                mock_select.return_value.ask.side_effect = [
                    "日本語",
                    "Keep section headings in English (Added, Changed, etc.)",
                ]
                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "✓ Set language to 日本語" in result.output
                assert "KITTYLOG_LANGUAGE=Japanese" in result.output
                assert "KITTYLOG_TRANSLATE_HEADINGS=false" in result.output
                assert fake_path.exists()

                content = fake_path.read_text()
                assert "KITTYLOG_LANGUAGE=Japanese" in content
                assert "KITTYLOG_TRANSLATE_HEADINGS=false" in content


def test_language_select_english_removes_setting():
    """Test selecting English removes language settings."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".kittylog.env"
        fake_path.write_text("KITTYLOG_LANGUAGE=Spanish\nKITTYLOG_TRANSLATE_HEADINGS=true\n")

        with patch("kittylog.language_cli.KITTYLOG_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select, patch("kittylog.language_cli.unset_key") as mock_unset:
                mock_select.return_value.ask.return_value = "English"
                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "✓ Set language to English (default)" in result.output
                assert "Removed KITTYLOG_LANGUAGE" in result.output
                mock_unset.assert_any_call(str(fake_path), "KITTYLOG_LANGUAGE")
                mock_unset.assert_any_call(str(fake_path), "KITTYLOG_TRANSLATE_HEADINGS")

                content = fake_path.read_text()
                assert "KITTYLOG_LANGUAGE" not in content
                assert "KITTYLOG_TRANSLATE_HEADINGS" not in content


def test_language_select_custom_language():
    """Test selecting a custom language."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".kittylog.env"
        with patch("kittylog.language_cli.KITTYLOG_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select, patch("questionary.text") as mock_text:
                mock_select.return_value.ask.side_effect = [
                    "Custom",
                    "Keep section headings in English (Added, Changed, etc.)",
                ]
                mock_text.return_value.ask.return_value = "Esperanto"

                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "✓ Set language to Custom" in result.output
                assert "KITTYLOG_LANGUAGE=Esperanto" in result.output
                assert fake_path.exists()

                content = fake_path.read_text()
                assert "KITTYLOG_LANGUAGE=Esperanto" in content
                assert "KITTYLOG_TRANSLATE_HEADINGS=false" in content


def test_language_select_custom_with_whitespace():
    """Test selecting a custom language with whitespace trimmed."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".kittylog.env"
        with patch("kittylog.language_cli.KITTYLOG_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select, patch("questionary.text") as mock_text:
                mock_select.return_value.ask.side_effect = [
                    "Custom",
                    "Keep section headings in English (Added, Changed, etc.)",
                ]
                mock_text.return_value.ask.return_value = "  Klingon  "

                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "KITTYLOG_LANGUAGE=Klingon" in result.output


def test_language_custom_cancelled_empty_input():
    """Test cancelling custom language when input is empty."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".kittylog.env"
        with patch("kittylog.language_cli.KITTYLOG_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select, patch("questionary.text") as mock_text:
                mock_select.return_value.ask.return_value = "Custom"
                mock_text.return_value.ask.return_value = ""

                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "No language entered. Cancelled." in result.output
                if fake_path.exists():
                    content = fake_path.read_text()
                    assert "KITTYLOG_LANGUAGE" not in content


def test_language_selection_cancelled():
    """Test behaviour when language selection is cancelled."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / ".kittylog.env"
        with patch("kittylog.language_cli.KITTYLOG_ENV_PATH", fake_path):
            with patch("questionary.select") as mock_select:
                mock_select.return_value.ask.return_value = None

                result = runner.invoke(language)

                assert result.exit_code == 0
                assert "Language selection cancelled." in result.output
                assert not fake_path.exists()
