"""Changelog Updater - AI-powered changelog updates using git tags."""

from kittylog.__version__ import __version__
from kittylog.changelog import update_changelog
from kittylog.git_operations import get_commits_between_tags, get_tags_since_last_changelog

__all__ = [
    "__version__",
    "get_commits_between_tags",
    "get_tags_since_last_changelog",
    "update_changelog",
]
