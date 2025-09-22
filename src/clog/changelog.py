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


def find_end_of_unreleased_section(lines: list[str], unreleased_start: int) -> int:
    """Find the end position of the [Unreleased] section content."""
    # Look for the next section header after the unreleased section
    # This could be either another version section or the end of file
    for i in range(unreleased_start + 1, len(lines)):
        # Check if this is a version section header
        if re.match(r"##\s*\[v?\d+\.\d+\.\d+", lines[i], re.IGNORECASE):
            return i

        # Check if this is a section header with bracketed content like [Unreleased] or [version]
        # but not just any markdown heading
        if re.match(r"##\s*\[.*\]", lines[i], re.IGNORECASE):
            # Additional check - make sure it's not the unreleased section we're looking for
            if not re.match(r"##\s*\[unreleased\]", lines[i], re.IGNORECASE):
                return i

    # If no next section found, return the end of file
    return len(lines)


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

    # For unreleased changes, we include the header UNLESS we're appending to an existing section
    if tag is None:
        # For unreleased changes, we still want the header when creating a new section
        entry = "## [Unreleased]\n\n"
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
    else:
        # For regular tags, include the header
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
    file_path: str | None = "CHANGELOG.md",
    existing_content: str | None = None,
    from_tag: str | None = None,
    to_tag: str | None = None,
    model: str = "",
    hint: str = "",
    show_prompt: bool = False,
    quiet: bool = False,
    replace_unreleased: bool = False,
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
        # Default to CHANGELOG.md if no file path provided
        changelog_path = file_path or "CHANGELOG.md"
        existing_content = read_changelog(changelog_path)

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
    # For unreleased changes, use "Unreleased" as the tag name
    tag_name = to_tag or "Unreleased"
    ai_content = generate_changelog_entry(
        commits=commits,
        tag=tag_name,
        from_tag=from_tag,
        model=model,
        hint=hint,
        show_prompt=show_prompt,
        quiet=quiet,
    )

    # Get tag date (None for unreleased changes)
    tag_date = get_tag_date(to_tag) if to_tag else None

    # Format the new entry
    new_entry = format_changelog_entry(tag_name, commits, ai_content, tag_date)

    # Find where to insert the new entry
    lines = existing_content.split("\n")

    # Special handling for unreleased changes when an unreleased section already exists
    if to_tag is None and find_unreleased_section(existing_content) is not None:
        # For unreleased changes with existing section, we don't want the header
        # Extract just the content part (skip the ## [Unreleased] header line)
        entry_lines = new_entry.strip().split("\n")
        if entry_lines and entry_lines[0].strip().startswith("## [Unreleased]"):
            content_to_append = "\n".join(entry_lines[1:])  # Skip the header line
        else:
            content_to_append = new_entry.strip()

        if replace_unreleased:
            # Replace mode: Remove existing content and insert new content

            # Find the start and end of the existing unreleased section
            unreleased_line = find_unreleased_section(existing_content)
            if unreleased_line is not None:
                end_line = find_end_of_unreleased_section(lines, unreleased_line)

                # In replace mode, we want to replace all content between the Unreleased header
                # and the next section header, but we need to be careful about removing
                # only the content and keeping appropriate structure

                # Find the first content line (skip empty lines after the header)
                start_content_line = unreleased_line + 1
                while start_content_line < len(lines) and not lines[start_content_line].strip():
                    start_content_line += 1
            else:
                # This shouldn't happen in replace mode, but handle gracefully
                end_line = len(lines)
                start_content_line = end_line

            # Replace the content between the Unreleased header and the next section
            # Keep the header line and replace everything after it until the next section
            lines = lines[:start_content_line] + content_to_append.split("\n") + lines[end_line:]
        else:
            # Append mode: Insert just the AI content at the end of the existing unreleased section
            insert_line = None

            # Find the end of the existing unreleased section (next ## heading or end of file)
            unreleased_line = find_unreleased_section(existing_content)
            if unreleased_line is not None:
                for i in range(unreleased_line + 1, len(lines)):
                    if lines[i].strip().startswith("##"):
                        insert_line = i
                        break

            # If no next section found, insert at end
            if insert_line is None:
                insert_line = len(lines)

            # Insert the AI content (without header) at the end of existing unreleased section
            lines.insert(insert_line, content_to_append.rstrip())
    else:
        # Standard insertion logic
        insert_line = find_insertion_point(existing_content)

        # Insert the new entry
        lines.insert(insert_line, new_entry.rstrip())

    # Join back together
    updated_content = "\n".join(lines)

    # Clean up any excessive blank lines
    updated_content = re.sub(r"\n{3,}", "\n\n", updated_content)

    # Remove empty [Unreleased] sections (only when there's no content between header and next section)
    # This regex looks for ## [Unreleased] followed by only whitespace until the next ## section
    updated_content = re.sub(r"##\s*\[Unreleased\]\s*\n(\s*\n)*(?=##\s*\[)", "", updated_content, flags=re.IGNORECASE)

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
