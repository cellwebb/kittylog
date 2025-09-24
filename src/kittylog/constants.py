"""Constants for the Changelog Updater project."""

import os
from enum import Enum


class FileStatus(Enum):
    """File status for Git operations."""

    MODIFIED = "M"
    ADDED = "A"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNTRACKED = "?"


class EnvDefaults:
    """Default values for environment variables."""

    MAX_RETRIES: int = 3
    TEMPERATURE: float = 0.7
    MAX_OUTPUT_TOKENS: int = 1024
    WARNING_LIMIT_TOKENS: int = 16384
    GROUPING_MODE: str = "tags"
    GAP_THRESHOLD_HOURS: float = 4.0
    DATE_GROUPING: str = "daily"


class Logging:
    """Logging configuration constants."""

    DEFAULT_LEVEL: str = "WARNING"
    LEVELS: list[str] = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Utility:
    """General utility constants."""

    DEFAULT_ENCODING: str = "cl100k_base"  # LLM encoding
    MAX_WORKERS: int = os.cpu_count() or 4  # Maximum number of parallel workers
    DEFAULT_MAX_MESSAGE_LENGTH: int = 80  # Default max length for commit messages
    DEFAULT_MAX_FILES: int = 5  # Default max number of files to display


class ChangelogSections:
    """Standard changelog sections."""

    ADDED = "Added"
    CHANGED = "Changed"
    DEPRECATED = "Deprecated"
    REMOVED = "Removed"
    FIXED = "Fixed"
    SECURITY = "Security"

    ALL_SECTIONS = [ADDED, CHANGED, DEPRECATED, REMOVED, FIXED, SECURITY]


class CommitKeywords:
    """Keywords for categorizing commits."""

    FEATURE_KEYWORDS = ["feat:", "feature:", "add", "new", "implement", "introduce"]
    FIX_KEYWORDS = ["fix:", "bugfix:", "hotfix:", "fix", "bug", "issue", "problem", "error"]
    BREAKING_KEYWORDS = ["break:", "breaking:", "BREAKING CHANGE"]
    REMOVE_KEYWORDS = ["remove:", "delete:", "drop", "remove", "delete"]
    DEPRECATE_KEYWORDS = ["deprecate:", "deprecate"]
    SECURITY_KEYWORDS = ["security:", "sec:", "security", "vulnerability", "cve"]
    CHANGE_KEYWORDS = ["update", "change", "modify", "improve", "enhance", "refactor"]