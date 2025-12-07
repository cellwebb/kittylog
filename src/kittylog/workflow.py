"""Main workflow orchestration for kittylog.

This module contains the core business logic for changelog generation
workflow including mode selection, boundary processing, and coordination.
"""

from kittylog.ai import generate_changelog_entry
from kittylog.changelog.content import extract_preceding_entries
from kittylog.changelog.io import read_changelog
from kittylog.config import ChangelogOptions, WorkflowOptions, load_config
from kittylog.errors import AIError, ChangelogError, ConfigError, GitError, handle_error
from kittylog.mode_handlers import (
    handle_single_boundary_mode,
    handle_unreleased_mode,
)
from kittylog.utils.logging import get_logger, log_debug, log_info
from kittylog.workflow_ui import handle_dry_run_and_save
from kittylog.workflow_validation import validate_and_setup_workflow

logger = get_logger(__name__)


def _extract_bullet_points(entry: str) -> list[str]:
    """Extract bullet points from a generated changelog entry.

    Args:
        entry: Generated changelog entry text

    Returns:
        List of bullet point strings (without the leading "- ")
    """
    bullets = []
    for line in entry.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            bullets.append(line[2:])  # Remove "- " prefix
    return bullets


def _create_entry_generator(
    model: str,
    hint: str,
    show_prompt: bool,
    quiet: bool,
    include_diff: bool,
    language: str | None,
    translate_headings: bool,
    audience: str | None,
    changelog_file: str = "",
    context_entries_count: int = 0,
    detail_level: str = "normal",
):
    """Create a changelog entry generator function with captured parameters.

    Returns a function that can be passed to mode handlers as generate_entry_func.
    """
    # Track what's been generated in this session to prevent duplicates
    session_generated_items: list[str] = []

    def generator(commits: list[dict], tag: str, from_boundary: str | None = None, **kwargs) -> str:
        # Extract context entries fresh each time to include recently generated entries
        # This prevents duplicate content when processing multiple versions sequentially
        context_entries = ""
        if context_entries_count > 0 and changelog_file:
            try:
                changelog_content = read_changelog(changelog_file)
                context_entries = extract_preceding_entries(changelog_content, context_entries_count)
                if context_entries and not quiet:
                    log_debug(
                        logger,
                        "Extracted fresh context entries",
                        count=context_entries_count,
                        tag=tag,
                    )
            except (FileNotFoundError, OSError):
                # No existing changelog, so no context to extract
                pass

        # Build cumulative session context from previously generated items
        session_context = ""
        if session_generated_items:
            session_context = (
                "ITEMS ALREADY GENERATED IN THIS SESSION:\n"
                + "\n".join(f"- {item}" for item in session_generated_items)
            )

        entry, _usage = generate_changelog_entry(
            commits=commits,
            tag=tag,
            from_boundary=from_boundary,
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            quiet=quiet,
            language=language,
            translate_headings=translate_headings,
            audience=audience,
            context_entries=context_entries,
            session_context=session_context,
            detail_level=detail_level,
        )

        # Extract and accumulate bullet points from this entry for future reference
        new_items = _extract_bullet_points(entry)
        session_generated_items.extend(new_items)
        if new_items and not quiet:
            log_debug(
                logger,
                "Added items to session context",
                count=len(new_items),
                tag=tag,
            )

        return entry

    return generator


def process_workflow_modes(
    changelog_opts: ChangelogOptions,
    workflow_opts: WorkflowOptions,
    model: str,
    hint: str,
    effective_language: str | None,
    translate_headings: bool,
    effective_audience: str | None,
    incremental_save: bool = True,
) -> tuple[str, dict[str, int] | None]:
    """Process changelog workflow based on mode selection."""
    # Extract values from dataclasses
    changelog_file = changelog_opts.changelog_file
    from_tag = changelog_opts.from_tag
    to_tag = changelog_opts.to_tag
    special_unreleased_mode = changelog_opts.special_unreleased_mode
    grouping_mode = changelog_opts.grouping_mode

    # Log workflow start with context
    log_info(
        logger,
        "Starting workflow",
        grouping_mode=grouping_mode,
        changelog_file=changelog_file,
        from_tag=from_tag,
        to_tag=to_tag,
        special_unreleased=special_unreleased_mode,
    )

    show_prompt = workflow_opts.show_prompt
    quiet = workflow_opts.quiet
    dry_run = workflow_opts.dry_run
    update_all_entries = workflow_opts.update_all_entries
    no_unreleased = workflow_opts.no_unreleased

    include_diff = workflow_opts.include_diff
    context_entries_count = workflow_opts.context_entries_count

    # Create the entry generator function for mode handlers
    generate_entry_func = _create_entry_generator(
        model=model,
        hint=hint,
        show_prompt=show_prompt,
        quiet=quiet,
        include_diff=include_diff,
        language=effective_language,
        translate_headings=translate_headings,
        audience=effective_audience,
        changelog_file=changelog_file,
        context_entries_count=context_entries_count,
        detail_level=workflow_opts.detail_level,
    )

    # Handle special unreleased mode
    if special_unreleased_mode:
        _, content = handle_unreleased_mode(
            changelog_file=changelog_file,
            generate_entry_func=generate_entry_func,
            no_unreleased=no_unreleased,
            quiet=quiet,
            dry_run=dry_run,
            incremental_save=incremental_save,
        )
        return content, None

    # Handle different processing modes
    if from_tag is not None and to_tag is not None:
        # Range mode: process specific range (highest priority)
        # Look up boundaries by identifier
        from kittylog.tag_operations import get_boundary_by_identifier

        from_boundary = get_boundary_by_identifier(from_tag, grouping_mode)
        to_boundary = get_boundary_by_identifier(to_tag, grouping_mode)
        if to_boundary is None:
            raise ChangelogError(
                f"To boundary not found: {to_tag}",
                file_path=changelog_file,
            )

        # Note: handle_boundary_range_mode has different signature
        from kittylog.mode_handlers import handle_boundary_range_mode as range_handler

        _, content = range_handler(
            changelog_file=changelog_file,
            from_boundary=from_boundary,
            to_boundary=to_boundary,
            generate_entry_func=generate_entry_func,
            quiet=quiet,
            dry_run=dry_run,
            incremental_save=incremental_save,
        )
        return content, None

    if update_all_entries:
        # Update all existing entries (only when no from/to tags specified)
        from kittylog.mode_handlers import handle_update_all_mode

        _, content = handle_update_all_mode(
            changelog_file=changelog_file,
            generate_entry_func=generate_entry_func,
            mode=grouping_mode,
            quiet=quiet,
            dry_run=dry_run,
            incremental_save=incremental_save,
        )
        return content, None

    if from_tag is None and to_tag is None and not update_all_entries:
        # Normal mode: find missing entries
        from kittylog.mode_handlers import handle_missing_entries_mode

        _, content = handle_missing_entries_mode(
            changelog_file=changelog_file,
            generate_entry_func=generate_entry_func,
            mode=grouping_mode,  # ADD THIS
            date_grouping=changelog_opts.date_grouping,  # ADD THIS for dates mode
            gap_threshold=changelog_opts.gap_threshold_hours,  # ADD THIS for gaps mode
            quiet=quiet,
            dry_run=dry_run,
            incremental_save=incremental_save,
        )
        return content, None

    # Single tag mode: process specific tag
    assert to_tag is not None  # for mypy
    # Need to get boundary info first
    from kittylog.tag_operations import get_boundary_by_identifier

    boundary = get_boundary_by_identifier(to_tag, grouping_mode)
    if boundary is None:
        raise ChangelogError(
            f"Boundary not found: {to_tag}",
            file_path=changelog_file,
        )

    _, content = handle_single_boundary_mode(
        changelog_file=changelog_file,
        boundary=boundary,
        generate_entry_func=generate_entry_func,
        quiet=quiet,
        dry_run=dry_run,
        incremental_save=incremental_save,
    )
    return content, None


def main_business_logic(
    changelog_opts: ChangelogOptions,
    workflow_opts: WorkflowOptions,
    model: str | None = None,
    hint: str = "",
) -> tuple[bool, dict[str, int] | None]:
    """Modern main business logic using parameter objects.

    Replaces the massive 17-parameter function with clean, validated
    parameter objects. This is the new primary interface.

    Args:
        changelog_opts: Changelog file and boundary options
        workflow_opts: Workflow behavior and execution options
        model: AI model to use for generation
        hint: Additional context for AI generation

    Returns:
        Tuple of (success: bool, token_usage: dict | None)

    Examples:
        # Basic usage with defaults
        changelog_opts = ChangelogOptions()
        workflow_opts = WorkflowOptions()
        success, usage = main_business_logic(changelog_opts, workflow_opts)

        # Advanced usage
        changelog_opts = ChangelogOptions(
            grouping_mode=GroupingMode.DATES.value,
            date_grouping=DateGrouping.WEEKLY.value
        )
        workflow_opts = WorkflowOptions(dry_run=True, quiet=False)
        success, usage = main_business_logic(changelog_opts, workflow_opts)
    """
    log_debug(
        logger,
        "Main business logic started",
        grouping_mode=changelog_opts.grouping_mode,
        dry_run=workflow_opts.dry_run,
    )

    # Validate parameter objects (they handle their own validation)
    log_debug(logger, "Parameter objects validated")

    # Load config inside function to avoid module-level loading
    config = load_config()

    # Extract values from parameter objects for existing logic
    try:
        (
            changelog_file,
            effective_language,
            translate_headings,
            effective_audience,
        ) = validate_and_setup_workflow(
            changelog_opts=changelog_opts,
            workflow_opts=workflow_opts,
        )
    except (ConfigError, GitError, AIError, ChangelogError) as e:
        handle_error(e)
        return False, None

    # Get model from config if not specified
    if not model:
        model = config.model
        if not model:
            handle_error(Exception("No model specified in config"))
            return False, None

    # Store original content for change detection
    original_content = read_changelog(changelog_file)

    # Process workflow based on mode
    try:
        existing_content, token_usage = process_workflow_modes(
            changelog_opts=changelog_opts,
            workflow_opts=workflow_opts,
            model=model,
            hint=hint,
            effective_language=effective_language,
            translate_headings=translate_headings,
            effective_audience=effective_audience,
            incremental_save=workflow_opts.incremental_save,
        )
    except ChangelogError as e:
        handle_error(e)
        return False, None
    except (OSError, UnicodeEncodeError) as e:
        handle_error(ChangelogError(f"Unexpected error writing changelog: {e}"))
        return False, None

    # Handle dry run and saving
    return handle_dry_run_and_save(
        changelog_file=changelog_file,
        existing_content=existing_content,
        original_content=original_content,
        token_usage=token_usage,
        dry_run=workflow_opts.dry_run,
        quiet=workflow_opts.quiet,
        incremental_save=workflow_opts.incremental_save,
    )
