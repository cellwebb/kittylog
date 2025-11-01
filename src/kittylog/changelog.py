"""Changelog operations for updating CHANGELOG.md files.

This module handles reading, parsing, and updating changelog files using AI-generated content
based on git commit history and tag information.
"""

import logging
import re
from datetime import datetime
from pathlib import Path

from kittylog.ai import generate_changelog_entry
from kittylog.git_operations import get_commits_between_tags, get_git_diff, get_tag_date
from kittylog.postprocess import postprocess_changelog_content, remove_unreleased_sections

logger = logging.getLogger(__name__)


def limit_bullets_in_sections(content_lines: list[str], max_bullets: int = 6) -> list[str]:
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
        if stripped_line.startswith("### "):
            current_section = stripped_line
            section_bullet_count[current_section] = 0
            limited_lines.append(line)
        elif stripped_line.startswith("- ") and current_section:
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


def find_existing_boundaries(content: str) -> set[str]:
    """Find all existing boundaries in the changelog content.

    Args:
        content: The changelog content as a string

    Returns:
        Set of existing boundary identifiers (excluding 'unreleased')
    """
    existing_boundaries = set()
    lines = content.split("\n")

    for line in lines:
        # Match patterns like ## [0.1.0], ## [v0.1.0], ## [Unreleased], ## [2024-01-15], ## [Gap-2024-01-15], etc.
        # Handle nested brackets like ## [[2024-01-03] - January 03, 2024]
        match = re.match(r"##\s*\[+\s*([^\]]+)\s*\]+", line, re.IGNORECASE)
        if match:
            boundary_name = match.group(1).strip()
            if boundary_name.lower() != "unreleased":
                # Normalize boundary name by removing 'v' prefix if present
                normalized_boundary = boundary_name.lstrip("v")
                existing_boundaries.add(normalized_boundary)
            # Note: We don't add 'unreleased' to the set as it's not a version boundary

    logger.debug(f"Found existing boundaries: {existing_boundaries}")
    return existing_boundaries


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
            # Return the line index of the previous empty line if exists, otherwise return this line
            # Look back for empty lines between sections
            j = i - 1
            while j > unreleased_start and not lines[j].strip():
                j -= 1
            return j + 1

        # Check if this is a section header with bracketed content like [Unreleased] or [version]
        # but not just any markdown heading
        if re.match(r"##\s*\[.*\]", lines[i], re.IGNORECASE):
            # Additional check - make sure it's not the unreleased section we're looking for
            if not re.match(r"##\s*\[unreleased\]", lines[i], re.IGNORECASE):
                # Return the line index of the previous empty line if exists, otherwise return this line
                # Look back for empty lines between sections
                j = i - 1
                while j > unreleased_start and not lines[j].strip():
                    j -= 1
                return j + 1

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
        # Also check for other types of section headers that might appear in AI output
        if re.match(r"###\s+[A-Z][a-z]+", lines[i], re.IGNORECASE):
            # If we find a sub-section header, and we haven't found another version header yet,
            # continue looking for the real end of this version section
            continue

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


def find_insertion_point_by_version(content: str, new_version: str) -> int:
    """Find where to insert a new changelog entry based on semantic version ordering.

    Args:
        content: The existing changelog content
        new_version: The version to insert (e.g., "1.0.0" or "v1.0.0")

    Returns:
        The line index where the new entry should be inserted to maintain version order
    """
    lines = content.split("\n")

    def version_key(version_str: str) -> list[int | str]:
        """Extract version components for sorting."""
        # Remove 'v' prefix if present and any extra characters
        version_str = version_str.lstrip("v").strip()
        # Split by dots and convert to integers where possible
        parts: list[int | str] = []
        for part in version_str.split("."):
            try:
                # Handle pre-release versions like "1.0.0a1"
                if part.isdigit():
                    parts.append(int(part))
                else:
                    # Split alphanumeric parts (e.g., "0a1" -> [0, "a1"])
                    import re

                    numeric_match = re.match(r"^(\d+)", part)
                    if numeric_match:
                        parts.append(int(numeric_match.group(1)))
                        remainder = part[len(numeric_match.group(1)) :]
                        if remainder:
                            parts.append(remainder)
                    else:
                        parts.append(part)
            except ValueError:
                parts.append(part)
        return parts

    # Normalize the new version for comparison
    new_version_normalized = new_version.lstrip("v")
    new_version_key = version_key(new_version_normalized)

    # Find all version sections and their positions
    version_positions = []
    for i, line in enumerate(lines):
        match = re.match(r"##\s*\[\s*([^\]]+)\s*\]", line, re.IGNORECASE)
        if match:
            version_text = match.group(1).strip()
            if version_text.lower() != "unreleased":
                # Extract version from the text (handle dates and other formats)
                if re.match(r"v?\d+\.\d+", version_text):
                    version_positions.append((i, version_text, version_key(version_text)))

    # If no version sections found, use the original insertion point logic
    if not version_positions:
        return find_insertion_point(content)

    # Find the correct position by comparing version keys
    # Versions should be in descending order (newest first)
    for position, _version_text, version_components in version_positions:
        # If new version is greater than current version, insert before it
        if new_version_key > version_components:
            return position

    # If new version is smaller than all existing versions, insert after the last one
    # Find the end of the last version section
    last_position = version_positions[-1][0]
    for i in range(last_position + 1, len(lines)):
        # If we hit another version section or end of file, insert here
        if re.match(r"##\s*\[", lines[i]) or i == len(lines) - 1:
            return i if i < len(lines) - 1 else len(lines)

    # Fallback to end of file
    return len(lines)


def create_changelog_header(include_unreleased: bool = True) -> str:
    """Create a standard changelog header.

    Args:
        include_unreleased: Whether to include the Unreleased section in the header
    """
    header = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

"""

    if include_unreleased:
        header += "## [Unreleased]\n\n"

    return header


def format_changelog_entry(
    tag: str,
    commits: list[dict],
    ai_content: str,
    tag_date: datetime | None = None,
    include_unreleased_header: bool = True,
    boundary_mode: str = "tags",
) -> str:
    """Format a changelog entry for a specific boundary.

    Args:
        tag: The boundary identifier (tag name, date, etc.)
        commits: List of commit dictionaries
        ai_content: AI-generated changelog content
        tag_date: Date the boundary was created
        include_unreleased_header: Whether to include the Unreleased header (used in append mode)
        boundary_mode: The boundary mode ('tags', 'dates', 'gaps')

    Returns:
        Formatted changelog entry as a string
    """
    # Generate proper display name for boundary
    if tag is None:
        display_tag = "Unreleased"
        date_str = ""
    else:
        # Use boundary-aware display generation
        if boundary_mode == "tags":
            display_tag = tag.lstrip("v")
            date_str = f" - {tag_date.strftime('%Y-%m-%d')}" if tag_date else ""
        else:
            # For dates and gaps, create a boundary object to generate display name
            from kittylog.git_operations import generate_boundary_display_name

            boundary = {
                "hash": "dummy",  # We don't need the actual hash for display
                "date": tag_date or datetime.now(),
                "identifier": tag,
                "boundary_type": boundary_mode.rstrip("s"),  # 'dates' -> 'date', 'gaps' -> 'gap'
            }
            display_name = generate_boundary_display_name(boundary, boundary_mode)
            # Extract just the display part, removing the "## " prefix if present
            display_tag = display_name.replace("## ", "")
            date_str = ""  # Date is already included in the display name

    # For unreleased changes, the AI now generates the version header
    # Check if AI content already includes a version header
    if tag is None:
        entry = ""
        if ai_content.strip():
            # Check if AI content starts with a version header like ## [1.2.0]
            ai_lines = ai_content.strip().split("\n")
            first_line = ai_lines[0].strip() if ai_lines else ""
            logger.debug(f"AI first line: {repr(first_line)}")
            if ai_lines and re.match(r"^##\s*\[\d+\.\d+\.\d+\]", first_line):
                # AI already included the version header, just use the content as-is
                logger.info(f"AI generated version header: {first_line}")
                entry = ai_content.strip() + "\n\n"
            else:
                # Fallback: no version header found, add the traditional Unreleased header
                logger.warning(
                    f"AI did not generate version header, using Unreleased. First line was: {repr(first_line)}"
                )
                entry = "## [Unreleased]\n\n" + ai_content.strip() + "\n\n"
        else:
            logger.warning("No AI content generated for tag: %s", tag)
            # Fallback: create a simple list from commit messages with traditional header
            entry = "## [Unreleased]\n\n"
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
            logger.warning("No AI content generated for tag: %s", tag)
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


def handle_unreleased_section(
    lines: list[str],
    new_entry: str,
    existing_content: str,
    current_commit_is_tagged: bool,
) -> list[str]:
    """Handle updating the unreleased section of the changelog with intelligent behavior."""
    from kittylog.git_operations import get_latest_tag

    logger.debug("Processing unreleased section with intelligent behavior")

    # Check if there are actually unreleased commits
    latest_tag = get_latest_tag()
    unreleased_commits = get_commits_between_tags(latest_tag, None)

    # If current commit is tagged and matches latest tag, remove unreleased section
    if current_commit_is_tagged and not unreleased_commits:
        logger.debug("Current commit is tagged and up to date - removing unreleased section")
        unreleased_line = find_unreleased_section(existing_content)
        if unreleased_line is not None:
            end_line = find_end_of_unreleased_section(lines, unreleased_line)
            # Remove entire unreleased section including header
            del lines[unreleased_line:end_line]
        return lines

    # If no unreleased commits, don't add unreleased section
    if not unreleased_commits:
        logger.debug("No unreleased commits found - skipping unreleased section")
        return lines

    # Find the unreleased section
    unreleased_line = find_unreleased_section(existing_content)

    if unreleased_line is not None:
        end_line = find_end_of_unreleased_section(lines, unreleased_line)
        logger.debug(f"Found end_line: {end_line}")

        # Find where actual content starts in the existing section (skip empty lines after header)
        content_start_line = unreleased_line + 1
        while content_start_line < len(lines) and not lines[content_start_line].strip():
            content_start_line += 1
        logger.debug(f"Content starts at line: {content_start_line}")

        # Replace existing unreleased content with fresh content - this keeps it fresh and up-to-date
        logger.debug("Replacing existing unreleased content with fresh content")
        # Replace the content between the Unreleased header and the next section
        del lines[content_start_line:end_line]

        # Insert new content with bullet limiting
        # Filter out any lines that might be Unreleased headers to prevent duplicates
        new_entry_lines = [
            line
            for line in new_entry.split("\n")
            if line.strip() and not re.match(r"^##\s*\[\s*Unreleased\s*\]", line, re.IGNORECASE)
        ]
        limited_content_lines = limit_bullets_in_sections(new_entry_lines)

        for line in reversed(limited_content_lines):
            lines.insert(content_start_line, line)
    else:
        # No existing unreleased section - create one if there are unreleased commits
        logger.debug("Creating new unreleased section")
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

    return lines


def handle_tagged_version(lines: list[str], new_entry: str, tag_name: str, existing_content: str) -> list[str]:
    """Handle updating a tagged version section of the changelog."""
    # For tagged versions, find and replace the existing version section
    version = tag_name.lstrip("v")
    version_start_line: int | None
    version_end_line: int | None
    version_start_line, version_end_line = find_version_section(existing_content, version)

    if version_start_line is not None and version_end_line is not None:
        # Remove existing content for this version
        del lines[version_start_line:version_end_line]

        # Insert new content with bullet limiting at the same position
        entry_lines = [line for line in new_entry.rstrip().split("\n") if line.strip()]
        limited_entry_lines = limit_bullets_in_sections(entry_lines)

        for line in reversed(limited_entry_lines):
            lines.insert(version_start_line, line)
    else:
        # Version section not found, insert at appropriate position based on version ordering
        insert_line = find_insertion_point_by_version(existing_content, tag_name)

        # Insert the new entry with bullet limiting
        entry_lines = [line for line in new_entry.rstrip().split("\n") if line.strip()]
        limited_entry_lines = limit_bullets_in_sections(entry_lines)

        for line in reversed(limited_entry_lines):
            lines.insert(insert_line, line)

    return lines


def format_and_clean_content(content: str, no_unreleased: bool = False) -> str:
    """Apply formatting and cleanup rules to changelog content."""
    # Clean up any excessive blank lines and ensure proper spacing
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Remove any "### Changelog" sections that might have been generated
    content = re.sub(r"###\s+Changelog\s*\n", "", content, flags=re.MULTILINE)

    # Ensure there's proper spacing between sections (two newlines between sections)
    content = re.sub(r"(\S)\n(##\s*\[)", r"\1\n\n\2", content)

    # Remove empty [Unreleased] sections (only when there's no content between header and next section)
    # This regex looks for ## [Unreleased] followed by only whitespace until the next ## section
    if no_unreleased:
        content = re.sub(r"##\s*\[Unreleased\]\s*\n(\s*\n)*(?=##\s*\[)", "", content, flags=re.IGNORECASE)
        # Also remove any standalone [Unreleased] sections
        content = re.sub(r"##\s*\[Unreleased\]\s*\n\s*\n", "", content, flags=re.IGNORECASE)

    # Ensure there's a space before each version section (after the first one)
    content = re.sub(r"(\S)(\n##\s*\[)", r"\1\n\n\2", content)

    # Apply postprocessing to ensure proper line breaks around section headers
    content = postprocess_changelog_content(content)

    return content


def update_changelog(
    file_path: str | None = "CHANGELOG.md",
    existing_content: str | None = None,
    from_tag: str | None = None,
    to_tag: str | None = None,
    model: str = "",
    hint: str = "",
    show_prompt: bool = False,
    quiet: bool = False,
    no_unreleased: bool = False,
    grouping_mode: str = "tags",
    gap_threshold_hours: float = 4.0,
    date_grouping: str = "daily",
    include_diff: bool = False,
    language: str | None = None,
    translate_headings: bool = False,
    audience: str | None = None,
) -> tuple[str, dict[str, int] | None]:
    """Update changelog with entries for new boundaries.

    Args:
        file_path: Path to the changelog file (used when existing_content is None)
        existing_content: Existing changelog content (takes precedence over file reading)
        from_tag: Starting boundary (exclusive)
        to_tag: Ending boundary (inclusive)
        model: AI model to use for generation
        hint: Additional context for AI
        show_prompt: Whether to show the prompt
        quiet: Whether to suppress output
        no_unreleased: Whether to skip creating unreleased sections (default False)
        grouping_mode: Boundary grouping mode ('tags', 'dates', 'gaps')
        gap_threshold_hours: Hours threshold for gap detection
        date_grouping: Date grouping granularity ('daily', 'weekly', 'monthly')
        include_diff: Whether to include git diff in AI context (warning: high token usage)
        language: Optional language override for changelog entries
        translate_headings: Whether to translate section headings into the selected language
        audience: Target audience slug controlling tone and emphasis

    Returns:
        The updated changelog content
    """
    # Import git operations function early to avoid scoping issues
    from kittylog.git_operations import is_current_commit_tagged

    logger.info(f"Updating changelog from {from_tag or 'beginning'} to {to_tag}")

    # Read existing changelog if content wasn't provided
    if existing_content is None:
        # Default to CHANGELOG.md if no file path provided
        changelog_path = file_path or "CHANGELOG.md"
        existing_content = read_changelog(changelog_path)

    # If no_unreleased is True, remove any existing Unreleased sections
    if no_unreleased:
        lines = existing_content.split("\n")
        lines = remove_unreleased_sections(lines)
        existing_content = "\n".join(lines)

    # Get commits for this boundary range
    if grouping_mode != "tags":
        from kittylog.git_operations import (
            generate_boundary_identifier,
            get_all_boundaries,
            get_commits_between_boundaries,
        )

        # Convert boundary identifiers to boundary objects
        all_boundaries = get_all_boundaries(grouping_mode)
        from_boundary = None
        to_boundary = None

        if from_tag:
            for boundary in all_boundaries:
                if generate_boundary_identifier(boundary, grouping_mode) == from_tag:
                    from_boundary = boundary
                    break

        if to_tag:
            for boundary in all_boundaries:
                if generate_boundary_identifier(boundary, grouping_mode) == to_tag:
                    to_boundary = boundary
                    break

        commits = get_commits_between_boundaries(from_boundary, to_boundary, grouping_mode)
    else:
        from kittylog.git_operations import get_commits_between_tags

        commits = get_commits_between_tags(from_tag, to_tag)

    if not commits:
        logger.info(f"No commits found between {from_tag} and {to_tag}")
        return existing_content, None

    logger.info(f"Found {len(commits)} commits between {from_tag or 'beginning'} and {to_tag}")

    # If file is empty or very short, create header
    if len(existing_content.strip()) < 50:
        existing_content = create_changelog_header(include_unreleased=not no_unreleased)

    # Get git diff for better context (only if requested)
    diff_content = ""
    if include_diff:
        if grouping_mode != "tags":
            from kittylog.git_operations import get_git_diff_by_boundaries

            diff_content = get_git_diff_by_boundaries(from_tag, to_tag, grouping_mode)
        else:
            diff_content = get_git_diff(from_tag, to_tag)

    # Generate AI content for this version
    # For unreleased changes, the AI will determine and include the version header
    tag_name = to_tag or "Unreleased"  # Fallback for display purposes

    # If no_unreleased is True and we're processing unreleased content, skip processing
    if no_unreleased and to_tag is None:
        return existing_content, None

    ai_content, token_usage = generate_changelog_entry(
        commits=commits,
        tag=tag_name,
        from_tag=from_tag,
        model=model,
        hint=hint,
        show_prompt=show_prompt,
        quiet=quiet,
        diff_content=diff_content,
        boundary_mode=grouping_mode,
        language=language,
        translate_headings=translate_headings,
        audience=audience,
    )

    # Post-process the AI content to ensure proper formatting
    current_commit_is_tagged_value = is_current_commit_tagged()
    logger.debug(f"AI content before postprocessing: {repr(ai_content)}")
    ai_content = postprocess_changelog_content(
        ai_content, is_current_commit_tagged=(to_tag is not None and current_commit_is_tagged_value)
    )
    logger.debug(f"AI content after postprocessing: {repr(ai_content)}")

    # Get boundary date (None for unreleased changes)
    if grouping_mode != "tags" and to_tag:
        from kittylog.git_operations import get_boundary_date

        tag_date = get_boundary_date(to_tag, grouping_mode) if to_tag else None
    else:
        tag_date = get_tag_date(to_tag) if to_tag else None

    # Format new entries
    # For both tagged releases and unreleased changes, we use the same formatting function
    # For unreleased changes, don't include the Unreleased header in the formatted entry
    # because it will be inserted into content that already has the header
    include_header = to_tag is not None
    new_entry = format_changelog_entry(tag_name, commits, ai_content, tag_date, include_header, grouping_mode)

    # Log the AI content for debugging
    logger.debug(f"AI-generated content for {tag_name}: {ai_content}")

    # Find where to insert the new entry
    lines = existing_content.split("\n")

    # Check if current commit is tagged
    current_commit_is_tagged = is_current_commit_tagged()

    # If the current commit is tagged AND we're processing a specific version (not unreleased),
    # remove any Unreleased sections from the existing content, but only if there's no existing Unreleased section
    # or if we're actually processing the Unreleased section itself
    if current_commit_is_tagged and to_tag is not None and not no_unreleased:
        # Only remove unreleased sections if there isn't already an unreleased section in the content
        # This preserves existing unreleased sections when adding new version sections
        has_unreleased = find_unreleased_section(existing_content) is not None
        if not has_unreleased:
            lines = remove_unreleased_sections(lines)

    # Route to appropriate handler based on whether this is unreleased or tagged content
    if to_tag is None and not no_unreleased:
        lines = handle_unreleased_section(lines, new_entry, existing_content, current_commit_is_tagged)
    elif to_tag is not None:
        lines = handle_tagged_version(lines, new_entry, tag_name, existing_content)
    # If no_unreleased is True and to_tag is None, we skip processing unreleased sections

    # Join back together and apply formatting/cleanup
    updated_content = "\n".join(lines)
    updated_content = format_and_clean_content(updated_content, no_unreleased=no_unreleased)

    return updated_content, token_usage


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


def preview_changelog_entry(tag: str, commits: list[dict], ai_content: str, boundary_mode: str = "tags") -> str:
    """Generate a preview of what the changelog entry would look like."""
    if boundary_mode == "tags":
        tag_date = get_tag_date(tag)
    else:
        from kittylog.git_operations import get_boundary_date

        tag_date = get_boundary_date(tag, boundary_mode)
    return format_changelog_entry(tag, commits, ai_content, tag_date, boundary_mode=boundary_mode)
