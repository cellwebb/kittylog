"""CLI command for preparing changelog releases."""

import logging
import sys

import click

from kittylog.changelog.io import prepare_release, read_changelog
from kittylog.config import ChangelogOptions, WorkflowOptions, load_config
from kittylog.constants import EnvDefaults, Logging
from kittylog.errors import AIError, ChangelogError, ConfigError, GitError, handle_error
from kittylog.main import main_business_logic
from kittylog.output import get_output_manager, set_output_mode
from kittylog.utils import setup_logging

logger = logging.getLogger(__name__)


@click.command()
@click.argument("version", required=True)
@click.option("--file", "-f", default="CHANGELOG.md", help="Path to changelog file")
@click.option("--dry-run", "-d", is_flag=True, help="Show what would be done without making changes")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--skip-generate", is_flag=True, help="Skip changelog generation, only finalize release")
@click.option("--model", "-m", default=None, help="Override default model for generation")
@click.option("--hint", "-h", default="", help="Additional context for the prompt")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
@click.option("--verbose", "-v", is_flag=True, help="Increase output verbosity")
@click.option(
    "--log-level",
    type=click.Choice(Logging.LEVELS, case_sensitive=False),
    help="Set log level",
)
def release(
    version,
    file,
    dry_run,
    yes,
    skip_generate,
    model,
    hint,
    quiet,
    verbose,
    log_level,
):
    """Prepare changelog for a release.

    Generates changelog entries (unless --skip-generate) and converts the
    [Unreleased] section to a versioned release with today's date.

    VERSION is the version to release (e.g., 2.3.0 or v2.3.0).

    Examples:

        kittylog release 2.3.0              # Generate changelog & prepare release

        kittylog release 2.3.0 --skip-generate  # Only finalize existing Unreleased

        kittylog release v2.3.0 --dry-run   # Preview what would happen
    """
    try:
        config = load_config()

        # Set up logging
        effective_log_level = log_level or config.log_level or EnvDefaults.LOG_LEVEL
        if verbose and effective_log_level not in ("DEBUG", "INFO"):
            effective_log_level = "INFO"
        if quiet:
            effective_log_level = "ERROR"
        setup_logging(effective_log_level)
        set_output_mode(quiet=quiet, verbose=verbose)

        output = get_output_manager()

        # Normalize version
        normalized_version = version.lstrip("v")

        logger.info(f"Preparing release {normalized_version}")

        # Step 1: Generate changelog entries (unless skipped)
        if not skip_generate:
            output.info(f"Generating changelog entries for {normalized_version}...")

            changelog_opts = ChangelogOptions(
                changelog_file=file,
                from_tag=None,
                to_tag=None,
                special_unreleased_mode=True,  # Process commits since last tag for the release
            )
            workflow_opts = WorkflowOptions(
                quiet=quiet,
                require_confirmation=False,  # Don't prompt during release
                dry_run=dry_run,
                yes=True,  # Auto-confirm
                language=EnvDefaults.LANGUAGE,
                audience=EnvDefaults.AUDIENCE,
                no_unreleased=False,
                interactive=False,
            )

            success, _token_usage = main_business_logic(
                changelog_opts=changelog_opts,
                workflow_opts=workflow_opts,
                model=model,
                hint=hint,
            )

            if not success:
                output.error("Failed to generate changelog entries")
                sys.exit(1)

        # Step 2: Prepare release (convert Unreleased to versioned)
        if dry_run:
            content = read_changelog(file)
            if "## [Unreleased]" in content:
                output.info(f"Would convert [Unreleased] to [{normalized_version}] - <today's date>")
            else:
                output.warning("No [Unreleased] section found to convert")
            output.success(f"Dry run complete for release {normalized_version}")
        else:
            output.info(f"Finalizing release {normalized_version}...")
            prepare_release(file, normalized_version)
            output.success(f"Prepared changelog for release {normalized_version}")

    except (ConfigError, GitError, AIError, ChangelogError) as e:
        handle_error(e)
        sys.exit(1)


if __name__ == "__main__":
    release()
