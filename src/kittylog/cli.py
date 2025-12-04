"""CLI entry point for kittylog.

Defines the Click-based command-line interface and delegates execution to the main workflow.
"""

import logging
import sys
from collections.abc import Callable

import click

from kittylog import __version__
from kittylog.auth_cli import auth as auth_cli
from kittylog.config import ChangelogOptions, WorkflowOptions, load_config
from kittylog.config import config as config_cli
from kittylog.constants import Audiences, DateGrouping, EnvDefaults, GroupingMode, Logging
from kittylog.errors import AIError, ChangelogError, ConfigError, GitError, handle_error
from kittylog.init_changelog_cli import init_changelog
from kittylog.init_cli import init as init_cli
from kittylog.language_cli import language as language_cli
from kittylog.main import main_business_logic
from kittylog.model_cli import model as model_cli
from kittylog.output import get_output_manager, set_output_mode
from kittylog.release_cli import release as release_cli
from kittylog.ui.prompts import interactive_configuration
from kittylog.update_cli import update_version
from kittylog.utils import setup_logging

# No need for lazy loading - breaking compatibility for cleaner code

logger = logging.getLogger(__name__)


# Shared option decorators to reduce CLI duplication


def workflow_options(f: Callable) -> Callable:
    """Common workflow control options."""
    f = click.option("--dry-run", "-d", is_flag=True, help="Dry run the changelog update workflow")(f)
    f = click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")(f)
    f = click.option("--all", "-a", is_flag=True, help="Update all entries (not just missing ones)")(f)
    return f


def changelog_options(f: Callable) -> Callable:
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
        "--context-entries",
        "-C",
        type=int,
        default=0,
        help="Number of preceding changelog entries to include for style reference (default: 0, disabled)",
    )(f)
    f = click.option(
        "--interactive/--no-interactive",
        "-i",
        default=True,
        help="Interactive mode with guided questions for configuration (default: enabled)",
    )(f)
    f = click.option(
        "--grouping-mode",
        type=click.Choice([mode.value for mode in GroupingMode], case_sensitive=False),
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
        type=click.Choice([mode.value for mode in DateGrouping], case_sensitive=False),
        default=None,
        help="Date grouping period for date-based grouping (default: daily)",
    )(f)
    return f


def model_options(f: Callable) -> Callable:
    """Common model-related options."""
    f = click.option("--model", "-m", default=None, help="Override default model")(f)
    return f


def logging_options(f: Callable) -> Callable:
    """Common logging and output options."""
    f = click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")(f)
    f = click.option("--verbose", "-v", is_flag=True, help="Increase output verbosity to INFO")(f)
    f = click.option(
        "--log-level",
        type=click.Choice(Logging.LEVELS, case_sensitive=False),
        help="Set log level",
    )(f)
    return f


def common_options(f: Callable) -> Callable:
    """All common options combined."""
    f = workflow_options(f)
    f = changelog_options(f)
    f = model_options(f)
    f = logging_options(f)
    return f


def setup_command_logging(log_level: str | None, verbose: bool, quiet: bool) -> None:
    """Set up logging for CLI commands with consistent logic."""
    effective_log_level = log_level or load_config().log_level or EnvDefaults.LOG_LEVEL
    if verbose and effective_log_level not in ("DEBUG", "INFO"):
        effective_log_level = "INFO"
    if quiet:
        effective_log_level = "ERROR"
    setup_logging(effective_log_level)

    # Configure output manager mode
    set_output_mode(quiet=quiet, verbose=verbose)


def _validate_cli_options(
    grouping_mode: str | None,
    from_tag: str | None,
    to_tag: str | None,
    gap_threshold: float | None,
    date_grouping: str | None,
) -> None:
    """Validate CLI option combinations and fail fast with clear errors.

    This function converts what were previously warnings into validation errors
    to prevent execution with conflicting or incompatible options.
    """
    # Use defaults if values are None for validation purposes
    effective_grouping_mode = grouping_mode or EnvDefaults.GROUPING_MODE
    effective_date_grouping = date_grouping or EnvDefaults.DATE_GROUPING
    effective_gap_threshold = gap_threshold or EnvDefaults.GAP_THRESHOLD_HOURS

    # Validate: from-tag and to-tag require tags grouping mode
    if effective_grouping_mode != GroupingMode.TAGS.value and (from_tag or to_tag):
        raise click.UsageError(f"--from-tag and --to-tag require --grouping-mode tags, got {effective_grouping_mode}")

    # Validate: date-grouping doesn't work with gaps grouping mode
    if effective_grouping_mode == GroupingMode.GAPS.value and effective_date_grouping != DateGrouping.DAILY.value:
        raise click.UsageError(f"--date-grouping {effective_date_grouping} is incompatible with --grouping-mode gaps")

    # Validate: gap-threshold doesn't work with dates grouping mode
    if (
        effective_grouping_mode == GroupingMode.DATES.value
        and effective_gap_threshold != EnvDefaults.GAP_THRESHOLD_HOURS
    ):
        raise click.UsageError("--gap-threshold is incompatible with --grouping-mode dates")


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
    context_entries,
    interactive,
    grouping_mode,
    gap_threshold,
    date_grouping,
):
    """Add missing changelog entries or update a specific tag entry.

    Modern CLI using parameter objects internally for clean, maintainable code.
    No backward compatibility constraints - can evolve freely.

    Args:
        file: Changelog file path
        from_tag: Starting tag
        to_tag: Ending tag
        ... other CLI args

    Examples:
        kittylog                           # Update missing entries
        kittylog v1.2.0                   # Update specific tag
        kittylog --grouping-mode dates     # Date-based grouping
    """
    try:
        setup_command_logging(log_level, verbose, quiet)
        logger.info("Starting kittylog")

        # Interactive mode configuration
        selected_audience = audience  # Initialize with CLI-provided audience
        if interactive and not quiet:
            grouping_mode, gap_threshold, date_grouping, include_diff, yes, selected_audience = (
                interactive_configuration(
                    grouping_mode, gap_threshold, date_grouping, include_diff, yes, quiet, audience
                )
            )
        elif quiet:
            # In quiet mode, apply same defaults as interactive_configuration would
            from kittylog.config import load_config

            config = load_config()
            grouping_mode = grouping_mode or "tags"
            gap_threshold = gap_threshold or 4.0
            date_grouping = date_grouping or "daily"
            include_diff = include_diff or False
            yes = yes or True  # Auto-accept in quiet mode for scripting
            selected_audience = audience or config.audience or "stakeholders"

        # Early validation of option combinations - fail fast instead of warnings
        _validate_cli_options(grouping_mode, from_tag, to_tag, gap_threshold, date_grouping)

        # Create parameter objects directly - no compatibility layer needed
        workflow_opts = WorkflowOptions(
            dry_run=dry_run,
            quiet=quiet,
            verbose=verbose,
            require_confirmation=not yes,
            update_all_entries=all,
            no_unreleased=no_unreleased,
            include_diff=include_diff,
            interactive=interactive,
            yes=yes,
            audience=selected_audience or EnvDefaults.AUDIENCE,
            language=language or EnvDefaults.LANGUAGE,
            hint=hint or "",
            show_prompt=show_prompt,
            context_entries_count=context_entries,
        )

        changelog_opts = ChangelogOptions(
            changelog_file=file,
            from_tag=from_tag,
            to_tag=to_tag,
            grouping_mode=grouping_mode or EnvDefaults.GROUPING_MODE,
            gap_threshold_hours=gap_threshold or EnvDefaults.GAP_THRESHOLD_HOURS,
            date_grouping=date_grouping or EnvDefaults.DATE_GROUPING,
            special_unreleased_mode=False,
        )

        # Language/audience already set in WorkflowOptions constructor

        # Language/audience already set in WorkflowOptions constructor

        # If a specific tag is provided, process only that tag
        if tag:
            # Normalize tag (remove 'v' prefix if present)
            normalized_tag = tag.lstrip("v")
            # Try to add 'v' prefix if not present (to match git tags)
            git_tag = f"v{normalized_tag}" if not tag.startswith("v") else tag

            # Process specific tag with modern API
            changelog_opts.to_tag = git_tag
        # Modern main_business_logic call with parameter objects
        success, _token_usage = main_business_logic(
            changelog_opts=changelog_opts,
            workflow_opts=workflow_opts,
            model=model,
            hint=hint,
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
            context_entries=0,
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
cli.add_command(release_cli, "release")
cli.add_command(auth_cli)
cli.add_command(model_cli)


@click.command(context_settings=language_cli.context_settings)
@click.pass_context
def lang(ctx):
    """Set the language for changelog entries interactively. (Alias for 'language')"""
    ctx.forward(language_cli)


cli.add_command(lang)


if __name__ == "__main__":
    cli()
