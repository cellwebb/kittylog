"""Post-processing utilities for changelog entries.

This module provides functions to clean up and format changelog entries after AI generation
but before they're written to the changelog file, ensuring proper spacing and compliance
with Keep a Changelog standards.
"""

import re
from typing import List


def ensure_newlines_around_section_headers(lines: List[str]) -> List[str]:
    """Ensure proper newlines around section headers in changelog content.

    Args:
        lines: List of changelog content lines

    Returns:
        List of lines with proper spacing around section headers
    """
    if not lines:
        return lines

    processed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped_line = line.strip()

        # Check if this is a version section header (## [version])
        if re.match(r"^##\s*\[.*\]", stripped_line):
            # Add blank line before version header if previous line isn't blank
            if (processed_lines and processed_lines[-1].strip()) or not processed_lines:
                processed_lines.append("")
            processed_lines.append(line)

            # Add blank line after version header
            if i + 1 < len(lines) and lines[i + 1].strip():
                processed_lines.append("")

        # Check if this is a category section header (### Added/Changed/Fixed/etc.)
        elif re.match(r"^###\s+[A-Z][a-z]+", stripped_line):
            # Add blank line before category header if previous line isn't blank
            if processed_lines and processed_lines[-1].strip():
                processed_lines.append("")
            processed_lines.append(line)

            # Add blank line after category header
            if i + 1 < len(lines) and lines[i + 1].strip():
                processed_lines.append("")
        else:
            processed_lines.append(line)

        i += 1

    # Ensure file ends with a single newline
    if processed_lines and not processed_lines[-1]:
        processed_lines.pop()
    processed_lines.append("")

    return processed_lines


def clean_duplicate_sections(lines: List[str]) -> List[str]:
    """Remove duplicate section headers from changelog content.

    Args:
        lines: List of changelog content lines

    Returns:
        List of lines with duplicate sections removed
    """
    processed_lines = []
    seen_sections = set()

    for line in lines:
        stripped_line = line.strip()

        # Check for section headers
        section_match = re.match(r"^(##|###)\s+(.+)$", stripped_line)
        if section_match:
            header_level = section_match.group(1)
            section_name = section_match.group(2)

            # If we've seen this section at this level, skip it
            section_key = f"{header_level}:{section_name}"
            if section_key in seen_sections:
                continue
            else:
                seen_sections.add(section_key)
                processed_lines.append(line)
        else:
            processed_lines.append(line)

    return processed_lines


def postprocess_changelog_content(content: str) -> str:
    """Apply all post-processing steps to changelog content.

    Args:
        content: Raw changelog content

    Returns:
        Cleaned and properly formatted changelog content
    """
    if not content:
        return content

    # Split into lines
    lines = content.split("\n")

    # Clean duplicate sections
    lines = clean_duplicate_sections(lines)

    # Ensure proper newlines around section headers
    lines = ensure_newlines_around_section_headers(lines)

    # Join back together
    processed_content = "\n".join(lines)

    # Clean up excessive newlines
    processed_content = re.sub(r"\n{3,}", "\n\n", processed_content)

    return processed_content