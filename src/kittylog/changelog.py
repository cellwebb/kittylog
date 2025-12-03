"""Changelog operations for updating CHANGELOG.md files.

This module handles the core changelog update functionality using the specialized
changelog_io and changelog_parser modules for file operations and parsing.
"""

import logging
import re

from kittylog.ai import generate_changelog_entry
from kittylog.changelog_io import create_changelog_header, read_changelog, write_changelog
from kittylog.changelog_parser import (
    find_end_of_unreleased_section,
    find_existing_boundaries,
    find_insertion_point,
    find_insertion_point_by_version,
    find_unreleased_section,
    limit_bullets_in_sections,
)
from kittylog.git_operations import get_commits_between_tags, get_git_diff, get_tag_date, is_current_commit_tagged
from kittylog.postprocess import remove_unreleased_sections

logger = logging.getLogger(__name__)


# create_changelog_header is imported from changelog_io.py


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
    """Handle updating the unreleased section of the changelog."""
    from kittylog.git_operations import get_latest_tag

    logger.debug("Processing unreleased section with intelligent behavior")

    # Check if there are actually unreleased commits
    latest_tag = get_latest_tag()
    unreleased_commits = get_commits_between_tags(latest_tag, None)

    # If no unreleased commits, don't add unreleased section
    if not unreleased_commits:
        logger.debug("No unreleased commits found - skipping unreleased section")
        # Remove unreleased section if it exists
        content = _remove_unreleased_section_if_empty(existing_content, unreleased_commits)
        return content

    # Generate AI content for unreleased section
    try:
        if include_diff:
            diff_content = get_git_diff(latest_tag, None, max_lines=500) if latest_tag else ""
        else:
            diff_content = ""

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

        # Update the changelog with the new unreleased content
        updated_content = _update_unreleased_section(existing_content, new_entry, is_current_commit_tagged())

        logger.debug("Successfully updated unreleased section")
        return updated_content

    except Exception as e:
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
        if include_diff:
            diff_content = get_git_diff(from_boundary, to_boundary, max_lines=500)
        else:
            diff_content = ""

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

        # Create the version section
        version_section = f"## [{to_boundary}] - {version_date}\n\n{new_entry}"

        # Update the changelog with the new version section
        updated_content = _update_version_section(existing_content, version_section, to_boundary)

        logger.debug(f"Successfully updated version section for {to_boundary}")
        return updated_content

    except Exception as e:
        logger.error(f"Failed to update version section for {to_boundary}: {e}")
        raise


def _update_unreleased_section(
    existing_content: str,
    new_entry: str,
    current_commit_is_tagged: bool,
) -> str:
    """Handle updating the unreleased section of the changelog with intelligent behavior."""
    from kittylog.git_operations import get_latest_tag

    logger.debug("Processing unreleased section with intelligent behavior")

    # Check if there are actually unreleased commits
    latest_tag = get_latest_tag()
    unreleased_commits = get_commits_between_tags(latest_tag, None)

    lines = existing_content.split("\n")

    # If current commit is tagged and matches latest tag, remove unreleased section
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
        return existing_content

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
        new_lines = [""] + version_section.split("\n")  # Add blank line before

        for line in reversed(new_lines):
            lines.insert(insert_point, line)

        logger.debug(f"Inserted new version section for {tag_name} at line {insert_point}")

    return "\n".join(lines)


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


# Re-export functions from specialized modules for backward compatibility
__all__ = [
    # Core functions
    "create_changelog_header",
    "update_changelog",
    "handle_unreleased_section_update",
    "handle_version_update",
    # Re-exported for backward compatibility
    "read_changelog",
    "write_changelog",
    "find_existing_boundaries",
    "limit_bullets_in_sections",
    "find_end_of_unreleased_section",
    "find_insertion_point",
    "find_insertion_point_by_version",
    "find_unreleased_section",
    "remove_unreleased_sections",
]
