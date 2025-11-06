"""Git operations for kittylog.

This module provides Git operations and functions as a unified interface
to the specialized tag_operations and commit_analyzer modules.

This refactoring maintains backward compatibility while organizing
functionality into focused, maintainable modules.
"""

import logging

from git import InvalidGitRepositoryError, Repo
from kittylog.commit_analyzer import (
    clear_commit_analyzer_cache,
    get_all_commits_chronological,
    get_all_tags_with_dates,
    get_commits_between_boundaries,
    get_commits_between_hashes,
    get_commits_between_tags,
    get_commits_by_date_boundaries,
    get_commits_by_gap_boundaries,
    get_git_diff,
)
from kittylog.tag_operations import (
    clear_git_cache,
    determine_new_tags,
    generate_boundary_display_name,
    generate_boundary_identifier,
    get_all_boundaries,
    get_all_tags,
    get_current_commit_hash,
    get_latest_boundary,
    get_latest_tag,
    get_previous_boundary,
    get_repo,
    get_tag_date,
    is_current_commit_tagged,
)
from kittylog.utils import run_subprocess

logger = logging.getLogger(__name__)

# Re-export all functions for backward compatibility
__all__ = [
    # From git module
    "Repo",
    "InvalidGitRepositoryError",
    # From tag_operations
    "clear_git_cache",
    "generate_boundary_display_name",
    "generate_boundary_identifier",
    "get_all_boundaries",
    "get_all_tags",
    "get_current_commit_hash",
    "get_latest_boundary",
    "get_latest_tag",
    "get_previous_boundary",
    "get_repo",
    "get_tag_date",
    "is_current_commit_tagged",
    "determine_new_tags",
    # From commit_analyzer
    "get_all_commits_chronological",
    "get_all_tags_with_dates",
    "get_commits_between_boundaries",
    "get_commits_between_hashes",
    "get_commits_between_tags",
    "get_commits_by_date_boundaries",
    "get_commits_by_gap_boundaries",
    "get_git_diff",
    "clear_commit_analyzer_cache",
]

# Alias for backward compatibility
def get_tags_since_last_changelog(changelog_file: str = "CHANGELOG.md"):
    """Alias for determine_new_tags for backward compatibility."""
    return determine_new_tags(changelog_file)[1]

# Alias for backward compatibility
def run_git_command(args):
    """Alias for run_subprocess for backward compatibility."""
    return run_subprocess(args)

# For complete backward compatibility, also expose a combined clear function
def clear_all_caches():
    """Clear all git operation caches."""
    clear_git_cache()
    clear_commit_analyzer_cache()

__all__.append("clear_all_caches")
__all__.append("get_tags_since_last_changelog")
__all__.append("run_git_command")
