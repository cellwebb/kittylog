"""Changelog Updater - AI-powered changelog updates using git tags."""

from clog.__version__ import __version__
from clog.changelog import update_changelog
from clog.git_operations import get_commits_between_tags, get_tags_since_last_changelog

__all__ = [
    "__version__",
    "get_tags_since_last_changelog",
    "get_commits_between_tags",
    "update_changelog",
]
