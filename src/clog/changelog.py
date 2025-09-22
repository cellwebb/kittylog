"""Changelog operations for updating CHANGELOG.md files.

This module handles reading, parsing, and updating changelog files using AI-generated content
based on git commit history and tag information.
"""

import logging
import re
from datetime import datetime
from pathlib import Path

from clog.ai import generate_changelog_entry
from clog.git import get_commits_between_tags, get_tag_date

logger = logging.getLogger(__name__)


def read_changelog(file_path: str) -> str:
    """Read the contents of a changelog file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.info(f"Changelog file {file_path} not found, will create new one")
        return ""
    except Exception as e:
        logger.error(f"Error reading changelog file: {e}")
        raise


def find_unreleased_section(content: str) -> int | None:
    """Find the position of the [Unreleased] section in the changelog.

    Returns:
        The line index where the [Unreleased] section starts, or None if not found.
    """
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if re.match(r"##\s*\[unreleased\]", line, re.IGNORECASE):
            return i
    return None


def find_insertion_point(content: str) -> int:
    """Find where to insert new changelog entries.

    Returns:
        The line index where new entries should be inserted.
    """
    lines = content.split("\n")

    # Look for the first version section (## [version])
    for i, line in enumerate(lines):
        if re.match(r"##\s*\[v?\d+\.\d+\.\d+", line, re.IGNORECASE):
            return i

    # If no version sections found, look for the end of the header
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith("#") and "changelog" not in line.lower():
            return i

    # If nothing found, insert after the first non-empty line
    for i, line in enumerate(lines):
        if line.strip():
            return i + 1

    # Empty file, insert at the beginning
    return 0


def create_changelog_header() -> str:
    """Create a standard changelog header."""
    return """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

"""


def format_changelog_entry(tag: str, commits: list[dict], ai_content: str, tag_date: datetime | None = None) -> str:
    """Format a changelog entry for a specific tag.

    Args:
        tag: The version tag
        commits: List of commit dictionaries
        ai_content: AI-generated changelog content
        tag_date: Date the tag was created

    Returns:
        Formatted changelog entry as a string
    """
    # Clean up the tag name for display
    if tag is None:
        display_tag = "Unreleased"
    else:
        display_tag = tag.lstrip("v")

    # Format the date
    date_str = ""
    if tag_date and tag is not None:
        date_str = f" - {tag_date.strftime('%Y-%m-%d')}"

    # Start with the version header
    entry = f"## [{display_tag}]{date_str}\n\n"

    # Add the AI-generated content
    if ai_content.strip():
        entry += ai_content.strip() + "\n\n"
    else:
        # Fallback: create a simple list from commit messages
        entry += "### Changed\n\n"
        for commit in commits:
            # Get first line of commit message
            first_line = commit["message"].split("\n")[0].strip()
            entry += f"- {first_line}\n"
        entry += "\n"

    # Clean up excessive newlines at the end of the entry
    entry = entry.rstrip() + "\n\n"

    return entry


def update_changelog(
    file_path: str | None = None,
    existing_content: str | None = None,
    from_tag: str | None = None,
    to_tag: str | None = None,
    model: str = "",
    hint: str = "",
    show_prompt: bool = False,
    quiet: bool = False,
) -> str:
    """Update changelog with entries for new tags.

    Args:
        file_path: Path to the changelog file (used when existing_content is None)
        existing_content: Existing changelog content (takes precedence over file reading)
        from_tag: Starting tag (exclusive)
        to_tag: Ending tag (inclusive)
        model: AI model to use for generation
        hint: Additional context for AI
        show_prompt: Whether to show the prompt
        quiet: Whether to suppress output

    Returns:
        The updated changelog content
    """
    logger.info(f"Updating changelog from {from_tag or 'beginning'} to {to_tag}")

    # Read existing changelog if content wasn't provided
    if existing_content is None:
        existing_content = read_changelog(file_path)

    # If file is empty or very short, create header
    if len(existing_content.strip()) < 50:
        existing_content = create_changelog_header()

    # Get commits for this tag range
    commits = get_commits_between_tags(from_tag, to_tag)

    if not commits:
        logger.info(f"No commits found between {from_tag} and {to_tag}")
        return existing_content

    logger.info(f"Found {len(commits)} commits between {from_tag or 'beginning'} and {to_tag}")

    # Generate AI content for this version
    ai_content = generate_changelog_entry(
        commits=commits,
        tag=to_tag,
        from_tag=from_tag,
        model=model,
        hint=hint,
        show_prompt=show_prompt,
        quiet=quiet,
    )

    # Get tag date
    tag_date = get_tag_date(to_tag)

    # Format the new entry
    new_entry = format_changelog_entry(to_tag, commits, ai_content, tag_date)

    # Find where to insert the new entry
    lines = existing_content.split("\n")

    # Look for [Unreleased] section to insert after
    unreleased_line = find_unreleased_section(existing_content)
    if unreleased_line is not None:
        # Insert after the [Unreleased] section
        # Find the end of the unreleased section (next ## heading or end of file)
        insert_line = unreleased_line + 1
        for i in range(unreleased_line + 1, len(lines)):
            if lines[i].strip().startswith("##"):
                insert_line = i
                break
        else:
            # No next section found, insert at end
            insert_line = len(lines)
    else:
        # No [Unreleased] section, find the best insertion point
        insert_line = find_insertion_point(existing_content)

    # Insert the new entry
    lines.insert(insert_line, new_entry.rstrip())

    # Join back together
    updated_content = "\n".join(lines)

    # Clean up any excessive blank lines
    updated_content = re.sub(r"\n{3,}", "\n\n", updated_content)

    # Remove empty [Unreleased] sections
    updated_content = re.sub(r"##\s*\[Unreleased\]\s*\n\s*(?=##\s*\[)", "", updated_content, flags=re.IGNORECASE)

    # Ensure there's a space before each version section (after the first one)
    updated_content = re.sub(r"(\S)(\n##\s*\[)", r"\1\n\n\2", updated_content)

    return updated_content


def write_changelog(file_path: str, content: str) -> None:
    """Write content to a changelog file."""
    try:
        # Ensure the directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Updated changelog file: {file_path}")
    except Exception as e:
        logger.error(f"Error writing changelog file: {e}")
        raise


def preview_changelog_entry(tag: str, commits: list[dict], ai_content: str) -> str:
    """Generate a preview of what the changelog entry would look like."""
    tag_date = get_tag_date(tag)
    return format_changelog_entry(tag, commits, ai_content, tag_date)
