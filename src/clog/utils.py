"""Utility functions for changelog-updater."""

import logging
import os
import re
import subprocess
from pathlib import Path

import tiktoken
from rich.console import Console
from rich.theme import Theme

from clog.constants import Logging, Utility
from clog.errors import ChangelogUpdaterError

logger = logging.getLogger(__name__)


def setup_logging(
    log_level: int | str | None = Logging.DEFAULT_LEVEL,
    quiet: bool = False,
    force: bool = False,
    suppress_noisy: bool = False,
) -> None:
    """Configure logging for the application.

    Args:
        log_level: Log level to use (DEBUG, INFO, WARNING, ERROR)
        quiet: If True, suppress all output except errors
        force: If True, force reconfiguration of logging
        suppress_noisy: If True, suppress noisy third-party loggers
    """
    # Handle None or sentinel values by defaulting to WARNING
    if log_level is None or (hasattr(log_level, "name") and log_level.name == "UNSET"):
        log_level = logging.WARNING

    if isinstance(log_level, str):
        # Handle invalid log levels by defaulting to WARNING
        log_level_upper = log_level.upper()
        if log_level_upper not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            log_level = logging.WARNING
        else:
            log_level = getattr(logging, log_level_upper, logging.WARNING)

    if quiet:
        log_level = logging.ERROR

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if suppress_noisy:
        for noisy_logger in ["requests", "urllib3", "git"]:
            logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    logger.info(f"Logging initialized with level: {logging.getLevelName(log_level)}")


theme = Theme(
    {
        "success": "green bold",
        "info": "blue",
        "warning": "yellow",
        "error": "red bold",
        "header": "magenta",
        "notification": "bright_cyan bold",
    }
)
console = Console(theme=theme)


def print_message(message: str, level: str = "info") -> None:
    """Print a styled message with the specified level."""
    console.print(message, style=level)


def run_subprocess(
    command: list[str],
    silent: bool = False,
    timeout: int = 60,
    check: bool = True,
    strip_output: bool = True,
    raise_on_error: bool = True,
) -> str:
    """Run a subprocess command safely and return the output.

    Args:
        command: List of command arguments
        silent: If True, suppress debug logging
        timeout: Command timeout in seconds
        check: Whether to check return code (for compatibility)
        strip_output: Whether to strip whitespace from output
        raise_on_error: Whether to raise an exception on error

    Returns:
        Command output as string

    Raises:
        ChangelogUpdaterError: If the command times out
        subprocess.CalledProcessError: If the command fails and raise_on_error is True
    """
    if not silent:
        logger.debug(f"Running command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )

        should_raise = result.returncode != 0 and (check or raise_on_error)

        if should_raise:
            if not silent:
                logger.debug(f"Command stderr: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)

        output = result.stdout
        if strip_output:
            output = output.strip()

        return output
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout} seconds: {' '.join(command)}")
        raise ChangelogUpdaterError(f"Command timed out: {' '.join(command)}") from e
    except subprocess.CalledProcessError as e:
        if not silent:
            logger.error(f"Command failed: {e.stderr.strip() if e.stderr else str(e)}")
        if raise_on_error:
            raise
        return ""
    except Exception as e:
        if not silent:
            logger.debug(f"Command error: {e}")
        if raise_on_error:
            # Convert generic exceptions to CalledProcessError for consistency
            raise subprocess.CalledProcessError(1, command, "", str(e)) from e
        return ""


def count_tokens(text: str, model: str) -> int:
    """Count tokens in text using tiktoken.

    Args:
        text: The text to count tokens for
        model: The model name (used to determine encoding)

    Returns:
        Number of tokens in the text
    """
    if not text:
        return 0

    try:
        # Try to get model-specific encoding
        if "gpt" in model.lower():
            encoding = tiktoken.encoding_for_model(model.split(":")[-1])
        else:
            # Use default encoding for other models
            encoding = tiktoken.get_encoding(Utility.DEFAULT_ENCODING)

        return len(encoding.encode(text))
    except Exception as e:
        logger.debug(f"Token counting failed: {e}, using character-based estimation")
        # If encoding fails, return 0
        return 0


def format_commit_for_display(commit: dict, max_message_length: int | None = None, max_files: int | None = None) -> str:
    """Format a commit dictionary for display.

    Args:
        commit: Dictionary containing commit data (hash, message, author, files, date)
        max_message_length: Maximum length for commit message (optional)
        max_files: Maximum number of files to display (optional)

    Returns:
        Formatted string representation of the commit
    """
    # Use default values from constants if not provided
    if max_message_length is None:
        max_message_length = Utility.DEFAULT_MAX_MESSAGE_LENGTH
    if max_files is None:
        max_files = Utility.DEFAULT_MAX_FILES

    # Extract commit data with safe defaults
    short_hash = commit.get("short_hash", commit.get("hash", "")[:7] if commit.get("hash") else "")
    message = commit.get("message", "No message")
    author = commit.get("author", "Unknown author")
    date = commit.get("date")
    files = commit.get("files", [])

    # Truncate message if needed
    if max_message_length and len(message) > max_message_length:
        message = truncate_text(message, max_message_length)

    # Ensure the first line doesn't exceed 80 characters ONLY when max_message_length is specified
    formatted = f"* {short_hash}: {message} ({author})"
    if date:
        formatted += f" [Date: {date.strftime('%Y-%m-%d')}]"

    first_line = formatted.split("\n")[0]
    # Only truncate if the line exceeds 80 characters by a significant margin
    if max_message_length and len(first_line) > 85:
        # Calculate how much we need to truncate the message
        excess = len(first_line) - 80
        if len(message) > excess + 3:  # Only truncate if we can add '...'
            message = message[: -(excess + 3)] + "..."
        # Use the truncated message for the final formatted string
        formatted = f"* {short_hash}: {message} ({author})"
        if date:
            formatted += f" [Date: {date.strftime('%Y-%m-%d')}]"

    # Add files if present
    if files:
        if max_files and len(files) > max_files:
            shown_files = files[:max_files]
            remaining = len(files) - max_files
            formatted += f"\n  Files: {', '.join(shown_files)} (... and {remaining} more files)"
        else:
            formatted += f"\n  Files: {', '.join(files)}"

    return formatted


def clean_changelog_content(content: str) -> str:
    """Clean AI-generated changelog content by removing markdown code blocks and AI chatter.

    Args:
        content: Raw changelog content from AI

    Returns:
        Cleaned changelog content without markdown formatting
    """
    # Remove markdown code block markers
    content = content.replace("```markdown", "").replace("```", "")

    # Remove common AI chatter patterns
    ai_patterns = [
        "Here's the changelog:",
        "Here's the updated changelog:",
        "I'll help you create a changelog entry.",
        "Let me know if you need anything else!",
        "The changelog entry above shows the changes.",
        "Is there anything else you'd like me to adjust?",
        "Here is the changelog entry",
        "Here's what I came up with",
        "Sure, here's a changelog entry",
    ]

    for pattern in ai_patterns:
        content = content.replace(pattern, "")

    # Special case: if content indicates no changes, return empty string
    if "No changes found" in content:
        return ""

    # Remove any leading/trailing whitespace
    return content.strip()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length with an optional suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length of the text
        suffix: Suffix to append if text is truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    # Truncate and add suffix
    return text[: max_length - len(suffix)] + suffix


def is_semantic_version(version: str) -> bool:
    """Check if a string is a valid semantic version.

    Args:
        version: Version string to check

    Returns:
        True if the string is a valid semantic version, False otherwise
    """
    # Remove 'v' prefix if present
    if version.startswith("v"):
        version = version[1:]

    # Check semantic version format (X.Y.Z with optional pre-release and build metadata)
    pattern = r"^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?$"
    return bool(re.match(pattern, version))


def normalize_tag(tag: str) -> str:
    """Normalize a git tag by removing the 'v' prefix if present.

    Args:
        tag: Git tag to normalize

    Returns:
        Normalized tag without 'v' prefix
    """
    if tag.startswith("v") or tag.startswith("V"):
        return tag[1:]
    return tag


def find_changelog_file(directory: str = ".") -> str:
    """Find the changelog file in the given directory.

    Searches for changelog files in the following order of preference:
    1. CHANGELOG.md (root)
    2. changelog.md (root)
    3. CHANGES.md (root)
    4. changes.md (root)
    5. CHANGELOG.md (docs/)
    6. changelog.md (docs/)
    7. CHANGES.md (docs/)
    8. changes.md (docs/)

    Args:
        directory: Directory to search in (default: current directory)

    Returns:
        Path to the found changelog file, or "CHANGELOG.md" as fallback

    Raises:
        None: Always returns a valid path, using "CHANGELOG.md" as fallback
    """
    changelog_filenames = ["CHANGELOG.md", "changelog.md", "CHANGES.md", "changes.md"]

    # First check root directory - get actual files in directory to avoid case-insensitive issues
    root_dir_path = Path(directory)
    if root_dir_path.exists() and root_dir_path.is_dir():
        root_files = [f.name for f in root_dir_path.iterdir() if f.is_file()]
        # Check for exact matches in priority order
        for filename in changelog_filenames:
            if filename in root_files:
                logger.debug(f"Found changelog file: {os.path.join(directory, filename)}")
                return filename

    # Then check docs/ directory
    docs_directory = os.path.join(directory, "docs")
    docs_dir_path = Path(docs_directory)
    if docs_dir_path.exists() and docs_dir_path.is_dir():
        docs_files = [f.name for f in docs_dir_path.iterdir() if f.is_file()]
        # Check for exact matches in priority order
        for filename in changelog_filenames:
            if filename in docs_files:
                relative_path = os.path.join("docs", filename)
                logger.debug(f"Found changelog file: {os.path.join(docs_directory, filename)}")
                return relative_path

    # Fallback to CHANGELOG.md if no existing file found
    logger.debug("No existing changelog file found, using default: CHANGELOG.md")
    return "CHANGELOG.md"


def get_changelog_file_patterns() -> list[str]:
    """Get the list of changelog file patterns for exclusion in git operations.

    Returns:
        List of pathspec patterns to exclude changelog files from git operations
    """
    return [":(exclude)CHANGELOG.md", ":(exclude)changelog.md", ":(exclude)CHANGES.md", ":(exclude)changes.md"]
