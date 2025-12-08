"""Comprehensive tests for auth_cli.py module."""

from pathlib import Path
from unittest import mock

import pytest
from click.testing import CliRunner

from kittylog.auth_cli import (
    auth,
    claude_code_login,
    claude_code_logout,
    claude_code_status,
    qwen_login,
    qwen_logout,
    qwen_status,
)


class TestShowAuthStatus:
    """Test the _show_auth_status function."""

    def test_shows_authenticated_claude_code(self, tmp_path):
        """Test status display when Claude Code is authenticated."""
        with mock.patch("kittylog.auth_cli.load_stored_token") as mock_load:
            mock_load.return_value = "fake_token"
            with mock.patch("kittylog.auth_cli.TokenStore") as mock_store:
                mock_instance = mock_store.return_value
                mock_instance.get_token.return_value = None

                runner = CliRunner()
                result = runner.invoke(auth, [])

                assert result.exit_code == 0
                assert "Claude Code: ✓ Authenticated" in result.output
                assert "Qwen:        ✗ Not authenticated" in result.output

    def test_shows_authenticated_qwen(self, tmp_path):
        """Test status display when Qwen is authenticated."""
        with mock.patch("kittylog.auth_cli.load_stored_token") as mock_load:
            mock_load.return_value = None
            with mock.patch("kittylog.auth_cli.TokenStore") as mock_store:
                mock_instance = mock_store.return_value
                mock_instance.get_token.return_value = {"access_token": "fake_token"}

                runner = CliRunner()
                result = runner.invoke(auth, [])

                assert result.exit_code == 0
                assert "Claude Code: ✗ Not authenticated" in result.output
                assert "Qwen:        ✓ Authenticated" in result.output

    def test_shows_both_authenticated(self):
        """Test status display when both providers are authenticated."""
        with mock.patch("kittylog.auth_cli.load_stored_token") as mock_load:
            mock_load.return_value = "fake_token"
            with mock.patch("kittylog.auth_cli.TokenStore") as mock_store:
                mock_instance = mock_store.return_value
                mock_instance.get_token.return_value = {"access_token": "fake_token"}

                runner = CliRunner()
                result = runner.invoke(auth, [])

                assert result.exit_code == 0
                assert "Claude Code: ✓ Authenticated" in result.output
                assert "Qwen:        ✓ Authenticated" in result.output


class TestClaudeCodeCommands:
    """Test Claude Code authentication commands."""

    def test_claude_code_login_success(self):
        """Test successful Claude Code login."""
        with mock.patch("kittylog.auth_cli.authenticate_and_save") as mock_auth:
            mock_auth.return_value = True

            runner = CliRunner()
            result = runner.invoke(claude_code_login, [])

            assert result.exit_code == 0
            assert "Successfully authenticated with Claude Code" in result.output

    def test_claude_code_login_failure(self):
        """Test failed Claude Code login."""
        with mock.patch("kittylog.auth_cli.authenticate_and_save") as mock_auth:
            mock_auth.return_value = False

            runner = CliRunner()
            result = runner.invoke(claude_code_login, [])

            assert result.exit_code == 1
            assert "Authentication failed" in result.output

    def test_claude_code_login_quiet_mode(self):
        """Test Claude Code login in quiet mode."""
        with mock.patch("kittylog.auth_cli.authenticate_and_save") as mock_auth:
            mock_auth.return_value = True

            runner = CliRunner()
            result = runner.invoke(claude_code_login, ["--quiet"])

            assert result.exit_code == 0
            mock_auth.assert_called_once_with(quiet=True)

    def test_claude_code_logout_when_no_token_file(self):
        """Test Claude Code logout when no token file exists."""
        with mock.patch("kittylog.auth_cli.get_token_storage_path") as mock_path:
            mock_path.return_value = Path("/fake/path/.env")
            with mock.patch("kittylog.auth_cli.Path.exists") as mock_exists:
                mock_exists.return_value = False

                runner = CliRunner()
                result = runner.invoke(claude_code_logout, [])

                assert result.exit_code == 0
                assert "No Claude Code token found to remove" in result.output

    def test_claude_code_logout_success(self):
        """Test successful Claude Code logout."""
        with mock.patch("kittylog.auth_cli.get_token_storage_path") as mock_path:
            mock_path.return_value = Path("/fake/path/.env")
            with mock.patch("kittylog.auth_cli.Path.exists") as mock_exists:
                mock_exists.return_value = True
                with mock.patch("dotenv.unset_key") as mock_unset:
                    runner = CliRunner()
                    result = runner.invoke(claude_code_logout, [])

                    assert result.exit_code == 0
                    assert "Successfully logged out from Claude Code" in result.output
                    mock_unset.assert_called_once()

    def test_claude_code_logout_import_error_fallback(self):
        """Test Claude Code logout fallback when unset_key is not available."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "dotenv":
                raise ImportError("No dotenv")
            return original_import(name, *args, **kwargs)

        with (
            mock.patch("builtins.__import__", side_effect=mock_import),
            mock.patch("kittylog.auth_cli.get_token_storage_path") as mock_path,
        ):
            mock_path.return_value = Path("/fake/path/.env")
            with mock.patch("kittylog.auth_cli.Path.exists") as mock_exists:
                mock_exists.return_value = True
                with mock.patch("kittylog.auth_cli.Path.read_text") as mock_read:
                    mock_read.return_value = "CLAUDE_CODE_ACCESS_TOKEN=fake\nOTHER=value"
                    with mock.patch("kittylog.auth_cli.Path.write_text"):
                        runner = CliRunner()
                        result = runner.invoke(claude_code_logout, [])

                        assert result.exit_code == 0
                        assert "Successfully logged out from Claude Code" in result.output

    def test_claude_code_logout_with_exception(self):
        """Test Claude Code logout with exception handling."""
        with mock.patch("kittylog.auth_cli.get_token_storage_path") as mock_path:
            mock_path.return_value = Path("/fake/path/.env")
            with mock.patch("kittylog.auth_cli.Path.exists") as mock_exists:
                mock_exists.return_value = True
                with mock.patch("dotenv.unset_key") as mock_unset:
                    mock_unset.side_effect = Exception("Test error")

                    runner = CliRunner()
                    result = runner.invoke(claude_code_logout, [])

                    assert result.exit_code == 1
                    assert "Error removing token" in result.output

    def test_claude_code_status_authenticated(self):
        """Test Claude Code status when authenticated."""
        with mock.patch("kittylog.auth_cli.load_stored_token") as mock_load:
            mock_load.return_value = "fake_token_1234567890"
            with mock.patch("kittylog.auth_cli.get_token_storage_path") as mock_path:
                mock_path.return_value = Path("/fake/path/.env")

                runner = CliRunner()
                result = runner.invoke(claude_code_status, [])

                assert result.exit_code == 0
                assert "Status: ✓ Authenticated" in result.output
                assert "Token preview: fake_token_123456789" in result.output

    def test_claude_code_status_not_authenticated(self):
        """Test Claude Code status when not authenticated."""
        with mock.patch("kittylog.auth_cli.load_stored_token") as mock_load:
            mock_load.return_value = None

            runner = CliRunner()
            result = runner.invoke(claude_code_status, [])

            assert result.exit_code == 0
            assert "Status: ✗ Not authenticated" in result.output
            assert "kittylog auth claude-code login" in result.output


class TestQwenCommands:
    """Test Qwen authentication commands."""

    def test_qwen_login_success(self):
        """Test successful Qwen login."""
        with mock.patch("kittylog.auth_cli.QwenOAuthProvider") as mock_provider:
            mock_instance = mock_provider.return_value
            mock_instance.is_authenticated.return_value = False
            mock_instance.initiate_auth.return_value = None

            runner = CliRunner()
            result = runner.invoke(qwen_login, [])

            assert result.exit_code == 0
            assert "Successfully authenticated with Qwen" in result.output

    def test_qwen_login_no_browser_flag(self):
        """Test Qwen login with no-browser flag."""
        with mock.patch("kittylog.auth_cli.QwenOAuthProvider") as mock_provider:
            mock_instance = mock_provider.return_value
            mock_instance.is_authenticated.return_value = False
            mock_instance.initiate_auth.return_value = None

            runner = CliRunner()
            result = runner.invoke(qwen_login, ["--no-browser"])

            assert result.exit_code == 0
            mock_instance.initiate_auth.assert_called_once_with(open_browser=False)

    def test_qwen_login_already_authenticated_cancelled(self):
        """Test Qwen login when already authenticated and user cancels."""
        with mock.patch("kittylog.auth_cli.QwenOAuthProvider") as mock_provider:
            mock_instance = mock_provider.return_value
            mock_instance.is_authenticated.return_value = True

            runner = CliRunner()
            result = runner.invoke(qwen_login, [], input="n\n")

            assert result.exit_code == 0
            assert "Already authenticated with Qwen" in result.output
            assert "Authentication cancelled" in result.output
            mock_instance.initiate_auth.assert_not_called()

    def test_qwen_login_already_authenticated_reauthenticate(self):
        """Test Qwen login when already authenticated and user wants to re-authenticate."""
        with mock.patch("kittylog.auth_cli.QwenOAuthProvider") as mock_provider:
            mock_instance = mock_provider.return_value
            mock_instance.is_authenticated.return_value = True
            mock_instance.initiate_auth.return_value = None

            runner = CliRunner()
            result = runner.invoke(qwen_login, [], input="y\n")

            assert result.exit_code == 0
            mock_instance.initiate_auth.assert_called_once()

    def test_qwen_login_keyboard_interrupt(self):
        """Test Qwen login with keyboard interrupt."""
        with mock.patch("kittylog.auth_cli.QwenOAuthProvider") as mock_provider:
            mock_instance = mock_provider.return_value
            mock_instance.is_authenticated.return_value = False
            mock_instance.initiate_auth.side_effect = KeyboardInterrupt()

            runner = CliRunner()
            result = runner.invoke(qwen_login, [])

            assert result.exit_code == 1
            assert "Authentication cancelled by user" in result.output

    def test_qwen_login_other_exception(self):
        """Test Qwen login with other exception."""
        with mock.patch("kittylog.auth_cli.QwenOAuthProvider") as mock_provider:
            mock_instance = mock_provider.return_value
            mock_instance.is_authenticated.return_value = False
            mock_instance.initiate_auth.side_effect = Exception("Test error")

            runner = CliRunner()
            result = runner.invoke(qwen_login, [])

            assert result.exit_code == 1
            assert "Authentication failed" in result.output

    def test_qwen_logout_success(self):
        """Test successful Qwen logout."""
        with mock.patch("kittylog.auth_cli.QwenOAuthProvider") as mock_provider:
            mock_instance = mock_provider.return_value
            mock_instance.logout.return_value = None

            runner = CliRunner()
            result = runner.invoke(qwen_logout, [])

            assert result.exit_code == 0
            assert "Successfully logged out from Qwen" in result.output
            mock_instance.logout.assert_called_once()

    def test_qwen_logout_exception(self):
        """Test Qwen logout with exception."""
        with mock.patch("kittylog.auth_cli.QwenOAuthProvider") as mock_provider:
            mock_instance = mock_provider.return_value
            mock_instance.logout.side_effect = Exception("Test error")

            runner = CliRunner()
            result = runner.invoke(qwen_logout, [])

            assert result.exit_code == 1
            assert "Error during logout" in result.output

    def test_qwen_status_authenticated_with_expiry(self):
        """Test Qwen status when authenticated with expiry."""
        import time

        future_time = time.time() + 3600  # 1 hour from now

        with mock.patch("kittylog.auth_cli.TokenStore") as mock_store:
            mock_instance = mock_store.return_value
            mock_instance.get_token.return_value = {
                "access_token": "fake_token",
                "expiry": future_time,
                "scope": "read write",
            }

            runner = CliRunner()
            result = runner.invoke(qwen_status, [])

            assert result.exit_code == 0
            assert "Status: ✓ Authenticated" in result.output
            assert "Expires:" in result.output
            assert "Time remaining:" in result.output
            assert "Scopes: read write" in result.output

    def test_qwen_status_authenticated_expired(self):
        """Test Qwen status when token is expired."""
        import time

        past_time = time.time() - 3600  # 1 hour ago

        with mock.patch("kittylog.auth_cli.TokenStore") as mock_store:
            mock_instance = mock_store.return_value
            mock_instance.get_token.return_value = {"access_token": "fake_token", "expiry": past_time}

            runner = CliRunner()
            result = runner.invoke(qwen_status, [])

            assert result.exit_code == 0
            assert "Status: ✓ Authenticated" in result.output
            assert "Expired:" in result.output
            assert "Token is expired" in result.output

    def test_qwen_status_not_authenticated(self):
        """Test Qwen status when not authenticated."""
        with mock.patch("kittylog.auth_cli.TokenStore") as mock_store:
            mock_instance = mock_store.return_value
            mock_instance.get_token.return_value = None

            runner = CliRunner()
            result = runner.invoke(qwen_status, [])

            assert result.exit_code == 0
            assert "Status: ✗ Not authenticated" in result.output
            assert "kittylog auth qwen login" in result.output


class TestAuthCommand:
    """Test the main auth command."""

    def test_auth_without_subcommand_shows_status(self):
        """Test auth command without subcommand shows status."""
        with mock.patch("kittylog.auth_cli._show_auth_status") as mock_show:
            runner = CliRunner()
            result = runner.invoke(auth, [])

            mock_show.assert_called_once()
            assert result.exit_code == 0

    def test_auth_with_subcommand(self):
        """Test auth command with subcommand."""
        runner = CliRunner()
        result = runner.invoke(auth, ["claude-code", "status"])

        # Should invoke the subcommand
        assert result.exit_code == 0


class TestAuthCliIntegration:
    """Integration tests for auth CLI module."""

    def test_complete_claude_code_login_flow(self):
        """Test complete Claude Code login flow."""
        with mock.patch("kittylog.auth_cli.authenticate_and_save") as mock_auth:
            mock_auth.return_value = True

            runner = CliRunner()
            result = runner.invoke(claude_code_login, [])

            assert result.exit_code == 0
            assert "Starting Claude Code OAuth authentication" in result.output
            assert "Successfully authenticated with Claude Code" in result.output

    def test_complete_qwen_login_flow_with_already_authenticated_reauth(self):
        """Test complete Qwen login flow with re-authentication."""
        with mock.patch("kittylog.auth_cli.QwenOAuthProvider") as mock_provider:
            mock_instance = mock_provider.return_value
            mock_instance.is_authenticated.return_value = True
            mock_instance.initiate_auth.return_value = None

            runner = CliRunner()
            result = runner.invoke(qwen_login, [], input="y\n")

            assert result.exit_code == 0
            assert "Already authenticated with Qwen" in result.output
            assert "Successfully authenticated with Qwen" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
