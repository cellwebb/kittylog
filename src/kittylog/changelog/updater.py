"""Changelog update operations for kittylog.

This module handles the core changelog update functionality using the specialized
io and parser modules for file operations and parsing.
"""

import logging
import re

from kittylog.ai import generate_changelog_entry
from kittylog.changelog.content import limit_bullets_in_sections
from kittylog.changelog.insertion import (
    find_end_of_unreleased_section,
    find_insertion_point,
    find_insertion_point_by_version,
    find_unreleased_section,
)
from kittylog.commit_analyzer import get_commits_between_tags, get_git_diff
from kittylog.errors import AIError
from kittylog.tag_operations import get_latest_tag, get_tag_date, is_current_commit_tagged
from kittylog.utils.text import format_version_for_changelog

logger = logging.getLogger(__name__)


def update_changelog(
    existing_content: str,
    from_boundary: str | None,
    to_boundary: str | None,
    model: str,
    hint: str = "",
    show_prompt: bool = False,
    quiet: bool = False,
    no_unreleased: bool = False,
    include_diff: bool = False,
    language: str | None = None,
    translate_headings: bool = False,
    audience: str | None = None,
) -> tuple[str, dict[str, int] | None]:
    """Update changelog content using AI-generated content.

    Args:
        existing_content: Current changelog content
        from_boundary: Starting boundary (exclusive). If None, starts from beginning.
        to_boundary: Ending boundary (inclusive). If None, goes to HEAD or creates unreleased.
        model: AI model to use for generation
        hint: Additional context for AI generation
        show_prompt: Display the AI prompt
        quiet: Suppress output
        no_unreleased: Skip unreleased section management
        include_diff: Include git diff in AI context
        language: Language for changelog entries
        translate_headings: Whether to translate section headings
        audience: Target audience for changelog

    Returns:
        Tuple of (updated_content, token_usage_dict)
    """
    logger.debug(f"Updating changelog from {from_boundary or 'beginning'} to {to_boundary or 'unreleased'}")

    # Get commits for the range
    if to_boundary is None:
        # Handle unreleased section
        if not no_unreleased:
            changelog_content = handle_unreleased_section_update(
                existing_content, model, hint, show_prompt, quiet, include_diff, language, translate_headings, audience
            )
        else:
            changelog_content = existing_content
    else:
        # Handle specific version
        changelog_content = handle_version_update(
            existing_content,
            from_boundary,
            to_boundary,
            model,
            hint,
            show_prompt,
            quiet,
            include_diff,
            language,
            translate_headings,
            audience,
        )

    return changelog_content, None  # Token usage would be added here if tracked


def handle_unreleased_section_update(
    existing_content: str,
    model: str,
    hint: str,
    show_prompt: bool,
    quiet: bool,
    include_diff: bool,
    language: str | None,
    translate_headings: bool,
    audience: str | None,
) -> str:
    """Consolidated function for updating the unreleased section of the changelog.

    This function consolidates the previous duplication between handle_unreleased_section_update
    and _update_unreleased_section for better maintainability.
    """
    logger.debug("Processing unreleased section with intelligent behavior")

    # Check if there are actually unreleased commits
    latest_tag = get_latest_tag()
    unreleased_commits = get_commits_between_tags(latest_tag, None)
    current_commit_is_tagged = is_current_commit_tagged()

    lines = existing_content.split("\n")

    # Smart removal logic: remove unreleased section if appropriate
    if current_commit_is_tagged and not unreleased_commits:
        logger.debug("Current commit is tagged and up to date - removing unreleased section")
        unreleased_line = find_unreleased_section(existing_content)
        if unreleased_line is not None:
            end_line = find_end_of_unreleased_section(lines, unreleased_line)
            # Remove entire unreleased section including header
            del lines[unreleased_line:end_line]
        return "\n".join(lines)

    # If no unreleased commits, don't add unreleased section
    if not unreleased_commits:
        logger.debug("No unreleased commits found - skipping unreleased section")
        content = _remove_unreleased_section_if_empty(existing_content, unreleased_commits)
        return content

    # Generate and add AI content for unreleased section
    try:
        diff_content = (get_git_diff(latest_tag, None, max_lines=500) if latest_tag else "") if include_diff else ""

        new_entry, _token_usage = generate_changelog_entry(
            commits=unreleased_commits,
            tag="Unreleased",
            from_boundary=latest_tag,
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            diff_content=diff_content,
            language=language,
            translate_headings=translate_headings,
            audience=audience,
        )

        if not new_entry.strip():
            logger.warning("AI generated empty content for unreleased section")
            return existing_content

        # Apply bullet limiting to AI-generated content
        new_entry_lines = new_entry.split("\n")
        limited_entry_lines = limit_bullets_in_sections(new_entry_lines, max_bullets=6)
        limited_new_entry = "\n".join(limited_entry_lines)

        # Update the changelog with the limited content
        updated_content = _insert_unreleased_entry(existing_content, limited_new_entry)

        logger.debug("Successfully updated unreleased section")
        return updated_content

    except (AIError, ValueError, KeyError) as e:
        logger.error(f"Failed to update unreleased section: {e}")
        raise


def handle_version_update(
    existing_content: str,
    from_boundary: str | None,
    to_boundary: str,
    model: str,
    hint: str,
    show_prompt: bool,
    quiet: bool,
    include_diff: bool,
    language: str | None,
    translate_headings: bool,
    audience: str | None,
) -> str:
    """Handle updating a specific version section of the changelog."""
    logger.debug(f"Processing version section for {to_boundary}")

    try:
        # Get commits for the version range
        commits = get_commits_between_tags(from_boundary, to_boundary)

        if not commits:
            logger.warning(f"No commits found between {from_boundary or 'beginning'} and {to_boundary}")
            return existing_content

        # Get additional context
        tag_date = get_tag_date(to_boundary)
        previous_tag = from_boundary

        # Generate AI content
        diff_content = get_git_diff(from_boundary, to_boundary, max_lines=500) if include_diff else ""

        from datetime import datetime

        version_date = tag_date.strftime("%Y-%m-%d") if tag_date else datetime.now().strftime("%Y-%m-%d")

        new_entry, _token_usage = generate_changelog_entry(
            commits=commits,
            tag=to_boundary,
            from_boundary=previous_tag,
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            diff_content=diff_content,
            language=language,
            translate_headings=translate_headings,
            audience=audience,
        )

        if not new_entry.strip():
            logger.warning(f"AI generated empty content for version {to_boundary}")
            return existing_content

        # Apply bullet limiting to AI-generated content
        new_entry_lines = new_entry.split("\n")
        limited_entry_lines = limit_bullets_in_sections(new_entry_lines, max_bullets=6)
        limited_new_entry = "\n".join(limited_entry_lines)

        # Create the version section
        version_section = f"## [{format_version_for_changelog(to_boundary, existing_content)}] - {version_date}\n\n{limited_new_entry}"

        # Update the changelog with the new version section
        updated_content = _update_version_section(existing_content, version_section, to_boundary)

        logger.debug(f"Successfully updated version section for {to_boundary}")
        return updated_content

    except (AIError, ValueError, KeyError) as e:
        logger.error(f"Failed to update version section for {to_boundary}: {e}")
        raise


def _insert_unreleased_entry(existing_content: str, new_entry: str) -> str:
    """Helper function to insert content into the unreleased section.

    Extracted from the duplicated _update_unreleased_section function.
    """
    lines = existing_content.split("\n")

    # Find the unreleased section
    unreleased_line = find_unreleased_section(existing_content)

    if unreleased_line is not None:
        end_line = find_end_of_unreleased_section(lines, unreleased_line)
        logger.debug(f"Found existing unreleased section ending at line: {end_line}")

        # Find content start and replace existing content
        content_start_line = unreleased_line + 1
        while content_start_line < len(lines) and not lines[content_start_line].strip():
            content_start_line += 1

        # Remove existing content, keep header
        del lines[content_start_line:end_line]
        insert_line = content_start_line
    else:
        # Create new unreleased section after header
        insert_line = find_insertion_point(existing_content)
        lines.insert(insert_line, "## [Unreleased]")
        lines.insert(insert_line + 1, "")
        insert_line += 2

    # Insert new content
    lines.insert(insert_line, new_entry)
    return "\n".join(lines)


def _update_version_section(
    existing_content: str,
    version_section: str,
    tag_name: str,
) -> str:
    """Handle updating a tagged version section of the changelog."""
    # For tagged versions, find and replace the existing version section
    version = tag_name.lstrip("v")
    lines = existing_content.split("\n")

    # Find the existing version section
    version_start = None
    version_pattern = rf"##\s*\[\s*{re.escape(version)}\s*\]"

    for i, line in enumerate(lines):
        if re.match(version_pattern, line, re.IGNORECASE):
            version_start = i
            break

    if version_start is not None:
        # Replace existing version section
        # Find the end of this version section
        version_end = len(lines)
        for j in range(version_start + 1, len(lines)):
            if lines[j].startswith("## "):
                version_end = j
                break

        # Replace the section
        new_lines = version_section.split("\n")
        lines[version_start:version_end] = new_lines
        logger.debug(f"Replaced existing version section for {tag_name}")
    else:
        # Insert new version section at the appropriate position
        insert_point = find_insertion_point_by_version(existing_content, tag_name)

        # Insert the version section
        for line in reversed(version_section.split("\n")):
            lines.insert(insert_point, line)

        logger.debug(f"Inserted new version section for {tag_name} at line {insert_point}")

    # Post-process: normalize spacing to have exactly 2 blank lines between version sections

    # Parse all sections first
    header_lines = []
    version_sections = []
    unreleased_section = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith("## [Unreleased]"):
            # Extract unreleased section
            unreleased_section.append(line)
            i += 1
            while i < len(lines) and not lines[i].startswith("## ["):
                unreleased_section.append(lines[i])
                i += 1
        elif line.startswith("## ["):
            # Extract version section
            section_content = [line]
            i += 1
            while i < len(lines) and not lines[i].startswith("## ["):
                section_content.append(lines[i])
                i += 1
            version_sections.append(section_content)
        else:
            # Header content
            header_lines.append(line)
            i += 1

    # Rebuild with exact 2 blank lines between version sections
    result_lines = header_lines.copy() if header_lines else ["# Changelog"]

    # Add unreleased section if it exists (preserving its structure but normalizing trailing blanks)
    if unreleased_section:
        clean_unreleased = unreleased_section.copy()
        while clean_unreleased and clean_unreleased[-1].strip() == "":
            clean_unreleased.pop()
        result_lines.extend(clean_unreleased)
        if version_sections:
            result_lines.append("")
            result_lines.append("")  # 2 blanks before first version

    # Add version sections with exactly 2 blank lines between them
    for j, section in enumerate(version_sections):
        # Clean section: normalize internal blanks but preserve one blank between subsections
        clean_section = []
        i = 0
        while i < len(section):
            line = section[i]
            clean_section.append(line)
            i += 1

            # Collapse consecutive blanks to single blanks (except keep one blank after headers)
            while i < len(section) and section[i].strip() == "":
                # Skip additional consecutive blanks
                i += 1

        # Strip trailing blanks completely
        while clean_section and clean_section[-1].strip() == "":
            clean_section.pop()

        # Add the section
        result_lines.extend(clean_section)

        # Add exactly 2 blank lines after each version section except the last one
        if j < len(version_sections) - 1:
            result_lines.append("")
            result_lines.append("")

    return "\n".join(result_lines)


def _remove_unreleased_section_if_empty(existing_content: str, unreleased_commits: list) -> str:
    """Remove unreleased section if there are no unreleased commits."""
    if not unreleased_commits:
        lines = existing_content.split("\n")
        unreleased_line = find_unreleased_section(existing_content)

        if unreleased_line is not None:
            end_line = find_end_of_unreleased_section(lines, unreleased_line)
            del lines[unreleased_line:end_line]
            return "\n".join(lines)

    return existing_content


# Legacy compatibility - re-export for backward compatibility
def remove_unreleased_sections(content: str) -> str:
    """Legacy function for backward compatibility. Use postprocess.remove_unreleased_sections instead."""
    from ..postprocess import remove_unreleased_sections as post_remove_unreleased_sections

    lines = content.split("\n")
    result_lines = post_remove_unreleased_sections(lines)
    return "\n".join(result_lines)
