"""Missing entries mode handler for kittylog."""

from kittylog.changelog.parser import find_existing_boundaries, find_insertion_point_by_version
from kittylog.commit_analyzer import get_commits_between_tags
from kittylog.errors import AIError, GitError
from kittylog.tag_operations import get_all_tags, get_tag_date


def determine_missing_entries(changelog_file: str) -> list[str]:
    """Determine which tags have missing changelog entries.

    Args:
        changelog_file: Path to changelog file

    Returns:
        List of tag names that need changelog entries
    """
    try:
        from kittylog.changelog.io import read_changelog

        existing_content = read_changelog(changelog_file)
        existing_versions = find_existing_boundaries(existing_content)

    except FileNotFoundError:
        # If changelog doesn't exist, all tags are missing
        existing_versions = set()

    # Get all tags and find missing ones
    # Normalize tags by stripping 'v' prefix for comparison since
    # find_existing_boundaries normalizes changelog versions the same way
    all_tags = get_all_tags()
    missing_tags = [tag for tag in all_tags if tag.lstrip("v") not in existing_versions]

    return missing_tags


def handle_missing_entries_mode(
    changelog_file: str,
    generate_entry_func,
    quiet: bool = False,
    yes: bool = False,
    dry_run: bool = False,
    **kwargs,
) -> tuple[bool, str]:
    """Handle missing entries mode workflow.

    Args:
        changelog_file: Path to changelog file
        generate_entry_func: Function to generate changelog entry
        quiet: Suppress non-error output
        yes: Skip confirmation prompts
        dry_run: Preview changes without saving
        **kwargs: Additional arguments for entry generation

    Returns:
        Tuple of (success, updated_content)
    """
    from kittylog.changelog.io import read_changelog
    from kittylog.output import get_output_manager

    output = get_output_manager()

    # Determine which tags need entries
    missing_tags = determine_missing_entries(changelog_file)

    if not missing_tags:
        output.info("No missing changelog entries found")
        try:
            existing_content = read_changelog(changelog_file)
        except FileNotFoundError:
            existing_content = ""
        return True, existing_content

    output.info(f"Found {len(missing_tags)} missing changelog entries: {', '.join(missing_tags)}")

    # Read existing changelog
    try:
        existing_content = read_changelog(changelog_file)
    except FileNotFoundError:
        existing_content = ""

    # Process each missing tag in REVERSE order (newest first)
    # This ensures proper changelog ordering (newest at top)
    updated_content = existing_content
    success = True

    for tag in reversed(missing_tags):
        try:
            # Get commits for this tag
            commits = get_commits_between_tags(
                from_tag=None,  # From beginning
                to_tag=tag,
            )

            if not commits:
                output.info(f"No commits found for tag {tag}, skipping")
                continue

            output.info(f"Processing missing tag: {tag} ({len(commits)} commits)")

            # Generate changelog entry
            entry = generate_entry_func(commits=commits, tag=tag, from_boundary=None, **kwargs)

            if not entry.strip():
                output.warning(f"AI generated empty content for tag {tag}")
                continue

            # Get tag date for proper formatting
            from datetime import datetime

            tag_date = get_tag_date(tag)
            version_date = tag_date.strftime("%Y-%m-%d") if tag_date else datetime.now().strftime("%Y-%m-%d")

            # Create version section
            version_section = f"## [{tag}] - {version_date}\n\n{entry}"

            # Find correct insertion point based on semantic version ordering
            lines = updated_content.split("\n")
            insert_point = find_insertion_point_by_version(updated_content, tag)

            # Insert the new section at the correct position
            new_lines = ["", *version_section.split("\n")]
            for i, line in enumerate(new_lines):
                lines.insert(insert_point + i, line)

            updated_content = "\n".join(lines)

        except (GitError, AIError, OSError, TimeoutError, ValueError, KeyError) as e:
            output.warning(f"Failed to process tag {tag}: {e}")
            success = False
            continue

    return success, updated_content
