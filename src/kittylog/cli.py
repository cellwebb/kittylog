"""CLI entry point for changelog-updater.

Defines the Click-based command-line interface and delegates execution to the main workflow.
"""

import logging
import sys

import click

from kittylog import __version__
from kittylog.config import load_config
from kittylog.config_cli import config as config_cli
from kittylog.constants import Logging
from kittylog.errors import handle_error
from kittylog.init_changelog import init_changelog
from kittylog.init_cli import init as init_cli
from kittylog.main import main_business_logic
from kittylog.output import get_output_manager, set_output_mode
from kittylog.update_cli import update_version
from kittylog.utils import setup_logging

config = load_config()
logger = logging.getLogger(__name__)


# Shared option decorators to reduce CLI duplication
def workflow_options(f):
    """Common workflow control options."""
    f = click.option("--dry-run", "-d", is_flag=True, help="Dry run the changelog update workflow")(f)
    f = click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")(f)
    f = click.option("--all", "-a", is_flag=True, help="Update all entries (not just missing ones)")(f)
    return f


def changelog_options(f):
    """Common changelog-related options."""
    f = click.option("--file", "-f", default="CHANGELOG.md", help="Path to changelog file")(f)
    f = click.option("--from-tag", "-s", default=None, help="Start from specific tag")(f)
    f = click.option("--to-tag", "-t", default=None, help="Update up to specific tag")(f)
    f = click.option("--show-prompt", "-p", is_flag=True, help="Show the prompt sent to the LLM")(f)
    f = click.option("--hint", "-h", default="", help="Additional context for the prompt")(f)
    f = click.option("--no-unreleased", is_flag=True, help="Skip creating unreleased section")(f)
    return f


def model_options(f):
    """Common model-related options."""
    f = click.option("--model", "-m", default=None, help="Override default model")(f)
    return f


def logging_options(f):
    """Common logging and output options."""
    f = click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")(f)
    f = click.option("--verbose", "-v", is_flag=True, help="Increase output verbosity to INFO")(f)
    f = click.option(
        "--log-level",
        type=click.Choice(Logging.LEVELS, case_sensitive=False),
        help="Set log level",
    )(f)
    return f


def common_options(f):
    """All common options combined."""
    f = workflow_options(f)
    f = changelog_options(f)
    f = model_options(f)
    f = logging_options(f)
    return f


def setup_command_logging(log_level, verbose, quiet):
    """Set up logging for CLI commands with consistent logic."""
    effective_log_level = log_level or config["log_level"]
    if verbose and effective_log_level not in ("DEBUG", "INFO"):
        effective_log_level = "INFO"
    if quiet:
        effective_log_level = "ERROR"
    setup_logging(effective_log_level)

    # Configure output manager mode
    set_output_mode(quiet=quiet, verbose=verbose)


@click.command(context_settings={"ignore_unknown_options": True})
@common_options
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
    all,
    tag,
    no_unreleased,
):
    """Add missing changelog entries or update a specific tag entry.

    When run without arguments, adds entries for tags missing from changelog.
    When run with a specific tag, processes only that tag (overwrites if exists).
    When --all flag is used, updates all entries in changelog.
    """
    try:
        setup_command_logging(log_level, verbose, quiet)
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
                no_unreleased=no_unreleased,
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
                no_unreleased=no_unreleased,
            )

        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        output = get_output_manager()
        output.warning("Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        handle_error(e)
        sys.exit(1)


@click.command()
@common_options
@click.argument("version", required=False)
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
    all,
    version,
    no_unreleased,
):
    """Compatibility update command for integration tests."""

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
            no_unreleased=no_unreleased,
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
            no_unreleased=no_unreleased,
        )

    if not success:
        sys.exit(1)


@click.command()
@common_options
@click.argument("version", required=False)
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
    all,
    no_unreleased,
):
    """Generate unreleased changelog entries from beginning to specified version or HEAD."""
    # Import here to avoid circular imports
    from kittylog.main import main_business_logic

    # Set up logging
    setup_command_logging(log_level, verbose, quiet)

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
        special_unreleased_mode=True,
        no_unreleased=no_unreleased,
    )

    if not success:
        sys.exit(1)


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show the version of the Changelog Updater tool")
@click.pass_context
def cli(ctx, version):
    """Changelog Updater - Generate changelog entries from git tags with AI."""
    if version:
        output = get_output_manager()
        output.echo(f"changelog-updater version: {__version__}")
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
