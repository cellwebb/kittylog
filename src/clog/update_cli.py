"""CLI command for updating specific versions in changelog."""

import logging
import sys
from pathlib import Path

import click

from clog.changelog import create_changelog_header, read_changelog, write_changelog, find_existing_tags
from clog.git_operations import get_all_tags, get_commits_between_tags, get_previous_tag, get_latest_tag
from clog.main import main_business_logic
from clog.config import load_config
from clog.utils import setup_logging
from clog.constants import Logging
from clog.errors import handle_error

logger = logging.getLogger(__name__)
config = load_config()


@click.command()
@click.argument("version", required=False)
@click.option("--dry-run", "-d", is_flag=True, help="Dry run the changelog update workflow")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--file", "-f", default="CHANGELOG.md", help="Path to changelog file")
@click.option("--model", "-m", default=None, help="Override default model")
@click.option("--hint", "-h", default="", help="Additional context for the prompt")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
@click.option("--verbose", "-v", is_flag=True, help="Increase output verbosity to INFO")
@click.option(
    "--log-level",
    type=click.Choice(Logging.LEVELS, case_sensitive=False),
    help="Set log level",
)
def update_version(version, dry_run, yes, file, model, hint, quiet, verbose, log_level):
    """Update changelog for a specific version or all missing tags if no version specified.

    Example: clog update v0.1.0
    """
    try:
        # Set up logging
        effective_log_level = log_level or config["log_level"]
        if verbose and effective_log_level not in ("DEBUG", "INFO"):
            effective_log_level = "INFO"
        if quiet:
            effective_log_level = "ERROR"
        setup_logging(effective_log_level)

        logger.info("Starting clog update")

        # Check if changelog exists, create if not
        changelog_path = Path(file)
        if not changelog_path.exists():
            if yes or click.confirm(f"No changelog found. Create {file} with standard header?"):
                header_content = create_changelog_header()
                write_changelog(file, header_content)
                click.echo(f"Created {file} with standard header")
            else:
                click.echo("Changelog creation cancelled.")
                sys.exit(1)

        # If no version is specified, process all missing tags (original behavior)
        if version is None:
            # Run main business logic with default behavior (process all missing tags)
            success = main_business_logic(
                changelog_file=file,
                model=model,
                hint=hint,
                show_prompt=False,
                require_confirmation=not yes,
                quiet=quiet,
                dry_run=dry_run,
                preserve_existing=False,
                replace_unreleased=False,  # Default behavior for missing tags
            )

            if not success:
                sys.exit(1)
            return

        # Normalize version (remove 'v' prefix for internal processing)
        normalized_version = version.lstrip('v')
        git_version = f"v{normalized_version}" if not version.startswith('v') else version

        # Check if version already exists in changelog
        existing_content = read_changelog(file)
        existing_tags = find_existing_tags(existing_content)

        if normalized_version in existing_tags:
            if not yes and click.confirm(f"Version {version} already exists in changelog. Overwrite it?"):
                # Proceed with overwriting
                click.echo(f"Overwriting existing entry for {version}")
            elif yes:
                # Automatic overwrite
                click.echo(f"Overwriting existing entry for {version} (automatic mode)")
            else:
                click.echo("Update cancelled.")
                return

        # Get previous tag for commit range
        previous_tag = get_previous_tag(git_version)

        # Run main business logic for this specific version
        success = main_business_logic(
            changelog_file=file,
            from_tag=previous_tag,
            to_tag=git_version,
            model=model,
            hint=hint,
            show_prompt=False,
            require_confirmation=not yes,
            quiet=quiet,
            dry_run=dry_run,
            preserve_existing=False,
            replace_unreleased=True,  # Always overwrite for specific versions
        )

        if not success:
            sys.exit(1)

    except Exception as e:
        handle_error(e)
        sys.exit(1)


if __name__ == "__main__":
    update_version()