"""Tag operations and boundary detection for kittylog.

This module handles tag-related operations, semantic version sorting,
boundary detection across different modes, and changelog synchronization.
"""

import logging
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from git import InvalidGitRepositoryError, Repo

from kittylog.errors import GitError

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_repo() -> Repo:
    """Get the Git repository object for the current directory.

    This function is cached to avoid repeated initialization overhead
    during a single execution.
    """
    try:
        return Repo(".", search_parent_directories=True)
    except InvalidGitRepositoryError as e:
        raise GitError("Not in a git repository") from e


@lru_cache(maxsize=1)
def get_all_tags() -> list[str]:
    """Get all git tags sorted by semantic version if possible, otherwise by creation date.

    This function is cached to avoid repeated git operations and sorting
    during a single execution.
    """
    try:
        repo = get_repo()
        tags = list(repo.tags)

        # Try to sort by semantic version
        def version_key(tag):
            """Extract version components for sorting."""
            # Remove 'v' prefix if present
            version_str = tag.name.lstrip("v")
            # Split by dots and convert to integers where possible
            parts = []
            for part in version_str.split("."):
                try:
                    parts.append(int(part))
                except ValueError:
                    # If conversion fails, use string comparison
                    parts.append(part)
            return parts

        try:
            # Sort by semantic version
            tags.sort(key=version_key)
        except (ValueError, TypeError):
            # Fall back to chronological sorting
            tags.sort(key=lambda t: t.commit.committed_date)

        tag_names = [tag.name for tag in tags]
        logger.debug(f"All tags: {tag_names}")

        return tag_names
    except Exception as e:
        logger.error(f"Failed to get tags: {e!s}")
        raise GitError(f"Failed to get tags: {e!s}") from e


@lru_cache(maxsize=1)
def get_latest_tag() -> str | None:
    """Get the latest tag (highest semantic version or most recent).

    Returns:
        The latest tag name or None if no tags exist
    """
    tags = get_all_tags()
    return tags[-1] if tags else None


@lru_cache(maxsize=1)
def get_current_commit_hash() -> str:
    """Get the current commit hash (HEAD).

    This function is cached to avoid repeated git operations
    during a single execution.
    """
    try:
        repo = get_repo()
        return repo.head.commit.hexsha
    except Exception as e:
        logger.error(f"Failed to get current commit hash: {e!s}")
        raise GitError(f"Failed to get current commit hash: {e!s}") from e


def is_current_commit_tagged() -> bool:
    """Check if the current commit (HEAD) has a tag pointing to it.

    Returns:
        True if HEAD is tagged, False otherwise.
    """
    try:
        repo = get_repo()
        current_commit = get_current_commit_hash()

        # Check if any tag points to the current commit
        return any(tag.commit.hexsha == current_commit for tag in repo.tags)
    except Exception as e:
        logger.error(f"Failed to check if current commit is tagged: {e!s}")
        return False


def determine_new_tags(changelog_file: str = "CHANGELOG.md") -> tuple[str | None, list[str]]:
    """Determine which tags are new since the last changelog entry.

    Args:
        changelog_file: Path to changelog file

    Returns:
        Tuple of (last_tag_in_changelog, new_tags_list)
    """
    # Auto-detect changelog file if using default
    if changelog_file == "CHANGELOG.md":
        from kittylog.utils import find_changelog_file

        changelog_file = find_changelog_file()
        logger.debug(f"Auto-detected changelog file: {changelog_file}")

    try:
        # Read the changelog file to find the last version mentioned
        last_changelog_tag = None
        try:
            content = Path(changelog_file).read_text(encoding="utf-8")

            # Look for version patterns in the changelog
            # Matches patterns like [0.1.0], [v0.1.0], ## [0.1.0], ## 0.1.0, etc.
            version_patterns = [
                r"##?\s*\[?v?(\d+\.\d+\.\d+(?:\.\d+)?)\]?",  # ## [0.1.0] or ## 0.1.0 or [v0.1.0]
                r"\[(\d+\.\d+\.\d+(?:\.\d+)?)\]",  # [0.1.0]
                r"v(\d+\.\d+\.\d+(?:\.\d+)?)",  # v0.1.0
            ]

            for pattern in version_patterns:
                matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
                if matches:
                    # Get the first match (should be the most recent)
                    last_changelog_tag = f"v{matches[0]}" if not matches[0].startswith("v") else matches[0]
                    break

        except FileNotFoundError:
            logger.info(f"Changelog file {changelog_file} not found, will consider all tags as new")
        except Exception as e:
            logger.warning(f"Could not read changelog file: {e}")

        # Get all tags
        all_tags = get_all_tags()

        if not all_tags:
            logger.info("No tags found in repository")
            return None, []

        if not last_changelog_tag:
            logger.info("No previous version found in changelog, considering all tags as new")
            return None, all_tags

        # Find the index of the last changelog tag
        try:
            # Try exact match first
            last_tag_index = all_tags.index(last_changelog_tag)
        except ValueError:
            # Try without 'v' prefix
            alt_tag = last_changelog_tag.lstrip("v") if last_changelog_tag.startswith("v") else f"v{last_changelog_tag}"
            try:
                last_tag_index = all_tags.index(alt_tag)
                last_changelog_tag = alt_tag
            except ValueError:
                logger.warning(f"Tag {last_changelog_tag} not found in repository, considering all tags as new")
                return None, all_tags

        # Return tags that come after the last changelog tag
        new_tags = all_tags[last_tag_index + 1 :]

        logger.info(f"Last changelog tag: {last_changelog_tag}")
        logger.info(f"All tags: {all_tags}")
        logger.info(f"New tags found: {new_tags}")

        return last_changelog_tag, new_tags

    except Exception as e:
        logger.error(f"Failed to determine new tags: {e!s}")
        raise GitError(f"Failed to determine new tags: {e!s}") from e


def get_tag_date(tag_name: str) -> datetime | None:
    """Get the date when a tag was created."""
    try:
        repo = get_repo()
        tag = repo.tags[tag_name]
        return tag.commit.committed_datetime
    except Exception as e:
        logger.warning(f"Failed to get date for tag {tag_name}: {e}")
        return None


def generate_boundary_display_name(boundary: dict, mode: str) -> str:
    """Generate a human-readable display name for a boundary."""
    if mode == "tags":
        return boundary["identifier"]
    elif mode == "dates":
        date = boundary["date"]
        if isinstance(date, datetime):
            return date.strftime("%Y-%m-%d")
        return str(date)
    elif mode == "gaps":
        date = boundary["date"]
        timestamp = date.isoformat() if isinstance(date, datetime) else str(date)
        return f"Gap-{timestamp[:10]}"
    else:
        return boundary.get("identifier", str(boundary))


def generate_boundary_identifier(boundary: dict, mode: str) -> str:
    """Generate a unique identifier for a boundary."""
    if mode == "tags":
        return boundary["identifier"]
    elif mode == "dates":
        date = boundary["date"]
        if isinstance(date, datetime):
            return date.strftime("%Y-%m-%d")
        return str(date)
    elif mode == "gaps":
        return boundary["hash"]
    else:
        return boundary.get("identifier", boundary.get("hash", str(boundary)))


def get_latest_boundary(mode: str = "tags", **kwargs) -> dict | None:
    """Get the latest boundary based on the specified mode."""
    from kittylog.commit_analyzer import (
        get_commits_by_date_boundaries,
        get_commits_by_gap_boundaries,
    )

    if mode == "tags":
        latest_tag = get_latest_tag()
        if latest_tag:
            from kittylog.commit_analyzer import get_all_tags_with_dates

            tags_data = get_all_tags_with_dates()
            for tag_data in tags_data:
                if tag_data["identifier"] == latest_tag:
                    return tag_data
        return None
    elif mode == "dates":
        date_grouping = kwargs.get("date_grouping", "daily")
        boundaries = get_commits_by_date_boundaries(date_grouping=date_grouping)
        return boundaries[-1] if boundaries else None
    elif mode == "gaps":
        gap_threshold_hours = kwargs.get("gap_threshold_hours", 4.0)
        boundaries = get_commits_by_gap_boundaries(gap_threshold_hours=gap_threshold_hours)
        return boundaries[-1] if boundaries else None
    else:
        raise ValueError(f"Unsupported mode: {mode}")


def get_previous_boundary(boundary: dict, mode: str, **kwargs) -> dict | None:
    """Get the previous boundary before the given boundary."""
    from kittylog.commit_analyzer import (
        get_all_tags_with_dates,
        get_commits_by_date_boundaries,
        get_commits_by_gap_boundaries,
    )

    try:
        if mode == "tags":
            all_boundaries = get_all_tags_with_dates()
        elif mode == "dates":
            date_grouping = kwargs.get("date_grouping", "daily")
            all_boundaries = get_commits_by_date_boundaries(date_grouping=date_grouping)
        elif mode == "gaps":
            gap_threshold_hours = kwargs.get("gap_threshold_hours", 4.0)
            all_boundaries = get_commits_by_gap_boundaries(gap_threshold_hours=gap_threshold_hours)
        else:
            raise ValueError(f"Unsupported mode: {mode}")

        # Find the target boundary in the list
        target_index = None
        for i, b in enumerate(all_boundaries):
            if boundary["hash"] == b["hash"]:
                target_index = i
                break

        if target_index is None:
            # Target boundary not found in the list
            return None

        # Return the previous boundary if it exists
        if target_index > 0:
            return all_boundaries[target_index - 1]
        else:
            # This is the first boundary, so return None
            return None

    except Exception as e:
        logger.debug(
            f"Could not determine previous boundary for {boundary.get('identifier', boundary.get('hash', 'unknown'))}: {e}"
        )
        return None


def get_all_boundaries(mode: str = "tags", **kwargs) -> list[dict]:
    """Get all boundaries based on the specified mode.

    Args:
        mode: Boundary detection mode ('tags', 'dates', or 'gaps')
        **kwargs: Additional parameters for specific modes
            - date_grouping: For 'dates' mode ('daily', 'weekly', 'monthly')
            - gap_threshold_hours: For 'gaps' mode (minimum gap in hours)

    Returns:
        List of boundary dictionaries
    """
    from kittylog.commit_analyzer import (
        get_all_tags_with_dates,
        get_commits_by_date_boundaries,
        get_commits_by_gap_boundaries,
    )

    if mode == "tags":
        return get_all_tags_with_dates()
    elif mode == "dates":
        date_grouping = kwargs.get("date_grouping", "daily")
        return get_commits_by_date_boundaries(date_grouping=date_grouping)
    elif mode == "gaps":
        gap_threshold_hours = kwargs.get("gap_threshold_hours", 4.0)
        return get_commits_by_gap_boundaries(gap_threshold_hours=gap_threshold_hours)
    else:
        raise ValueError(f"Unsupported mode: {mode}")


def clear_git_cache() -> None:
    """Clear all git operation caches.

    This is useful for testing or when the git repository state
    might have changed during execution.
    """
    get_repo.cache_clear()
    get_all_tags.cache_clear()
    get_latest_tag.cache_clear()
    get_current_commit_hash.cache_clear()
    # Also clear caches from the commit_analyzer module
    try:
        from kittylog.commit_analyzer import clear_commit_analyzer_cache

        clear_commit_analyzer_cache()
    except ImportError:
        pass
