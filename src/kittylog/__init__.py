"""Changelog Updater - AI-powered changelog updates using git tags."""

from kittylog.__version__ import __version__
from kittylog.changelog import update_changelog
from kittylog.commit_analyzer import get_commits_between_tags
from kittylog.tag_operations import determine_new_tags

__all__ = [
    "__version__",
    "get_commits_between_tags",
    "determine_new_tags",
    "update_changelog",
]
