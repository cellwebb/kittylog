"""CLI command for updating specific versions in changelog."""

import logging
import sys
from pathlib import Path

import click

from kittylog.changelog import create_changelog_header, find_existing_boundaries, read_changelog, write_changelog
from kittylog.config import load_config
from kittylog.constants import Languages, Logging
from kittylog.errors import handle_error
from kittylog.git_operations import get_previous_tag
from kittylog.main import main_business_logic
from kittylog.utils import setup_logging

logger = logging.getLogger(__name__)
config = load_config()


@click.command()
@click.argument("version", required=False)
@click.option("--dry-run", "-d", is_flag=True, help="Dry run the changelog update workflow")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--all", "-a", is_flag=True, help="Update all entries (not just missing ones)")
@click.option("--file", "-f", default="CHANGELOG.md", help="Path to changelog file")
@click.option("--from-tag", "-s", default=None, help="Start from specific tag")
@click.option("--to-tag", "-t", default=None, help="Update up to specific tag")
@click.option("--show-prompt", "-p", is_flag=True, help="Show the prompt sent to the LLM")
@click.option("--hint", "-h", default="", help="Additional context for the prompt")
@click.option(
    "--language",
    "-l",
    default=None,
    help="Override the language for changelog entries (e.g., 'Spanish', 'es', 'zh-CN')",
)
@click.option("--model", "-m", default=None, help="Override default model")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
@click.option("--verbose", "-v", is_flag=True, help="Increase output verbosity to INFO")
@click.option("--no-unreleased", is_flag=True, help="Skip creating unreleased section")
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
    language,
    quiet,
    verbose,
    log_level,
    from_tag,
    to_tag,
    show_prompt,
    all,
    no_unreleased,
):
    """Update changelog for a specific version or all missing tags if no version specified.

    Example: kittylog update v0.1.0
    """
    try:
        # Set up logging
        effective_log_level = log_level or config["log_level"]
        if verbose and effective_log_level not in ("DEBUG", "INFO"):
            effective_log_level = "INFO"
        if quiet:
            effective_log_level = "ERROR"
        setup_logging(effective_log_level)

        logger.info("Starting kittylog update")

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
            resolved_language = Languages.resolve_code(language) if language else None
            # Run main business logic with update behavior (process all tags)
            success, token_usage = main_business_logic(
                changelog_file=file,
                from_tag=from_tag,
                to_tag=to_tag,
                model=model,
                hint=hint,
                show_prompt=show_prompt,
                require_confirmation=not yes,
                quiet=quiet,
                dry_run=dry_run,
                update_all_entries=True,  # Update command processes all entries by default
                yes=yes,
                language=resolved_language,
            )

            if not success:
                sys.exit(1)
            return

        # Normalize version (remove 'v' prefix for internal processing)
        normalized_version = version.lstrip("v")
        git_version = f"v{normalized_version}" if not version.startswith("v") else version

        # Check if version already exists in changelog
        existing_content = read_changelog(file)
        existing_tags = find_existing_boundaries(existing_content)

        if normalized_version in existing_tags:
            # When updating a specific version, always overwrite existing entry
            if not quiet:
                click.echo(f"Updating existing entry for {version}")

        # Get previous tag for commit range
        previous_tag = get_previous_tag(git_version)

        # Run main business logic for this specific version
        resolved_language = Languages.resolve_code(language) if language else None
        success, token_usage = main_business_logic(
            changelog_file=file,
            from_tag=from_tag or previous_tag,  # Use provided from_tag or fallback to previous_tag
            to_tag=git_version,
            model=model,
            hint=hint,
            show_prompt=show_prompt,
            require_confirmation=not yes,
            quiet=quiet,
            dry_run=dry_run,
            yes=yes,
            language=resolved_language,
        )

        if not success:
            sys.exit(1)

    except Exception as e:
        handle_error(e)
        sys.exit(1)


if __name__ == "__main__":
    update_version()
