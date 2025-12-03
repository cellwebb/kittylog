"""Utilities for kittylog.

This module provides a unified interface to all utility functions.
"""

# Import all utility functions from specialized modules
from .utils_commit import format_commit_for_display
from .utils_logging import (
    get_safe_encodings,
    print_message,
    setup_logging,
)
from .utils_system import (
    exit_with_error,
    run_subprocess,
    run_subprocess_with_encoding,
)
from .utils_text import (
    clean_changelog_content,
    count_tokens,
    determine_next_version,
    find_changelog_file,
    get_changelog_file_patterns,
    is_semantic_version,
    normalize_tag,
    truncate_text,
)

# Re-export everything for backward compatibility
__all__ = [
    "clean_changelog_content",
    "count_tokens",
    "determine_next_version",
    "exit_with_error",
    "find_changelog_file",
    "format_commit_for_display",
    "get_changelog_file_patterns",
    "get_safe_encodings",
    "is_semantic_version",
    "normalize_tag",
    "print_message",
    "run_subprocess",
    "run_subprocess_with_encoding",
    "setup_logging",
    "truncate_text",
]
