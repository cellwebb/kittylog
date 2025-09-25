"""Git operations for kittylog.

This module provides Git operations for changelog generation using various boundary detection methods.
It extends the concepts from gac but supports tag-based, date-based, and gap-based commit grouping.
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import git
from git import InvalidGitRepositoryError, Repo

from kittylog.errors import GitError
from kittylog.utils import run_subprocess

logger = logging.getLogger(__name__)


def clear_git_cache() -> None:
    """Clear all git operation caches.

    This is useful for testing or when the git repository state
    might have changed during execution.
    """
    get_repo.cache_clear()
    get_all_tags.cache_clear()
    get_current_commit_hash.cache_clear()


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
        logger.error(f"Failed to get tags: {str(e)}")
        raise GitError(f"Failed to get tags: {str(e)}") from e


def get_all_commits_chronological() -> list[dict]:
    """Get all git commits sorted chronologically by commit date.

    Returns:
        List of commit dictionaries with hash, message, author, date, and files.
    """
    try:
        repo = get_repo()
        commits = []

        # Get all commits in reverse chronological order (latest first)
        # then reverse the list to get chronological order (oldest first)
        commit_iter = repo.iter_commits("--all", reverse=True)

        for commit in commit_iter:
            # Get changed files for this commit
            changed_files = []
            try:
                if commit.parents:
                    # Compare with first parent to get changed files
                    diff = commit.parents[0].diff(commit)
                    changed_files = [item.a_path or item.b_path for item in diff]
                else:
                    # Initial commit - all files are new
                    changed_files = [str(key) for key in commit.stats.files.keys()]
            except Exception as e:
                logger.debug(f"Could not get changed files for commit {commit.hexsha[:8]}: {e}")

            commits.append(
                {
                    "hash": commit.hexsha,
                    "short_hash": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": datetime.fromtimestamp(commit.committed_date, tz=timezone.utc),
                    "files": changed_files,
                }
            )

        logger.debug(f"Retrieved {len(commits)} commits in chronological order")
        return commits
    except Exception as e:
        logger.error(f"Failed to get commits chronologically: {str(e)}")
        raise GitError(f"Failed to get commits chronologically: {str(e)}") from e


def get_commits_by_date_boundaries(grouping: str = "daily") -> list[dict]:
    """Get commit boundaries based on calendar dates.

    Args:
        grouping: How to group commits ('daily', 'weekly', or 'monthly')

    Returns:
        List of boundary commit dictionaries with additional 'boundary_type' field
    """
    commits = get_all_commits_chronological()
    if not commits:
        return []

    boundaries = []
    current_date = None
    commits_per_day = {}  # Track commits per day for activity analysis

    for commit in commits:
        commit_date = commit["date"]  # This is always a UTC datetime from get_all_commits_chronological
        daily_date = commit_date.date()

        # Track daily activity for warnings
        commits_per_day[daily_date] = commits_per_day.get(daily_date, 0) + 1

        # Apply grouping logic (using UTC dates for consistency across timezones)
        if grouping == "daily":
            boundary_date = commit_date.date()
        elif grouping == "weekly":
            # Get the Monday of the week for this commit
            boundary_date = commit_date.date() - timedelta(days=commit_date.weekday())
        elif grouping == "monthly":
            # Get the first day of the month for this commit
            boundary_date = commit_date.date().replace(day=1)
        else:
            raise ValueError(f"Invalid grouping option: {grouping}")

        # If this is the first commit of a new date group, mark it as a boundary
        if current_date != boundary_date:
            current_date = boundary_date
            commit["boundary_type"] = "date"
            boundaries.append(commit)

    logger.debug(f"Found {len(boundaries)} date boundaries with {grouping} grouping")

    # Warn about potentially too many boundaries for very active repos
    if grouping == "daily" and len(boundaries) > 50:
        logger.warning(
            f"Found {len(boundaries)} daily boundaries. Consider using --date-grouping weekly/monthly for large repositories."
        )
    elif grouping == "weekly" and len(boundaries) > 100:
        logger.warning(
            f"Found {len(boundaries)} weekly boundaries. Consider using --date-grouping monthly for very large repositories."
        )

    # Warn about very active days that might benefit from gap-based grouping
    if grouping == "daily":
        max_commits_per_day = max(commits_per_day.values()) if commits_per_day else 0
        high_activity_days = [date for date, count in commits_per_day.items() if count > 10]

        if max_commits_per_day > 20:
            logger.warning(
                f"Repository has very active days with up to {max_commits_per_day} commits per day. Consider --grouping-mode gaps for activity-based grouping."
            )
        elif len(high_activity_days) > len(commits_per_day) * 0.3:  # More than 30% of days are high activity
            logger.info(
                f"Repository has {len(high_activity_days)} high-activity days (>10 commits). Consider --grouping-mode gaps or --date-grouping weekly."
            )

    return boundaries


def get_commits_by_gap_boundaries(gap_threshold_hours: float = 4.0) -> list[dict]:
    """Get commit boundaries based on time gaps between commits.

    Args:
        gap_threshold_hours: Minimum gap in hours to consider a boundary

    Returns:
        List of boundary commit dictionaries with additional 'boundary_type' field
    """
    commits = get_all_commits_chronological()
    if len(commits) < 2:
        # If 0 or 1 commits, all are boundaries
        for commit in commits:
            commit["boundary_type"] = "gap"
        return commits

    # Add boundary_type to all commits first
    for commit in commits:
        commit["boundary_type"] = "gap"

    # Calculate all gaps for statistical analysis
    gaps = []
    for i in range(1, len(commits)):
        time_gap_hours = (commits[i]["date"] - commits[i - 1]["date"]).total_seconds() / 3600
        gaps.append(time_gap_hours)

    # Analyze commit patterns for irregular repositories
    if gaps:
        avg_gap = sum(gaps) / len(gaps)
        max_gap = max(gaps)

        # Detect irregular patterns and provide suggestions
        gap_variance = sum((gap - avg_gap) ** 2 for gap in gaps) / len(gaps)
        gap_std_dev = gap_variance**0.5

        if gap_std_dev > avg_gap * 2:  # High variability
            logger.info(
                f"Repository has irregular commit patterns (std dev: {gap_std_dev:.1f}h vs avg: {avg_gap:.1f}h). Gap-based grouping may work well."
            )

        if max_gap > gap_threshold_hours * 10:  # Very long gaps detected
            logger.info(
                f"Repository has very long gaps (max: {max_gap:.1f}h). Consider increasing --gap-threshold or using --date-grouping monthly."
            )

        if avg_gap < gap_threshold_hours * 0.1:  # Very frequent commits
            logger.info(
                f"Repository has very frequent commits (avg gap: {avg_gap:.2f}h). Consider decreasing --gap-threshold or using --date-grouping daily."
            )

    boundaries = [commits[0]]  # First commit is always a boundary
    gap_threshold_seconds = gap_threshold_hours * 3600

    for i in range(1, len(commits)):
        current_commit = commits[i]
        previous_commit = commits[i - 1]

        # Calculate time gap between commits
        time_gap = (current_commit["date"] - previous_commit["date"]).total_seconds()

        # If gap exceeds threshold, mark current commit as boundary
        if time_gap > gap_threshold_seconds:
            boundaries.append(current_commit)

    logger.debug(f"Found {len(boundaries)} gap boundaries with {gap_threshold_hours} hour threshold")
    return boundaries


def get_all_boundaries(mode: str = "tags", **kwargs) -> list[dict]:
    """Get all boundaries based on the specified mode.

    Args:
        mode: Boundary detection mode ('tags', 'dates', or 'gaps')
        **kwargs: Additional parameters for specific modes
            - date_grouping: For 'dates' mode ('daily', 'weekly', 'monthly')
            - gap_threshold_hours: For 'gaps' mode (minimum gap in hours)

    Returns:
        List of boundary dictionaries with consistent format
    """
    if mode == "tags":
        tag_names = get_all_tags()
        boundaries: list[dict] = []
        repo = get_repo()
        for tag_name in tag_names:
            tag = repo.tags[tag_name]
            boundaries.append(
                {
                    "hash": tag.commit.hexsha,
                    "short_hash": tag.commit.hexsha[:8],
                    "message": tag.commit.message.strip(),
                    "author": str(tag.commit.author),
                    "date": datetime.fromtimestamp(tag.commit.committed_date),
                    "files": [],  # We don't track files for tags
                    "boundary_type": "tag",
                    "identifier": tag_name,
                }
            )
        return boundaries
    elif mode == "dates":
        return get_commits_by_date_boundaries(kwargs.get("date_grouping", "daily"))
    elif mode == "gaps":
        return get_commits_by_gap_boundaries(kwargs.get("gap_threshold_hours", 4.0))
    else:
        raise ValueError(f"Invalid mode: {mode}")


def get_latest_tag() -> str | None:
    """Get the most recent tag."""
    tags = get_all_tags()
    return tags[-1] if tags else None


def get_latest_boundary(mode: str) -> dict | None:
    """Get the most recent boundary based on mode.

    Args:
        mode: Boundary detection mode

    Returns:
        The latest boundary dictionary, or None if no boundaries exist
    """
    boundaries = get_all_boundaries(mode)
    return boundaries[-1] if boundaries else None


def get_previous_tag(target_tag: str) -> str | None:
    """Get the tag that comes before the target tag in version order.

    Args:
        target_tag: The tag to find the predecessor for

    Returns:
        The previous tag name, or None if target_tag is the first tag
    """
    try:
        # Handle case where target_tag is None or doesn't have lstrip method
        if target_tag is None:
            return None

        all_tags = get_all_tags()
        if not all_tags:
            return None

        # Find the index of the target tag
        try:
            target_index = all_tags.index(target_tag)
        except ValueError:
            # If exact match not found, try with 'v' prefix variations
            target_tag_str = str(target_tag)  # Convert to string to ensure it has lstrip method
            if target_tag_str.startswith("v"):
                alt_tag = target_tag_str.lstrip("v")
            else:
                alt_tag = f"v{target_tag_str}"

            try:
                target_index = all_tags.index(alt_tag)
                target_tag = alt_tag  # Use the matching tag name
            except ValueError:
                # Target tag not found in the list
                return None

        # Return the previous tag if it exists
        if target_index > 0:
            return all_tags[target_index - 1]
        else:
            # This is the first tag, so start from beginning of history
            return None

    except Exception as e:
        logger.debug(f"Could not determine previous tag for {target_tag}: {e}")
        return None


def get_previous_boundary(target_boundary: dict, mode: str) -> dict | None:
    """Get the boundary that comes before the target boundary.

    Args:
        target_boundary: The boundary to find the predecessor for
        mode: Boundary detection mode

    Returns:
        The previous boundary dictionary, or None if target_boundary is the first
    """
    try:
        all_boundaries = get_all_boundaries(mode)
        if not all_boundaries:
            return None

        # Find the index of the target boundary
        target_index = None
        for i, boundary in enumerate(all_boundaries):
            if boundary["hash"] == target_boundary["hash"]:
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
            f"Could not determine previous boundary for {target_boundary.get('identifier', target_boundary.get('hash', 'unknown'))}: {e}"
        )
        return None


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
        logger.error(f"Failed to get current commit hash: {str(e)}")
        raise GitError(f"Failed to get current commit hash: {str(e)}") from e


def is_current_commit_tagged() -> bool:
    """Check if the current commit (HEAD) has a tag pointing to it.

    Returns:
        True if HEAD is tagged, False otherwise.
    """
    try:
        repo = get_repo()
        current_commit = get_current_commit_hash()

        # Check if any tag points to the current commit
        for tag in repo.tags:
            if tag.commit.hexsha == current_commit:
                return True
        return False
    except Exception as e:
        logger.error(f"Failed to check if current commit is tagged: {str(e)}")
        return False


def get_commits_between_tags(from_tag: str | None, to_tag: str | None) -> list[dict]:
    """Get commits between two tags or from a tag to HEAD.

    Args:
        from_tag: Starting tag (exclusive). If None, starts from beginning of history.
        to_tag: Ending tag (inclusive). If None, goes to HEAD.

    Returns:
        List of commit dictionaries with hash, message, author, date, and files.
    """
    try:
        repo = get_repo()

        # Build revision range
        if from_tag and to_tag:
            rev_range = f"{from_tag}..{to_tag}"
        elif from_tag:
            rev_range = f"{from_tag}..HEAD"
        elif to_tag:
            # From beginning to specific tag
            rev_range = to_tag
        else:
            # All commits
            rev_range = "HEAD"

        commits = []
        try:
            commit_iter = repo.iter_commits(rev_range)
        except git.exc.GitCommandError as e:
            if from_tag and ("unknown revision" in str(e).lower() or "bad revision" in str(e).lower()):
                logger.warning(f"Tag '{from_tag}' not found, using full history")
                commit_iter = repo.iter_commits("HEAD")
            else:
                raise

        for commit in commit_iter:
            # Get changed files for this commit
            changed_files = []
            try:
                if commit.parents:
                    # Compare with first parent to get changed files
                    diff = commit.parents[0].diff(commit)
                    changed_files = [item.a_path or item.b_path for item in diff]
                else:
                    # Initial commit - all files are new
                    changed_files = [str(key) for key in commit.stats.files.keys()]
            except Exception as e:
                logger.debug(f"Could not get changed files for commit {commit.hexsha[:8]}: {e}")

            commits.append(
                {
                    "hash": commit.hexsha,
                    "short_hash": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": datetime.fromtimestamp(commit.committed_date, tz=timezone.utc),
                    "files": changed_files,
                }
            )

        return commits
    except Exception as e:
        logger.error(f"Failed to get commits between tags: {str(e)}")
        # Return empty list instead of raising exception
        return []


def get_commits_between_boundaries(from_boundary: dict | None, to_boundary: dict | None, mode: str) -> list[dict]:
    """Get commits between two boundaries regardless of boundary type.

    Args:
        from_boundary: Starting boundary (exclusive). If None, starts from beginning of history.
        to_boundary: Ending boundary (inclusive). If None, goes to HEAD.
        mode: Boundary detection mode for context

    Returns:
        List of commit dictionaries with hash, message, author, date, and files.
    """
    try:
        repo = get_repo()

        # Determine the revision range based on boundary types
        if from_boundary and to_boundary:
            rev_range = f"{from_boundary['hash']}..{to_boundary['hash']}"
        elif from_boundary:
            rev_range = f"{from_boundary['hash']}..HEAD"
        elif to_boundary:
            # From beginning to specific boundary
            rev_range = to_boundary["hash"]
        else:
            # All commits
            rev_range = "HEAD"

        commits = []
        try:
            commit_iter = repo.iter_commits(rev_range)
        except git.exc.GitCommandError as e:
            if from_boundary and ("unknown revision" in str(e).lower() or "bad revision" in str(e).lower()):
                logger.warning(
                    f"Boundary {from_boundary.get('identifier', from_boundary.get('hash', 'unknown'))} not found, using full history"
                )
                commit_iter = repo.iter_commits("HEAD")
            else:
                raise

        for commit in commit_iter:
            # Get changed files for this commit
            changed_files = []
            try:
                if commit.parents:
                    # Compare with first parent to get changed files
                    diff = commit.parents[0].diff(commit)
                    changed_files = [item.a_path or item.b_path for item in diff]
                else:
                    # Initial commit - all files are new
                    changed_files = [str(key) for key in commit.stats.files.keys()]
            except Exception as e:
                logger.debug(f"Could not get changed files for commit {commit.hexsha[:8]}: {e}")

            commits.append(
                {
                    "hash": commit.hexsha,
                    "short_hash": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": datetime.fromtimestamp(commit.committed_date, tz=timezone.utc),
                    "files": changed_files,
                }
            )

        return commits
    except Exception as e:
        logger.error(f"Failed to get commits between boundaries: {str(e)}")
        # Return empty list instead of raising exception
        return []


def get_tags_since_last_changelog(changelog_file: str = "CHANGELOG.md") -> tuple[str | None, list[str]]:
    """Get tags that have been created since the last changelog update.

    Args:
        changelog_file: Path to the changelog file

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
            with open(changelog_file, encoding="utf-8") as f:
                content = f.read()

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
        logger.error(f"Failed to determine new tags: {str(e)}")
        raise GitError(f"Failed to determine new tags: {str(e)}") from e


def get_tag_date(tag_name: str) -> datetime | None:
    """Get the date when a tag was created."""
    try:
        repo = get_repo()
        tag = repo.tags[tag_name]
        return datetime.fromtimestamp(tag.commit.committed_date)
    except Exception as e:
        logger.debug(f"Could not get date for tag {tag_name}: {e}")
        return None


def generate_boundary_identifier(boundary: dict, mode: str) -> str:
    """Generate a consistent identifier for a boundary.

    Args:
        boundary: Boundary dictionary
        mode: Boundary detection mode

    Returns:
        Formatted boundary identifier string
    """
    if mode == "tags":
        return boundary.get("identifier", boundary["hash"][:8])
    elif mode == "dates":
        return boundary["date"].strftime("%Y-%m-%d")
    elif mode == "gaps":
        return f"{boundary['date'].strftime('%Y-%m-%d')}-{boundary['short_hash']}"
    else:
        raise ValueError(f"Invalid mode: {mode}")


def generate_boundary_display_name(boundary: dict, mode: str) -> str:
    """Generate a user-friendly display name for a boundary.

    Args:
        boundary: Boundary dictionary
        mode: Boundary detection mode

    Returns:
        Formatted boundary display name string
    """
    if mode == "tags":
        return boundary.get("identifier", boundary["hash"][:8])
    elif mode == "dates":
        return f"[{boundary['date'].strftime('%Y-%m-%d')}] - {boundary['date'].strftime('%B %d, %Y')}"
    elif mode == "gaps":
        return f"[Gap-{boundary['date'].strftime('%Y-%m-%d')}] - Development session"
    else:
        raise ValueError(f"Invalid mode: {mode}")


def run_git_command(args: list[str], silent: bool = False, timeout: int = 30) -> str:
    """Run a git command and return the output."""
    command = ["git"] + args
    return run_subprocess(command, silent=silent, timeout=timeout, raise_on_error=False, strip_output=True)


def get_git_diff(from_tag: str | None, to_tag: str | None) -> str:
    """Get the git diff between two tags or from beginning to a tag.

    Args:
        from_tag: Starting tag (exclusive). If None, starts from beginning of history.
        to_tag: Ending tag (inclusive). If None, goes to HEAD.

    Returns:
        String containing the git diff output
    """
    try:
        # Build revision range for diff
        if from_tag and to_tag:
            rev_range = f"{from_tag}..{to_tag}"
        elif from_tag:
            rev_range = f"{from_tag}..HEAD"
        elif to_tag:
            # From beginning to specific tag
            rev_range = to_tag
        else:
            # All changes from beginning to HEAD
            rev_range = "HEAD"

        logger.debug(f"Getting git diff for range: {rev_range}")

        # Get the diff, excluding changelog files
        from kittylog.utils import get_changelog_file_patterns

        exclude_patterns = get_changelog_file_patterns()
        diff_command = ["diff", rev_range, "--", "."] + exclude_patterns
        diff_output = run_git_command(diff_command)
        return diff_output

    except Exception as e:
        logger.debug(f"Could not get git diff: {e}")
        return ""
