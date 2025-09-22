#!/usr/bin/env python3
"""Business logic for changelog-updater.

Orchestrates the changelog update workflow including git operations, AI generation, and file updates.
"""

import logging

import click
from rich.console import Console
from rich.panel import Panel

from clog.changelog import (
    create_changelog_header,
    find_existing_tags,
    read_changelog,
    update_changelog,
    write_changelog,
)
from clog.config import load_config
from clog.errors import AIError, GitError, handle_error
from clog.git_operations import (
    get_all_tags,
    get_commits_between_tags,
    get_latest_tag,
    get_previous_tag,
    is_current_commit_tagged,
)

logger = logging.getLogger(__name__)
config = load_config()
console = Console()


console = Console()


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
    preserve_existing: bool = False,
    replace_unreleased: bool | None = None,
    special_unreleased_mode: bool = False,
    update_all_entries: bool = False,
) -> bool:
    """Main application logic for changelog-updater.

    Returns True on success, False on failure.
    """
    logger.debug(f"main_business_logic called with special_unreleased_mode={special_unreleased_mode}")
    try:
        # Validate we're in a git repository
        all_tags = get_all_tags()
        # In special_unreleased_mode, we don't require tags
        if not all_tags and not special_unreleased_mode:
            console.print("[yellow]No git tags found. Create some tags first to generate changelog entries.[/yellow]")
            return True

    except GitError as e:
        handle_error(e)
        return False

    if model is None:
        model_value = config["model"]
        if model_value is None:
            print("DEBUG: No model specified in config")
            handle_error(
                AIError.model_error(
                    "No model specified. Please set the CHANGELOG_UPDATER_MODEL environment variable or use --model."
                )
            )
            return False
        model = str(model_value)

    # Determine which tags to process
    if special_unreleased_mode:
        # For special unreleased mode, only process the unreleased section
        logger.debug(f"In special_unreleased_mode, changelog_file={changelog_file}")
        existing_content = read_changelog(changelog_file)

        # If changelog doesn't exist, create header
        if not existing_content.strip():
            changelog_content = create_changelog_header()
            logger.info("Created new changelog header")
        else:
            changelog_content = existing_content

        logger.debug(f"Existing changelog content: {repr(changelog_content[:200])}")

        # Process only the unreleased section
        logger.info("Processing unreleased section only")

        if not quiet:
            console.print("[bold blue]Processing unreleased section...[/bold blue]")

        # Get latest tag for commit range
        latest_tag = get_latest_tag()
        logger.debug(f"Latest tag: {latest_tag}")

        # Update changelog for unreleased changes only
        # In special unreleased mode, we should process regardless of whether current commit is tagged
        replace_unreleased_value = (
            replace_unreleased if replace_unreleased is not None else bool(config.get("replace_unreleased", True))
        )
        logger.debug(f"Calling update_changelog with replace_unreleased_value: {replace_unreleased_value}")
        updated_content = update_changelog(
            existing_content=changelog_content,
            from_tag=latest_tag,
            to_tag=None,  # None means HEAD for unreleased
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            quiet=quiet,
            replace_unreleased=replace_unreleased_value,
        )
        logger.debug(f"Updated changelog_content different from original: {updated_content != changelog_content}")
        changelog_content = updated_content
    elif from_tag is None and to_tag is None:
        # In simplified mode by default, process all tags with proper AI-generated content
        all_tags = get_all_tags()

        # If update_all_entries flag is set, process all tags; otherwise process only missing tags
        if not update_all_entries:
            # Read existing changelog content
            existing_content = read_changelog(changelog_file)
            # Find tags that already exist in changelog
            existing_tags = find_existing_tags(existing_content)

            # Filter to only process tags that are missing from changelog
            tags_to_process = [tag for tag in all_tags if tag.lstrip("v") not in existing_tags]

            if not quiet:
                missing_tag_list = ", ".join(tags_to_process) if tags_to_process else "none"
                existing_tag_list = ", ".join(existing_tags) if existing_tags else "none"
                console.print(f"[cyan]Found {len(all_tags)} total tags[/cyan]")
                console.print(f"[cyan]Existing tags in changelog: {existing_tag_list}[/cyan]")
                console.print(f"[cyan]Missing tags to process: {missing_tag_list}[/cyan]")
        else:
            # Process all tags when update_all_entries is True
            tags_to_process = all_tags
            if not quiet:
                tag_list = ", ".join(tags_to_process) if tags_to_process else "none"
                console.print(f"[cyan]Updating all {len(tags_to_process)} tags: {tag_list}[/cyan]")

        # Read existing changelog content
        existing_content = read_changelog(changelog_file)

        # If changelog doesn't exist, create header
        if not existing_content.strip():
            changelog_content = create_changelog_header()
            logger.info("Created new changelog header")
        else:
            changelog_content = existing_content

        logger.info(f"Found {len(all_tags)} tags: {all_tags}")

        if not quiet:
            tag_list = ", ".join(all_tags) if all_tags else "none"
            console.print(f"[cyan]Found {len(all_tags)} tags: {tag_list}[/cyan]")

        # Process each tag with AI-generated content (overwrite existing placeholders)
        try:
            for tag in tags_to_process:
                logger.info(f"Processing tag {tag}")

                if not quiet:
                    console.print(f"[bold blue]Processing {tag}...[/bold blue]")

                # Get previous tag to determine the range
                previous_tag = get_previous_tag(tag)

                # Update changelog for this tag only (overwrite existing content)
                changelog_content = update_changelog(
                    existing_content=changelog_content,
                    from_tag=previous_tag,
                    to_tag=tag,
                    model=model,
                    hint=hint,
                    show_prompt=show_prompt,
                    quiet=quiet,
                    replace_unreleased=True,  # Always replace for tagged versions
                )

        except Exception as e:
            handle_error(e)
            return False

        # Check if we have unreleased changes
        has_unreleased_changes = False
        latest_tag = get_latest_tag()
        if latest_tag and not is_current_commit_tagged():
            # If the current commit isn't tagged, we have unreleased changes
            # But only if there are actually commits since the last tag
            unreleased_commits = get_commits_between_tags(latest_tag, None)
            if len(unreleased_commits) > 0:
                has_unreleased_changes = True
        elif not latest_tag and not is_current_commit_tagged():
            # If no tags exist in repo at all, check if we have commits
            all_commits = get_commits_between_tags(None, None)
            if all_commits:
                has_unreleased_changes = True

        # Process unreleased changes if needed
        # For special_unreleased_mode, we should process regardless of whether current commit is tagged
        if has_unreleased_changes or special_unreleased_mode:
            logger.info("Processing unreleased changes")

            if not quiet:
                console.print("[bold blue]Processing unreleased changes...[/bold blue]")

            # Update changelog for unreleased changes
            changelog_content = update_changelog(
                existing_content=changelog_content,
                from_tag=latest_tag,
                to_tag=None,  # None means HEAD
                model=model,
                hint=hint,
                show_prompt=show_prompt,
                quiet=quiet,
                replace_unreleased=True,  # Always overwrite unreleased content
            )
    elif to_tag is not None and from_tag is None:
        # When only to_tag is specified, find the previous tag to use as from_tag
        changelog_content = read_changelog(changelog_file)

        # If changelog doesn't exist, create header
        if not changelog_content.strip():
            changelog_content = create_changelog_header()
            logger.info("Created new changelog header")

        # Get previous tag to determine the range
        previous_tag = get_previous_tag(to_tag)

        if not quiet:
            console.print(f"[cyan]Processing tag {to_tag} (from {previous_tag or 'beginning'} to {to_tag})[/cyan]")

        # Update changelog for this specific tag only (overwrite if exists)
        changelog_content = update_changelog(
            existing_content=changelog_content,
            from_tag=previous_tag,
            to_tag=to_tag,
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            quiet=quiet,
            replace_unreleased=True,  # Always replace for specific tags
        )

    else:
        # Process specific tag range
        if to_tag is None and not special_unreleased_mode:
            to_tag = get_latest_tag()
            if to_tag is None:
                console.print("[red]No tags found in repository.[/red]")
                return False
        elif from_tag is None and to_tag is not None and not special_unreleased_mode:
            # When only to_tag is specified, find the previous tag to use as from_tag
            from_tag = get_previous_tag(to_tag)

        logger.info(f"Processing specific range: {from_tag or 'beginning'} to {to_tag}")

        if not quiet:
            console.print(f"[cyan]Processing from {from_tag or 'beginning'} to {to_tag}[/cyan]")

        # Update changelog for specified range
        try:
            changelog_content = update_changelog(
                file_path=changelog_file,
                from_tag=from_tag,
                to_tag=to_tag,
                model=model,
                hint=hint,
                show_prompt=show_prompt,
                quiet=quiet,
                replace_unreleased=True
                if special_unreleased_mode
                else (
                    replace_unreleased
                    if replace_unreleased is not None
                    else bool(config.get("replace_unreleased", True))
                ),
            )
        except Exception as e:
            handle_error(e)
            return False

    # Show preview and get confirmation
    if dry_run:
        console.print("[yellow]Dry run: Changelog content generated but not saved[/yellow]")
        console.print("\nPreview of updated changelog:")
        console.print(Panel(changelog_content, title="Updated Changelog", border_style="cyan"))
        return True

    if require_confirmation:
        console.print("\n[bold green]Updated changelog preview:[/bold green]")
        # Show just the new parts for confirmation
        preview_lines = changelog_content.split("\n")[:50]  # First 50 lines
        preview_text = "\n".join(preview_lines)
        if len(changelog_content.split("\n")) > 50:
            preview_text += "\n\n... (content truncated for preview)"

        console.print(Panel(preview_text, title="Changelog Preview", border_style="cyan"))

        proceed = click.confirm("\nSave the updated changelog?", default=True)
        if not proceed:
            console.print("[yellow]Changelog update cancelled.[/yellow]")
            return True

    # Write the updated changelog
    try:
        write_changelog(changelog_file, changelog_content)
    except Exception as e:
        handle_error(e)
        return False

    if not quiet:
        logger.info(f"Successfully updated changelog: {changelog_file}")

    return True
