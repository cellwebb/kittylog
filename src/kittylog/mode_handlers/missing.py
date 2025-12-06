"""Missing entries mode handler for kittylog."""

from kittylog.changelog.parser import find_existing_boundaries, find_insertion_point_by_version
from kittylog.commit_analyzer import get_commits_between_boundaries, get_commits_between_tags
from kittylog.errors import AIError, GitError
from kittylog.tag_operations import get_all_boundaries, get_tag_date
from kittylog.utils.text import format_version_for_changelog


def determine_missing_entries(changelog_file: str, mode: str = "tags", **kwargs) -> list[str]:
    """Determine which boundaries have missing changelog entries.

    Args:
        changelog_file: Path to changelog file
        mode: Boundary detection mode ('tags', 'dates', or 'gaps')
        **kwargs: Additional parameters for specific modes
            - date_grouping: For 'dates' mode ('daily', 'weekly', 'monthly')
            - gap_threshold_hours: For 'gaps' mode (minimum gap in hours)

    Returns:
        List of boundary identifiers that need changelog entries
    """
    try:
        from kittylog.changelog.io import read_changelog

        existing_content = read_changelog(changelog_file)
        existing_versions = find_existing_boundaries(existing_content)

    except FileNotFoundError:
        # If changelog doesn't exist, all tags are missing
        existing_versions = set()

    # Get all boundaries based on mode
    all_boundaries = get_all_boundaries(mode=mode, **kwargs)

    # Debug logging
    from kittylog.utils.logging import get_logger

    logger = get_logger(__name__)
    logger.debug(f"Found {len(all_boundaries)} total boundaries in {mode} mode")
    for i, boundary in enumerate(all_boundaries[:5]):  # Log first 5 for brevity
        logger.debug(f"Boundary {i}: {boundary}")
    logger.debug(f"Existing versions: {existing_versions}")

    # Extract boundary identifiers and find missing ones
    if mode == "tags":
        # For tags mode, normalize by stripping 'v' prefix for comparison since
        # find_existing_boundaries normalizes changelog versions the same way
        missing_boundaries = []
        for boundary in all_boundaries:
            # Use the same identifier logic as the rest of the function
            identifier = boundary.get("identifier") or boundary.get("name") or boundary.get("display_name") or "unknown"
            if identifier.lstrip("v") not in existing_versions:
                missing_boundaries.append(identifier)
    else:
        # For dates and gaps modes, use the boundary identifier directly
        missing_boundaries = []
        for boundary in all_boundaries:
            # Try multiple keys that might represent the boundary identifier
            identifier = (
                boundary.get("identifier")
                or boundary.get("name")
                or boundary.get("display_name")
                or str(boundary.get("date", "unknown"))
            )
            if identifier not in existing_versions:
                missing_boundaries.append(identifier)

    logger.debug(f"Missing boundaries determined: {missing_boundaries}")
    return missing_boundaries


def handle_missing_entries_mode(
    changelog_file: str,
    generate_entry_func,
    mode: str = "tags",  # ADD
    date_grouping: str = "daily",  # ADD
    gap_threshold: float = 4.0,  # ADD
    quiet: bool = False,
    dry_run: bool = False,
    incremental_save: bool = True,
    **kwargs,
) -> tuple[bool, str]:
    """Handle missing entries mode workflow.

    DEBUG: This function is being called!

    Args:
        changelog_file: Path to changelog file
        generate_entry_func: Function to generate changelog entry
        quiet: Suppress non-error output
        yes: Auto-accept without previews
        dry_run: Preview changes without saving
        incremental_save: Save after each entry is generated instead of all at once
        **kwargs: Additional arguments for entry generation

    Returns:
        Tuple of (success, updated_content)
    """
    from kittylog.changelog.io import ensure_changelog_exists, read_changelog, write_changelog
    from kittylog.output import get_output_manager

    output = get_output_manager()

    # Determine which boundaries need entries
    missing_boundaries = determine_missing_entries(
        changelog_file, mode=mode, date_grouping=date_grouping, gap_threshold_hours=gap_threshold
    )

    if not missing_boundaries:
        output.info("No missing changelog entries found")
        try:
            existing_content = read_changelog(changelog_file)
        except FileNotFoundError:
            existing_content = ""
        return True, existing_content

    output.info(f"Found {len(missing_boundaries)} missing changelog entries: {', '.join(missing_boundaries)}")

    # Ensure changelog exists, creating it if needed
    updated_content = ensure_changelog_exists(changelog_file)

    success = True

    # Get all boundaries to find the ones we need to process
    all_boundaries = get_all_boundaries(mode=mode, date_grouping=date_grouping, gap_threshold_hours=gap_threshold)

    # Create a mapping from identifier to boundary dict
    boundary_map = {}
    for boundary in all_boundaries:
        # Use the same identifier logic as determine_missing_entries
        identifier = (
            boundary.get("identifier")
            or boundary.get("name")
            or boundary.get("display_name")
            or str(boundary.get("date", "unknown"))
        )
        boundary_map[identifier] = boundary

    # Process each missing boundary in chronological order (oldest first)
    # This ensures the AI has historical context from previously generated entries
    # Note: Insertion point logic handles correct changelog placement regardless of processing order
    for i, boundary_id in enumerate(missing_boundaries):
        try:
            boundary = boundary_map[boundary_id]

            # Find the previous boundary to use as a starting point
            boundary_idx = -1
            for idx, b in enumerate(all_boundaries):
                # Calculate identifier for comparison matches how boundary_map specific keys were created
                b_id = b.get("identifier") or b.get("name") or b.get("display_name") or str(b.get("date", "unknown"))
                if b_id == boundary_id:
                    boundary_idx = idx
                    break

            prev_boundary = all_boundaries[boundary_idx - 1] if boundary_idx > 0 else None

            # Get commits for this boundary
            if mode == "tags":
                # For tags mode, use the existing tag-based function
                tag_name = boundary.get("name", boundary_id)
                from_tag_name = prev_boundary.get("name", prev_boundary.get("identifier")) if prev_boundary else None

                commits = get_commits_between_tags(
                    from_tag=from_tag_name,  # From previous tag
                    to_tag=tag_name,
                )
                tag = tag_name
            else:
                # For dates and gaps modes, use the boundary-aware function
                commits = get_commits_between_boundaries(
                    from_boundary=prev_boundary,  # From previous boundary
                    to_boundary=boundary,
                    mode=mode,
                )
                tag = boundary_id

            if not commits:
                output.info(f"No commits found for {boundary_id}, skipping")
                continue

            output.info(f"Processing missing boundary: {boundary_id} ({len(commits)} commits)")

            # Generate changelog entry
            entry = generate_entry_func(commits=commits, tag=tag, from_boundary=None, **kwargs)

            if not entry.strip():
                output.warning(f"AI generated empty content for {boundary_id}")
                continue

            # Get date for proper formatting
            from datetime import datetime

            if mode == "tags":
                # For tags mode, get tag date
                tag_date = get_tag_date(tag)
                version_date = tag_date.strftime("%Y-%m-%d") if tag_date else datetime.now().strftime("%Y-%m-%d")
                version_name = format_version_for_changelog(tag, updated_content)
            else:
                # For dates and gaps modes, use boundary date
                boundary_date = boundary.get("date")
                if boundary_date:
                    version_date = boundary_date.strftime("%Y-%m-%d")
                else:
                    version_date = datetime.now().strftime("%Y-%m-%d")
                version_name = boundary_id

            # Create version section
            version_section = f"## [{version_name}] - {version_date}\n\n{entry}"

            # Find correct insertion point
            lines = updated_content.split("\n")
            if mode == "tags":
                # For tags mode, use semantic version ordering
                insert_point = find_insertion_point_by_version(updated_content, tag)
            else:
                # For dates and gaps modes, find insertion point by date
                insert_point = find_insertion_point_by_version(updated_content, boundary_id)

            # Insert the new section at the correct position
            for j, line in enumerate(version_section.split("\n")):
                lines.insert(insert_point + j, line)

            updated_content = "\n".join(lines)

            # Save incrementally if enabled and not in dry run mode
            if incremental_save and not dry_run:
                write_changelog(changelog_file, updated_content)
                if not quiet:
                    progress = f"({i + 1}/{len(missing_boundaries)})"
                    output.success(f"✓ Saved changelog entry for {boundary_id} {progress}")

        except (GitError, AIError, OSError, TimeoutError, ValueError, KeyError) as e:
            output.warning(f"Failed to process boundary {boundary_id}: {e}")
            success = False
            continue

    return success, updated_content
