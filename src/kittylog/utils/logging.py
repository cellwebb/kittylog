"""Logging utilities for kittylog."""

import logging
import sys

from kittylog.constants import Logging


def get_safe_encodings() -> list[str]:
    """Get a list of safe text encodings to try.

    Returns:
        List of encoding names ordered by preference
    """
    return ["utf-8", "utf-8-sig", "latin-1", "cp1252"]


def setup_logging(
    log_level: str = Logging.DEFAULT_LEVEL,
    quiet: bool = False,
    verbose: bool = False,
) -> None:
    """Set up logging configuration for the application.

    Args:
        log_level: Logging level to use (DEBUG, INFO, WARNING, ERROR)
        quiet: Suppress all output except errors
        verbose: Enable verbose output
    """
    if quiet:
        effective_level = logging.ERROR
    elif verbose:
        effective_level = logging.INFO
    else:
        effective_level = getattr(logging, log_level.upper(), logging.WARNING)

    # Configure root logger
    logging.basicConfig(
        level=effective_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stderr),
        ],
    )

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def print_message(message: str, level: str = "info") -> None:
    """Print a message with optional level prefix.

    Args:
        message: Message to print
        level: Log level prefix (info, warning, error)
    """
    if level == "error":
        print(f"Error: {message}", file=sys.stderr)
    elif level == "warning":
        print(f"Warning: {message}", file=sys.stderr)
    else:
        print(message)
