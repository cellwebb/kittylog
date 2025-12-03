"""Commit analysis operations for kittylog.

This module handles commit analysis, diff operations, and boundary detection
based on commit patterns and time gaps.
"""

import logging
from datetime import timedelta

import git
from git import InvalidGitRepositoryError, Repo

from kittylog.cache import cached
from kittylog.errors import GitError
from kittylog.utils import run_subprocess

logger = logging.getLogger(__name__)


@cached
def get_repo() -> Repo:
    """Get the Git repository object for the current directory.

    This function is cached to avoid repeated initialization overhead
    during a single execution.
    """
    try:
        return Repo(".", search_parent_directories=True)
    except InvalidGitRepositoryError as e:
        raise GitError("Not in a git repository") from e


@cached
def get_all_commits_chronological() -> list[dict]:
    """Get all commits in chronological order with metadata.

    Returns:
        List of commit dictionaries with hash, message, author, date, and files.
    """
    try:
        repo = get_repo()
        commits = []

        # Get all commits in chronological order (oldest first)
        for commit in repo.iter_commits(repo.active_branch):
            commit_info = {
                "hash": commit.hexsha,
                "short_hash": commit.hexsha[:8],
                "message": commit.message.strip(),
                "author": str(commit.author),
                "date": commit.committed_datetime,
                "summary": commit.summary,
                "files": [
                    item.a_path
                    for item in commit.diff(commit.parents[0] if commit.parents else None, create_patch=False)
                ],
            }
            commits.append(commit_info)

        # Reverse to get chronological order (oldest first)
        commits.reverse()

        logger.debug(f"Found {len(commits)} commits in chronological order")
        return commits

    except (InvalidGitRepositoryError, git.GitCommandError, git.GitError) as e:
        logger.error(f"Failed to get commits: {e!s}")
        raise GitError(f"Failed to get commits: {e!s}") from e
    except Exception as e:
        logger.error(f"Unexpected error getting commits: {e!s}")
        raise GitError(f"Unexpected error getting commits: {e!s}") from e


@cached
def get_all_tags_with_dates() -> list[dict]:
    """Get all tags with their commit information and dates.

    Returns:
        List of tag dictionaries with identifier, hash, date, and commit info.
    """
    try:
        repo = get_repo()
        tags = []

        for tag in repo.tags:
            try:
                tag_info = {
                    "identifier": tag.name,
                    "hash": tag.commit.hexsha,
                    "short_hash": tag.commit.hexsha[:8],
                    "date": tag.commit.committed_datetime,
                    "message": tag.commit.message.strip(),
                    "author": str(tag.commit.author),
                    "summary": tag.commit.summary,
                }
                tags.append(tag_info)
            except Exception as e:
                logger.warning(f"Failed to process tag {tag.name}: {e}")
                continue

        # Sort tags by commit date
        tags.sort(key=lambda t: t["date"])  # type: ignore[arg-type, return-value]  # Dict values are datetime objects, mypy can't infer this

        logger.debug(f"Found {len(tags)} tags with dates")
        return tags

    except (InvalidGitRepositoryError, git.GitCommandError, git.GitError) as e:
        logger.error(f"Failed to get tags with dates: {e!s}")
        raise GitError(f"Failed to get tags with dates: {e!s}") from e
    except Exception as e:
        logger.error(f"Unexpected error getting tags: {e!s}")
        raise GitError(f"Unexpected error getting tags: {e!s}") from e


def get_commits_by_date_boundaries(date_grouping: str = "daily") -> list[dict]:
    """Get commit boundaries based on date grouping.

    Args:
        date_grouping: How to group commits by date ('daily', 'weekly', 'monthly')

    Returns:
        List of boundary commit dictionaries with additional 'boundary_type' field
    """
    commits = get_all_commits_chronological()
    if not commits:
        return []

    # Group commits by date
    grouped_commits: dict = {}
    for commit in commits:
        commit_date = commit["date"]

        if date_grouping == "daily":
            group_key = commit_date.date()
        elif date_grouping == "weekly":
            # Use ISO week (Monday start)
            week_start = commit_date - timedelta(days=commit_date.weekday())
            group_key = week_start.date()
        elif date_grouping == "monthly":
            group_key = commit_date.replace(day=1).date()
        else:
            raise ValueError(f"Unsupported date grouping: {date_grouping}")

        if group_key not in grouped_commits:
            grouped_commits[group_key] = []
        grouped_commits[group_key].append(commit)

    # Create boundaries (take the last commit of each group)
    boundaries = []
    for _group_date, group_commits in sorted(grouped_commits.items()):
        boundary_commit = group_commits[-1]  # Last commit in the group
        boundary_commit["boundary_type"] = "date"
        boundaries.append(boundary_commit)

    logger.debug(f"Found {len(boundaries)} date-based boundaries with {date_grouping} grouping")
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

        logger.debug(f"Getting commits for range: {rev_range}")

        commits = []
        for commit in repo.iter_commits(rev_range):
            try:
                # Determine parent commits for diff
                parent_commits = list(commit.parents)
                if parent_commits:
                    changed_files = [item.a_path for item in commit.diff(parent_commits[0], create_patch=False)]
                else:
                    # Initial commit has no parents
                    changed_files = [item.a_path for item in commit.diff(git.NULL_TREE, create_patch=False)]

                commit_info = {
                    "hash": commit.hexsha,
                    "short_hash": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": commit.committed_datetime,
                    "summary": commit.summary,
                    "files": changed_files,
                }
                commits.append(commit_info)
            except Exception as e:
                logger.warning(f"Failed to process commit {commit.hexsha}: {e}")
                continue

        logger.debug(f"Found {len(commits)} commits between {from_tag or 'beginning'} and {to_tag or 'HEAD'}")
        return commits

    except Exception as e:
        logger.error(f"Failed to get commits between tags: {e!s}")
        raise GitError(f"Failed to get commits between tags: {e!s}") from e


def get_commits_between_boundaries(from_boundary: dict | None, to_boundary: dict | None, mode: str) -> list[dict]:
    """Get commits between two boundaries based on the specified mode.

    Args:
        from_boundary: Starting boundary dict (exclusive). If None, starts from beginning.
        to_boundary: Ending boundary dict (inclusive). If None, goes to HEAD.
        mode: Boundary detection mode ('tags', 'dates', or 'gaps')

    Returns:
        List of commit dictionaries
    """
    try:
        if mode == "tags":
            from_tag = from_boundary["identifier"] if from_boundary else None
            to_tag = to_boundary["identifier"] if to_boundary else None
            return get_commits_between_tags(from_tag, to_tag)
        elif mode == "dates":
            # For date and gap modes, use commit hashes directly
            from_hash = from_boundary["hash"] if from_boundary else None
            to_hash = to_boundary["hash"] if to_boundary else None
            return get_commits_between_hashes(from_hash, to_hash)
        elif mode == "gaps":
            from_hash = from_boundary["hash"] if from_boundary else None
            to_hash = to_boundary["hash"] if to_boundary else None
            return get_commits_between_hashes(from_hash, to_hash)
        else:
            raise ValueError(f"Unsupported mode: {mode}")

    except Exception as e:
        logger.error(f"Failed to get commits between boundaries: {e!s}")
        raise GitError(f"Failed to get commits between boundaries: {e!s}") from e


def get_commits_between_hashes(from_hash: str | None, to_hash: str | None) -> list[dict]:
    """Get commits between two commit hashes.

    Args:
        from_hash: Starting commit hash (exclusive). If None, starts from beginning.
        to_hash: Ending commit hash (inclusive). If None, goes to HEAD.

    Returns:
        List of commit dictionaries
    """
    try:
        repo = get_repo()

        # Build revision range
        if from_hash and to_hash:
            rev_range = f"{from_hash}..{to_hash}"
        elif from_hash:
            rev_range = f"{from_hash}..HEAD"
        elif to_hash:
            rev_range = to_hash
        else:
            rev_range = "HEAD"

        logger.debug(f"Getting commits for hash range: {rev_range}")

        commits = []
        for commit in repo.iter_commits(rev_range):
            try:
                parent_commits = list(commit.parents)
                if parent_commits:
                    changed_files = [item.a_path for item in commit.diff(parent_commits[0], create_patch=False)]
                else:
                    changed_files = [item.a_path for item in commit.diff(git.NULL_TREE, create_patch=False)]

                commit_info = {
                    "hash": commit.hexsha,
                    "short_hash": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": commit.committed_datetime,
                    "summary": commit.summary,
                    "files": changed_files,
                }
                commits.append(commit_info)
            except Exception as e:
                logger.warning(f"Failed to process commit {commit.hexsha}: {e}")
                continue

        logger.debug(f"Found {len(commits)} commits for hash range")
        return commits

    except Exception as e:
        logger.error(f"Failed to get commits between hashes: {e!s}")
        raise GitError(f"Failed to get commits between hashes: {e!s}") from e


def get_git_diff(from_hash: str | None = None, to_hash: str | None = "HEAD", max_lines: int = 500) -> str:
    """Get git diff between two commits with optional truncation.

    Args:
        from_hash: Starting commit hash. If None, uses the parent of to_hash.
        to_hash: Ending commit hash. Defaults to HEAD.
        max_lines: Maximum number of lines to include in the diff

    Returns:
        The git diff output, possibly truncated if too long
    """
    try:
        rev_range = f"{from_hash}..{to_hash}" if from_hash else f"HEAD^1..{to_hash}"

        # Use git command for better compatibility and speed
        diff_cmd = ["git", "diff", rev_range]
        try:
            diff_output = run_subprocess(diff_cmd)
            diff_content = diff_output.strip()
        except Exception:
            # Fallback to repository object
            repo = get_repo()
            if from_hash:
                from_commit = repo.commit(from_hash)
                to_commit = repo.commit(to_hash)
                diff_content = repo.git.diff(from_commit, to_commit)
            else:
                # Diff of the last commit
                diff_content = repo.git.diff("HEAD^1", "HEAD")

        # Truncate if too long
        if diff_content and len(diff_content.splitlines()) > max_lines:
            lines = diff_content.splitlines()
            truncated = lines[:max_lines]
            diff_content = "\n".join(truncated) + f"\n\n... (diff truncated to {max_lines} lines)"

        logger.debug(f"Generated diff with {len(diff_content or '')} characters")
        return diff_content or ""

    except Exception as e:
        logger.warning(f"Failed to get git diff: {e}")
        return ""


def clear_commit_analyzer_cache() -> None:
    """Clear all commit analyzer caches."""
    get_repo.cache_clear()
    get_all_commits_chronological.cache_clear()
    # Clear get_all_tags_with_dates cache if it exists
    if hasattr(get_all_tags_with_dates, "cache_clear"):
        get_all_tags_with_dates.cache_clear()
