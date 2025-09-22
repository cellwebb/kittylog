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
from clog.init_cli import init as init_cli
from clog.main import main_business_logic
from clog.utils import setup_logging

config = load_config()
logger = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show the version of the Changelog Updater tool")
@click.pass_context
def cli(ctx, version):
    """Changelog Updater - Generate changelog entries from git tags with AI."""
    if version:
        click.echo(f"changelog-updater version: {__version__}")
        sys.exit(0)
    # If no subcommand was invoked, run the update command by default
    if ctx.invoked_subcommand is None:
        ctx.invoke(update)


# Add subcommands
cli.add_command(config_cli)
cli.add_command(init_cli)


@click.command(context_settings={"ignore_unknown_options": True})
# Git workflow options
@click.option("--dry-run", "-d", is_flag=True, help="Dry run the changelog update workflow")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
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
@click.option(
    "--replace-unreleased",
    is_flag=True,
    help="Replace existing unreleased content instead of appending to it",
)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def update(
    file, from_tag, to_tag, show_prompt, quiet, yes, hint, model, dry_run, verbose, log_level, replace_unreleased, args
):
    """Update changelog with AI-generated content."""
    try:
        effective_log_level = log_level or config["log_level"]
        if verbose and effective_log_level not in ("DEBUG", "INFO"):
            effective_log_level = "INFO"
        if quiet:
            effective_log_level = "ERROR"
        setup_logging(effective_log_level)
        logger.info("Starting changelog-updater")

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


# Add the update command
cli.add_command(update)


if __name__ == "__main__":
    cli()
