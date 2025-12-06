"""Configuration options dataclasses for kittylog.

Contains dataclasses for CLI and workflow options.
"""

from dataclasses import dataclass, field

from kittylog.constants import EnvDefaults


@dataclass
class WorkflowOptions:
    """Options for workflow control."""

    dry_run: bool = False
    yes: bool = False
    all: bool = False
    no_unreleased: bool = False
    interactive: bool = True
    include_diff: bool = False
    quiet: bool = False
    require_confirmation: bool = True
    update_all_entries: bool = False
    language: str | None = None
    audience: str | None = None
    show_prompt: bool = False
    hint: str = ""
    verbose: bool = False
    context_entries_count: int = field(default_factory=lambda: EnvDefaults.CONTEXT_ENTRIES)
    incremental_save: bool = True
    detail_level: str = "normal"  # concise, normal, or detailed


@dataclass
class ChangelogOptions:
    """Options for changelog generation and output."""

    changelog_file: str = "CHANGELOG.md"
    from_tag: str | None = None
    to_tag: str | None = None
    show_prompt: bool = False
    hint: str = ""
    language: str | None = None
    audience: str | None = None
    grouping_mode: str = field(default_factory=lambda: EnvDefaults.GROUPING_MODE)
    gap_threshold_hours: float = field(default_factory=lambda: EnvDefaults.GAP_THRESHOLD_HOURS)
    date_grouping: str = field(default_factory=lambda: EnvDefaults.DATE_GROUPING)
    special_unreleased_mode: bool = False
