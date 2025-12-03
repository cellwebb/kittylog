"""Configuration data classes for kittylog.

Contains dataclasses and related structures for configuration management.
"""

from dataclasses import dataclass, field

from kittylog.constants import DateGrouping, EnvDefaults, GroupingMode


@dataclass
class KittylogConfigData:
    """Centralized configuration with validation.

    This dataclass replaces TypedDict with proper validation
    and default values.
    """

    model: str = field(default_factory=lambda: EnvDefaults.MODEL)
    temperature: float = field(default_factory=lambda: EnvDefaults.TEMPERATURE)
    max_output_tokens: int = field(default_factory=lambda: EnvDefaults.MAX_OUTPUT_TOKENS)
    max_retries: int = field(default_factory=lambda: EnvDefaults.MAX_RETRIES)
    log_level: str = field(default_factory=lambda: EnvDefaults.LOG_LEVEL)
    warning_limit_tokens: int = field(default_factory=lambda: EnvDefaults.WARNING_LIMIT_TOKENS)
    grouping_mode: str = field(default_factory=lambda: EnvDefaults.GROUPING_MODE)
    gap_threshold_hours: float = field(default_factory=lambda: EnvDefaults.GAP_THRESHOLD_HOURS)
    date_grouping: str = field(default_factory=lambda: EnvDefaults.DATE_GROUPING)
    language: str = field(default_factory=lambda: EnvDefaults.LANGUAGE)
    audience: str = field(default_factory=lambda: EnvDefaults.AUDIENCE)
    translate_headings: bool = field(default_factory=lambda: EnvDefaults.TRANSLATE_HEADINGS)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {self.temperature}")
        if self.max_output_tokens < 1:
            raise ValueError(f"Max output tokens must be positive, got {self.max_output_tokens}")
        if self.max_retries < 0:
            raise ValueError(f"Max retries must be non-negative, got {self.max_retries}")
        if self.gap_threshold_hours <= 0 or self.gap_threshold_hours > 168:
            raise ValueError(f"Gap threshold hours must be between 0 and 168, got {self.gap_threshold_hours}")
        if self.grouping_mode not in [mode.value for mode in GroupingMode]:
            raise ValueError(f"Invalid grouping mode: {self.grouping_mode}")
        if self.date_grouping not in [mode.value for mode in DateGrouping]:
            raise ValueError(f"Invalid date grouping: {self.date_grouping}")


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
