"""Workflow validation components for kittylog.

This module contains validation logic for changelog generation workflow
including prerequisite checks, parameter validation, and workflow setup.
"""

import logging
import os
from pathlib import Path

from kittylog.config import ChangelogOptions, WorkflowOptions, load_config
from kittylog.constants import Audiences, GroupingMode, Languages, Limits
from kittylog.errors import ChangelogError, ConfigError, GitError, handle_error
from kittylog.output import get_output_manager
from kittylog.tag_operations import get_all_boundaries, get_repo
from kittylog.utils import find_changelog_file

logger = logging.getLogger(__name__)


def validate_workflow_prereqs(
    changelog_file: str,
    gap_threshold_hours: float,
    grouping_mode: str,
) -> None:
    """Perform early validation of workflow requirements.

    Args:
        changelog_file: Path to changelog file
        gap_threshold_hours: Gap threshold for date/gaps mode
        grouping_mode: The boundary grouping mode

    Raises:
        ChangelogError: If changelog file is not writable
        GitError: If git repository is invalid
        ConfigError: If gap_threshold_hours is invalid
    """
    # Validate changelog file is writable
    try:
        # Check if we can write to the directory
        changelog_dir = Path(changelog_file).resolve().parent
        if not os.access(str(changelog_dir), os.W_OK):
            raise ChangelogError(
                f"Cannot write to changelog directory: {changelog_dir}",
                file_path=changelog_file,
            )

        # If file exists, check if it's writable
        changelog_path = Path(changelog_file)
        if changelog_path.exists() and not os.access(changelog_file, os.W_OK):
            raise ChangelogError(
                f"Changelog file is not writable: {changelog_file}",
                file_path=changelog_file,
            )

    except OSError as e:
        raise ChangelogError(
            f"Cannot access changelog file: {e}",
            file_path=changelog_file,
        ) from e

    # Validate git repository exists and is valid
    try:
        get_repo()  # This will raise GitError if invalid
    except GitError as e:
        raise GitError(
            f"Invalid git repository: {e}",
            command="git status",
            stderr=str(e),
        ) from e

    # Validate gap threshold bounds
    if grouping_mode in [GroupingMode.GAPS.value, GroupingMode.DATES.value] and (
        gap_threshold_hours <= 0 or gap_threshold_hours > Limits.MAX_GAP_THRESHOLD_HOURS
    ):  # 1 week max
        raise ConfigError(
            f"gap_threshold_hours must be between 0 and {Limits.MAX_GAP_THRESHOLD_HOURS}, got: {gap_threshold_hours}",
            config_key="gap_threshold_hours",
            config_value=str(gap_threshold_hours),
        )


def validate_and_setup_workflow(
    changelog_opts: "ChangelogOptions",
    workflow_opts: "WorkflowOptions",
) -> tuple[str, str | None, bool, str | None]:
    """Validate inputs and setup workflow parameters."""
    # Load config inside function to avoid module-level loading
    config = load_config()

    # Extract values from dataclasses
    changelog_file = changelog_opts.changelog_file
    grouping_mode = changelog_opts.grouping_mode
    gap_threshold_hours = changelog_opts.gap_threshold_hours
    date_grouping = changelog_opts.date_grouping
    special_unreleased_mode = changelog_opts.special_unreleased_mode
    language = workflow_opts.language
    audience = workflow_opts.audience

    # Early validation
    validate_workflow_prereqs(changelog_file, gap_threshold_hours, grouping_mode)

    # Auto-detect changelog file if using default
    if changelog_file == "CHANGELOG.md":
        changelog_file = find_changelog_file()
        logger.debug(f"Auto-detected changelog file: {changelog_file}")

    # Determine language preferences (CLI overrides config)
    effective_language = language.strip() if language else None
    if not effective_language:
        config_language_value = config.language
        effective_language = config_language_value.strip() if config_language_value else None

    if effective_language:
        effective_language = Languages.resolve_code(effective_language)

    translate_headings_value = config.translate_headings
    translate_headings = translate_headings_value is True  # Explicit True check, False/None → False
    if not effective_language:
        translate_headings = False

    config_audience = config.audience
    effective_audience = Audiences.resolve(audience) if audience else Audiences.resolve(config_audience)

    # Validate we're in a git repository and have boundaries
    try:
        all_boundaries = get_all_boundaries(
            mode=grouping_mode, gap_threshold_hours=gap_threshold_hours, date_grouping=date_grouping
        )
        # In special_unreleased_mode, we don't require boundaries
        if not all_boundaries and not special_unreleased_mode:
            output = get_output_manager()
            if grouping_mode == GroupingMode.TAGS.value:
                output.warning("No git tags found. Create some tags first to generate changelog entries.")
                output.info(
                    "💡 Tip: Try 'git tag v1.0.0' to create your first tag, or use --grouping-mode dates/gaps for tagless workflows"
                )
            elif grouping_mode == GroupingMode.DATES.value:
                output.warning("No date-based boundaries found. This repository might have very few commits.")
                output.info(
                    "💡 Tip: Try --date-grouping weekly/monthly for longer periods, or --grouping-mode gaps for activity-based grouping"
                )
            elif grouping_mode == GroupingMode.GAPS.value:
                output.warning(f"No gap-based boundaries found with {gap_threshold_hours} hour threshold.")
                output.info(
                    f"💡 Tip: Try --gap-threshold {gap_threshold_hours / 2} for shorter gaps, or --grouping-mode dates for time-based grouping"
                )
            raise GitError(
                f"No {grouping_mode} boundaries found in repository",
                command=f"git log --{grouping_mode}",
            )
    except GitError:
        # Re-raise GitError for no boundaries - it will be caught upstream
        raise
    except (ConfigError, ValueError, KeyError) as e:
        handle_error(e)
        raise

    return changelog_file, effective_language, translate_headings, effective_audience
