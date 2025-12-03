"""Main workflow orchestration for kittylog.

This module contains the core business logic for changelog generation
workflow including mode selection, boundary processing, and coordination.
"""

import logging
from pathlib import Path

import click

from kittylog.changelog import read_changelog, write_changelog
from kittylog.config import load_config
from kittylog.constants import Audiences, Languages
from kittylog.errors import AIError, ChangelogError, ConfigError, GitError, handle_error
from kittylog.git_operations import get_all_boundaries
from kittylog.mode_handlers import (
    handle_boundary_range_mode,
    handle_single_boundary_mode,
    handle_unreleased_mode,
)
from kittylog.output import get_output_manager
from kittylog.utils import find_changelog_file

logger = logging.getLogger(__name__)
config = load_config()


def process_workflow_modes(
    changelog_file: str,
    from_tag: str | None,
    to_tag: str | None,
    model: str,
    hint: str,
    show_prompt: bool,
    quiet: bool,
    dry_run: bool,
    special_unreleased_mode: bool,
    update_all_entries: bool,
    no_unreleased: bool,
    grouping_mode: str,
    gap_threshold_hours: float,
    date_grouping: str,
    yes: bool,
    include_diff: bool,
    effective_language: str | None,
    translate_headings: bool,
    effective_audience: str | None,
) -> tuple[str, dict[str, int] | None]:
    """Process changelog workflow based on mode selection."""
    # Handle special unreleased mode
    if special_unreleased_mode:
        return handle_unreleased_mode(
            changelog_file=changelog_file,
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            quiet=quiet,
            no_unreleased=no_unreleased,
            grouping_mode=grouping_mode,
            gap_threshold_hours=gap_threshold_hours,
            date_grouping=date_grouping,
            yes=yes,
            include_diff=include_diff,
            language=effective_language,
            translate_headings=translate_headings,
            audience=effective_audience,
        )

    # Handle different processing modes
    if from_tag is None and to_tag is None and not update_all_entries:
        # Normal mode: find missing entries
        from kittylog.mode_handlers import handle_missing_entries_mode

        return handle_missing_entries_mode(
            changelog_file=changelog_file,
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            quiet=quiet,
            no_unreleased=no_unreleased,
            grouping_mode=grouping_mode,
            gap_threshold_hours=gap_threshold_hours,
            date_grouping=date_grouping,
            yes=yes,
            include_diff=include_diff,
            language=effective_language,
            translate_headings=translate_headings,
            audience=effective_audience,
        )

    if update_all_entries:
        # Update all existing entries
        from kittylog.mode_handlers import handle_update_all_mode

        return handle_update_all_mode(
            changelog_file=changelog_file,
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            quiet=quiet,
            no_unreleased=no_unreleased,
            grouping_mode=grouping_mode,
            gap_threshold_hours=gap_threshold_hours,
            date_grouping=date_grouping,
            yes=yes,
            include_diff=include_diff,
            language=effective_language,
            translate_headings=translate_headings,
            audience=effective_audience,
        )

    if from_tag is not None and to_tag is not None:
        # Range mode: process specific range
        return handle_boundary_range_mode(
            changelog_file=changelog_file,
            from_boundary=from_tag,
            to_boundary=to_tag,
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            quiet=quiet,
            special_unreleased_mode=False,
            no_unreleased=no_unreleased,
            grouping_mode=grouping_mode,
            gap_threshold_hours=gap_threshold_hours,
            date_grouping=date_grouping,
            yes=yes,
            include_diff=include_diff,
            language=effective_language,
            translate_headings=translate_headings,
            audience=effective_audience,
        )

    # Single tag mode: process specific tag
    assert to_tag is not None  # for mypy
    return handle_single_boundary_mode(
        changelog_file=changelog_file,
        to_boundary=to_tag,
        model=model,
        hint=hint,
        show_prompt=show_prompt,
        quiet=quiet,
        no_unreleased=no_unreleased,
        yes=yes,
        include_diff=include_diff,
        language=effective_language,
        translate_headings=translate_headings,
        audience=effective_audience,
        grouping_mode=grouping_mode,
        gap_threshold_hours=gap_threshold_hours,
        date_grouping=date_grouping,
    )


def handle_dry_run_and_confirmation(
    changelog_file: str,
    existing_content: str,
    original_content: str,
    token_usage: dict[str, int] | None,
    dry_run: bool,
    require_confirmation: bool,
    quiet: bool,
    yes: bool,
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
        preview_lines = existing_content.split("\n")[:50]  # First 50 lines
        preview_text = "\n".join(preview_lines)
        if len(existing_content.split("\n")) > 50:
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

    # Write the updated changelog
    try:
        write_changelog(changelog_file, existing_content)
    except Exception as e:
        handle_error(e)
        return False, None

    if not quiet:
        logger.info(f"Successfully updated changelog: {changelog_file}")

    return True, token_usage


def validate_workflow_prereqs(
    changelog_file: str,
    gap_threshold_hours: float,
    grouping_mode: str,
) -> None:
    """Perform early validation of workflow requirements.

    Args:
        changelog_file: Path to changelog file
        gap_threshold_hours: Gap threshold for date/gaps mode
        grouping_mode: The boundary grouping mode

    Raises:
        ChangelogError: If changelog file is not writable
        GitError: If git repository is invalid
        ConfigError: If gap_threshold_hours is invalid
    """
    import os

    from kittylog.git_operations import get_repo

    # Validate changelog file is writable
    try:
        # Check if we can write to the directory
        changelog_dir = Path(changelog_file).resolve().parent
        if not os.access(str(changelog_dir), os.W_OK):
            raise ChangelogError(f"Cannot write to changelog directory: {changelog_dir}")

        # If file exists, check if it's writable
        changelog_path = Path(changelog_file)
        if changelog_path.exists() and not os.access(changelog_file, os.W_OK):
            raise ChangelogError(f"Changelog file is not writable: {changelog_file}")

    except OSError as e:
        raise ChangelogError(f"Cannot access changelog file: {e}") from e

    # Validate git repository exists and is valid
    try:
        get_repo()  # This will raise GitError if invalid
    except Exception as e:
        raise GitError(f"Invalid git repository: {e}") from e

    # Validate gap threshold bounds
    if grouping_mode in ["gaps", "dates"] and (gap_threshold_hours <= 0 or gap_threshold_hours > 168):  # 1 week max
        raise ConfigError(
            f"gap_threshold_hours must be between 0 and 168, got: {gap_threshold_hours}",
            config_key="gap_threshold_hours",
            config_value=str(gap_threshold_hours),
        )


def validate_and_setup_workflow(
    changelog_file: str,
    language: str | None,
    audience: str | None,
    grouping_mode: str,
    gap_threshold_hours: float,
    date_grouping: str,
    special_unreleased_mode: bool,
) -> tuple[str, str | None, bool, str | None]:
    """Validate inputs and setup workflow parameters."""
    # Early validation
    validate_workflow_prereqs(changelog_file, gap_threshold_hours, grouping_mode)

    # Auto-detect changelog file if using default
    if changelog_file == "CHANGELOG.md":
        changelog_file = find_changelog_file()
        logger.debug(f"Auto-detected changelog file: {changelog_file}")

    # Determine language preferences (CLI overrides config)
    effective_language = language.strip() if language else None
    if not effective_language:
        config_language_value = config.get("language")
        effective_language = config_language_value.strip() if config_language_value else None

    if effective_language:
        effective_language = Languages.resolve_code(effective_language)

    translate_headings_value = config.get("translate_headings")
    translate_headings = translate_headings_value is True  # Explicit True check, False/None → False
    if not effective_language:
        translate_headings = False

    config_audience = config.get("audience")
    effective_audience = Audiences.resolve(audience) if audience else Audiences.resolve(config_audience)

    # Validate we're in a git repository and have boundaries
    try:
        all_boundaries = get_all_boundaries(
            mode=grouping_mode, gap_threshold_hours=gap_threshold_hours, date_grouping=date_grouping
        )
        # In special_unreleased_mode, we don't require boundaries
        if not all_boundaries and not special_unreleased_mode:
            output = get_output_manager()
            if grouping_mode == "tags":
                output.warning("No git tags found. Create some tags first to generate changelog entries.")
                output.info(
                    "💡 Tip: Try 'git tag v1.0.0' to create your first tag, or use --grouping-mode dates/gaps for tagless workflows"
                )
            elif grouping_mode == "dates":
                output.warning("No date-based boundaries found. This repository might have very few commits.")
                output.info(
                    "💡 Tip: Try --date-grouping weekly/monthly for longer periods, or --grouping-mode gaps for activity-based grouping"
                )
            elif grouping_mode == "gaps":
                output.warning(f"No gap-based boundaries found with {gap_threshold_hours} hour threshold.")
                output.info(
                    f"💡 Tip: Try --gap-threshold {gap_threshold_hours / 2} for shorter gaps, or --grouping-mode dates for time-based grouping"
                )
            raise GitError(f"No {grouping_mode} boundaries found in repository")
    except GitError:
        # Re-raise GitError for no boundaries - it will be caught upstream
        raise
    except Exception as e:
        handle_error(e)
        raise

    return changelog_file, effective_language, translate_headings, effective_audience


def main_business_logic(
    changelog_file: str = "CHANGELOG.md",
    from_tag: str | None = None,
    to_tag: str | None = None,
    model: str | None = None,
    hint: str = "",
    language: str | None = None,
    audience: str | None = None,
    show_prompt: bool = False,
    require_confirmation: bool = True,
    quiet: bool = False,
    dry_run: bool = False,
    special_unreleased_mode: bool = False,
    update_all_entries: bool = False,
    no_unreleased: bool = False,
    grouping_mode: str = "tags",
    gap_threshold_hours: float = 4.0,
    date_grouping: str = "daily",
    yes: bool = False,
    include_diff: bool = False,
) -> tuple[bool, dict[str, int] | None]:
    """Main application logic for kittylog.

    Orchestrates the changelog generation process using configurable boundary detection modes.
    Supports tags (default), dates, and gap-based grouping for flexible changelog workflows.

    Args:
        changelog_file: Path to changelog file
        from_tag: Starting boundary identifier (optional)
        to_tag: Ending boundary identifier (optional)
        model: AI model to use for generation
        hint: Additional context for AI generation
        language: Override language for changelog entries
        audience: Override audience slug influencing tone (developers/users/stakeholders)
        show_prompt: Display the AI prompt
        require_confirmation: Ask for user confirmation
        quiet: Suppress output
        dry_run: Preview only, don't write changes
        special_unreleased_mode: Handle unreleased section only
        update_all_entries: Update all existing entries
        no_unreleased: Skip unreleased section management
        grouping_mode: Boundary detection mode ('tags', 'dates', 'gaps')
        gap_threshold_hours: Hours threshold for gap detection (gaps mode)
        date_grouping: Date grouping granularity ('daily', 'weekly', 'monthly')

    Returns:
        Tuple of (success: bool, token_usage: dict | None)

    Examples:
        # Default tags mode
        success, usage = main_business_logic()

        # Date-based grouping
        success, usage = main_business_logic(grouping_mode="dates", date_grouping="weekly")

        # Gap-based grouping with 8-hour threshold
        success, usage = main_business_logic(grouping_mode="gaps", gap_threshold_hours=8.0)
    """
    logger.debug(f"main_business_logic called with special_unreleased_mode={special_unreleased_mode}")

    # Validate and setup workflow
    try:
        (
            changelog_file,
            effective_language,
            translate_headings,
            effective_audience,
        ) = validate_and_setup_workflow(
            changelog_file=changelog_file,
            language=language,
            audience=audience,
            grouping_mode=grouping_mode,
            gap_threshold_hours=gap_threshold_hours,
            date_grouping=date_grouping,
            special_unreleased_mode=special_unreleased_mode,
        )
    except (ConfigError, GitError, AIError, ChangelogError) as e:
        handle_error(e)
        return False, None

    # Get model from config if not specified
    if not model:
        model = config.get("model")
        if not model:
            handle_error(Exception("No model specified in config"))
            return False, None

    # Store original content for change detection
    original_content = read_changelog(changelog_file)

    # Process workflow based on mode
    try:
        existing_content, token_usage = process_workflow_modes(
            changelog_file=changelog_file,
            from_tag=from_tag,
            to_tag=to_tag,
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            quiet=quiet,
            dry_run=dry_run,
            special_unreleased_mode=special_unreleased_mode,
            update_all_entries=update_all_entries,
            no_unreleased=no_unreleased,
            grouping_mode=grouping_mode,
            gap_threshold_hours=gap_threshold_hours,
            date_grouping=date_grouping,
            yes=yes,
            include_diff=include_diff,
            effective_language=effective_language,
            translate_headings=translate_headings,
            effective_audience=effective_audience,
        )
    except Exception as e:
        handle_error(e)
        return False, None

    # Handle dry run, confirmation, and saving
    return handle_dry_run_and_confirmation(
        changelog_file=changelog_file,
        existing_content=existing_content,
        original_content=original_content,
        token_usage=token_usage,
        dry_run=dry_run,
        require_confirmation=require_confirmation,
        quiet=quiet,
        yes=yes,
    )
