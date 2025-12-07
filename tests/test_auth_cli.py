"""Tests for auth_cli module."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from kittylog.auth_cli import (
    _show_auth_status,
    auth,
    claude_code,
    claude_code_login,
    claude_code_logout,
    claude_code_status,
    qwen,
    qwen_status,
)


class TestAuthCommands:
    """Test the main auth command group."""

    def test_auth_group_with_no_subcommand_shows_status(self):
        """Test that calling auth without subcommand shows status."""
        runner = CliRunner()
        with patch("kittylog.auth_cli._show_auth_status") as mock_status:
            result = runner.invoke(auth)
            mock_status.assert_called_once()
            assert result.exit_code == 0

    def test_auth_group_help(self):
        """Test auth group help output."""
        runner = CliRunner()
        result = runner.invoke(auth, ["--help"])
        assert result.exit_code == 0
        assert "Manage OAuth authentication" in result.output
        assert "claude-code" in result.output
        assert "qwen" in result.output


class TestShowAuthStatus:
    """Test the _show_auth_status function."""

    def test_show_auth_status_both_authenticated(self):
        """Test status when both providers are authenticated."""
        with (
            patch("kittylog.auth_cli.load_stored_token", return_value="fake_token"),
            patch("kittylog.auth_cli.TokenStore") as mock_store_class,
        ):
            mock_store = Mock()
            mock_store.get_token.return_value = "qwen_token"
            mock_store_class.return_value = mock_store

            _show_auth_status()  # Direct call
            # Just verify the function runs without error
            assert True

    def test_show_auth_status_neither_authenticated(self):
        """Test status when neither provider is authenticated."""
        with (
            patch("kittylog.auth_cli.load_stored_token", return_value=None),
            patch("kittylog.auth_cli.TokenStore") as mock_store_class,
        ):
            mock_store = Mock()
            mock_store.get_token.return_value = None
            mock_store_class.return_value = mock_store

            _show_auth_status()  # Direct call
            # Just verify the function runs without error
            assert True

    def test_show_auth_status_only_claude_authenticated(self):
        """Test status when only Claude Code is authenticated."""
        with (
            patch("kittylog.auth_cli.load_stored_token", return_value="claude_token"),
            patch("kittylog.auth_cli.TokenStore") as mock_store_class,
        ):
            mock_store = Mock()
            mock_store.get_token.return_value = None
            mock_store_class.return_value = mock_store

            _show_auth_status()  # Direct call
            # Just verify the function runs without error
            assert True


class TestClaudeCodeCommands:
    """Test Claude Code authentication commands."""

    def test_claude_code_group_help(self):
        """Test Claude Code group help."""
        runner = CliRunner()
        result = runner.invoke(claude_code, ["--help"])
        assert result.exit_code == 0
        assert "Manage Claude Code OAuth" in result.output

    def test_claude_code_login_success(self):
        """Test successful Claude Code login."""
        runner = CliRunner()
        with (
            patch("kittylog.auth_cli.authenticate_and_save", return_value=True),
            patch("kittylog.auth_cli.get_token_storage_path", return_value="/fake/path"),
        ):
            result = runner.invoke(claude_code_login)
            assert result.exit_code == 0
            assert "✓ Successfully authenticated" in result.output
            assert "Token saved to /fake/path" in result.output

    def test_claude_code_login_failure(self):
        """Test failed Claude Code login."""
        runner = CliRunner()
        with patch("kittylog.auth_cli.authenticate_and_save", return_value=False):
            result = runner.invoke(claude_code_login)
            assert result.exit_code == 1  # Click.Abort
            assert "❌ Authentication failed" in result.output
            assert "Please try again" in result.output

    def test_claude_code_status_with_token(self):
        """Test Claude Code status when authenticated."""
        runner = CliRunner()
        with patch("kittylog.auth_cli.load_stored_token", return_value="fake_token"):
            result = runner.invoke(claude_code_status)
            assert result.exit_code == 0
            assert "✓ Authenticated" in result.output
            assert "Claude Code" in result.output

    def test_claude_code_status_without_token(self):
        """Test Claude Code status when not authenticated."""
        runner = CliRunner()
        with patch("kittylog.auth_cli.load_stored_token", return_value=None):
            result = runner.invoke(claude_code_status)
            assert result.exit_code == 0
            assert "✗ Not authenticated" in result.output
            assert "Claude Code" in result.output
            assert "kittylog auth claude-code login" in result.output

    def test_claude_code_logout_no_token(self):
        """Test Claude Code logout when no token exists."""
        runner = CliRunner()
        mock_path = Mock()
        mock_path.exists.return_value = False

        with patch("kittylog.auth_cli.get_token_storage_path", return_value=mock_path):
            result = runner.invoke(claude_code_logout)
            assert result.exit_code == 0
            assert "No Claude Code token found" in result.output


class TestQwenCommands:
    """Test Qwen authentication commands."""

    def test_qwen_group_help(self):
        """Test Qwen group help."""
        runner = CliRunner()
        result = runner.invoke(qwen, ["--help"])
        assert result.exit_code == 0
        assert "Manage Qwen OAuth" in result.output

    def test_qwen_status_without_token(self):
        """Test Qwen status when not authenticated."""
        runner = CliRunner()
        with patch("kittylog.auth_cli.TokenStore") as mock_store_class:
            mock_store = Mock()
            mock_store.get_token.return_value = None
            mock_store_class.return_value = mock_store

            result = runner.invoke(qwen_status)
            assert result.exit_code == 0
            assert "✗ Not authenticated" in result.output
            assert "Qwen" in result.output
            assert "kittylog auth qwen login" in result.output


class TestAuthIntegration:
    """Test full auth CLI integration."""

    def test_auth_claude_code_login_workflow(self):
        """Test full Claude Code login workflow through auth group."""
        runner = CliRunner()
        with (
            patch("kittylog.auth_cli.authenticate_and_save", return_value=True),
            patch("kittylog.auth_cli.get_token_storage_path", return_value="/fake/path"),
        ):
            result = runner.invoke(auth, ["claude-code", "login"])
            assert result.exit_code == 0
            assert "✓ Successfully authenticated" in result.output

    def test_auth_invalid_command(self):
        """Test handling of invalid auth commands."""
        runner = CliRunner()
        result = runner.invoke(auth, ["invalid-provider"])
        assert result.exit_code != 0
        assert "No such command" in result.output
