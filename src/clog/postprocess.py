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


def postprocess_changelog_content(content: str, is_current_commit_tagged: bool = False) -> str:
    """Apply all post-processing steps to changelog content.

    Args:
        content: Raw changelog content
        is_current_commit_tagged: Whether the current commit is tagged

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

    # If the current commit is tagged, remove any [Unreleased] sections
    if is_current_commit_tagged:
        lines = remove_unreleased_sections(lines)

    # Join back together
    processed_content = "\n".join(lines)

    # Clean up excessive newlines
    processed_content = re.sub(r"\n{3,}", "\n\n", processed_content)

    return processed_content


def remove_unreleased_sections(lines: List[str]) -> List[str]:
    """Remove any [Unreleased] sections from the changelog content.

    Args:
        lines: List of changelog content lines

    Returns:
        List of lines with [Unreleased] sections removed
    """
    if not lines:
        return lines

    processed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped_line = line.strip()

        # Check if this is an Unreleased section header
        if re.match(r"^##\s*\[\s*Unreleased\s*\]", stripped_line, re.IGNORECASE):
            # Skip this line and any subsequent lines until we reach the next version section
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                # If we find another version section header, break and continue processing
                if re.match(r"^##\s*\[.*\]", next_line):
                    break
                # If we find a category section header, check if it has content
                elif re.match(r"^###\s+[A-Z][a-z]+", next_line):
                    # Look ahead to see if this category has any bullet points
                    has_content = False
                    temp_i = i + 1
                    while temp_i < len(lines):
                        temp_line = lines[temp_i].strip()
                        # If we find a bullet point, this category has content
                        if temp_line.startswith("- "):
                            has_content = True
                            break
                        # If we find another section header, stop looking
                        elif re.match(r"^###+\s+", temp_line):
                            break
                        temp_i += 1

                    # If this category has no content, skip it
                    if not has_content:
                        i += 1
                        continue
                    else:
                        # Otherwise, process this line normally
                        processed_lines.append(line)
                        break
                # If we find other content, skip it
                elif next_line:
                    i += 1
                else:
                    # Empty line, just skip it
                    i += 1
        else:
            processed_lines.append(line)
        i += 1

    return processed_lines