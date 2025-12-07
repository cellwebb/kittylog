"""Utilities for kittylog.

This module provides a unified interface to all utility functions.
"""

# Import all utility functions from specialized modules
# Import from postprocess module
from kittylog.postprocess import clean_changelog_content

from .commit import format_commit_for_display
from .logging import (
    StructuredLoggerAdapter,
    get_logger,
    get_safe_encodings,
    log_debug,
    log_error,
    log_info,
    log_warning,
    log_with_context,
    print_message,
    setup_logging,
)
from .system import (
    exit_with_error,
    run_subprocess,
    run_subprocess_with_encoding,
)
from .text import (
    count_tokens,
    detect_changelog_version_style,
    determine_next_version,
    find_changelog_file,
    format_version_for_changelog,
    get_changelog_file_patterns,
    is_semantic_version,
    normalize_tag,
    truncate_text,
)

# Re-export everything for backward compatibility
__all__ = [
    "StructuredLoggerAdapter",
    "clean_changelog_content",
    "count_tokens",
    "detect_changelog_version_style",
    "determine_next_version",
    "exit_with_error",
    "find_changelog_file",
    "format_commit_for_display",
    "format_version_for_changelog",
    "get_changelog_file_patterns",
    "get_logger",
    "get_safe_encodings",
    "is_semantic_version",
    "log_debug",
    "log_error",
    "log_info",
    "log_warning",
    "log_with_context",
    "normalize_tag",
    "print_message",
    "run_subprocess",
    "run_subprocess_with_encoding",
    "setup_logging",
    "truncate_text",
]
