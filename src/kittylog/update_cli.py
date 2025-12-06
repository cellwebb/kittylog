"""CLI command for updating specific versions in changelog."""

import logging
import sys
from pathlib import Path

import click

from kittylog.changelog.io import create_changelog_header, read_changelog, write_changelog
from kittylog.changelog.parser import find_existing_boundaries
from kittylog.commit_analyzer import get_all_tags_with_dates
from kittylog.config import ChangelogOptions, WorkflowOptions, load_config
from kittylog.constants import Audiences, EnvDefaults, Languages, Logging
from kittylog.errors import AIError, ChangelogError, ConfigError, GitError, handle_error
from kittylog.main import main_business_logic
from kittylog.tag_operations import generate_boundary_identifier
from kittylog.utils.logging import setup_command_logging

logger = logging.getLogger(__name__)
config = load_config()


@click.command()
@click.argument("version", required=False)
@click.option("--dry-run", "-d", is_flag=True, help="Dry run the changelog update workflow")
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
@click.option(
    "--audience",
    "-u",
    default=None,
    type=click.Choice(Audiences.slugs(), case_sensitive=False),
    help="Target audience for changelog tone (developers, users, stakeholders)",
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
    file,
    model,
    hint,
    language,
    audience,
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
        # Set up logging using shared utility
        setup_command_logging(log_level, verbose, quiet)

        logger.info("Starting kittylog update")

        # Check if changelog exists, create if not
        changelog_path = Path(file)
        if not changelog_path.exists():
            if click.confirm(f"No changelog found. Create {file} with standard header?"):
                header_content = create_changelog_header()
                write_changelog(file, header_content)
                click.echo(f"Created {file} with standard header")
            else:
                click.echo("Changelog creation cancelled.")
                sys.exit(1)

        # If no version is specified, determine mode based on from/to tags
        if version is None:
            resolved_language = Languages.resolve_code(language) if language else EnvDefaults.LANGUAGE
            resolved_audience = Audiences.resolve(audience)

            # Determine if this is range mode or update all mode
            update_all_entries = not (from_tag is not None or to_tag is not None)

            # Run main business logic with appropriate mode
            changelog_opts = ChangelogOptions(
                changelog_file=file,
                from_tag=from_tag,
                to_tag=to_tag,
            )
            workflow_opts = WorkflowOptions(
                quiet=quiet,
                dry_run=dry_run,
                update_all_entries=update_all_entries,
                language=resolved_language,
                audience=resolved_audience,
            )
            success, _token_usage = main_business_logic(
                changelog_opts=changelog_opts,
                workflow_opts=workflow_opts,
                model=model,
                hint=hint,
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

        if normalized_version in existing_tags and not quiet:
            # When updating a specific version, always overwrite existing entry
            click.echo(f"Updating existing entry for {version}")

        # Get previous tag for commit range
        all_tags = get_all_tags_with_dates()
        current_tag_index = None
        for i, tag in enumerate(all_tags):
            if tag["identifier"] == git_version:
                current_tag_index = i
                break

        previous_tag = None
        if current_tag_index is not None and current_tag_index > 0:
            previous_tag = generate_boundary_identifier(all_tags[current_tag_index - 1], "tags")

        # Run main business logic for this specific version
        resolved_language = Languages.resolve_code(language) if language else EnvDefaults.LANGUAGE
        resolved_audience = Audiences.resolve(audience)
        changelog_opts = ChangelogOptions(
            changelog_file=file,
            from_tag=from_tag or previous_tag,  # Use provided from_tag or fallback to previous_tag
            to_tag=git_version,
        )
        workflow_opts = WorkflowOptions(
            quiet=quiet,
            dry_run=dry_run,
            language=resolved_language,
            audience=resolved_audience,
        )
        success, _token_usage = main_business_logic(
            changelog_opts=changelog_opts,
            workflow_opts=workflow_opts,
            model=model,
            hint=hint,
        )

        if not success:
            sys.exit(1)

    except (ConfigError, GitError, AIError, ChangelogError) as e:
        handle_error(e)
        sys.exit(1)


if __name__ == "__main__":
    update_version()
