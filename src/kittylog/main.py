#!/usr/bin/env python3
"""Business logic for kittylog.

Orchestrates the changelog update workflow including git operations, AI generation, and file updates.
"""

import logging

import click

from kittylog.changelog import (
    create_changelog_header,
    find_existing_tags,
    read_changelog,
    update_changelog,
    write_changelog,
)
from kittylog.config import load_config
from kittylog.errors import AIError, GitError, handle_error
from kittylog.git_operations import (
    get_all_tags,
    get_commits_between_tags,
    get_latest_tag,
    get_previous_tag,
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
    """Handle unreleased changes workflow."""
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
    if grouping_mode != "tags":
        from kittylog.git_operations import get_latest_boundary, generate_boundary_identifier
        latest_boundary = get_latest_boundary(grouping_mode)
        latest_tag = generate_boundary_identifier(latest_boundary, grouping_mode) if latest_boundary else None
    else:
        latest_tag = get_latest_tag()
        
    logger.debug(f"Latest tag: {latest_tag}")

    # Update changelog for unreleased changes only - always replace in special unreleased mode
    updated_content, token_usage = update_changelog(
        existing_content=changelog_content,
        from_tag=latest_tag,
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
    from kittylog.git_operations import (
        get_all_boundaries,
        get_commits_between_boundaries,
        get_latest_boundary,
        get_previous_boundary,
        generate_boundary_identifier,
        generate_boundary_display_name,
    )
    
    # In simplified mode by default, process all boundaries with proper AI-generated content
    all_boundaries = get_all_boundaries(
        mode=grouping_mode,
        gap_threshold_hours=gap_threshold_hours,
        date_grouping=date_grouping
    )

    # If update_all_entries flag is set, process all boundaries; otherwise process only missing ones
    if not update_all_entries:
        # Read existing changelog content
        existing_content = read_changelog(changelog_file)
        
        # Find boundaries that already exist in changelog
        existing_boundaries = find_existing_tags(existing_content)

        # Filter to only process boundaries that are missing from changelog
        boundaries_to_process = [
            boundary for boundary in all_boundaries 
            if generate_boundary_identifier(boundary, grouping_mode) not in existing_boundaries
        ]

        if not quiet:
            missing_boundary_list = ", ".join([
                generate_boundary_display_name(boundary, grouping_mode) 
                for boundary in boundaries_to_process
            ]) if boundaries_to_process else "none"
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
                    unreleased_commits = get_commits_between_tags(
                        latest_boundary.get("identifier"), None
                    )
                else:
                    unreleased_commits = get_commits_between_boundaries(
                        latest_boundary, None, grouping_mode
                    )
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
            boundary_list = ", ".join([
                generate_boundary_display_name(boundary, grouping_mode)
                for boundary in boundaries_to_process
            ]) if boundaries_to_process else "none"
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
        boundary_list = ", ".join([
            generate_boundary_display_name(boundary, grouping_mode)
            for boundary in all_boundaries
        ]) if all_boundaries else "none"
        output = get_output_manager()
        output.info(f"Found {len(all_boundaries)} boundaries: {boundary_list}")

    # Process each boundary with AI-generated content (overwrite existing placeholders)
    for boundary in boundaries_to_process:
        logger.info(f"Processing boundary {generate_boundary_display_name(boundary, grouping_mode)}")

        if not quiet:
            output = get_output_manager()
            output.processing(f"Processing {generate_boundary_display_name(boundary, grouping_mode)}...")

        # Get previous boundary to determine the range
        if grouping_mode == "tags":
            previous_boundary = get_previous_tag(boundary.get("identifier"))
        else:
            previous_boundary = get_previous_boundary(boundary, grouping_mode)

        # Update changelog for this boundary only (overwrite existing content)
        changelog_content, token_usage = update_changelog(
            existing_content=changelog_content,
            from_tag=previous_boundary if grouping_mode == "tags" else (
                previous_boundary.get("identifier") if previous_boundary else None
            ),
            to_tag=boundary.get("identifier") if grouping_mode == "tags" else (
                generate_boundary_identifier(boundary, grouping_mode)
            ),
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
            unreleased_commits = get_commits_between_tags(
                latest_boundary.get("identifier"), None
            )
        else:
            unreleased_commits = get_commits_between_boundaries(
                latest_boundary, None, grouping_mode
            )
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


def handle_single_tag_mode(
    changelog_file: str,
    to_tag: str,
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
    # When only to_tag is specified, find the previous tag/boundary to use as from_tag
    changelog_content = read_changelog(changelog_file)

    # If changelog doesn't exist, create header
    if not changelog_content.strip():
        changelog_content = create_changelog_header(include_unreleased=not no_unreleased)
        logger.info("Created new changelog header")

    # Get previous boundary to determine the range
    if grouping_mode != "tags":
        from kittylog.git_operations import get_all_boundaries, get_previous_boundary, generate_boundary_identifier
        # We need to find the boundary corresponding to to_tag
        all_boundaries = get_all_boundaries(
            mode=grouping_mode,
            gap_threshold_hours=gap_threshold_hours,
            date_grouping=date_grouping
        )
        previous_tag = None
        target_boundary = None
        for i, boundary in enumerate(all_boundaries):
            if generate_boundary_identifier(boundary, grouping_mode) == to_tag:
                target_boundary = boundary
                if i > 0:
                    previous_tag = generate_boundary_identifier(all_boundaries[i-1], grouping_mode)
                break
        
        if target_boundary:
            # Get previous boundary if it exists
            prev_boundary = get_previous_boundary(target_boundary, grouping_mode)
            previous_tag = generate_boundary_identifier(prev_boundary, grouping_mode) if prev_boundary else None
    else:
        previous_tag = get_previous_tag(to_tag)

    if not quiet:
        output = get_output_manager()
        output.info(f"Processing tag {to_tag} (from {previous_tag or 'beginning'} to {to_tag})")

    # Update changelog for this specific tag only (overwrite if exists)
    changelog_content, token_usage = update_changelog(
        existing_content=changelog_content,
        from_tag=previous_tag,
        to_tag=to_tag,
        model=model,
        hint=hint,
        show_prompt=show_prompt,
        quiet=quiet,
        no_unreleased=no_unreleased,
    )

    return changelog_content, token_usage


def handle_tag_range_mode(
    changelog_file: str,
    from_tag: str | None,
    to_tag: str | None,
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
    if to_tag is None and not special_unreleased_mode:
        if grouping_mode != "tags":
            from kittylog.git_operations import get_latest_boundary, generate_boundary_identifier
            latest_boundary = get_latest_boundary(grouping_mode)
            to_tag = generate_boundary_identifier(latest_boundary, grouping_mode) if latest_boundary else None
        else:
            to_tag = get_latest_tag()
            
        if to_tag is None and grouping_mode == "tags":
            output = get_output_manager()
            output.error("No tags found in repository.")
            raise ValueError("No tags found in repository")
    elif from_tag is None and to_tag is not None and not special_unreleased_mode:
        # When only to_tag is specified, find the previous boundary to use as from_tag
        if grouping_mode != "tags":
            from kittylog.git_operations import get_all_boundaries, get_previous_boundary, generate_boundary_identifier
            # We need to find the boundary corresponding to to_tag
            all_boundaries = get_all_boundaries(
                mode=grouping_mode,
                gap_threshold_hours=gap_threshold_hours,
                date_grouping=date_grouping
            )
            from_tag = None
            target_boundary = None
            for i, boundary in enumerate(all_boundaries):
                if generate_boundary_identifier(boundary, grouping_mode) == to_tag:
                    target_boundary = boundary
                    if i > 0:
                        from_tag = generate_boundary_identifier(all_boundaries[i-1], grouping_mode)
                    break
            
            if target_boundary:
                # Get previous boundary if it exists
                prev_boundary = get_previous_boundary(target_boundary, grouping_mode)
                from_tag = generate_boundary_identifier(prev_boundary, grouping_mode) if prev_boundary else None
        else:
            from_tag = get_previous_tag(to_tag)

    logger.info(f"Processing specific range: {from_tag or 'beginning'} to {to_tag}")

    if not quiet:
        output = get_output_manager()
        output.info(f"Processing from {from_tag or 'beginning'} to {to_tag}")

    # Update changelog for specified range
    changelog_content, token_usage = update_changelog(
        file_path=changelog_file,
        from_tag=from_tag,
        to_tag=to_tag,
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
        # Validate we're in a git repository
        all_tags = get_all_tags()
        # In special_unreleased_mode, we don't require tags
        if not all_tags and not special_unreleased_mode:
            output = get_output_manager()
            output.warning("No git tags found. Create some tags first to generate changelog entries.")
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
                    changelog_file, model, hint, show_prompt, quiet, no_unreleased,
                    grouping_mode, gap_threshold_hours, date_grouping
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
                changelog_content, token_usage = handle_single_tag_mode(
                    changelog_file, to_tag, model, hint, show_prompt, quiet, no_unreleased,
                    grouping_mode, gap_threshold_hours, date_grouping
                )
            else:
                changelog_content, token_usage = handle_single_tag_mode(
                    changelog_file, to_tag, model, hint, show_prompt, quiet, no_unreleased
                )
        else:
            if grouping_mode != "tags":
                # Use boundary-aware function for non-tag modes
                changelog_content, token_usage = handle_tag_range_mode(
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
                changelog_content, token_usage = handle_tag_range_mode(
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
