"""Configuration dataclass for kittylog.

Provides type-safe configuration with proper defaults and validation.
"""

from dataclasses import dataclass

from kittylog.constants import EnvDefaults


@dataclass
class KittylogConfigData:
    """Type-safe configuration dataclass for kittylog.

    All configuration values with proper defaults and type hints.
    Replaces dict-based configuration for better IDE support and type safety.
    """

    # AI Model configuration
    model: str | None = None  # None when not set, will use EnvDefaults.MODEL in apply_defaults
    temperature: float = EnvDefaults.TEMPERATURE
    max_output_tokens: int = EnvDefaults.MAX_OUTPUT_TOKENS
    max_retries: int = EnvDefaults.MAX_RETRIES

    # Logging configuration
    log_level: str = EnvDefaults.LOG_LEVEL
    warning_limit_tokens: int = EnvDefaults.WARNING_LIMIT_TOKENS

    # Changelog grouping configuration
    grouping_mode: str = EnvDefaults.GROUPING_MODE
    gap_threshold_hours: float = EnvDefaults.GAP_THRESHOLD_HOURS
    date_grouping: str = EnvDefaults.DATE_GROUPING

    # Content configuration
    language: str | None = None  # None when not set, will use EnvDefaults.LANGUAGE in apply_defaults
    audience: str = EnvDefaults.AUDIENCE
    translate_headings: bool = EnvDefaults.TRANSLATE_HEADINGS

    # Advanced configuration
    context_entries: int = EnvDefaults.CONTEXT_ENTRIES

    def apply_defaults(self) -> "KittylogConfigData":
        """Apply default values for None fields.

        Returns:
            New KittylogConfigData instance with defaults applied
        """
        return KittylogConfigData(
            model=self.model if self.model is not None else EnvDefaults.MODEL,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            max_retries=self.max_retries,
            log_level=self.log_level,
            warning_limit_tokens=self.warning_limit_tokens,
            grouping_mode=self.grouping_mode,
            gap_threshold_hours=self.gap_threshold_hours,
            date_grouping=self.date_grouping,
            language=self.language if self.language is not None else EnvDefaults.LANGUAGE,
            audience=self.audience,
            translate_headings=self.translate_headings,
            context_entries=self.context_entries,
        )

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If any configuration value is invalid
        """
        # Temperature validation
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"Invalid temperature: must be between 0.0 and 2.0, got {self.temperature}")

        # Token validation
        if self.max_output_tokens < 1:
            raise ValueError(f"Invalid max_output_tokens: must be positive, got {self.max_output_tokens}")

        # Retry validation (must be >= 1)
        if self.max_retries < 1:
            raise ValueError(f"Invalid max_retries: must be at least 1, got {self.max_retries}")

        # Gap threshold validation
        if self.gap_threshold_hours <= 0:
            raise ValueError(f"Invalid gap_threshold_hours: must be positive, got {self.gap_threshold_hours}")

        # Log level validation
        from kittylog.constants.logging import Logging

        if self.log_level not in Logging.LEVELS:
            raise ValueError(f"Invalid log_level: {self.log_level}. Valid: {Logging.LEVELS}")

        # Validate enum-like values using the dict-based validation
        # This keeps compatibility with existing validation logic
        config_dict = self.to_dict()
        from kittylog.config.loader import validate_config_dict

        validate_config_dict(config_dict)

    def to_dict(self) -> dict:
        """Convert dataclass to dictionary for backward compatibility.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "max_retries": self.max_retries,
            "log_level": self.log_level,
            "warning_limit_tokens": self.warning_limit_tokens,
            "grouping_mode": self.grouping_mode,
            "gap_threshold_hours": self.gap_threshold_hours,
            "date_grouping": self.date_grouping,
            "language": self.language,
            "audience": self.audience,
            "translate_headings": self.translate_headings,
            "context_entries": self.context_entries,
        }

    @classmethod
    def from_dict(cls, config_dict: dict) -> "KittylogConfigData":
        """Create dataclass from dictionary.

        Args:
            config_dict: Dictionary containing configuration values

        Returns:
            KittylogConfigData instance
        """
        return cls(
            model=config_dict.get("model"),
            temperature=config_dict.get("temperature", EnvDefaults.TEMPERATURE),
            max_output_tokens=config_dict.get("max_output_tokens", EnvDefaults.MAX_OUTPUT_TOKENS),
            max_retries=config_dict.get("max_retries", EnvDefaults.MAX_RETRIES),
            log_level=config_dict.get("log_level", EnvDefaults.LOG_LEVEL),
            warning_limit_tokens=config_dict.get("warning_limit_tokens", EnvDefaults.WARNING_LIMIT_TOKENS),
            grouping_mode=config_dict.get("grouping_mode", EnvDefaults.GROUPING_MODE),
            gap_threshold_hours=config_dict.get("gap_threshold_hours", EnvDefaults.GAP_THRESHOLD_HOURS),
            date_grouping=config_dict.get("date_grouping", EnvDefaults.DATE_GROUPING),
            language=config_dict.get("language"),
            audience=config_dict.get("audience", EnvDefaults.AUDIENCE),
            translate_headings=config_dict.get("translate_headings", EnvDefaults.TRANSLATE_HEADINGS),
            context_entries=config_dict.get("context_entries", EnvDefaults.CONTEXT_ENTRIES),
        )
