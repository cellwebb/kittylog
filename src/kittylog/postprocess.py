"""Post-processing utilities for changelog entries.

This module provides functions to clean up and format changelog entries after AI generation
but before they're written to the changelog file, ensuring proper spacing and formatting.
"""

import re

# Mapping from developer headers to audience-specific headers
HEADER_MAPPING: dict[str, dict[str, str]] = {
    "users": {
        "### Added": "### What's New",
        "### Changed": "### Improvements",
        "### Fixed": "### Bug Fixes",
        "### Deprecated": "### Bug Fixes",  # Map deprecated to bug fixes for users
        "### Removed": "### Improvements",  # Map removed to improvements for users
        "### Security": "### Bug Fixes",  # Map security to bug fixes for users
    },
    "stakeholders": {
        "### Added": "### Highlights",
        "### Changed": "### Platform Improvements",
        "### Fixed": "### Platform Improvements",
        "### Deprecated": "### Platform Improvements",
        "### Removed": "### Platform Improvements",
        "### Security": "### Platform Improvements",
    },
}


def remap_headers_for_audience(content: str, audience: str) -> str:
    """Remap developer-style headers to audience-specific headers.

    Args:
        content: Content with headers
        audience: Target audience ('developers', 'users', 'stakeholders')

    Returns:
        Content with remapped headers
    """
    if audience not in HEADER_MAPPING:
        return content

    mapping = HEADER_MAPPING[audience]

    # Use regex for more robust matching (handles whitespace variations)
    for old_header, new_header in mapping.items():
        # Extract the section name (e.g., "Added" from "### Added")
        old_section = old_header.replace("### ", "")
        new_section = new_header.replace("### ", "")

        # Match variations like "### Added", "###Added", "### added", etc.
        pattern = rf"^###\s*{re.escape(old_section)}\s*$"
        content = re.sub(pattern, f"### {new_section}", content, flags=re.MULTILINE | re.IGNORECASE)

    return content


def clean_changelog_content(content: str, preserve_version_header: bool = False, audience: str = "developers") -> str:
    """Clean and format AI-generated changelog content.

    Args:
        content: Raw AI-generated content
        preserve_version_header: Whether to preserve version headers (for unreleased changes)
        audience: Target audience for header remapping

    Returns:
        Cleaned and formatted changelog content
    """
    # Handle empty or whitespace-only content
    if not content or not content.strip():
        return ""

    # Remove markdown code blocks around the entire content
    content = re.sub(r"^```(?:markdown)?\s*\n(.*?)\n```\s*$", r"\1", content, flags=re.MULTILINE | re.DOTALL)

    # Remove AI-generated preamble
    content = re.sub(r"^Here(\'s| is) the changelog[^#]*", "", content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r"^I(\'ll| will) help you.*?\n\n", "", content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r"^I(\'ve| have) generated.*?\n\n", "", content, flags=re.IGNORECASE | re.DOTALL)

    # Remove trailing AI chatter
    content = re.sub(r"\n\nLet me know if you need anything.*$", "", content, flags=re.IGNORECASE)
    content = re.sub(r"\n\nIs there anything else.*$", "", content, flags=re.IGNORECASE)
    content = re.sub(r"\n\nThe changelog entry above.*$", "", content, flags=re.IGNORECASE)

    # Remove version headers unless we want to preserve them (for unreleased changes)
    if not preserve_version_header:
        # Remove numeric version headers like ## [1.2.3] or ## v1.2.3
        content = re.sub(r"^##\s*\[?v?\d+\.\d+\.\d+[^\n]*\n?", "", content, flags=re.MULTILINE)
        # Remove placeholder version headers like ## [X.Y.Z] that AI might output
        content = re.sub(r"^##\s*\[X\.Y\.Z\][^\n]*\n?", "", content, flags=re.MULTILINE)
        # Remove any other version-like headers (e.g., ## [Unreleased])
        content = re.sub(r"^##\s*\[Unreleased\][^\n]*\n?", "", content, flags=re.MULTILINE | re.IGNORECASE)

    # Remove any "### Changelog" sections that might have been included
    content = re.sub(r"^###\s+Changelog\s*\n?", "", content, flags=re.MULTILINE)

    # Remove any date stamps
    content = re.sub(r"- \d{4}-\d{2}-\d{2}[^\n]*\n?", "", content, flags=re.MULTILINE)

    # Remove explanatory introductions and conclusions
    explanatory_patterns = [
        r"^Based on the commits.*?:\s*\n?",
        r"^Here's? .*? changelog.*?:\s*\n?",
        r"^.*comprehensive changelog.*?:\s*\n?",
        r"^.*changelog entry.*?:\s*\n?",
        r"^.*following.*change.*?:\s*\n?",
        r"^.*version.*include.*?:\s*\n?",
        r"^.*summary of changes.*?:\s*\n?",
        r"^.*changes made.*?:\s*\n?",
    ]

    for pattern in explanatory_patterns:
        content = re.sub(pattern, "", content, flags=re.MULTILINE | re.IGNORECASE)

    # Remove any remaining lines that are purely explanatory
    lines = content.split("\n")
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        # Skip lines that look like explanatory text
        if (
            stripped
            and not stripped.startswith("###")
            and not stripped.startswith("-")
            and not stripped.startswith("*")
            and any(
                phrase in stripped.lower()
                for phrase in [
                    "based on",
                    "here is",
                    "here's",
                    "changelog for",
                    "version",
                    "following changes",
                    "summary",
                    "commits",
                    "entry for",
                ]
            )
            and len(stripped) > 30
        ):  # Only remove longer explanatory lines
            continue
        cleaned_lines.append(line)

    content = "\n".join(cleaned_lines)

    # Clean up any XML tags that might have leaked
    xml_tags = [
        "<thinking>",
        "</thinking>",
        "<analysis>",
        "<summary>",
        "</summary>",
        "<changelog>",
        "</changelog>",
        "<entry>",
        "</entry>",
        "<version>",
        "</version>",
    ]

    for tag in xml_tags:
        content = content.replace(tag, "")

    # Normalize whitespace
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = content.strip()

    # Handle empty-ish content that has no real changelog sections
    if content and not re.search(r"###\s+\w+|^-\s+", content, re.MULTILINE):
        return ""

    # Ensure sections have proper spacing
    content = re.sub(r"\n(### [^\n]+)\n([^\n])", r"\n\1\n\n\2", content)

    # Normalize section headers to use ### format consistently
    content = re.sub(r"^##\s+([A-Z][a-z]+)", r"### \1", content, flags=re.MULTILINE)

    # Normalize bullet points to use consistent format (- instead of *)
    content = re.sub(r"^\*\s+", "- ", content, flags=re.MULTILINE)

    # Remap headers for non-developer audiences
    content = remap_headers_for_audience(content, audience)

    # Apply structural post-processing
    content = postprocess_changelog_content(content)

    return content


def ensure_newlines_around_section_headers(lines: list[str]) -> list[str]:
    """Ensure proper newlines around section headers in changelog content.

    Args:
        lines: List of changelog content lines

    Returns:
        List of lines with proper spacing around section headers
    """
    if not lines:
        return lines

    processed_lines: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped_line = line.strip()

        # Check if this is a version section header (## [version])
        if re.match(r"^##\s*\[.*\]", stripped_line):
            # Add blank line before version header if it's not the first line
            if processed_lines:
                processed_lines.append("")
            processed_lines.append(line)
            # Always add blank line after version header
            processed_lines.append("")

        # Check if this is a category section header (### Added/Changed/Fixed/etc.)
        elif re.match(r"^###\s+\S+", stripped_line):
            # Always add blank line before category header if there are existing lines
            if processed_lines and processed_lines[-1].strip():
                processed_lines.append("")
            processed_lines.append(line)
            # Always add blank line after category header
            processed_lines.append("")
        else:
            processed_lines.append(line)

        i += 1

    # Remove excess trailing empty lines but ensure file ends with a single newline
    while processed_lines and not processed_lines[-1].strip() and len(processed_lines) > 1:
        processed_lines.pop()
    if (processed_lines and processed_lines[-1].strip()) or not processed_lines:
        processed_lines.append("")

    return processed_lines


def clean_duplicate_sections(lines: list[str]) -> list[str]:
    """Remove duplicate section headers from changelog content.

    Args:
        lines: List of changelog content lines

    Returns:
        List of lines with duplicate sections removed
    """
    processed_lines = []
    current_version_sections: set[str] = set()

    for line in lines:
        stripped_line = line.strip()

        # Check for version headers (## [version])
        if re.match(r"^##\s*\[.*\]", stripped_line):
            # Reset section tracking for the new version
            current_version_sections = set()
            processed_lines.append(line)
        # Check for category section headers (### Added/Changed/Fixed/etc.)
        elif re.match(r"^###\s+\S+", stripped_line):
            # Only check for duplicates within the current version section
            if stripped_line in current_version_sections:
                continue  # Skip duplicate section header within this version
            else:
                current_version_sections.add(stripped_line)
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


def remove_unreleased_sections(lines: list[str]) -> list[str]:
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
            # Skip this line and all subsequent lines until we reach the next version section
            i += 1
            while i < len(lines):
                next_line = lines[i]
                stripped_next_line = next_line.strip()
                # If we find another section header, break and continue processing
                if re.match(r"^##\s*\[.*\]", stripped_next_line):
                    # Don't increment i here, let the outer loop handle it
                    break
                # Skip all content lines until we find the next section header
                i += 1
        else:
            processed_lines.append(line)
            i += 1

    return processed_lines
