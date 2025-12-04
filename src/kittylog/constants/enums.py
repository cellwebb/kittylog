"""Enum definitions for the Changelog Updater project."""

from enum import Enum


class FileStatus(Enum):
    """File status for Git operations."""

    MODIFIED = "M"
    ADDED = "A"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNTRACKED = "?"


class GroupingMode(str, Enum):
    """Grouping modes for changelog entries."""

    TAGS = "tags"
    DATES = "dates"
    GAPS = "gaps"


class DateGrouping(str, Enum):
    """Date grouping strategies."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
