#!/usr/bin/env python3
"""Business logic for kittylog.

Orchestrates the changelog update workflow including git operations, AI generation, and file updates.
"""

import logging

import click

from kittylog.changelog import (
    create_changelog_header,
    find_existing_boundaries,
    read_changelog,
    update_changelog,
    write_changelog,
)
from kittylog.config import load_config
from kittylog.errors import AIError, GitError, handle_error
from kittylog.git_operations import (
    generate_boundary_display_name,
    generate_boundary_identifier,
    get_all_boundaries,
    get_commits_between_boundaries,
    get_latest_boundary,
    get_previous_boundary,
    is_current_commit_tagged,
)
from kittylog.output import get_output_manager

logger = logging.getLogger(__name__)
config = load_config()


def handle_unreleased_mode(
    changelog_file: str,
    model: str,
    hint: str,
    show_prompt: bool,
    quiet: bool,
    no_unreleased: bool,
    grouping_mode: str = "tags",
    gap_threshold_hours: float = 4.0,
    date_grouping: str = "daily",
) -> tuple[str, dict[str, int] | None]:
    """Handle unreleased changes workflow for all boundary modes."""
    logger.debug(f"In special_unreleased_mode, changelog_file={changelog_file}")
    existing_content = read_changelog(changelog_file)

    # If changelog doesn't exist, create header
    if not existing_content.strip():
        changelog_content = create_changelog_header(include_unreleased=not no_unreleased)
        logger.info("Created new changelog header")
    else:
        changelog_content = existing_content

    logger.debug(f"Existing changelog content: {repr(changelog_content[:200])}")

    # Process only the unreleased section
    logger.info("Processing unreleased section only")

    output = get_output_manager()
    output.processing("Processing unreleased section...")

    # Get latest boundary for commit range based on mode
    latest_boundary = get_latest_boundary(grouping_mode)
    from_boundary = generate_boundary_identifier(latest_boundary, grouping_mode) if latest_boundary else None

    logger.debug(f"From boundary: {from_boundary}")

    # Update changelog for unreleased changes only - always replace in special unreleased mode
    updated_content, token_usage = update_changelog(
        existing_content=changelog_content,
        from_tag=from_boundary,
        to_tag=None,  # None means HEAD for unreleased
        model=model,
        hint=hint,
        show_prompt=show_prompt,
        quiet=quiet,
        no_unreleased=no_unreleased,
    )
    logger.debug(f"Updated changelog_content different from original: {updated_content != changelog_content}")
    return updated_content, token_usage


def handle_auto_mode(
    changelog_file: str,
    model: str,
    hint: str,
    show_prompt: bool,
    quiet: bool,
    update_all_entries: bool,
    special_unreleased_mode: bool = False,
    no_unreleased: bool = False,
    grouping_mode: str = "tags",
    gap_threshold_hours: float = 4.0,
    date_grouping: str = "daily",
) -> tuple[str, dict[str, int] | None]:
    """Handle automatic boundary detection workflow."""

    # In simplified mode by default, process all boundaries with proper AI-generated content
    all_boundaries = get_all_boundaries(
        mode=grouping_mode, gap_threshold_hours=gap_threshold_hours, date_grouping=date_grouping
    )

    # If update_all_entries flag is set, process all boundaries; otherwise process only missing ones
    if not update_all_entries:
        # Read existing changelog content
        existing_content = read_changelog(changelog_file)

        # Find boundaries that already exist in changelog
        existing_boundaries = find_existing_boundaries(existing_content)

        # Filter to only process boundaries that are missing from changelog
        boundaries_to_process = [
            boundary
            for boundary in all_boundaries
            if generate_boundary_identifier(boundary, grouping_mode) not in existing_boundaries
        ]

        if not quiet:
            missing_boundary_list = (
                ", ".join(
                    [generate_boundary_display_name(boundary, grouping_mode) for boundary in boundaries_to_process]
                )
                if boundaries_to_process
                else "none"
            )
            existing_boundary_list = ", ".join(existing_boundaries) if existing_boundaries else "none"
            output = get_output_manager()
            output.info(f"Found {len(all_boundaries)} total boundaries")
            output.info(f"Existing boundaries in changelog: {existing_boundary_list}")
            output.info(f"Missing boundaries to process: {missing_boundary_list}")

        # If no boundaries to process and no unreleased changes, return early
        if not boundaries_to_process:
            has_unreleased_changes = False
            latest_boundary = get_latest_boundary(grouping_mode)
            if latest_boundary and not is_current_commit_tagged():
                # If the current commit isn't tagged, we have unreleased changes
                # But only if there are actually commits since the last boundary
                if grouping_mode == "tags":
                    unreleased_commits = get_commits_between_tags(latest_boundary.get("identifier"), None)
                else:
                    unreleased_commits = get_commits_between_boundaries(latest_boundary, None, grouping_mode)
                if len(unreleased_commits) > 0:
                    has_unreleased_changes = True
            elif not latest_boundary and not is_current_commit_tagged():
                # If no boundaries exist in repo at all, check if we have commits
                if grouping_mode == "tags":
                    all_commits = get_commits_between_tags(None, None)
                else:
                    all_commits = get_commits_between_boundaries(None, None, grouping_mode)
                if all_commits:
                    has_unreleased_changes = True

            # Only process unreleased changes if there are any or if in special mode
            if not has_unreleased_changes and not special_unreleased_mode:
                return existing_content, None
    else:
        # Process all boundaries when update_all_entries is True
        boundaries_to_process = all_boundaries
        if not quiet:
            boundary_list = (
                ", ".join(
                    [generate_boundary_display_name(boundary, grouping_mode) for boundary in boundaries_to_process]
                )
                if boundaries_to_process
                else "none"
            )
            output = get_output_manager()
            output.info(f"Updating all {len(boundaries_to_process)} boundaries: {boundary_list}")

    # Read existing changelog content
    existing_content = read_changelog(changelog_file)

    # If changelog doesn't exist, create header
    if not existing_content.strip():
        changelog_content = create_changelog_header(include_unreleased=not no_unreleased)
        logger.info("Created new changelog header")
    else:
        changelog_content = existing_content

    logger.info(f"Found {len(all_boundaries)} boundaries: {all_boundaries}")

    if not quiet:
        boundary_list = (
            ", ".join([generate_boundary_display_name(boundary, grouping_mode) for boundary in all_boundaries])
            if all_boundaries
            else "none"
        )
        output = get_output_manager()
        output.info(f"Found {len(all_boundaries)} boundaries: {boundary_list}")

    # Process each boundary with AI-generated content (overwrite existing placeholders)
    for boundary in boundaries_to_process:
        logger.info(f"Processing boundary {generate_boundary_display_name(boundary, grouping_mode)}")

        if not quiet:
            output = get_output_manager()
            output.processing(f"Processing {generate_boundary_display_name(boundary, grouping_mode)}...")

        # Get previous boundary to determine the range
        previous_boundary = get_previous_boundary(boundary, grouping_mode)

        # Update changelog for this boundary only (overwrite existing content)
        changelog_content, token_usage = update_changelog(
            existing_content=changelog_content,
            from_tag=previous_boundary
            if grouping_mode == "tags"
            else (previous_boundary.get("identifier") if previous_boundary else None),
            to_tag=boundary.get("identifier")
            if grouping_mode == "tags"
            else (generate_boundary_identifier(boundary, grouping_mode)),
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            quiet=quiet,
            no_unreleased=no_unreleased,
        )

    # Check if we have unreleased changes
    has_unreleased_changes = False
    latest_boundary = get_latest_boundary(grouping_mode)
    if latest_boundary and not is_current_commit_tagged():
        # If the current commit isn't tagged, we have unreleased changes
        # But only if there are actually commits since the last boundary
        if grouping_mode == "tags":
            unreleased_commits = get_commits_between_tags(latest_boundary.get("identifier"), None)
        else:
            unreleased_commits = get_commits_between_boundaries(latest_boundary, None, grouping_mode)
        if len(unreleased_commits) > 0:
            has_unreleased_changes = True
    elif not latest_boundary and not is_current_commit_tagged():
        # If no boundaries exist in repo at all, check if we have commits
        if grouping_mode == "tags":
            all_commits = get_commits_between_tags(None, None)
        else:
            all_commits = get_commits_between_boundaries(None, None, grouping_mode)
        if all_commits:
            has_unreleased_changes = True

    # Process unreleased changes if needed
    if has_unreleased_changes or special_unreleased_mode:
        logger.info("Processing unreleased changes")

        if not quiet:
            output = get_output_manager()
            output.processing("Processing unreleased changes...")

        # Update changelog for unreleased changes
        changelog_content, unreleased_token_usage = update_changelog(
            existing_content=changelog_content,
            from_tag=latest_boundary.get("identifier") if latest_boundary and grouping_mode == "tags" else None,
            to_tag=None,  # None means HEAD
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            quiet=quiet,
            no_unreleased=no_unreleased,
        )

        # Keep the token usage for display
        token_usage = unreleased_token_usage

    return changelog_content, token_usage


def handle_single_boundary_mode(
    changelog_file: str,
    to_boundary: str,
    model: str,
    hint: str,
    show_prompt: bool,
    quiet: bool,
    no_unreleased: bool,
    grouping_mode: str = "tags",
    gap_threshold_hours: float = 4.0,
    date_grouping: str = "daily",
) -> tuple[str, dict[str, int] | None]:
    """Handle single boundary processing workflow."""
    # When only to_boundary is specified, find the previous boundary to use as from_boundary
    changelog_content = read_changelog(changelog_file)

    # If changelog doesn't exist, create header
    if not changelog_content.strip():
        changelog_content = create_changelog_header(include_unreleased=not no_unreleased)
        logger.info("Created new changelog header")

    # Get previous boundary to determine the range
    if grouping_mode != "tags":
        from kittylog.git_operations import generate_boundary_identifier, get_all_boundaries, get_previous_boundary

        # We need to find the boundary corresponding to to_boundary
        all_boundaries = get_all_boundaries(
            mode=grouping_mode, gap_threshold_hours=gap_threshold_hours, date_grouping=date_grouping
        )
        previous_boundary = None
        target_boundary = None
        for i, boundary in enumerate(all_boundaries):
            if generate_boundary_identifier(boundary, grouping_mode) == to_boundary:
                target_boundary = boundary
                if i > 0:
                    previous_boundary = generate_boundary_identifier(all_boundaries[i - 1], grouping_mode)
                break

        if target_boundary:
            # Get previous boundary if it exists
            prev_boundary = get_previous_boundary(target_boundary, grouping_mode)
            previous_boundary = generate_boundary_identifier(prev_boundary, grouping_mode) if prev_boundary else None
    else:
        # For tags mode, we need to find the boundary object first
        target_boundary = None
        for boundary in get_all_boundaries(mode="tags"):
            if generate_boundary_identifier(boundary, "tags") == to_boundary:
                target_boundary = boundary
                break

        if target_boundary:
            prev_boundary = get_previous_boundary(target_boundary, "tags")
            previous_boundary = generate_boundary_identifier(prev_boundary, "tags") if prev_boundary else None
        else:
            previous_boundary = None

    if not quiet:
        output = get_output_manager()
        output.info(f"Processing boundary {to_boundary} (from {previous_boundary or 'beginning'} to {to_boundary})")

    # Update changelog for this specific boundary only (overwrite if exists)
    changelog_content, token_usage = update_changelog(
        existing_content=changelog_content,
        from_tag=previous_boundary,
        to_tag=to_boundary,
        model=model,
        hint=hint,
        show_prompt=show_prompt,
        quiet=quiet,
        no_unreleased=no_unreleased,
    )

    return changelog_content, token_usage


def handle_boundary_range_mode(
    changelog_file: str,
    from_boundary: str | None,
    to_boundary: str | None,
    model: str,
    hint: str,
    show_prompt: bool,
    quiet: bool,
    special_unreleased_mode: bool = False,
    no_unreleased: bool = False,
    grouping_mode: str = "tags",
    gap_threshold_hours: float = 4.0,
    date_grouping: str = "daily",
) -> tuple[str, dict[str, int] | None]:
    """Handle boundary range processing workflow."""
    # Process specific boundary range
    if to_boundary is None and not special_unreleased_mode:
        latest_boundary = get_latest_boundary(grouping_mode)
        to_boundary = generate_boundary_identifier(latest_boundary, grouping_mode) if latest_boundary else None

        if to_boundary is None and grouping_mode == "tags":
            output = get_output_manager()
            output.error("No tags found in repository.")
            raise ValueError("No tags found in repository")
    elif from_boundary is None and to_boundary is not None and not special_unreleased_mode:
        # When only to_boundary is specified, find the previous boundary to use as from_boundary
        if grouping_mode != "tags":
            from kittylog.git_operations import generate_boundary_identifier, get_all_boundaries, get_previous_boundary

            # We need to find the boundary corresponding to to_boundary
            all_boundaries = get_all_boundaries(
                mode=grouping_mode, gap_threshold_hours=gap_threshold_hours, date_grouping=date_grouping
            )
            from_boundary = None
            target_boundary = None
            for i, boundary in enumerate(all_boundaries):
                if generate_boundary_identifier(boundary, grouping_mode) == to_boundary:
                    target_boundary = boundary
                    if i > 0:
                        from_boundary = generate_boundary_identifier(all_boundaries[i - 1], grouping_mode)
                    break

            if target_boundary:
                # Get previous boundary if it exists
                prev_boundary = get_previous_boundary(target_boundary, grouping_mode)
                from_boundary = generate_boundary_identifier(prev_boundary, grouping_mode) if prev_boundary else None
        else:
            # For tags mode, we need to find the boundary object first
            target_boundary = None
            for boundary in get_all_boundaries(mode="tags"):
                if generate_boundary_identifier(boundary, "tags") == to_boundary:
                    target_boundary = boundary
                    break

            if target_boundary:
                prev_boundary = get_previous_boundary(target_boundary, "tags")
                from_boundary = generate_boundary_identifier(prev_boundary, "tags") if prev_boundary else None
            else:
                from_boundary = None

    logger.info(f"Processing specific range: {from_boundary or 'beginning'} to {to_boundary}")

    if not quiet:
        output = get_output_manager()
        output.info(f"Processing from {from_boundary or 'beginning'} to {to_boundary}")

    # Update changelog for specified range
    changelog_content, token_usage = update_changelog(
        file_path=changelog_file,
        from_tag=from_boundary,
        to_tag=to_boundary,
        model=model,
        hint=hint,
        show_prompt=show_prompt,
        quiet=quiet,
        no_unreleased=no_unreleased,
    )

    return changelog_content, token_usage


def main_business_logic(
    changelog_file: str = "CHANGELOG.md",
    from_tag: str | None = None,
    to_tag: str | None = None,
    model: str | None = None,
    hint: str = "",
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
) -> tuple[bool, dict[str, int] | None]:
    """Main application logic for kittylog.

    Returns True on success, False on failure.
    """
    logger.debug(f"main_business_logic called with special_unreleased_mode={special_unreleased_mode}")

    # Auto-detect changelog file if using default
    if changelog_file == "CHANGELOG.md":
        from kittylog.utils import find_changelog_file

        changelog_file = find_changelog_file()
        logger.debug(f"Auto-detected changelog file: {changelog_file}")

    try:
        # Validate we're in a git repository and have boundaries
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
            return True, None

    except GitError as e:
        handle_error(e)
        return False, None

    if model is None:
        model_value = config["model"]
        if model_value is None:
            print("DEBUG: No model specified in config")
            handle_error(
                AIError.model_error(
                    "No model specified. Please set the KITTYLOG_MODEL environment variable or use --model."
                )
            )
            return False, None
        model = str(model_value)

    # Determine which workflow to use based on input parameters
    token_usage = None
    try:
        if special_unreleased_mode:
            if grouping_mode != "tags":
                # Use boundary-aware function for non-tag modes
                changelog_content, token_usage = handle_unreleased_mode(
                    changelog_file,
                    model,
                    hint,
                    show_prompt,
                    quiet,
                    no_unreleased,
                    grouping_mode,
                    gap_threshold_hours,
                    date_grouping,
                )
            else:
                changelog_content, token_usage = handle_unreleased_mode(
                    changelog_file, model, hint, show_prompt, quiet, no_unreleased
                )
        elif from_tag is None and to_tag is None:
            if grouping_mode != "tags":
                # Use boundary-aware function for non-tag modes
                changelog_content, token_usage = handle_auto_mode(
                    changelog_file,
                    model,
                    hint,
                    show_prompt,
                    quiet,
                    update_all_entries,
                    special_unreleased_mode,
                    no_unreleased,
                    grouping_mode,
                    gap_threshold_hours,
                    date_grouping,
                )
            else:
                changelog_content, token_usage = handle_auto_mode(
                    changelog_file,
                    model,
                    hint,
                    show_prompt,
                    quiet,
                    update_all_entries,
                    special_unreleased_mode,
                    no_unreleased,
                )
        elif to_tag is not None and from_tag is None:
            if grouping_mode != "tags":
                # Use boundary-aware function for non-tag modes
                changelog_content, token_usage = handle_single_boundary_mode(
                    changelog_file,
                    to_tag,
                    model,
                    hint,
                    show_prompt,
                    quiet,
                    no_unreleased,
                    grouping_mode,
                    gap_threshold_hours,
                    date_grouping,
                )
            else:
                changelog_content, token_usage = handle_single_boundary_mode(
                    changelog_file, to_tag, model, hint, show_prompt, quiet, no_unreleased
                )
        else:
            if grouping_mode != "tags":
                # Use boundary-aware function for non-tag modes
                changelog_content, token_usage = handle_boundary_range_mode(
                    changelog_file,
                    from_tag,
                    to_tag,
                    model,
                    hint,
                    show_prompt,
                    quiet,
                    special_unreleased_mode,
                    no_unreleased,
                    grouping_mode,
                    gap_threshold_hours,
                    date_grouping,
                )
            else:
                changelog_content, token_usage = handle_boundary_range_mode(
                    changelog_file,
                    from_tag,
                    to_tag,
                    model,
                    hint,
                    show_prompt,
                    quiet,
                    special_unreleased_mode,
                    no_unreleased,
                )
    except Exception as e:
        handle_error(e)
        return False, None

    # Show preview and get confirmation
    if dry_run:
        output = get_output_manager()
        output.warning("Dry run: Changelog content generated but not saved")
        output.echo("\nPreview of updated changelog:")
        output.panel(changelog_content, title="Updated Changelog", style="cyan")
        return True, token_usage

    if require_confirmation:
        output = get_output_manager()
        output.print("\n[bold green]Updated changelog preview:[/bold green]")
        # Show just the new parts for confirmation
        preview_lines = changelog_content.split("\n")[:50]  # First 50 lines
        preview_text = "\n".join(preview_lines)
        if len(changelog_content.split("\n")) > 50:
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
        write_changelog(changelog_file, changelog_content)
    except Exception as e:
        handle_error(e)
        return False, None

    if not quiet:
        logger.info(f"Successfully updated changelog: {changelog_file}")

    return True, token_usage
