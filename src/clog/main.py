#!/usr/bin/env python3
"""Business logic for changelog-updater.

Orchestrates the changelog update workflow including git operations, AI generation, and file updates.
"""

import logging

import click
from rich.console import Console
from rich.panel import Panel

from clog.changelog import create_changelog_header, read_changelog, update_changelog, write_changelog
from clog.config import load_config
from clog.errors import AIError, GitError, handle_error
from clog.git_operations import (
    get_all_tags,
    get_commits_between_tags,
    get_latest_tag,
    get_tags_since_last_changelog,
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
) -> bool:
    """Main application logic for changelog-updater.

    Returns True on success, False on failure.
    """
    try:
        # Validate we're in a git repository
        all_tags = get_all_tags()
        if not all_tags:
            console.print("[yellow]No git tags found. Create some tags first to generate changelog entries.[/yellow]")
            return True

    except GitError as e:
        handle_error(e)
        return False

    if model is None:
        model_value = config["model"]
        if model_value is None:
            handle_error(
                AIError.model_error(
                    "No model specified. Please set the CHANGELOG_UPDATER_MODEL environment variable or use --model."
                )
            )
            return False
        model = str(model_value)

    # Determine which tags to process
    if from_tag is None and to_tag is None:
        # In retroactive mode by default, process all tags
        all_tags = get_all_tags()

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

        if not all_tags and not has_unreleased_changes:
            console.print("[yellow]No git tags found. Create some tags first to generate changelog entries.[/yellow]")
            return True

        # Log all tags being processed
        logger.info(f"Found {len(all_tags)} tags: {all_tags}")
        if has_unreleased_changes:
            logger.info("Found unreleased changes since the latest tag")

        if not quiet:
            tag_list = ", ".join(all_tags) if all_tags else "none"
            console.print(f"[cyan]Processing {len(all_tags)} tags: {tag_list}[/cyan]")
            if has_unreleased_changes:
                console.print("[cyan]Also processing unreleased changes[/cyan]")

        # Start with an empty changelog or the existing one if preserving
        changelog_content = read_changelog(changelog_file) if preserve_existing else create_changelog_header()

        # Process each tag in order
        current_from_tag = None
        try:
            for tag in all_tags:
                logger.info(f"Processing tag {tag} (from {current_from_tag or 'beginning'})")

                if not quiet:
                    console.print(f"[bold blue]Processing {tag}...[/bold blue]")

                # Update changelog for this tag
                changelog_content = update_changelog(
                    existing_content=changelog_content,
                    from_tag=current_from_tag,
                    to_tag=tag,
                    model=model,
                    hint=hint,
                    show_prompt=show_prompt,
                    quiet=quiet,
                    replace_unreleased=True,  # Always replace for tagged versions
                )

                current_from_tag = tag

            # Process unreleased changes if needed
            if has_unreleased_changes:
                logger.info(f"Processing unreleased changes (from {current_from_tag or 'beginning'} to HEAD)")

                if not quiet:
                    console.print("[bold blue]Processing unreleased changes...[/bold blue]")

                # Update changelog for unreleased changes
                changelog_content = update_changelog(
                    existing_content=changelog_content,
                    from_tag=current_from_tag,
                    to_tag=None,  # None means HEAD
                    model=model,
                    hint=hint,
                    show_prompt=show_prompt,
                    quiet=quiet,
                    replace_unreleased=replace_unreleased if replace_unreleased is not None else config.get("replace_unreleased", True),
                )
        except Exception as e:
            handle_error(e)
            return False

    else:
        # Process specific tag range
        if to_tag is None:
            to_tag = get_latest_tag()
            if to_tag is None:
                console.print("[red]No tags found in repository.[/red]")
                return False

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
                replace_unreleased=replace_unreleased if replace_unreleased is not None else config.get("replace_unreleased", True),
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
