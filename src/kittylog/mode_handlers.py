"""Mode handlers for different changelog processing modes.

This module contains handlers for unreleased mode, single boundary mode,
range mode, and update-all mode workflows.
"""

import logging

import click

from kittylog.ai import generate_changelog_entry
from kittylog.changelog import (
    find_existing_boundaries,
    read_changelog,
    update_changelog,
)
from kittylog.commit_analyzer import (
    get_commits_between_boundaries,
    get_commits_between_tags,
)
from kittylog.output import get_output_manager
from kittylog.tag_operations import (
    generate_boundary_display_name,
    generate_boundary_identifier,
    get_all_boundaries,
    get_latest_boundary,
    get_latest_tag,
    get_previous_boundary,
    is_current_commit_tagged,
)
from kittylog.utils import determine_next_version

logger = logging.getLogger(__name__)


def _find_previous_boundary_id(
    target_boundary_id: str,
    grouping_mode: str,
    gap_threshold_hours: float = 4.0,
    date_grouping: str = "daily",
) -> str | None:
    """Find the previous boundary identifier for a given target boundary.

    Args:
        target_boundary_id: The identifier of the target boundary
        grouping_mode: The boundary grouping mode (tags, dates, gaps)
        gap_threshold_hours: Gap threshold for gaps mode
        date_grouping: Date grouping for dates mode

    Returns:
        The previous boundary identifier, or None if target is the first boundary
    """
    if grouping_mode == "tags":
        all_boundaries = get_all_boundaries(mode="tags")
    else:
        all_boundaries = get_all_boundaries(
            mode=grouping_mode, gap_threshold_hours=gap_threshold_hours, date_grouping=date_grouping
        )

    for i, boundary in enumerate(all_boundaries):
        if generate_boundary_identifier(boundary, grouping_mode) == target_boundary_id:
            if i > 0:
                return generate_boundary_identifier(all_boundaries[i - 1], grouping_mode)
            return None
    return None


def _ensure_changelog_exists(changelog_file: str, no_unreleased: bool) -> str:
    """Create changelog with header if it doesn't exist, return content.

    Args:
        changelog_file: Path to the changelog file
        no_unreleased: Whether to exclude the unreleased section

    Returns:
        The changelog content (new if created, existing if already present)
    """
    from kittylog.changelog_io import create_changelog_header

    changelog_content = read_changelog(changelog_file)
    if not changelog_content.strip():
        changelog_content = create_changelog_header(include_unreleased=not no_unreleased)
    return changelog_content


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
    yes: bool = False,
    include_diff: bool = False,
    language: str | None = None,
    translate_headings: bool = False,
    audience: str | None = None,
) -> tuple[str, dict[str, int] | None]:
    """Handle unreleased changes workflow for all boundary modes."""
    logger.debug(f"In special_unreleased_mode, changelog_file={changelog_file}")
    changelog_content = _ensure_changelog_exists(changelog_file, no_unreleased)

    logger.debug(f"Existing changelog content: {changelog_content[:200]!r}")

    # Get latest tag to determine next version
    latest_tag = get_latest_tag()
    latest_boundary = get_latest_boundary(grouping_mode)

    # Get commits for version analysis
    from_boundary = generate_boundary_identifier(latest_boundary, grouping_mode) if latest_boundary else None
    commits = get_commits_between_boundaries(latest_boundary, None, grouping_mode)

    # Determine next version
    next_version = determine_next_version(latest_tag, commits)

    # Process only the unreleased section
    logger.info(f"Processing next version: {next_version}")

    if not quiet:
        output = get_output_manager()
        output.processing(f"Processing version {next_version}...")

        # Ask for confirmation before making LLM call (unless --yes flag)
        if not yes:
            output.info(f"About to generate 1 changelog entry using model: {model}")
            output.info(f"Entry to process: {next_version}")

            if not click.confirm("\nProceed with generating changelog entry?", default=True):
                output.warning("Operation cancelled by user.")
                return changelog_content, None

    # Get latest boundary for commit range based on mode
    # (already calculated above as latest_boundary and from_boundary)

    logger.debug(f"From boundary: {from_boundary}")
    logger.debug("To boundary: None (unreleased)")

    # Update changelog for this version
    changelog_content, token_usage = update_changelog(
        existing_content=changelog_content,
        from_boundary=from_boundary,
        to_boundary=None,  # None indicates unreleased
        model=model,
        hint=hint,
        show_prompt=show_prompt,
        quiet=quiet,
        no_unreleased=no_unreleased,
        include_diff=include_diff,
        language=language,
        translate_headings=translate_headings,
        audience=audience,
    )

    return changelog_content, token_usage


def handle_single_boundary_mode(
    changelog_file: str,
    to_boundary: str,
    model: str,
    hint: str,
    show_prompt: bool,
    quiet: bool,
    no_unreleased: bool,
    yes: bool = False,
    include_diff: bool = False,
    language: str | None = None,
    translate_headings: bool = False,
    audience: str | None = None,
    grouping_mode: str = "tags",
    gap_threshold_hours: float = 4.0,
    date_grouping: str = "daily",
) -> tuple[str, dict[str, int] | None]:
    """Handle single boundary processing workflow."""
    changelog_content = _ensure_changelog_exists(changelog_file, no_unreleased)

    # Determine previous boundary for context
    previous_boundary = _find_previous_boundary_id(to_boundary, grouping_mode, gap_threshold_hours, date_grouping)

    if not quiet:
        output = get_output_manager()
        output.info(f"Processing boundary {to_boundary} (from {previous_boundary or 'beginning'} to {to_boundary})")

        # Ask for confirmation before making LLM call (unless --yes flag)
        if not yes:
            output.info(f"About to generate 1 changelog entry using model: {model}")
            output.info(f"Entry to process: {to_boundary}")

            if not click.confirm("\nProceed with generating changelog entry?", default=True):
                output.warning("Operation cancelled by user.")
                return changelog_content, None

    # Update changelog for this specific boundary only (overwrite if exists)
    changelog_content, token_usage = update_changelog(
        existing_content=changelog_content,
        from_boundary=previous_boundary,
        to_boundary=to_boundary,
        model=model,
        hint=hint,
        show_prompt=show_prompt,
        quiet=quiet,
        no_unreleased=no_unreleased,
        include_diff=include_diff,
        language=language,
        translate_headings=translate_headings,
        audience=audience,
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
    yes: bool = False,
    include_diff: bool = False,
    language: str | None = None,
    translate_headings: bool = False,
    audience: str | None = None,
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
        from_boundary = _find_previous_boundary_id(to_boundary, grouping_mode, gap_threshold_hours, date_grouping)

    changelog_content = _ensure_changelog_exists(changelog_file, no_unreleased)

    if not quiet:
        output = get_output_manager()
        output.info(
            f"Processing range from {from_boundary or 'beginning'} to {to_boundary or 'HEAD'} (mode: {grouping_mode})"
        )

        # Ask for confirmation before making LLM call (unless --yes flag)
        if not yes:
            output.info(f"About to generate 1 changelog entry using model: {model}")
            output.info(f"Range: {from_boundary or 'beginning'} → {to_boundary or 'HEAD'}")

            if not click.confirm("\nProceed with generating changelog entry?", default=True):
                output.warning("Operation cancelled by user.")
                return changelog_content, None

    # Update changelog for this range
    changelog_content, token_usage = update_changelog(
        existing_content=changelog_content,
        from_boundary=from_boundary,
        to_boundary=to_boundary,
        model=model,
        hint=hint,
        show_prompt=show_prompt,
        quiet=quiet,
        no_unreleased=no_unreleased,
        include_diff=include_diff,
        language=language,
        translate_headings=translate_headings,
        audience=audience,
    )

    return changelog_content, token_usage


def handle_update_all_mode(
    changelog_file: str,
    model: str,
    hint: str,
    show_prompt: bool,
    quiet: bool,
    no_unreleased: bool,
    grouping_mode: str,
    gap_threshold_hours: float,
    date_grouping: str,
    yes: bool = False,
    include_diff: bool = False,
    language: str | None = None,
    translate_headings: bool = False,
    audience: str | None = None,
) -> tuple[str, dict[str, int] | None]:
    """Handle update all entries mode."""
    # Get all boundaries
    all_boundaries = get_all_boundaries(
        mode=grouping_mode, gap_threshold_hours=gap_threshold_hours, date_grouping=date_grouping
    )

    # Read existing changelog content and find existing boundaries
    existing_content = read_changelog(changelog_file)
    existing_boundaries = find_existing_boundaries(existing_content)

    # Filter to only existing boundaries that need updating
    boundaries_to_process = []
    for boundary in all_boundaries:
        boundary_id = generate_boundary_identifier(boundary, grouping_mode)
        # For version boundaries, strip 'v' prefix to match find_existing_boundaries behavior
        comparison_id = boundary_id.lstrip("v") if grouping_mode == "tags" else boundary_id
        if comparison_id in existing_boundaries:
            boundaries_to_process.append(boundary)

    if not quiet:
        boundary_list = (
            ", ".join([generate_boundary_display_name(boundary, grouping_mode) for boundary in boundaries_to_process])
            if boundaries_to_process
            else "none"
        )
        output = get_output_manager()
        output.info(f"Will update all {len(boundaries_to_process)} existing boundaries: {boundary_list}")

    changelog_content = _ensure_changelog_exists(changelog_file, no_unreleased)

    # Ask for confirmation before making LLM calls
    if boundaries_to_process and not quiet and not yes:
        output = get_output_manager()
        entry_word = "entry" if len(boundaries_to_process) == 1 else "entries"

        entries_list = [generate_boundary_display_name(boundary, grouping_mode) for boundary in boundaries_to_process]
        entries_text = ", ".join(entries_list)

        output.info(f"\nAbout to update {len(boundaries_to_process)} changelog {entry_word} using model: {model}")
        output.info(f"Entries to update: {entries_text}")

        if not click.confirm("\nProceed with updating changelog entries?", default=True):
            output.warning("Operation cancelled by user.")
            return changelog_content, None

    # Process each boundary
    total_token_usage: dict[str, int] = {}
    for boundary in boundaries_to_process:
        boundary_id = generate_boundary_identifier(boundary, grouping_mode)

        # Get previous boundary for context
        prev_boundary = get_previous_boundary(boundary, grouping_mode)
        from_boundary_id = generate_boundary_identifier(prev_boundary, grouping_mode) if prev_boundary else None

        if not quiet:
            output = get_output_manager()
            output.processing(f"Updating {generate_boundary_display_name(boundary, grouping_mode)}...")

        # Update this specific boundary (overwrite existing content)
        changelog_content, token_usage = update_changelog(
            existing_content=changelog_content,
            from_boundary=from_boundary_id,
            to_boundary=boundary_id,
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            quiet=quiet,
            no_unreleased=no_unreleased,
            include_diff=include_diff,
            language=language,
            translate_headings=translate_headings,
            audience=audience,
        )

        # Accumulate token usage
        if token_usage:
            for key, value in token_usage.items():
                total_token_usage[key] = total_token_usage.get(key, 0) + value

    return changelog_content, total_token_usage


def handle_missing_entries_mode(
    changelog_file: str,
    model: str,
    hint: str,
    show_prompt: bool,
    quiet: bool,
    no_unreleased: bool,
    grouping_mode: str,
    gap_threshold_hours: float,
    date_grouping: str,
    yes: bool = False,
    include_diff: bool = False,
    language: str | None = None,
    translate_headings: bool = False,
    audience: str | None = None,
) -> tuple[str, dict[str, int] | None]:
    """Handle missing entries mode - create entries for tags not in changelog."""
    # Get all boundaries from git
    all_boundaries = get_all_boundaries(
        mode=grouping_mode, gap_threshold_hours=gap_threshold_hours, date_grouping=date_grouping
    )

    # Read existing changelog and find boundaries already covered
    existing_content = read_changelog(changelog_file)
    existing_boundaries = find_existing_boundaries(existing_content)

    # Filter to only missing boundaries (exclude ones already in changelog)
    boundaries_to_process = []
    for boundary in all_boundaries:
        boundary_id = generate_boundary_identifier(boundary, grouping_mode)
        # For version boundaries, strip 'v' prefix to match find_existing_boundaries behavior
        comparison_id = boundary_id.lstrip("v") if grouping_mode == "tags" else boundary_id
        if comparison_id not in existing_boundaries:
            boundaries_to_process.append(boundary)

    if not quiet:
        boundary_list = (
            ", ".join([generate_boundary_display_name(boundary, grouping_mode) for boundary in boundaries_to_process])
            if boundaries_to_process
            else "none"
        )
        output = get_output_manager()
        output.info(f"Will create {len(boundaries_to_process)} missing entries: {boundary_list}")

    changelog_content = _ensure_changelog_exists(changelog_file, no_unreleased)

    # Process each missing boundary
    for boundary in boundaries_to_process:
        # Get commits between this boundary and the previous one
        previous_boundary = get_previous_boundary(boundary, grouping_mode)
        commits = get_commits_between_boundaries(previous_boundary, boundary, grouping_mode)

        # Generate changelog content for this boundary
        boundary_content, _stats = generate_changelog_entry(
            commits=commits,
            tag=generate_boundary_identifier(boundary, grouping_mode),
            from_boundary=generate_boundary_identifier(previous_boundary, grouping_mode) if previous_boundary else None,
            model=model,
            hint=hint,
            quiet=quiet,
            boundary_mode=grouping_mode,
            language=language,
            translate_headings=False,
            audience=audience,
        )

        # Update the changelog with the boundary content
        # Insert version header before the content sections
        if boundary_content.strip():
            boundary_id = generate_boundary_identifier(boundary, grouping_mode)
            # Format: ## [version] - date (if applicable)
            if grouping_mode == "tags":
                version_header = f"## [{boundary_id}]\n"
            else:
                # For date-based modes, include the date in the header
                boundary_date_raw = boundary.get("date", "")
                if boundary_date_raw:
                    # Handle both string and datetime objects
                    date_str = (
                        boundary_date_raw.isoformat()
                        if hasattr(boundary_date_raw, "isoformat")
                        else str(boundary_date_raw)
                    )
                    boundary_date = date_str.split("T")[0]
                else:
                    boundary_date = ""
                version_header = f"## [{boundary_id}] - {boundary_date}\n" if boundary_date else f"## [{boundary_id}]\n"

            full_entry = version_header + "\n" + boundary_content
            changelog_content = changelog_content.rstrip() + "\n\n" + full_entry

    return changelog_content, None


def determine_missing_entries(
    changelog_file: str,
    grouping_mode: str,
    gap_threshold_hours: float,
    date_grouping: str,
    no_unreleased: bool,
    special_unreleased_mode: bool,
) -> tuple[list, bool]:
    """Determine which boundaries have missing changelog entries."""
    # Get all boundaries from git
    all_boundaries = get_all_boundaries(
        mode=grouping_mode, gap_threshold_hours=gap_threshold_hours, date_grouping=date_grouping
    )

    # Read existing changelog and find boundaries already covered
    existing_content = read_changelog(changelog_file)
    existing_boundaries = find_existing_boundaries(existing_content)

    # Filter to only missing boundaries (exclude ones already in changelog)
    boundaries_to_process = []
    for boundary in all_boundaries:
        boundary_id = generate_boundary_identifier(boundary, grouping_mode)
        # For version boundaries, strip 'v' prefix to match find_existing_boundaries behavior
        comparison_id = boundary_id.lstrip("v") if grouping_mode == "tags" else boundary_id
        if comparison_id not in existing_boundaries:
            boundaries_to_process.append(boundary)

    # Check for unreleased changes to include in the count
    has_unreleased_changes = False
    latest_boundary = get_latest_boundary(grouping_mode)
    if latest_boundary and not is_current_commit_tagged():
        # If the current commit isn't tagged, we have unreleased changes
        # But only if there are actually commits since the last boundary
        if grouping_mode == "tags":
            unreleased_commits = get_commits_between_tags(latest_boundary.get("identifier"), None)
        else:
            unreleased_commits = get_commits_between_boundaries(latest_boundary, None, grouping_mode)

        if unreleased_commits:
            has_unreleased_changes = True
            # Calculate next version for display
            latest_tag = get_latest_tag()
            _ = determine_next_version(latest_tag, unreleased_commits)
    elif not latest_boundary and not is_current_commit_tagged():
        # If no boundaries exist in repo at all, check if we have commits
        if grouping_mode == "tags":
            all_commits = get_commits_between_tags(None, None)
        else:
            all_commits = get_commits_between_boundaries(None, None, grouping_mode)
        if all_commits:
            has_unreleased_changes = True
            # Calculate next version for display (no latest tag)
            _ = determine_next_version(None, all_commits)

    # If no missing boundaries and no unreleased changes, we're done
    if not boundaries_to_process and not has_unreleased_changes and not special_unreleased_mode:
        return [], False

    return boundaries_to_process, has_unreleased_changes
