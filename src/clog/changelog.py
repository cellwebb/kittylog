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
from clog.git_operations import get_commits_between_tags, get_tag_date

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

    # Format new entries
    # For both tagged releases and unreleased changes, we use the same formatting function
    new_entry = format_changelog_entry(tag_name, commits, ai_content, tag_date)

    # Find where to insert the new entry
    lines = existing_content.split("\n")

    # Special handling for unreleased changes
    if to_tag is None:
        # For unreleased changes, we use the formatted new_entry
        unreleased_line = find_unreleased_section(existing_content)
        
        if unreleased_line is not None and not replace_unreleased:
            # Append mode: Deduplicate new AI entry with existing unreleased content
            end_line = find_end_of_unreleased_section(lines, unreleased_line)
            
            # Extract existing unreleased content (skip header and empty lines)
            existing_unreleased_content = []
            content_start_line = unreleased_line + 1
            while content_start_line < len(lines) and not lines[content_start_line].strip():
                content_start_line += 1
            
            # Collect all non-empty lines from existing unreleased section
            for i in range(content_start_line, end_line):
                if lines[i].strip():  # Only collect non-empty lines
                    existing_unreleased_content.append(lines[i])
            
            # Parse new AI content and deduplicate against existing content
            # First, split into sections to better manage the existing content
            new_content_sections = {}
            current_section = None
            
            for line in new_entry.split('\n'):
                stripped = line.strip()
                if stripped.startswith('### '):
                    current_section = stripped
                    new_content_sections[current_section] = []
                elif current_section and stripped:  # Only add non-empty lines to sections
                    new_content_sections[current_section].append(line)
            
            # Create sets for fast lookup of existing items
            existing_bullets_set = set()
            for line in existing_unreleased_content:
                stripped = line.strip()
                if stripped.startswith('- '):
                    # Add both the bullet and the text content for matching
                    bullet_text = stripped[2:].strip()  # Remove '- ' prefix
                    existing_bullets_set.add(stripped)
                    existing_bullets_set.add(bullet_text)
            
            # Parse new content and filter out duplicates
            unique_content_lines = []
            seen_sections = set([line.strip() for line in existing_unreleased_content if line.strip().startswith('### ')])
            
            # Collect all content lines (section headers and non-bullet content)
            all_new_content_lines = []
            for section_header, section_lines in new_content_sections.items():
                # Add section header if it doesn't already exist
                if section_header not in seen_sections:
                    all_new_content_lines.append(section_header)
                
                # Add all bullets and non-bullet content
                for line in section_lines:
                    if line.strip().startswith('- '):
                        # Check if bullet already exists
                        bullet_text = line.strip()[2:].strip()  # Remove '- ' prefix
                        if line.strip() not in existing_bullets_set and bullet_text not in existing_bullets_set:
                            all_new_content_lines.append(line)
                    elif line.strip():  # Non-empty non-bullet line
                        all_new_content_lines.append(line)
            
            # Find where to insert new content (at the end of the existing unreleased section)
            insert_point = end_line
            
            # Combine existing and new content with bullet limiting applied to each section
            # Parse existing content into sections
            existing_sections = {}
            current_section = None
            
            for line in existing_unreleased_content:
                stripped = line.strip()
                if stripped.startswith('### '):
                    current_section = stripped
                    if current_section not in existing_sections:
                        existing_sections[current_section] = []
                elif current_section:  # Collect all lines in the section
                    existing_sections[current_section].append(line)
            
            # Parse new AI content into sections
            new_sections = {}
            current_section = None
            
            for line in new_entry.split('\n'):
                stripped = line.strip()
                if stripped.startswith('### '):
                    current_section = stripped
                    if current_section not in new_sections:
                        new_sections[current_section] = []
                elif current_section:  # Collect all lines in the section
                    new_sections[current_section].append(line)
            
            # Combine existing and new content
            combined_content = "\n".join(existing_unreleased_content) + "\n" + new_entry
            combined_lines = [line for line in combined_content.split("\n") if line.strip()]
            
            # Apply bullet limiting to combined content
            limited_combined_lines = limit_bullets_in_sections(combined_lines)
            
            # Replace the unreleased section content
            del lines[content_start_line:end_line]
            
            # Insert limited content (in correct order)
            if limited_combined_lines:
                # Add a blank line before content if needed
                if content_start_line > unreleased_line + 1 and lines[content_start_line - 1].strip():
                    lines.insert(content_start_line, "")
                    content_start_line += 1
                    
                for line in limited_combined_lines:
                    lines.insert(content_start_line, line)
                    content_start_line += 1
        elif unreleased_line is not None and replace_unreleased:
            # Replace mode: Remove existing unreleased content and replace with new AI content
            end_line = find_end_of_unreleased_section(lines, unreleased_line)
            
            # Find where actual content starts in the existing section (skip empty lines after header)
            content_start_line = unreleased_line + 1
            while content_start_line < len(lines) and not lines[content_start_line].strip():
                content_start_line += 1
            
            # Replace the content between the Unreleased header and the next section
            # Remove existing content
            del lines[content_start_line:end_line]
            
            # Insert new content with bullet limiting
            new_entry_lines = [line for line in new_entry.split("\n") if line.strip()]
            limited_content_lines = limit_bullets_in_sections(new_entry_lines)
            
            for line in reversed(limited_content_lines):
                lines.insert(content_start_line, line)
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
        # Standard insertion logic for tagged versions
        insert_line = find_insertion_point(existing_content)
        
        # Insert the new entry with bullet limiting
        entry_lines = [line for line in new_entry.rstrip().split("\n") if line.strip()]
        limited_entry_lines = limit_bullets_in_sections(entry_lines)
        
        for line in reversed(limited_entry_lines):
            lines.insert(insert_line, line)

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