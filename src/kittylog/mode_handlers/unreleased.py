"""Unreleased mode handler for kittylog."""

from kittylog.changelog.content import limit_bullets_in_sections
from kittylog.changelog.io import ensure_changelog_exists
from kittylog.changelog.updater import _insert_unreleased_entry
from kittylog.commit_analyzer import get_commits_between_tags
from kittylog.errors import AIError, GitError
from kittylog.tag_operations import get_latest_tag


def handle_unreleased_mode(
    changelog_file: str,
    generate_entry_func,
    no_unreleased: bool,
    quiet: bool = False,
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
        yes: Auto-accept without previews
        dry_run: Preview changes without saving
        incremental_save: Save immediately after generating the entry
        **kwargs: Additional arguments for entry generation

    Returns:
        Tuple of (success, updated_content)
    """
    from kittylog.output import get_output_manager
    from kittylog.tag_operations import is_current_commit_tagged

    output = get_output_manager()

    # Ensure changelog exists (creates with just "# Changelog" if missing)
    existing_content = ensure_changelog_exists(changelog_file)

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
