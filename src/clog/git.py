"""Git operations for changelog-updater.

This module provides Git operations specifically focused on tag-based changelog generation.
It extends the concepts from gac but focuses on tag operations and commit history.
"""

import logging
import re
from datetime import datetime

import git
from git import InvalidGitRepositoryError, Repo

from clog.errors import GitError
from clog.utils import run_subprocess

logger = logging.getLogger(__name__)


def get_repo() -> Repo:
    """Get the Git repository object for the current directory."""
    try:
        return Repo(".", search_parent_directories=True)
    except InvalidGitRepositoryError as e:
        raise GitError("Not in a git repository") from e


def get_all_tags() -> list[str]:
    """Get all git tags sorted by semantic version if possible, otherwise by creation date."""
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
        print(f"DEBUG: All tags: {tag_names}")

        return tag_names
    except Exception as e:
        logger.error(f"Failed to get tags: {str(e)}")
        raise GitError(f"Failed to get tags: {str(e)}") from e


def get_latest_tag() -> str | None:
    """Get the most recent tag."""
    tags = get_all_tags()
    return tags[-1] if tags else None


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
                    "date": datetime.fromtimestamp(commit.committed_date),
                    "files": changed_files,
                }
            )

        return commits
    except Exception as e:
        logger.error(f"Failed to get commits between tags: {str(e)}")
        # Return empty list instead of raising exception
        return []


def get_tags_since_last_changelog(changelog_file: str = "CHANGELOG.md") -> tuple[str | None, list[str]]:
    """Get tags that have been created since the last changelog update.

    Args:
        changelog_file: Path to the changelog file

    Returns:
        Tuple of (last_tag_in_changelog, new_tags_list)
    """
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
        print(f"DEBUG: Last changelog tag: {last_changelog_tag}")
        print(f"DEBUG: All tags: {all_tags}")
        print(f"DEBUG: New tags found: {new_tags}")

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


def run_git_command(args: list[str], silent: bool = False, timeout: int = 30) -> str:
    """Run a git command and return the output."""
    command = ["git"] + args
    return run_subprocess(command, silent=silent, timeout=timeout, raise_on_error=False, strip_output=True)
