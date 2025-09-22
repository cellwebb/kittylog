"""Changelog operations for updating CHANGELOG.md files.

This module handles reading, parsing, and updating changelog files using AI-generated content
based on git commit history and tag information.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List

from clog.ai import generate_changelog_entry
from clog.git_operations import get_commits_between_tags, get_tag_date, get_git_diff

logger = logging.getLogger(__name__)


def limit_bullets_in_sections(content_lines: List[str], max_bullets: int = 6) -> List[str]:
    """Limit the number of bullet points in each section to a maximum count.

    Args:
        content_lines: List of content lines to process
        max_bullets: Maximum number of bullets per section (default 6)

    Returns:
        List of lines with bullet points limited per section
    """
    limited_lines = []
    current_section = None
    section_bullet_count = {}

    for line in content_lines:
        stripped_line = line.strip()

        # Handle section headers
        if stripped_line.startswith('### '):
            current_section = stripped_line
            section_bullet_count[current_section] = 0
            limited_lines.append(line)
        elif stripped_line.startswith('- ') and current_section:
            # Handle bullet points - limit to max_bullets per section
            if section_bullet_count.get(current_section, 0) < max_bullets:
                limited_lines.append(line)
                section_bullet_count[current_section] = section_bullet_count.get(current_section, 0) + 1
        else:
            limited_lines.append(line)

    return limited_lines


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
            logger.debug(f"Found unreleased section at line {i}: {line}")
            return i
    logger.debug("No unreleased section found")
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


def find_version_section(content: str, version: str) -> tuple[int | None, int | None]:
    """Find the position of a specific version section in the changelog.

    Args:
        content: The changelog content as a string
        version: The version to find (e.g., "0.1.0" or "v0.1.0")

    Returns:
        Tuple of (start_line_index, end_line_index) or (None, None) if not found
    """
    lines = content.split("\n")
    version_pattern = rf"##\s*\[\s*v?{re.escape(version.lstrip('v'))}\s*\]"

    # Look for the version section header
    start_line = None
    for i, line in enumerate(lines):
        if re.match(version_pattern, line, re.IGNORECASE):
            start_line = i
            break

    if start_line is None:
        return None, None

    # Look for the next section header after this version section
    for i in range(start_line + 1, len(lines)):
        # Check if this is any section header
        if re.match(r"##\s*\[.*\]", lines[i], re.IGNORECASE):
            return start_line, i

    # If no next section found, the end of this section is the end of file
    return start_line, len(lines)


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
    replace_unreleased: bool = True,
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
        replace_unreleased: Whether to replace or append unreleased content (default True)

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

    # Get git diff for better context
    diff_content = get_git_diff(from_tag, to_tag)

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
        diff_content=diff_content,
    )

    # Get tag date (None for unreleased changes)
    tag_date = get_tag_date(to_tag) if to_tag else None

    # Format new entries
    # For both tagged releases and unreleased changes, we use the same formatting function
    new_entry = format_changelog_entry(tag_name, commits, ai_content, tag_date)

    # Find where to insert the new entry
    lines = existing_content.split("\n")

    # For unreleased changes, handle the unreleased section
    if to_tag is None:
        # Find the unreleased section
        unreleased_line = find_unreleased_section(existing_content)

        if unreleased_line is not None:
            end_line = find_end_of_unreleased_section(lines, unreleased_line)

            # Find where actual content starts in the existing section (skip empty lines after header)
            content_start_line = unreleased_line + 1
            while content_start_line < len(lines) and not lines[content_start_line].strip():
                content_start_line += 1

            if replace_unreleased:
                # Replace mode: Remove existing content and insert new content
                # Replace the content between the Unreleased header and the next section
                # Remove existing content
                del lines[content_start_line:end_line]

                # Insert new content with bullet limiting
                new_entry_lines = [line for line in new_entry.split("\n") if line.strip()]
                limited_content_lines = limit_bullets_in_sections(new_entry_lines)

                for line in reversed(limited_content_lines):
                    lines.insert(content_start_line, line)
            else:
                # Append mode: Preserve existing content and append new AI content
                # Apply bullet limiting to new content only (don't affect existing content)
                new_entry_lines = [line for line in new_entry.split("\n") if line.strip()]

                # Remove the ## [Unreleased] header from new content since we're appending to existing section
                content_lines = []
                for line in new_entry_lines:
                    if not re.match(r"##\s*\[unreleased\]", line, re.IGNORECASE):
                        content_lines.append(line)

                # Apply bullet limiting to new content
                limited_new_entry_lines = limit_bullets_in_sections(content_lines)

                # Insert limited new content at the end of the existing unreleased section content
                insert_point = end_line
                for line in reversed(limited_new_entry_lines):
                    lines.insert(insert_point, line)
        else:
            # No existing unreleased section - create one with new entry
            insert_line = find_insertion_point(existing_content)

            # Insert new content with bullet limiting
            new_entry_lines = [line for line in new_entry.split("\n") if line.strip()]
            limited_content_lines = limit_bullets_in_sections(new_entry_lines)

            # Add a blank line before inserting if needed
            if insert_line > 0 and lines[insert_line - 1].strip():
                lines.insert(insert_line, "")
                insert_line += 1

            for line in reversed(limited_content_lines):
                lines.insert(insert_line, line)
    else:
        # For tagged versions, find and replace the existing version section
        version = tag_name.lstrip("v")
        start_line, end_line = find_version_section(existing_content, version)

        if start_line is not None:
            # Remove existing content for this version
            del lines[start_line:end_line]

            # Insert new content with bullet limiting at the same position
            entry_lines = [line for line in new_entry.rstrip().split("\n") if line.strip()]
            limited_entry_lines = limit_bullets_in_sections(entry_lines)

            for line in reversed(limited_entry_lines):
                lines.insert(start_line, line)
        else:
            # Version section not found, insert at appropriate position
            insert_line = find_insertion_point(existing_content)

            # Insert the new entry with bullet limiting
            entry_lines = [line for line in new_entry.rstrip().split("\n") if line.strip()]
            limited_entry_lines = limit_bullets_in_sections(entry_lines)

            for line in reversed(limited_entry_lines):
                lines.insert(insert_line, line)

    # Join back together
    updated_content = "\n".join(lines)

    # Clean up any excessive blank lines and ensure proper spacing
    updated_content = re.sub(r"\n{3,}", "\n\n", updated_content)

    # Ensure there's proper spacing between sections (two newlines between sections)
    updated_content = re.sub(r"(\S)\n(##\s*\[)", r"\1\n\n\2", updated_content)

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