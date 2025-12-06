"""Workflow UI components for kittylog.

This module contains user interface logic for changelog generation workflow
including dry run handling and automatic save.
"""

import logging

from kittylog.changelog.io import write_changelog
from kittylog.errors import ChangelogError, handle_error
from kittylog.output import get_output_manager

logger = logging.getLogger(__name__)


def handle_dry_run_and_save(
    changelog_file: str,
    existing_content: str,
    original_content: str,
    token_usage: dict[str, int] | None,
    dry_run: bool,
    quiet: bool,
    incremental_save: bool = False,
) -> tuple[bool, dict[str, int] | None]:
    """Handle dry run and automatic save logic."""
    # Handle dry run mode
    if dry_run:
        output = get_output_manager()
        output.warning("Dry run: Changelog content generated but not saved")
        output.echo("\nPreview of updated changelog:")
        output.panel(existing_content, title="Updated Changelog", style="cyan")
        return True, token_usage

    # Check if content actually changed
    if existing_content == original_content:
        # No changes were made
        if not quiet:
            output = get_output_manager()
            output.info("No changes made to changelog.")
        return True, token_usage

    # Write the updated changelog (skip if already saved incrementally)
    if not incremental_save:
        try:
            write_changelog(changelog_file, existing_content)
            if not quiet:
                logger.info(f"Successfully updated changelog: {changelog_file}")
        except ChangelogError as e:
            handle_error(e)
            return False, None
        except (OSError, UnicodeEncodeError) as e:
            handle_error(ChangelogError(f"Unexpected error writing changelog: {e}"))
            return False, None
    elif not quiet:
        output = get_output_manager()
        output.success(f"Changelog updated incrementally: {changelog_file}")

    return True, token_usage
