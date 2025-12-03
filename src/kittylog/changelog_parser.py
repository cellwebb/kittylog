"""Changelog parsing and analysis operations for kittylog.

This module handles parsing changelog content, finding existing boundaries,
insertion points, and other analysis functions.
"""

import logging
import re

logger = logging.getLogger(__name__)


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
            boundary = match.group(1).strip()
            # Skip unreleased section
            if boundary.lower() != "unreleased":
                # For version boundaries, strip 'v' prefix for consistency
                if re.match(r"v?\d+\.\d+", boundary):
                    boundary = boundary.lstrip("v")
                existing_boundaries.add(boundary)

    logger.debug(f"Found existing boundaries: {existing_boundaries}")
    return existing_boundaries


def find_insertion_point(content: str) -> int:
    """Find the appropriate insertion point for new changelog entries.

    Args:
        content: The existing changelog content

    Returns:
        The line index where new entries should be inserted
    """
    lines = content.split("\n")

    # Look for unreleased section - if it exists, insert after it
    for i, line in enumerate(lines):
        if re.match(r"^##\s*\[\s*Unreleased\s*\]", line, re.IGNORECASE):
            # Check if this is the only section (no version sections)
            has_version_sections = any(
                re.match(r"^##\s*\[\s*", lines[line_idx])
                and not re.match(r"^##\s*\[\s*Unreleased\s*\]", lines[line_idx], re.IGNORECASE)
                for line_idx in range(i + 1, len(lines))
            )

            if not has_version_sections:
                # Only unreleased section exists, insert after first non-empty line
                for j, content_line in enumerate(lines):
                    if content_line.strip():
                        return j + 1
                return len(lines)
            else:
                # Has version sections, find end of unreleased section
                end_line = find_end_of_unreleased_section(lines, i)
                # Return the position after the unreleased section (where version starts)
                return end_line + 1 if end_line < len(lines) else end_line

    # If no unreleased section, insert after the header but before the first version
    for i, line in enumerate(lines):
        if line.startswith("## ["):
            return i

    # If no sections found, handle special cases
    has_any_header = any(re.match(r"^##\s*\[\s*", line) for line in lines)

    if not has_any_header:
        # Insert after the first non-empty line
        for i, line in enumerate(lines):
            if line.strip():
                return i + 1
        return len(lines)

    # Insert at the end of the header section
    for i, line in enumerate(lines):
        if line.strip() == "" and i > 0 and i < len(lines) - 1:
            # Look for end of header section (after main title and description)
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            if next_line.startswith("## ") or i > 5:  # Reasonable header length
                return i + 1

    # Default to end of file
    return len(lines)


def find_end_of_unreleased_section(lines: list[str], start_line: int) -> int:
    """Find the end of the unreleased section.

    Args:
        lines: The changelog content split into lines
        start_line: The line where the unreleased section starts

    Returns:
        The line index where the unreleased section ends
    """
    for i in range(start_line + 1, len(lines)):
        line = lines[i].strip()
        # Stop when we hit another section header
        if line.startswith("## "):
            # Return the line before the section header (empty line)
            return i - 1 if i > 0 else i

    # If we reach the end of the file
    return len(lines)


def find_unreleased_section(content: str) -> int | None:
    """Find the line number of the unreleased section header.

    Args:
        content: The changelog content

    Returns:
        The line index of the unreleased section header, or None if not found
    """
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if re.match(r"^##\s*\[\s*Unreleased\s*\]", line, re.IGNORECASE):
            return i
    return None


def find_version_section(content: str, version: str) -> tuple[int, int] | None:
    """Find the start and end lines of a specific version section.

    Args:
        content: The changelog content
        version: The version to find (e.g., "1.0.0" or "v1.0.0")

    Returns:
        Tuple of (start_line, end_line) or None if version not found
    """
    lines = content.split("\n")
    start_line = None

    # Find the version section
    for i, line in enumerate(lines):
        # Match patterns like ## [1.0.0], ## [v1.0.0], ## 1.0.0, etc.
        version_pattern = rf"##\s*\[?\s*v?{re.escape(version.lstrip('v'))}\s*\]?"
        if re.match(version_pattern, line, re.IGNORECASE):
            start_line = i
            break

    if start_line is None:
        return None

    # Find the end of the section (next version section or end of file)
    for i in range(start_line + 1, len(lines)):
        if lines[i].startswith("## "):
            return (start_line, i)

    # If we reach the end of the file
    return (start_line, len(lines))


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
            if version_text.lower() != "unreleased" and re.match(r"v?\d+\.\d+", version_text):
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


def extract_version_boundaries(content: str) -> list[dict]:
    """Extract version boundaries from changelog content.

    Args:
        content: The changelog content

    Returns:
        List of version boundary dictionaries
    """
    lines = content.split("\n")
    boundaries = []

    for i, line in enumerate(lines):
        match = re.match(r"##\s*\[\s*([^\]]+)\s*\]", line, re.IGNORECASE)
        if match:
            version = match.group(1).strip()
            if version.lower() != "unreleased" and re.match(r"v?\d+\.\d+", version):
                boundaries.append(
                    {
                        "identifier": version,
                        "line": i,
                        "raw_line": line,
                    }
                )

    return boundaries


def get_latest_version_in_changelog(content: str) -> str | None:
    """Get the latest version from changelog content.

    Args:
        content: The changelog content

    Returns:
        The latest version string or None if not found
    """
    boundaries = extract_version_boundaries(content)
    if not boundaries:
        return None

    # Return the first version (which should be the latest in Keep a Changelog format)
    return boundaries[0]["identifier"]


def is_version_in_changelog(content: str, version: str) -> bool:
    """Check if a version exists in the changelog.

    Args:
        content: The changelog content
        version: The version to check

    Returns:
        True if version exists, False otherwise
    """
    boundaries = extract_version_boundaries(content)
    version_patterns = [
        version,
        version.lstrip("v"),
        f"v{version}" if not version.startswith("v") else version,
    ]

    for boundary in boundaries:
        boundary_version = boundary["identifier"]
        if boundary_version in version_patterns:
            return True

    return False
