"""Tests for re-authentication functionality."""

import pytest

from kittylog.oauth import claude_code


def test_prompt_for_reauth_non_interactive(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that prompt_for_reauth returns False when not in interactive terminal."""
    import sys

    class FakeStdin:
        def isatty(self):
            return False

    monkeypatch.setattr(sys, "stdin", FakeStdin())

    result = claude_code.prompt_for_reauth()
    assert result is False


def test_prompt_for_reauth_user_declines(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that prompt_for_reauth returns False when user declines."""
    import sys

    class FakeStdin:
        def isatty(self):
            return True

    monkeypatch.setattr(sys, "stdin", FakeStdin())
    monkeypatch.setattr("builtins.input", lambda _: "n")

    result = claude_code.prompt_for_reauth()
    assert result is False


def test_prompt_for_reauth_user_accepts_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that prompt_for_reauth returns True when user accepts and auth succeeds."""
    import sys

    class FakeStdin:
        def isatty(self):
            return True

    monkeypatch.setattr(sys, "stdin", FakeStdin())
    monkeypatch.setattr("builtins.input", lambda _: "y")
    monkeypatch.setattr(claude_code, "authenticate_and_save", lambda quiet: True)

    result = claude_code.prompt_for_reauth()
    assert result is True


def test_prompt_for_reauth_user_accepts_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that prompt_for_reauth returns False when user accepts but auth fails."""
    import sys

    class FakeStdin:
        def isatty(self):
            return True

    monkeypatch.setattr(sys, "stdin", FakeStdin())
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    monkeypatch.setattr(claude_code, "authenticate_and_save", lambda quiet: False)

    result = claude_code.prompt_for_reauth()
    assert result is False


def test_prompt_for_reauth_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that prompt_for_reauth handles KeyboardInterrupt gracefully."""
    import sys

    class FakeStdin:
        def isatty(self):
            return True

    def raise_keyboard_interrupt(_):
        raise KeyboardInterrupt()

    monkeypatch.setattr(sys, "stdin", FakeStdin())
    monkeypatch.setattr("builtins.input", raise_keyboard_interrupt)

    result = claude_code.prompt_for_reauth()
    assert result is False


def test_prompt_for_reauth_eoferror(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that prompt_for_reauth handles EOFError gracefully."""
    import sys

    class FakeStdin:
        def isatty(self):
            return True

    def raise_eoferror(_):
        raise EOFError()

    monkeypatch.setattr(sys, "stdin", FakeStdin())
    monkeypatch.setattr("builtins.input", raise_eoferror)

    result = claude_code.prompt_for_reauth()
    assert result is False
