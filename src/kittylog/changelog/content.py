"""Content manipulation for changelog entries.

This module handles content-level operations like limiting bullets
and extracting entries for context.
"""

import re

from kittylog.constants import Limits


def limit_bullets_in_sections(content_lines: list[str], max_bullets: int = Limits.MAX_BULLETS_PER_SECTION) -> list[str]:
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


def extract_preceding_entries(content: str, n: int = 3) -> str:
    """Extract the N most recent changelog entries for context.

    This provides preceding entries to help AI understand the existing
    changelog style, format, and level of detail.

    Args:
        content: The changelog content
        n: Number of preceding entries to extract (default 3)

    Returns:
        String containing the extracted entries, or empty string if none found
    """
    if n <= 0 or not content:
        return ""

    lines = content.split("\n")
    entries = []
    current_entry_lines: list[str] = []
    in_entry = False

    for line in lines:
        # Check for version header (not Unreleased)
        match = re.match(r"##\s*\[\s*([^\]]+)\s*\]", line, re.IGNORECASE)
        if match:
            version = match.group(1).strip()
            # Skip unreleased section
            if version.lower() == "unreleased":
                continue

            # Save previous entry if we were in one
            if in_entry and current_entry_lines:
                entries.append("\n".join(current_entry_lines))
                if len(entries) >= n:
                    break

            # Start new entry
            current_entry_lines = [line]
            in_entry = True
        elif in_entry:
            # Stop at the next major header (# )
            if line.startswith("# ") and not line.startswith("## "):
                break
            current_entry_lines.append(line)

    # Don't forget the last entry if we're still in one
    if in_entry and current_entry_lines and len(entries) < n:
        entries.append("\n".join(current_entry_lines))

    if not entries:
        return ""

    # Format for context
    header = (
        f"## Previous {len(entries)} Changelog {'Entry' if len(entries) == 1 else 'Entries'} (for style reference):\n\n"
    )
    return header + "\n\n---\n\n".join(entries[:n])
