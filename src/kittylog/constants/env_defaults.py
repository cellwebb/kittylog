"""Default values for environment variables."""

from .enums import DateGrouping, GroupingMode


class EnvDefaults:
    """Default values for environment variables."""

    MODEL: str = "openai:gpt-4"
    MAX_RETRIES: int = 3
    TEMPERATURE: float = 1.0
    MAX_OUTPUT_TOKENS: int = 1024
    WARNING_LIMIT_TOKENS: int = 16384
    GROUPING_MODE: str = GroupingMode.TAGS.value
    GAP_THRESHOLD_HOURS: float = 4.0
    DATE_GROUPING: str = DateGrouping.DAILY.value
    TRANSLATE_HEADINGS: bool = False
    AUDIENCE: str = "developers"
    LOG_LEVEL: str = "WARNING"
    LANGUAGE: str = "English"
    CONTEXT_ENTRIES: int = 5  # Number of preceding entries for AI context (0 = disabled)
