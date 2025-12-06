"""Boundary mode handlers for kittylog."""

from collections.abc import Callable
from typing import Any

from kittylog.commit_analyzer import get_commits_between_boundaries
from kittylog.errors import AIError, GitError
from kittylog.tag_operations import get_all_boundaries
from kittylog.utils.text import format_version_for_changelog

# Type alias for the entry generator function
EntryGeneratorFunc = Callable[..., str]

# Type alias for boundary dictionaries
BoundaryDict = dict[str, Any]


def handle_single_boundary_mode(
    changelog_file: str,
    boundary: BoundaryDict,
    generate_entry_func: EntryGeneratorFunc,
    quiet: bool = False,
    dry_run: bool = False,
    incremental_save: bool = True,
    **kwargs: Any,
) -> tuple[bool, str]:
    """Handle single boundary mode workflow.

    Args:
        changelog_file: Path to changelog file
        boundary: Boundary dictionary
        generate_entry_func: Function to generate changelog entry
        quiet: Suppress non-error output
        yes: Auto-accept without previews
        dry_run: Preview changes without saving
        incremental_save: Save immediately after generating the entry
        **kwargs: Additional arguments for entry generation

    Returns:
        Tuple of (success, updated_content)
    """
    from kittylog.changelog.io import ensure_changelog_exists, write_changelog
    from kittylog.output import get_output_manager

    output = get_output_manager()

    # Ensure changelog exists, creating it if needed
    existing_content = ensure_changelog_exists(changelog_file)

    # Get boundary information
    boundary_name = boundary.get("identifier", boundary.get("hash", "unknown"))
    raw_date = boundary.get("date", "")
    # Format date as just YYYY-MM-DD for boundaries
    boundary_date = raw_date.date().isoformat() if raw_date else ""

    output.info(f"Processing boundary: {boundary_name} ({boundary_date})")

    # Get commits for this boundary
    try:
        commits = get_commits_between_boundaries(
            from_boundary=None,  # From beginning
            to_boundary=boundary,
            mode=boundary.get("mode", "tags"),
        )
    except (GitError, KeyError, ValueError) as e:
        raise GitError(
            f"Failed to get commits for boundary {boundary_name}: {e}",
            command=f"git log {boundary_name}",
            stderr=str(e),
        ) from e

    if not commits:
        output.info(f"No commits found for boundary {boundary_name}")
        return True, existing_content

    output.info(f"Found {len(commits)} commits for boundary {boundary_name}")

    # Generate changelog entry
    try:
        entry = generate_entry_func(commits=commits, tag=boundary_name, from_boundary=None, **kwargs)

        if not entry.strip():
            output.warning(f"AI generated empty content for boundary {boundary_name}")
            return True, existing_content

        # Update changelog (simplified for now)
        updated_content = (
            f"{existing_content}\n\n## [{format_version_for_changelog(boundary_name, existing_content)}]\n\n{entry}"
        )

        # Save incrementally if enabled and not in dry run mode
        if incremental_save and not dry_run:
            write_changelog(changelog_file, updated_content)
            if not quiet:
                output.success(f"✓ Saved changelog entry for {boundary_name}")

        return True, updated_content

    except (AIError, OSError, TimeoutError, ValueError) as e:
        from kittylog.errors import handle_error

        handle_error(e)
        return False, existing_content


def handle_boundary_range_mode(
    changelog_file: str,
    from_boundary: BoundaryDict | None,
    to_boundary: BoundaryDict,
    generate_entry_func: EntryGeneratorFunc,
    quiet: bool = False,
    dry_run: bool = False,
    incremental_save: bool = True,
    **kwargs: Any,
) -> tuple[bool, str]:
    """Handle boundary range mode workflow.

    Args:
        changelog_file: Path to changelog file
        from_boundary: Starting boundary (exclusive)
        to_boundary: Ending boundary (inclusive)
        generate_entry_func: Function to generate changelog entry
        quiet: Suppress non-error output
        yes: Auto-accept without previews
        dry_run: Preview changes without saving
        incremental_save: Save immediately after generating the entry
        **kwargs: Additional arguments for entry generation

    Returns:
        Tuple of (success, updated_content)
    """
    from kittylog.changelog.io import ensure_changelog_exists, write_changelog
    from kittylog.output import get_output_manager

    output = get_output_manager()

    # Ensure changelog exists, creating it if needed
    existing_content = ensure_changelog_exists(changelog_file)

    # Get boundary information
    to_name = to_boundary.get("identifier", to_boundary.get("hash", "unknown"))
    to_date = to_boundary.get("date", "")

    from_name = (
        from_boundary.get("identifier", from_boundary.get("hash", "beginning")) if from_boundary else "beginning"
    )

    output.info(f"Processing range: {from_name} to {to_name} ({to_date})")

    # Get commits for the range
    try:
        commits = get_commits_between_boundaries(
            from_boundary=from_boundary, to_boundary=to_boundary, mode=to_boundary.get("mode", "tags")
        )
    except (GitError, KeyError, ValueError) as e:
        raise GitError(
            f"Failed to get commits for range {from_name} to {to_name}: {e}",
            command=f"git log {from_name}..{to_name}",
            stderr=str(e),
        ) from e

    if not commits:
        output.info(f"No commits found for range {from_name} to {to_name}")
        return True, existing_content

    output.info(f"Found {len(commits)} commits for range {from_name} to {to_name}")

    # Generate changelog entry
    try:
        entry = generate_entry_func(
            commits=commits, tag=to_name, from_boundary=from_name if from_boundary else None, **kwargs
        )

        if not entry.strip():
            output.warning(f"AI generated empty content for range {from_name} to {to_name}")
            return True, existing_content

        # Update changelog (simplified for now)
        updated_content = (
            f"{existing_content}\n\n## [{format_version_for_changelog(to_name, existing_content)}]\n\n{entry}"
        )

        # Save incrementally if enabled and not in dry run mode
        if incremental_save and not dry_run:
            write_changelog(changelog_file, updated_content)
            if not quiet:
                output.success(f"✓ Saved changelog entry for range {from_name} to {to_name}")

        return True, updated_content

    except (AIError, OSError, TimeoutError, ValueError) as e:
        from kittylog.errors import handle_error

        handle_error(e)
        return False, existing_content


def handle_update_all_mode(
    changelog_file: str,
    generate_entry_func: EntryGeneratorFunc,
    mode: str,
    quiet: bool = False,
    dry_run: bool = False,
    incremental_save: bool = True,
    **kwargs: Any,
) -> tuple[bool, str]:
    """Handle update all mode workflow.

    Args:
        changelog_file: Path to changelog file
        generate_entry_func: Function to generate changelog entry
        mode: Boundary mode (tags, dates, gaps)
        quiet: Suppress non-error output
        yes: Auto-accept without previews
        dry_run: Preview changes without saving
        incremental_save: Save after each entry is generated instead of all at once
        **kwargs: Additional arguments for entry generation

    Returns:
        Tuple of (success, updated_content)
    """
    from kittylog.changelog.io import ensure_changelog_exists, write_changelog
    from kittylog.output import get_output_manager

    output = get_output_manager()

    # Ensure changelog exists, creating it if needed
    existing_content = ensure_changelog_exists(changelog_file)

    # Get all boundaries
    try:
        boundaries = get_all_boundaries(mode=mode)
    except (GitError, ValueError, KeyError) as e:
        raise GitError(
            f"Failed to get boundaries for mode {mode}: {e}",
            command=f"git log --{mode}",
            stderr=str(e),
        ) from e

    if not boundaries:
        output.info(f"No boundaries found for mode {mode}")
        return True, existing_content

    output.info(f"Found {len(boundaries)} boundaries for mode {mode}")

    success = True

    # Collect all boundary entries first, processing in chronological order (oldest first)
    # This ensures the AI has historical context from previously generated entries
    boundary_entries = []

    for i, boundary in enumerate(boundaries):
        boundary_name = boundary.get("identifier", boundary.get("hash", "unknown"))
        raw_date = boundary.get("date", "")
        # Format date as just YYYY-MM-DD for boundaries
        boundary_date = raw_date.date().isoformat() if raw_date else ""

        output.info(f"Processing boundary: {boundary_name} ({boundary_date})")

        # Get commits for this boundary
        try:
            commits = get_commits_between_boundaries(
                from_boundary=None,  # From beginning
                to_boundary=boundary,
                mode=mode,
            )
        except (GitError, KeyError, ValueError) as e:
            output.warning(f"Failed to get commits for boundary {boundary_name}: {e}")
            success = False
            continue

        if not commits:
            output.info(f"No commits found for boundary {boundary_name}, skipping")
            continue

        # Generate changelog entry
        try:
            entry = generate_entry_func(commits=commits, tag=boundary_name, from_boundary=None, **kwargs)

            if not entry.strip():
                output.warning(f"AI generated empty content for boundary {boundary_name}")
                continue

            # Collect the version section for later insertion
            version_section = (
                f"## [{format_version_for_changelog(boundary_name, existing_content)}] - {boundary_date}\n\n{entry}"
            )
            boundary_entries.append(
                {
                    "boundary_name": boundary_name,
                    "version_section": version_section,
                    "index": i,  # For progress tracking
                }
            )

        except (AIError, OSError, TimeoutError, ValueError) as e:
            output.warning(f"Failed to generate entry for boundary {boundary_name}: {e}")
            success = False
            continue

    # Insert all boundary entries in reverse order (newest first)
    if boundary_entries:
        output.info(f"Inserting {len(boundary_entries)} boundary entries in reverse chronological order")

        # For date boundaries, use direct insertion to ensure correct order
        lines = existing_content.split("\n")

        # Find the insertion point (after Unreleased section, before first version)
        insert_point = len(lines)  # Default to end

        # Look for unreleased section and insert after it
        for i, line in enumerate(lines):
            if line.strip().startswith("## [Unreleased]"):
                # Find the end of unreleased section
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith("## [") and "Unreleased" not in lines[j]:
                        insert_point = j
                        break
                    elif j == len(lines) - 1:  # End of file after unreleased
                        insert_point = j + 1
                        break
                break
        else:
            # No unreleased section found, find first version section
            for i, line in enumerate(lines):
                if line.strip().startswith("## [") and "Unreleased" not in line:
                    insert_point = i
                    break

        # Insert all entries in reverse chronological order (newest first)
        for entry_data in reversed(boundary_entries):
            # Split the version section into lines
            version_lines = entry_data["version_section"].split("\n")

            # Insert at the correct position
            for line in version_lines:
                lines.insert(insert_point, line)
                insert_point += 1

            # Add spacing between entries
            if insert_point < len(lines) and lines[insert_point].strip():
                lines.insert(insert_point, "")
                insert_point += 1

            if not quiet:
                progress = f"({entry_data['index'] + 1}/{len(boundaries)})"
                output.success(f"✓ Inserted changelog entry for {entry_data['boundary_name']} {progress}")

        # Reconstruct the content
        existing_content = "\n".join(lines)

    # Final save if enabled and not in dry run mode
    if boundary_entries and incremental_save and not dry_run:
        write_changelog(changelog_file, existing_content)
        if not quiet:
            output.success(f"✓ Saved changelog with {len(boundary_entries)} new entries")

    return success, existing_content
