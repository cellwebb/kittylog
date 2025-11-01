"""Tests for kittylog.constants.Languages resolution."""

import pytest

from kittylog.constants import Languages


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("en", "English"),
        ("es", "Spanish"),
        ("ES", "Spanish"),
        ("zh-cn", "Simplified Chinese"),
        ("ZH-TW", "Traditional Chinese"),
        ("ja", "Japanese"),
        ("de", "German"),
    ],
)
def test_resolve_language_codes(code, expected):
    """Ensure common language codes resolve to full names."""
    assert Languages.resolve_code(code) == expected


def test_resolve_language_name_passthrough():
    """Ensure full language names are returned unchanged."""
    assert Languages.resolve_code("French") == "French"
    assert Languages.resolve_code("Esperanto") == "Esperanto"


def test_resolve_unknown_code_returns_input():
    """Unknown codes should be passed through unchanged."""
    assert Languages.resolve_code("xx") == "xx"
    assert Languages.resolve_code("CustomLang") == "CustomLang"
