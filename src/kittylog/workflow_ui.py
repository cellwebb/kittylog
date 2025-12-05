"""Workflow UI components for kittylog.

This module contains user interface logic for changelog generation workflow
including dry run handling, confirmation prompts, and user interaction.
"""

import logging

import click

from kittylog.changelog.io import write_changelog
from kittylog.constants import Limits
from kittylog.errors import ChangelogError, handle_error
from kittylog.output import get_output_manager

logger = logging.getLogger(__name__)


def handle_dry_run_and_confirmation(
    changelog_file: str,
    existing_content: str,
    original_content: str,
    token_usage: dict[str, int] | None,
    dry_run: bool,
    require_confirmation: bool,
    quiet: bool,
    yes: bool,
    incremental_save: bool = False,
) -> tuple[bool, dict[str, int] | None]:
    """Handle dry run preview and confirmation logic."""
    # Show preview and get confirmation
    if dry_run:
        output = get_output_manager()
        output.warning("Dry run: Changelog content generated but not saved")
        output.echo("\nPreview of updated changelog:")
        output.panel(existing_content, title="Updated Changelog", style="cyan")
        return True, token_usage

    # Check if content actually changed (user might have cancelled)
    if existing_content == original_content:
        # No changes were made, skip save confirmation
        if not quiet:
            output = get_output_manager()
            output.info("No changes made to changelog.")
        return True, token_usage

    if require_confirmation and not quiet and not yes:
        output = get_output_manager()
        output.print("\n[bold green]Updated changelog preview:[/bold green]")
        # Show just the new parts for confirmation
        preview_lines = existing_content.split("\n")[: Limits.PREVIEW_LINE_COUNT]  # First N lines
        preview_text = "\n".join(preview_lines)
        if len(existing_content.split("\n")) > Limits.PREVIEW_LINE_COUNT:
            preview_text += "\n\n... (content truncated for preview)"

        output.panel(preview_text, title="Changelog Preview", style="cyan")

        # Display token usage if available
        if token_usage:
            output.info(
                f"Token usage: {token_usage['prompt_tokens']} input + {token_usage['completion_tokens']} output = {token_usage['total_tokens']} total"
            )

        proceed = click.confirm("\nSave the updated changelog?", default=True)
        if not proceed:
            output = get_output_manager()
            output.warning("Changelog update cancelled.")
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
