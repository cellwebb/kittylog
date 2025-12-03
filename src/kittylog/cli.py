"""CLI entry point for kittylog.

Defines the Click-based command-line interface and delegates execution to the main workflow.
"""

import logging
import sys

import click

from kittylog import __version__
from kittylog.config import load_config
from kittylog.config_cli import config as config_cli
from kittylog.constants import Audiences, Languages, Logging
from kittylog.errors import AIError, ChangelogError, ConfigError, GitError, handle_error
from kittylog.init_changelog import init_changelog
from kittylog.init_cli import init as init_cli
from kittylog.language_cli import language as language_cli
from kittylog.main import main_business_logic
from kittylog.output import get_output_manager, set_output_mode
from kittylog.ui.prompts import interactive_configuration
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
    f = click.option(
        "--language",
        "-l",
        default=None,
        help="Override the language for changelog entries (e.g., 'Spanish', 'es', 'zh-CN', 'ja')",
    )(f)
    f = click.option(
        "--audience",
        "-u",
        default=None,
        type=click.Choice(Audiences.slugs(), case_sensitive=False),
        help="Target audience for changelog tone (developers, users, stakeholders)",
    )(f)
    f = click.option("--no-unreleased", is_flag=True, help="Skip creating unreleased section")(f)
    f = click.option(
        "--include-diff",
        is_flag=True,
        help="Include git diff in AI context (warning: can dramatically increase token usage)",
    )(f)
    f = click.option(
        "--interactive/--no-interactive",
        "-i",
        default=True,
        help="Interactive mode with guided questions for configuration (default: enabled)",
    )(f)
    f = click.option(
        "--grouping-mode",
        type=click.Choice(["tags", "dates", "gaps"], case_sensitive=False),
        default=None,
        help="How to group commits: 'tags' uses git tags, 'dates' groups by time periods, 'gaps' detects natural breaks",
    )(f)
    f = click.option(
        "--gap-threshold",
        type=float,
        default=None,
        help="Time gap threshold in hours for gap-based grouping (default: 4.0)",
    )(f)
    f = click.option(
        "--date-grouping",
        type=click.Choice(["daily", "weekly", "monthly"], case_sensitive=False),
        default=None,
        help="Date grouping period for date-based grouping (default: daily)",
    )(f)
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


# Interactive configuration is now imported from kittylog.ui.prompts


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
    language,
    audience,
    model,
    dry_run,
    verbose,
    log_level,
    all,
    tag,
    no_unreleased,
    include_diff,
    interactive,
    grouping_mode,
    gap_threshold,
    date_grouping,
):
    """Add missing changelog entries or update a specific tag entry.

        When run without arguments, adds entries for tags missing from changelog.
        When run with a specific tag, processes only that tag (overwrites if exists).
        When --all flag is used, updates all entries in changelog.

        INTERACTIVE MODE:
        Interactive mode is enabled by default to guide you through configuration options.
    Use --no-interactive to disable guided setup for automation/advanced usage.

        BOUNDARY DETECTION MODES:

        --grouping-mode tags (default): Use git tags to create changelog sections
        Example: kittylog --grouping-mode tags

        --grouping-mode dates: Group commits by time periods
        Example: kittylog --grouping-mode dates --date-grouping weekly

        --grouping-mode gaps: Detect natural breaks in commit timing
        Example: kittylog --grouping-mode gaps --gap-threshold 6.0

        GIT DIFF OPTION:
        --include-diff: Add detailed git diff to AI context (⚠️  Warning: can dramatically increase token usage)
    """
    try:
        setup_command_logging(log_level, verbose, quiet)
        logger.info("Starting kittylog")

        # Initialize selected_audience before interactive check
        selected_audience = None

        # Interactive mode configuration (now default behavior)
        if interactive:
            grouping_mode, gap_threshold, date_grouping, include_diff, yes, selected_audience = (
                interactive_configuration(
                    grouping_mode, gap_threshold, date_grouping, include_diff, yes, quiet, audience
                )
            )

        # Use interactive or provided values consistently
        final_grouping_mode = grouping_mode or config["grouping_mode"] or "tags"
        final_gap_threshold = gap_threshold or config["gap_threshold_hours"] or 4.0
        final_date_grouping = date_grouping or config["date_grouping"] or "daily"
        final_include_diff = include_diff or False

        # Validate gap threshold
        if final_gap_threshold <= 0:
            click.echo("Error: --gap-threshold must be positive", err=True)
            sys.exit(1)

        # Validate for conflicting options
        if final_grouping_mode != "tags" and (from_tag or to_tag):
            click.echo(
                f"Warning: --from-tag and --to-tag are only supported with --grouping-mode tags. "
                f"Using {final_grouping_mode} mode instead.",
                err=True,
            )

        if final_grouping_mode == "gaps" and date_grouping:
            click.echo("Warning: --date-grouping is ignored when using --grouping-mode gaps", err=True)

        if final_grouping_mode == "dates" and gap_threshold:
            click.echo("Warning: --gap-threshold is ignored when using --grouping-mode dates", err=True)

        resolved_language = Languages.resolve_code(language) if language else None
        # Use interactively selected audience first, then command-line audience, then config/default
        config_audience = config.get("audience")
        final_audience = selected_audience or audience or config_audience
        resolved_audience = Audiences.resolve(final_audience) if final_audience else None

        # If a specific tag is provided, process only that tag
        if tag:
            # Normalize tag (remove 'v' prefix if present)
            normalized_tag = tag.lstrip("v")
            # Try to add 'v' prefix if not present (to match git tags)
            git_tag = f"v{normalized_tag}" if not tag.startswith("v") else tag

            # For specific tags, always overwrite the entry
            success, _token_usage = main_business_logic(
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
                grouping_mode=final_grouping_mode,
                gap_threshold_hours=final_gap_threshold,
                date_grouping=final_date_grouping,
                yes=yes,
                include_diff=final_include_diff,
                language=resolved_language,
                audience=resolved_audience,
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
                update_all_entries=all,
                grouping_mode=final_grouping_mode,
                gap_threshold_hours=final_gap_threshold,
                date_grouping=final_date_grouping,
                yes=yes,
                include_diff=final_include_diff,
                language=resolved_language,
                audience=resolved_audience,
            )

        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        output = get_output_manager()
        output.warning("Operation cancelled by user.")
        sys.exit(1)
    except (ConfigError, GitError, AIError, ChangelogError) as e:
        handle_error(e)
        sys.exit(1)


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show the kittylog version")
@click.pass_context
def cli(ctx, version):
    """kittylog - Generate polished changelog entries from your git history."""
    if version:
        output = get_output_manager()
        output.echo(f"kittylog version: {__version__}")
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
            language=None,
            audience=None,
            model=None,
            dry_run=False,
            verbose=False,
            log_level=None,
            all=False,
            tag=None,
            no_unreleased=False,
            include_diff=False,
            interactive=True,
            grouping_mode=None,
            gap_threshold=None,
            date_grouping=None,
        )


# Add subcommands
cli.add_command(config_cli)
cli.add_command(init_cli)
cli.add_command(language_cli)
cli.add_command(init_changelog)
cli.add_command(add)
cli.add_command(update_version, "update")


@click.command(context_settings=language_cli.context_settings)
@click.pass_context
def lang(ctx):
    """Set the language for changelog entries interactively. (Alias for 'language')"""
    ctx.forward(language_cli)


cli.add_command(lang)


if __name__ == "__main__":
    cli()
