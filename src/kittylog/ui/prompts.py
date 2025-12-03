"""Questionary prompt utilities for interactive configuration."""

import questionary

from kittylog.config import config
from kittylog.errors import ConfigError, GitError, AIError, ChangelogError
from kittylog.output import get_output_manager


def interactive_configuration(grouping_mode, gap_threshold, date_grouping, include_diff, yes, quiet, audience=None):
    """Interactive configuration using questionary prompts.

    Guides users through kittylog configuration with explanations and helpful defaults.
    Less tech-savvy users get clear guidance and warnings about options like git diff costs.
    """
    if quiet:
        # Skip prompts in quiet mode, use sensible defaults
        return (
            grouping_mode or "tags",
            gap_threshold or 4.0,
            date_grouping or "daily",
            include_diff or False,
            yes or True,  # Auto-accept in quiet mode for scripting
            audience or (config.get("audience") if isinstance(config, dict) else None) or "stakeholders",
        )

    output = get_output_manager()
    output.echo("🔧 Welcome to kittylog! Let's configure your changelog generation...")
    output.echo("")

    try:
        # Grouping mode selection with explanations
        grouping_mode_choices = [
            {"name": "Tags (Recommended) - Use git tags for version changes", "value": "tags"},
            {"name": "Dates - Group commits by time periods (daily/weekly/monthly)", "value": "dates"},
            {"name": "Gaps - Detect natural breaks in commit timing", "value": "gaps"},
        ]

        # Use the actual string value as default, not the variable
        default_grouping = grouping_mode or "tags"
        selected_grouping = questionary.select(
            "How would you like to group your changelog entries?", choices=grouping_mode_choices
        ).ask()

        if not selected_grouping:
            selected_grouping = default_grouping

        # Mode-specific configuration
        selected_gap_threshold = gap_threshold or 4.0
        selected_date_grouping = date_grouping or "daily"

        if selected_grouping == "gaps":
            output.echo("")
            output.echo("💡 Gap mode detects natural breaks in your development timeline.")

            gap_threshold_response = questionary.text(
                "How many hours of silence should indicate a new changelog section?",
                default=str(selected_gap_threshold),
                validate=lambda text: text.replace('.', '', 1).isdigit() and float(text) > 0,
            ).ask()

            if gap_threshold_response:
                selected_gap_threshold = float(gap_threshold_response)

        elif selected_grouping == "dates":
            output.echo("")
            output.echo("📅 Date mode groups commits by time periods.")

            date_grouping_choices = [
                {"name": "Daily - Create entries for each day", "value": "daily"},
                {"name": "Weekly - Create entries for each week", "value": "weekly"},
                {"name": "Monthly - Create entries for each month", "value": "monthly"},
            ]

            selected_date_grouping = questionary.select(
                "How would you like to group by date?", choices=date_grouping_choices
            ).ask()

        # Audience selection
        output.echo("")
        audience_choices = [
            {"name": "Developers - Technical details, API changes, implementation focus", "value": "developers"},
            {
                "name": "Stakeholders - Business impact, features, user-facing changes (Recommended)",
                "value": "stakeholders",
            },
            {"name": "End Users - Simple feature descriptions, what's new, improvements", "value": "end_users"},
        ]

        selected_audience = questionary.select(
            "Who is the primary audience for your changelog?",
            choices=audience_choices,
        ).ask()

        if not selected_audience:
            selected_audience = audience or config.get("audience") if isinstance(config, dict) else None
            selected_audience = selected_audience or "stakeholders"

        # Git diff inclusion with clear warning about costs
        output.echo("")
        output.echo("⚠️  Git diff adds detailed code changes to help AI understand context better.")
        output.echo("   However, this can dramatically increase API costs and processing time!")

        diff_response = questionary.confirm(
            "Include git diff? (Not recommended for regular use)", default=include_diff or False
        ).ask()

        if diff_response is None:
            selected_include_diff = include_diff or False
        else:
            selected_include_diff = diff_response

        # Confirmation prompt before proceeding
        output.echo("")
        output.echo("✨ Configuration complete!")
        output.echo("")

        return (
            selected_grouping or "tags",
            selected_gap_threshold or 4.0,
            selected_date_grouping or "daily",
            selected_include_diff or False,
            yes or False,
            selected_audience or "stakeholders",
        )

    except KeyboardInterrupt:
        output.warning("")
        output.warning("🛑 Configuration cancelled by user.")
        raise
    except (ConfigError, GitError, AIError, ChangelogError) as e:
        output.warning("")
        output.warning(f"⚠️  Configuration setup failed: {e}")
        output.warning("Falling back to default configuration...")
        raise