"""CLI command for updating specific versions in changelog."""

import logging
import sys
from pathlib import Path

import click

from clog.changelog import create_changelog_header, find_existing_tags, read_changelog, write_changelog
from clog.config import load_config
from clog.constants import Logging
from clog.errors import handle_error
from clog.git_operations import get_previous_tag
from clog.main import main_business_logic
from clog.utils import setup_logging

logger = logging.getLogger(__name__)
config = load_config()


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
def update_version(
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

        # If no version is specified, process all tags (update behavior)
        if version is None:
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

            # Run main business logic with update behavior (process all tags)
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
                update_all_entries=True,  # Update command processes all entries by default
            )

            if not success:
                sys.exit(1)
            return

        # Normalize version (remove 'v' prefix for internal processing)
        normalized_version = version.lstrip("v")
        git_version = f"v{normalized_version}" if not version.startswith("v") else version

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
            from_tag=from_tag or previous_tag,  # Use provided from_tag or fallback to previous_tag
            to_tag=git_version,
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            require_confirmation=not yes,
            quiet=quiet,
            dry_run=dry_run,
            preserve_existing=preserve_existing,
            replace_unreleased=True,  # Always overwrite for specific versions
        )

        if not success:
            sys.exit(1)

    except Exception as e:
        handle_error(e)
        sys.exit(1)


if __name__ == "__main__":
    update_version()
