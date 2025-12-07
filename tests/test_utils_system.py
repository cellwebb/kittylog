"""Tests for system utilities."""

from unittest.mock import Mock, patch

import pytest

from kittylog.utils.system import (
    exit_with_error,
    run_subprocess,
    run_subprocess_with_encoding,
)


class TestRunSubprocessWithEncoding:
    """Test the run_subprocess_with_encoding function."""

    def test_run_subprocess_with_encoding_success(self):
        """Test successful subprocess execution with encoding."""
        mock_result = Mock()
        mock_result.stdout = "success output"
        mock_result.returncode = 0

        with (
            patch("kittylog.utils.system.subprocess.run", return_value=mock_result),
            patch("kittylog.utils.logging.get_safe_encodings", return_value=["utf-8", "latin-1"]),
        ):
            result = run_subprocess_with_encoding(["echo", "test"], encoding="utf-8")
            assert result.stdout == "success output"
            assert result.returncode == 0

    def test_run_subprocess_with_encoding_fallback_encoding(self):
        """Test subprocess execution with encoding fallback."""
        mock_result = Mock()
        mock_result.stdout = "fallback output"
        mock_result.returncode = 0

        with patch("kittylog.utils.system.subprocess.run") as mock_run:
            mock_run.side_effect = [UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"), mock_result]
            with patch("kittylog.utils.logging.get_safe_encodings", return_value=["utf-8", "latin-1"]):
                result = run_subprocess_with_encoding(["echo", "test"], encoding="utf-8")
                assert result.stdout == "fallback output"
                assert mock_run.call_count == 2

    def test_run_subprocess_with_encoding_all_encodings_fail(self):
        """Test when all encoding attempts fail."""
        error = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")

        with (
            patch("kittylog.utils.system.subprocess.run", side_effect=error),
            patch("kittylog.utils.logging.get_safe_encodings", return_value=["utf-8", "latin-1"]),
            pytest.raises(UnicodeDecodeError),
        ):
            run_subprocess_with_encoding(["echo", "test"], encoding="utf-8")

    def test_run_subprocess_with_encoding_none_encoding(self):
        """Test subprocess execution with None encoding."""
        mock_result = Mock()
        mock_result.stdout = "no encoding output"
        mock_result.returncode = 0

        with patch("kittylog.utils.system.subprocess.run", return_value=mock_result):
            result = run_subprocess_with_encoding(["echo", "test"], encoding=None)
            assert result.stdout == "no encoding output"

    def test_run_subprocess_with_encoding_custom_options(self):
        """Test subprocess execution with custom options."""
        mock_result = Mock()
        mock_result.stdout = "custom output"
        mock_result.returncode = 0

        with (
            patch("kittylog.utils.system.subprocess.run", return_value=mock_result) as mock_run,
            patch("kittylog.utils.logging.get_safe_encodings", return_value=["utf-8"]),
        ):
            result = run_subprocess_with_encoding(
                ["echo", "test"], encoding="utf-8", capture_output=False, text=False, check=True
            )
            assert result.stdout == "custom output"
            # Verify subprocess.run was called with all the options
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["capture_output"] is False
            assert call_kwargs["text"] is False
            assert call_kwargs["check"] is True
            assert call_kwargs["encoding"] == "utf-8"

    def test_run_subprocess_with_encoding_unicode_error(self):
        """Test subprocess execution handling UnicodeError specifically."""
        error = UnicodeError("invalid unicode")
        mock_result = Mock()
        mock_result.stdout = "fallback output"
        mock_result.returncode = 0

        with patch("kittylog.utils.system.subprocess.run") as mock_run:
            mock_run.side_effect = [error, mock_result]
            with patch("kittylog.utils.logging.get_safe_encodings", return_value=["utf-8", "latin-1"]):
                result = run_subprocess_with_encoding(["echo", "test"], encoding="utf-8")
                assert result.stdout == "fallback output"
                assert mock_run.call_count == 2

    def test_run_subprocess_with_encoding_no_last_error_fallback(self):
        """Test fallback when no encodings are specified and no last error."""
        mock_result = Mock()
        mock_result.stdout = "default output"
        mock_result.returncode = 0

        with patch("kittylog.utils.system.subprocess.run", return_value=mock_result):
            result = run_subprocess_with_encoding(["echo", "test"], encoding="custom")
            assert result.stdout == "default output"


class TestRunSubprocess:
    """Test the run_subprocess function."""

    def test_run_subprocess_success(self):
        """Test successful subprocess execution returning stdout."""
        mock_result = Mock()
        mock_result.stdout = "test output"
        mock_result.returncode = 0

        with patch("kittylog.utils.system.run_subprocess_with_encoding", return_value=mock_result):
            result = run_subprocess(["echo", "test"])
            assert result == "test output"

    def test_run_subprocess_with_encoding(self):
        """Test subprocess execution with encoding parameter."""
        mock_result = Mock()
        mock_result.stdout = "encoded output"
        mock_result.returncode = 0

        with patch("kittylog.utils.system.run_subprocess_with_encoding", return_value=mock_result):
            result = run_subprocess(["echo", "test"], encoding="utf-8")
            assert result == "encoded output"

    def test_run_subprocess_with_options(self):
        """Test subprocess execution with all options."""
        mock_result = Mock()
        mock_result.stdout = "option output"
        mock_result.returncode = 0

        with patch("kittylog.utils.system.run_subprocess_with_encoding", return_value=mock_result) as mock_func:
            result = run_subprocess(["echo", "test"], encoding="latin-1", capture_output=False, text=False, check=True)
            assert result == "option output"
            mock_func.assert_called_once_with(
                cmd=["echo", "test"], encoding="latin-1", capture_output=False, text=False, check=True
            )

    def test_run_subprocess_command_failure(self):
        """Test subprocess execution when command fails but check=False."""
        mock_result = Mock()
        mock_result.stdout = "error output"
        mock_result.returncode = 1

        with patch("kittylog.utils.system.run_subprocess_with_encoding", return_value=mock_result):
            result = run_subprocess(["false"])
            assert result == "error output"


class TestExitWithError:
    """Test the exit_with_error function."""

    def test_exit_with_error_default_code(self):
        """Test exit_with_error with default exit code."""
        with (
            patch("kittylog.utils.logging.print_message") as mock_print,
            patch("kittylog.utils.system.exit", side_effect=SystemExit) as mock_exit,
        ):
            with pytest.raises(SystemExit):
                exit_with_error("Test error message")
            mock_print.assert_called_once_with("Test error message", "error")
            mock_exit.assert_called_once_with(1)

    def test_exit_with_error_custom_code(self):
        """Test exit_with_error with custom exit code."""
        with (
            patch("kittylog.utils.logging.print_message") as mock_print,
            patch("kittylog.utils.system.exit", side_effect=SystemExit) as mock_exit,
        ):
            with pytest.raises(SystemExit):
                exit_with_error("Custom error", exit_code=42)
            mock_print.assert_called_once_with("Custom error", "error")
            mock_exit.assert_called_once_with(42)

    def test_exit_with_error_complex_message(self):
        """Test exit_with_error with complex error message."""
        complex_message = "Multiple\nLines\nOf\nError"

        with (
            patch("kittylog.utils.logging.print_message") as mock_print,
            patch("kittylog.utils.system.exit", side_effect=SystemExit) as mock_exit,
        ):
            with pytest.raises(SystemExit):
                exit_with_error(complex_message, exit_code=2)
            mock_print.assert_called_once_with(complex_message, "error")
            mock_exit.assert_called_once_with(2)


class TestSystemIntegration:
    """Integration tests for system utilities."""

    def test_run_subprocess_real_command(self):
        """Test run_subprocess with a real command."""
        result = run_subprocess(["echo", "hello"])
        assert "hello" in result

    def test_run_subprocess_with_encoding_real_command(self):
        """Test run_subprocess_with_encoding with a real command."""
        result = run_subprocess_with_encoding(["echo", "test"], encoding="utf-8")
        assert result.returncode == 0
        assert "test" in result.stdout

    def test_run_subprocess_nonexistent_command(self):
        """Test run_subprocess with nonexistent command."""
        with pytest.raises(FileNotFoundError):
            run_subprocess(["nonexistent_command_12345"])
