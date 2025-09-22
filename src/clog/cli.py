"""CLI entry point for changelog-updater.

Defines the Click-based command-line interface and delegates execution to the main workflow.
"""

import logging
import sys

import click

from clog import __version__
from clog.config import load_config
from clog.config_cli import config as config_cli
from clog.constants import Logging
from clog.errors import handle_error
from clog.init_changelog import init_changelog
from clog.init_cli import init as init_cli
from clog.main import main_business_logic
from clog.update_cli import update_version
from clog.utils import setup_logging

config = load_config()
logger = logging.getLogger(__name__)


@click.command(context_settings={"ignore_unknown_options": True})
# Git workflow options
@click.option("--dry-run", "-d", is_flag=True, help="Dry run the changelog update workflow")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--all", "-a", is_flag=True, help="Update all entries (not just missing ones)")
@click.option("--preserve-existing", is_flag=True, help="Preserve existing changelog content instead of overwriting")
@click.option("--replace-unreleased", is_flag=True, help="Replace unreleased content instead of appending")
@click.option("--no-replace-unreleased", is_flag=True, help="Append to unreleased content instead of replacing")
# Changelog options
@click.option("--file", "-f", default="CHANGELOG.md", help="Path to changelog file")
@click.option("--from-tag", "-s", default=None, help="Start from specific tag")
@click.option("--to-tag", "-t", default=None, help="Update up to specific tag")
@click.option("--show-prompt", "-p", is_flag=True, help="Show the prompt sent to the LLM")
@click.option("--hint", "-h", default="", help="Additional context for the prompt")
# Model options
@click.option("--model", "-m", default=None, help="Override default model")
# Output options
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
@click.option("--verbose", "-v", is_flag=True, help="Increase output verbosity to INFO")
@click.option(
    "--log-level",
    type=click.Choice(Logging.LEVELS, case_sensitive=False),
    help="Set log level",
)
@click.argument("tag", required=False)
def add(
    file,
    from_tag,
    to_tag,
    show_prompt,
    quiet,
    yes,
    hint,
    model,
    dry_run,
    verbose,
    log_level,
    preserve_existing,
    replace_unreleased,
    no_replace_unreleased,
    all,
    tag,
):
    """Add missing changelog entries or update a specific tag entry.

    When run without arguments, adds entries for tags missing from changelog.
    When run with a specific tag, processes only that tag (overwrites if exists).
    When --all flag is used, updates all entries in changelog.
    """
    try:
        effective_log_level = log_level or config["log_level"]
        if verbose and effective_log_level not in ("DEBUG", "INFO"):
            effective_log_level = "INFO"
        if quiet:
            effective_log_level = "ERROR"
        setup_logging(effective_log_level)
        logger.info("Starting changelog-updater")

        # If a specific tag is provided, process only that tag
        if tag:
            # Normalize tag (remove 'v' prefix if present)
            normalized_tag = tag.lstrip("v")
            # Try to add 'v' prefix if not present (to match git tags)
            git_tag = f"v{normalized_tag}" if not tag.startswith("v") else tag

            # For specific tags, always overwrite the entry
            success = main_business_logic(
                changelog_file=file,
                from_tag=from_tag,  # Will use get_previous_tag in main logic if None
                to_tag=git_tag,  # Process the specific tag
                model=model,
                hint=hint,
                show_prompt=show_prompt,
                require_confirmation=not yes,
                quiet=quiet,
                dry_run=dry_run,
                preserve_existing=preserve_existing,
                replace_unreleased=True,  # Always overwrite for specific tags
            )
        else:
            # Default behavior: process all missing tags
            success = main_business_logic(
                changelog_file=file,
                from_tag=from_tag,
                to_tag=to_tag,
                model=model,
                hint=hint,
                show_prompt=show_prompt,
                require_confirmation=not yes,
                quiet=quiet,
                dry_run=dry_run,
                preserve_existing=preserve_existing,
                replace_unreleased=replace_unreleased,
            )

        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        click.echo("Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        handle_error(e)
        sys.exit(1)


@click.command()
@click.argument("version", required=False)
@click.option("--dry-run", "-d", is_flag=True, help="Dry run the changelog update workflow")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--all", "-a", is_flag=True, help="Update all entries (not just missing ones)")
@click.option("--preserve-existing", is_flag=True, help="Preserve existing changelog content instead of overwriting")
@click.option("--replace-unreleased", is_flag=True, help="Replace unreleased content instead of appending")
@click.option("--no-replace-unreleased", is_flag=True, help="Append to unreleased content instead of replacing")
@click.option("--file", "-f", default="CHANGELOG.md", help="Path to changelog file")
@click.option("--from-tag", "-s", default=None, help="Start from specific tag")
@click.option("--to-tag", "-t", default=None, help="Update up to specific tag")
@click.option("--show-prompt", "-p", is_flag=True, help="Show the prompt sent to the LLM")
@click.option("--hint", "-h", default="", help="Additional context for the prompt")
@click.option("--model", "-m", default=None, help="Override default model")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
@click.option("--verbose", "-v", is_flag=True, help="Increase output verbosity to INFO")
@click.option(
    "--log-level",
    type=click.Choice(Logging.LEVELS, case_sensitive=False),
    help="Set log level",
)
def update_compat(
    file,
    from_tag,
    to_tag,
    show_prompt,
    quiet,
    yes,
    hint,
    model,
    dry_run,
    verbose,
    log_level,
    preserve_existing,
    replace_unreleased,
    no_replace_unreleased,
    all,
    version,
):
    """Compatibility update command for integration tests."""

    # Handle conflicting flags
    if replace_unreleased and no_replace_unreleased:
        click.echo("Error: --replace-unreleased and --no-replace-unreleased cannot be used together")
        sys.exit(2)

    # Determine replace_unreleased value
    if no_replace_unreleased:
        replace_unreleased_value = False
    elif replace_unreleased is not None:
        replace_unreleased_value = replace_unreleased
    else:
        replace_unreleased_value = None

    if all:
        # Update all entries - process all tags
        success = main_business_logic(
            changelog_file=file,
            from_tag=from_tag,
            to_tag=to_tag,
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            require_confirmation=not yes,
            quiet=quiet,
            dry_run=dry_run,
            preserve_existing=preserve_existing,
            replace_unreleased=replace_unreleased_value,
        )
    else:
        # Default behavior: process missing tags only
        success = main_business_logic(
            changelog_file=file,
            from_tag=from_tag,
            to_tag=to_tag,
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            require_confirmation=not yes,
            quiet=quiet,
            dry_run=dry_run,
            preserve_existing=preserve_existing,
            replace_unreleased=replace_unreleased_value,
        )

    if not success:
        sys.exit(1)


@click.command()
@click.argument("version", required=False)
@click.option("--dry-run", "-d", is_flag=True, help="Dry run the changelog update workflow")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--all", "-a", is_flag=True, help="Update all entries (not just missing ones)")
@click.option("--preserve-existing", is_flag=True, help="Preserve existing changelog content instead of overwriting")
@click.option("--replace-unreleased", is_flag=True, help="Replace unreleased content instead of appending")
@click.option("--no-replace-unreleased", is_flag=True, help="Append to unreleased content instead of replacing")
@click.option("--file", "-f", default="CHANGELOG.md", help="Path to changelog file")
@click.option("--from-tag", "-s", default=None, help="Start from specific tag")
@click.option("--to-tag", "-t", default=None, help="Update up to specific tag")
@click.option("--show-prompt", "-p", is_flag=True, help="Show the prompt sent to the LLM")
@click.option("--hint", "-h", default="", help="Additional context for the prompt")
@click.option("--model", "-m", default=None, help="Override default model")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
@click.option("--verbose", "-v", is_flag=True, help="Increase output verbosity to INFO")
@click.option(
    "--log-level",
    type=click.Choice(Logging.LEVELS, case_sensitive=False),
    help="Set log level",
)
def unreleased(
    version,
    dry_run,
    yes,
    file,
    model,
    hint,
    quiet,
    verbose,
    log_level,
    from_tag,
    to_tag,
    show_prompt,
    preserve_existing,
    replace_unreleased,
    no_replace_unreleased,
    all,
):
    """Generate unreleased changelog entries from beginning to specified version or HEAD."""
    # Import here to avoid circular imports
    from clog.main import main_business_logic

    # Set up logging
    effective_log_level = log_level or config["log_level"]
    if verbose and effective_log_level not in ("DEBUG", "INFO"):
        effective_log_level = "INFO"
    if quiet:
        effective_log_level = "ERROR"
    setup_logging(effective_log_level)

    # Handle conflicting flags
    if replace_unreleased and no_replace_unreleased:
        click.echo("Error: --replace-unreleased and --no-replace-unreleased cannot be used together")
        sys.exit(2)

    # Determine replace_unreleased value
    if no_replace_unreleased:
        replace_unreleased_value = False
    elif replace_unreleased is not None:
        replace_unreleased_value = replace_unreleased
    else:
        replace_unreleased_value = None

    # Handle the special unreleased mode
    success = main_business_logic(
        changelog_file=file,
        from_tag=from_tag,
        to_tag=to_tag,
        model=model,
        hint=hint,
        show_prompt=show_prompt,
        require_confirmation=not yes,
        quiet=quiet,
        dry_run=dry_run,
        preserve_existing=preserve_existing,
        replace_unreleased=replace_unreleased_value,
        special_unreleased_mode=True,
    )

    if not success:
        sys.exit(1)


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show the version of the Changelog Updater tool")
@click.pass_context
def cli(ctx, version):
    """Changelog Updater - Generate changelog entries from git tags with AI."""
    if version:
        click.echo(f"changelog-updater version: {__version__}")
        sys.exit(0)
    # If no subcommand was invoked, run the add command by default
    if ctx.invoked_subcommand is None:
        ctx.invoke(
            add,
            file="CHANGELOG.md",
            from_tag=None,
            to_tag=None,
            show_prompt=False,
            quiet=False,
            yes=False,
            hint="",
            model=None,
            dry_run=False,
            verbose=False,
            log_level=None,
            preserve_existing=False,
            replace_unreleased=False,
            all=False,
            tag=None,
        )


# Add subcommands
cli.add_command(config_cli)
cli.add_command(init_cli)
cli.add_command(init_changelog)
cli.add_command(add)
cli.add_command(unreleased)
cli.add_command(update_version, "update")


if __name__ == "__main__":
    cli()
