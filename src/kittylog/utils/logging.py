"""Logging utilities for kittylog.

Provides structured logging with context for better debugging.
"""

import logging
import sys
from collections.abc import MutableMapping
from typing import Any

from kittylog.config import load_config
from kittylog.constants import EnvDefaults, Logging
from kittylog.output import set_output_mode


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


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the kittylog namespace.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"kittylog.{name}" if not name.startswith("kittylog") else name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **context: Any,
) -> None:
    """Log a message with structured context.

    Args:
        logger: Logger instance
        level: Log level (e.g., logging.INFO)
        message: Log message
        **context: Additional context as key-value pairs

    Example:
        log_with_context(
            logger, logging.INFO,
            "Processing commits",
            tag="v1.0.0",
            commit_count=15,
            provider="openai"
        )
    """
    if context:
        # Format context for readability
        context_str = " ".join(f"{k}={v}" for k, v in context.items())
        logger.log(level, f"{message} [{context_str}]")
    else:
        logger.log(level, message)


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds structured context to all log messages.

    Usage:
        logger = StructuredLoggerAdapter(
            logging.getLogger(__name__),
            {"component": "ai", "version": "1.0.0"}
        )
        logger.info("Processing", extra={"tag": "v1.0.0"})
    """

    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> tuple[str, MutableMapping[str, Any]]:
        """Add context to log message."""
        extra = kwargs.get("extra", {})

        # Merge adapter context with call-site context
        if self.extra:
            context = {**self.extra, **extra.get("context", {})}
            extra["context"] = context

        kwargs["extra"] = extra
        return msg, kwargs


def setup_command_logging(log_level: str | None, verbose: bool, quiet: bool) -> None:
    """Set up logging for CLI commands with consistent logic.

    Args:
        log_level: Optional log level override
        verbose: Whether to enable verbose output
        quiet: Whether to suppress non-error output
    """
    effective_log_level = log_level or load_config().log_level or EnvDefaults.LOG_LEVEL
    if verbose and effective_log_level not in ("DEBUG", "INFO"):
        effective_log_level = "INFO"
    if quiet:
        effective_log_level = "ERROR"
    setup_logging(effective_log_level)

    # Configure output manager mode
    set_output_mode(quiet=quiet, verbose=verbose)


# Convenience functions for common log levels
def log_debug(logger: logging.Logger, message: str, **context: Any) -> None:
    """Log a debug message with context."""
    log_with_context(logger, logging.DEBUG, message, **context)


def log_info(logger: logging.Logger, message: str, **context: Any) -> None:
    """Log an info message with context."""
    log_with_context(logger, logging.INFO, message, **context)


def log_warning(logger: logging.Logger, message: str, **context: Any) -> None:
    """Log a warning message with context."""
    log_with_context(logger, logging.WARNING, message, **context)


def log_error(logger: logging.Logger, message: str, **context: Any) -> None:
    """Log an error message with context."""
    log_with_context(logger, logging.ERROR, message, **context)
