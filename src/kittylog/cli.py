"""CLI entry point for kittylog.

Defines the Click-based command-line interface and delegates execution to the main workflow.
"""

import logging
import sys
from collections.abc import Callable

import click

from kittylog import __version__
from kittylog.auth_cli import auth as auth_cli
from kittylog.config import ChangelogOptions, WorkflowOptions
from kittylog.config import config as config_cli
from kittylog.constants import Audiences, DateGrouping, EnvDefaults, GroupingMode, Logging
from kittylog.errors import AIError, ChangelogError, ConfigError, GitError, handle_error
from kittylog.init_changelog_cli import init_changelog
from kittylog.init_cli import init as init_cli
from kittylog.language_cli import language as language_cli
from kittylog.main import main_business_logic
from kittylog.model_cli import model as model_cli
from kittylog.output import get_output_manager
from kittylog.release_cli import release as release_cli
from kittylog.ui.prompts import interactive_configuration
from kittylog.update_cli import update_version
from kittylog.ui.banner import print_banner
from kittylog.utils.logging import setup_command_logging

# No need for lazy loading - breaking compatibility for cleaner code

logger = logging.getLogger(__name__)


def _build_cli_options(
    *,
    # Workflow options
    dry_run: bool,
    quiet: bool,
    verbose: bool,
    yes: bool,
    all_entries: bool,
    no_unreleased: bool,
    include_diff: bool,
    interactive: bool,
    audience: str | None,
    language: str | None,
    hint: str,
    show_prompt: bool,
    context_entries: int,
    incremental_save: bool,
    detail: str,
    # Changelog options
    file: str,
    from_tag: str | None,
    to_tag: str | None,
    grouping_mode: str | None,
    gap_threshold: float | None,
    date_grouping: str | None,
) -> tuple[WorkflowOptions, ChangelogOptions]:
    """Build WorkflowOptions and ChangelogOptions from CLI parameters.

    This helper centralizes the construction of option objects, reducing
    boilerplate in command functions.

    Returns:
        Tuple of (WorkflowOptions, ChangelogOptions)
    """
    workflow_opts = WorkflowOptions(
        dry_run=dry_run,
        quiet=quiet,
        verbose=verbose,
        require_confirmation=not yes,
        update_all_entries=all_entries,
        no_unreleased=no_unreleased,
        include_diff=include_diff,
        interactive=interactive,
        yes=yes,
        audience=audience or EnvDefaults.AUDIENCE,
        language=language or EnvDefaults.LANGUAGE,
        hint=hint or "",
        show_prompt=show_prompt,
        context_entries_count=context_entries,
        incremental_save=incremental_save,
        detail_level=detail,
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

    return workflow_opts, changelog_opts


# Shared option decorators to reduce CLI duplication


def workflow_options(f: Callable) -> Callable:
    """Decorator for workflow control options.

    Adds options for controlling the changelog update workflow including:
    dry-run mode, auto-confirmation, processing scope, and save behavior.
    """
    f = click.option("--dry-run", "-d", is_flag=True, help="Dry run the changelog update workflow")(f)
    f = click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")(f)
    f = click.option("--all", "-a", is_flag=True, help="Update all entries (not just missing ones)")(f)
    f = click.option(
        "--incremental-save/--no-incremental-save",
        default=True,
        help="Save entries incrementally as they are generated (default: enabled)",
    )(f)
    return f


def changelog_options(f: Callable) -> Callable:
    """Decorator for changelog file and content options.

    Adds options for specifying changelog file location, tag ranges, language/audience,
    and content generation parameters.
    """
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
    f = click.option(
        "--detail",
        type=click.Choice(["concise", "normal", "detailed"], case_sensitive=False),
        default="normal",
        help="Output detail level: concise (brief, ~6 bullets), normal (default, ~10), detailed (~15)",
    )(f)
    return f


def model_options(f: Callable) -> Callable:
    """Decorator for AI model selection options.

    Adds options for overriding the default AI model used for changelog generation.
    """
    f = click.option("--model", "-m", default=None, help="Override default model")(f)
    return f


def logging_options(f: Callable) -> Callable:
    """Decorator for logging and output control options.

    Adds options for controlling output verbosity, log levels, and quiet mode.
    """
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
def add_cli(tag: str | None = None, **kwargs) -> None:
    """Add missing changelog entries or update a specific tag entry.

    Modern CLI using **kwargs to reduce parameter count from 26 to 2.
    Click passes all decorated options as keyword arguments.

    Args:
        tag: Optional specific tag to update
        **kwargs: All CLI options from decorators (file, from_tag, model, etc.)

    Examples:
        kittylog                           # Update missing entries
        kittylog v1.2.0                   # Update specific tag
        kittylog --grouping-mode dates     # Date-based grouping
    """
    # Extract options from kwargs with defaults
    quiet = kwargs.get("quiet", False)
    verbose = kwargs.get("verbose", False)
    log_level = kwargs.get("log_level")
    interactive = kwargs.get("interactive", True)
    model = kwargs.get("model")
    hint = kwargs.get("hint", "")

    # Mutable options that may be modified by interactive mode
    grouping_mode = kwargs.get("grouping_mode")
    gap_threshold = kwargs.get("gap_threshold")
    date_grouping = kwargs.get("date_grouping")
    include_diff = kwargs.get("include_diff", False)
    yes = kwargs.get("yes", False)
    audience = kwargs.get("audience")

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
        from_tag = kwargs.get("from_tag")
        to_tag = kwargs.get("to_tag")
        _validate_cli_options(grouping_mode, from_tag, to_tag, gap_threshold, date_grouping)

        # Build parameter objects using helper
        workflow_opts, changelog_opts = _build_cli_options(
            dry_run=kwargs.get("dry_run", False),
            quiet=quiet,
            verbose=verbose,
            yes=yes,
            all_entries=kwargs.get("all", False),
            no_unreleased=kwargs.get("no_unreleased", False),
            include_diff=include_diff,
            interactive=interactive,
            audience=selected_audience,
            language=kwargs.get("language"),
            hint=hint,
            show_prompt=kwargs.get("show_prompt", False),
            context_entries=kwargs.get("context_entries", 0),
            incremental_save=kwargs.get("incremental_save", True),
            detail=kwargs.get("detail", "normal"),
            file=kwargs.get("file", "CHANGELOG.md"),
            from_tag=from_tag,
            to_tag=to_tag,
            grouping_mode=grouping_mode,
            gap_threshold=gap_threshold,
            date_grouping=date_grouping,
        )

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

    # Print banner on startup
    # We check for quiet flag manually in sys.argv to avoid printing in quiet mode
    # before the command options are parsed and logging is set up.
    if "-q" not in sys.argv and "--quiet" not in sys.argv:
        print_banner(get_output_manager())

    # If no subcommand was invoked, run the add command by default
    if ctx.invoked_subcommand is None:
        ctx.invoke(
            add_cli,
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
            incremental_save=True,
            tag=None,
            no_unreleased=False,
            include_diff=False,
            context_entries=0,
            interactive=True,
            grouping_mode=None,
            gap_threshold=None,
            date_grouping=None,
            detail="normal",
        )


# Add subcommands
cli.add_command(config_cli)
cli.add_command(init_cli)
cli.add_command(language_cli)
cli.add_command(init_changelog)
cli.add_command(add_cli)
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
