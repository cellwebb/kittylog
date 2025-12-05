"""Unreleased mode handler for kittylog."""

from pathlib import Path

from kittylog.changelog.io import read_changelog
from kittylog.changelog.parser import limit_bullets_in_sections
from kittylog.changelog.updater import _insert_unreleased_entry
from kittylog.commit_analyzer import get_commits_between_tags
from kittylog.errors import AIError, GitError
from kittylog.tag_operations import get_latest_tag


def _find_previous_boundary_id(latest_tag: str | None) -> str | None:
    """Find the boundary ID from previous changelog section.

    Args:
        parser: ChangelogParser instance
        latest_tag: Latest version tag

    Returns:
        Previous boundary ID or None
    """
    if not latest_tag:
        return None

    # Simplified for now - just return None
    return None


def _ensure_changelog_exists(changelog_file: str, no_unreleased: bool) -> str:
    """Ensure changelog file exists, create if needed.

    Args:
        changelog_file: Path to changelog file
        no_unreleased: Whether to skip unreleased section

    Returns:
        Changelog file content
    """
    try:
        return read_changelog(changelog_file)
    except FileNotFoundError:
        # Create new changelog if it doesn't exist
        if no_unreleased:
            content = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
        else:
            content = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n## [Unreleased]\n\n"

        # Write the new changelog
        Path(changelog_file).write_text(content, encoding="utf-8")
        return content


def handle_unreleased_mode(
    changelog_file: str,
    generate_entry_func,
    no_unreleased: bool,
    quiet: bool = False,
    yes: bool = False,
    dry_run: bool = False,
    incremental_save: bool = True,
    **kwargs,
) -> tuple[bool, str]:
    """Handle unreleased mode workflow.

    Args:
        changelog_file: Path to changelog file
        generate_entry_func: Function to generate changelog entry
        no_unreleased: Skip unreleased section
        quiet: Suppress non-error output
        yes: Skip confirmation prompts
        dry_run: Preview changes without saving
        incremental_save: Save immediately after generating the entry
        **kwargs: Additional arguments for entry generation

    Returns:
        Tuple of (success, updated_content)
    """
    from kittylog.output import get_output_manager
    from kittylog.tag_operations import is_current_commit_tagged

    output = get_output_manager()

    # Ensure changelog exists
    existing_content = _ensure_changelog_exists(changelog_file, no_unreleased)

    if no_unreleased:
        output.info("Skipping unreleased section creation as requested")
        return True, existing_content

    # Check if current commit is tagged
    if is_current_commit_tagged():
        output.info("Current commit is tagged, no unreleased changes needed")
        return True, existing_content

    # Get commits since latest tag
    latest_tag = get_latest_tag()
    commits = get_commits_between_tags(from_tag=latest_tag, to_tag=None)
    if not commits:
        output.info("No new commits since last tag")
        return True, existing_content

    output.info(f"Found {len(commits)} commits since last tag")

    # Generate changelog entry for unreleased section
    try:
        entry = generate_entry_func(commits=commits, tag="Unreleased", **kwargs)

        if not entry.strip():
            output.warning("AI generated empty content for unreleased section")
            return True, existing_content

        # Apply bullet limiting to entry
        entry_lines = entry.split("\n")
        limited_entry_lines = limit_bullets_in_sections(entry_lines, max_bullets=6)
        entry = "\n".join(limited_entry_lines)

        output.debug(f"Generated unreleased entry: {entry}")

        # Insert entry into the [Unreleased] section (or create one if needed)
        updated_content = _insert_unreleased_entry(existing_content, entry)

        # Save incrementally if enabled and not in dry run mode
        if incremental_save and not dry_run:
            from kittylog.changelog.io import write_changelog

            write_changelog(changelog_file, updated_content)
            if not quiet:
                output.success("✓ Saved unreleased changelog entry")

        return True, updated_content

    except (AIError, OSError, TimeoutError, ValueError, GitError) as e:
        from kittylog.errors import handle_error

        handle_error(e)
        return False, existing_content
