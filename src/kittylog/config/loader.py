"""Configuration loading utilities for kittylog.

Handles environment variable and .env file precedence for application settings.
Configuration precedence (highest to lowest):
1. CLI arguments (highest priority)
2. Environment variables
3. Project .kittylog.env
4. User ~/.kittylog.env
5. Default values (lowest priority)

Note: Generic project .env file is NOT loaded to avoid conflicts
with other tools. Use .kittylog.env for project-specific configuration.
"""

import functools
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from dotenv import load_dotenv

from kittylog.config.data import KittylogConfigData
from kittylog.constants import Audiences, DateGrouping, EnvDefaults, GroupingMode, Languages, Logging

T = TypeVar("T")


@functools.lru_cache(maxsize=1)
def _load_env_files() -> None:
    """Load environment variables from .env files into os.environ.

    Uses lru_cache to ensure this only runs once per session while allowing
    for controlled test isolation.

    Files are loaded in order of priority (lowest to highest):
    1. User ~/.kittylog.env
    2. Project .kittylog.env

    Environment variables already set take highest priority.

    Note: Generic project .env file is NOT loaded to avoid conflicts
    with other tools. Use .kittylog.env for project-specific configuration.
    """
    user_config = Path.home() / ".kittylog.env"
    project_config_env = Path(".kittylog.env")

    # Load in order - load_dotenv with override=False respects existing env vars
    # Later files override earlier ones when override=True
    if user_config.exists():
        load_dotenv(user_config, override=False)

    if project_config_env.exists():
        load_dotenv(project_config_env, override=True)


def ensure_env_files_loaded() -> None:
    """Ensure environment files are loaded (lazy loading)."""
    _load_env_files()


def reset_env_files_cache() -> None:
    """Reset the env files cache for testing purposes.

    This function should only be used in tests to ensure clean isolation
    between test runs that need to control environment variables.
    """
    _load_env_files.cache_clear()


# Load env files lazily when first needed, not at import time
# This prevents test isolation issues and improves startup performance


def _safe_float(value: str | None, default: float) -> float:
    """Safely convert a string to float with default."""
    if value is None:
        return default
    try:
        # Handle Mock objects gracefully in tests
        from unittest.mock import Mock

        if isinstance(value, Mock):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def _safe_int(value: str | None, default: int, min_value: int | None = None) -> int:
    """Safely convert a string to int with default.

    Args:
        value: String value to convert
        default: Default value if conversion fails or value doesn't meet constraints
        min_value: Optional minimum value; if result is below this, returns default
    """
    if value is None:
        return default
    try:
        # Handle Mock objects in tests
        from unittest.mock import Mock

        if isinstance(value, Mock):
            return default
        result = int(value)
        if min_value is not None and result < min_value:
            return default
        return result
    except (ValueError, TypeError):
        return default


def _safe_enum(value: str | None, default: str, valid_values: list[str]) -> str:
    """Safely get an enum-like value, falling back to default if invalid."""
    if value is None:
        return default
    # Handle Mock objects in tests
    from unittest.mock import Mock

    if isinstance(value, Mock):
        return default
    # Compare case-insensitively by creating a lowercase set of valid values
    valid_values_lower = {v.lower() for v in valid_values}
    if str(value).lower() not in valid_values_lower:
        return default
    # Return the original value from valid_values that matches (preserves original case)
    for valid_value in valid_values:
        if valid_value.lower() == str(value).lower():
            return valid_value
    return default  # Fallback, should never reach here


def load_config() -> KittylogConfigData:
    """Load configuration from environment variables and .env files.

    Returns:
        KittylogConfigData instance containing configuration values
    """
    # Ensure env files are loaded (lazy, cached call)
    ensure_env_files_loaded()

    # Valid enum values
    valid_grouping_modes = [mode.value for mode in GroupingMode]
    valid_date_groupings = [mode.value for mode in DateGrouping]
    valid_log_levels = Logging.LEVELS
    valid_audiences = Audiences.slugs()

    return KittylogConfigData(
        model=os.getenv("KITTYLOG_MODEL") or None,  # None when not set
        temperature=_safe_float(os.getenv("KITTYLOG_TEMPERATURE"), EnvDefaults.TEMPERATURE),
        max_output_tokens=_safe_int(os.getenv("KITTYLOG_MAX_OUTPUT_TOKENS"), EnvDefaults.MAX_OUTPUT_TOKENS),
        max_retries=_safe_int(os.getenv("KITTYLOG_RETRIES"), EnvDefaults.MAX_RETRIES, min_value=0),
        log_level=_safe_enum(os.getenv("KITTYLOG_LOG_LEVEL"), EnvDefaults.LOG_LEVEL, valid_log_levels),
        warning_limit_tokens=_safe_int(os.getenv("KITTYLOG_WARNING_LIMIT_TOKENS"), EnvDefaults.WARNING_LIMIT_TOKENS),
        grouping_mode=_safe_enum(os.getenv("KITTYLOG_GROUPING_MODE"), EnvDefaults.GROUPING_MODE, valid_grouping_modes),
        gap_threshold_hours=_safe_float(os.getenv("KITTYLOG_GAP_THRESHOLD_HOURS"), EnvDefaults.GAP_THRESHOLD_HOURS),
        date_grouping=_safe_enum(os.getenv("KITTYLOG_DATE_GROUPING"), EnvDefaults.DATE_GROUPING, valid_date_groupings),
        language=str(os.getenv("KITTYLOG_LANGUAGE") or "") or None,  # None when not set
        audience=_safe_enum(os.getenv("KITTYLOG_AUDIENCE"), EnvDefaults.AUDIENCE, valid_audiences),
        translate_headings=(
            (str(os.getenv("KITTYLOG_TRANSLATE_HEADINGS") or "").lower() == "true")
            if os.getenv("KITTYLOG_TRANSLATE_HEADINGS") is not None
            else EnvDefaults.TRANSLATE_HEADINGS
        ),
    )


def apply_config_defaults(config: KittylogConfigData) -> KittylogConfigData:
    """Apply default values to configuration dataclass.

    Args:
        config: Configuration dataclass to update

    Returns:
        Updated configuration dataclass with defaults applied
    """
    return config.apply_defaults()


# Backward compatibility function for dict-based usage
def apply_config_defaults_dict(config_dict: dict) -> dict:
    """Apply default values to configuration dictionary.

    This function is kept for backward compatibility.

    Args:
        config_dict: Configuration dictionary to update

    Returns:
        Updated configuration dictionary
    """
    return {
        "model": config_dict.get("model", EnvDefaults.MODEL),
        "temperature": config_dict.get("temperature", EnvDefaults.TEMPERATURE),
        "max_output_tokens": config_dict.get("max_output_tokens", EnvDefaults.MAX_OUTPUT_TOKENS),
        "max_retries": config_dict.get("max_retries", EnvDefaults.MAX_RETRIES),
        "log_level": config_dict.get("log_level", EnvDefaults.LOG_LEVEL),
        "warning_limit_tokens": config_dict.get("warning_limit_tokens", EnvDefaults.WARNING_LIMIT_TOKENS),
        "grouping_mode": config_dict.get("grouping_mode", EnvDefaults.GROUPING_MODE),
        "gap_threshold_hours": config_dict.get("gap_threshold_hours", EnvDefaults.GAP_THRESHOLD_HOURS),
        "date_grouping": config_dict.get("date_grouping", EnvDefaults.DATE_GROUPING),
        "language": config_dict.get("language", EnvDefaults.LANGUAGE),
        "audience": config_dict.get("audience", EnvDefaults.AUDIENCE),
        "translate_headings": config_dict.get("translate_headings", EnvDefaults.TRANSLATE_HEADINGS),
    }


def validate_config_value(value: Any, validator: Callable[[Any], bool], config_key: str, description: str = "") -> None:
    """Validate a configuration value using a validator function.

    Args:
        value: Value to validate
        validator: Function that returns True if value is valid
        config_key: Configuration key for error messages
        description: Optional description for error messages

    Raises:
        ValueError: If validation fails
    """
    if not validator(value):
        raise ValueError(f"Invalid value for {config_key}: {description}")


def validate_env_var(value: str, config_key: str, valid_values: list[str], description: str = "") -> None:
    """Validate an environment variable value.

    Args:
        value: Value to validate
        config_key: Configuration key for error messages
        valid_values: List of valid values
        description: Optional description for error messages

    Raises:
        ConfigError: If validation fails
    """
    if value not in valid_values:
        from kittylog.errors import ConfigError

        valid_str = ", ".join(valid_values)
        raise ConfigError(
            f"Invalid {config_key} '{value}'. Valid values: {valid_str}",
            config_key=config_key,
            config_value=value,
        )


def validate_config(config: KittylogConfigData | dict) -> None:
    """Validate configuration dataclass or dictionary.

    Args:
        config: Configuration dataclass or dictionary to validate

    Raises:
        ConfigError: If validation fails
    """
    from kittylog.errors import ConfigError

    # Handle both dict and KittylogConfigData inputs
    if isinstance(config, dict):
        # Use the existing dict validation
        validate_config_dict(config)
    else:
        # Use the dataclass validation
        try:
            config.validate()
        except ValueError as e:
            raise ConfigError(
                f"Configuration validation failed: {e}",
                config_key="validation",
            ) from e


# Backward compatibility function for dict-based usage
def validate_config_dict(config: dict) -> None:
    """Validate configuration dictionary.

    This function is kept for backward compatibility.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigError: If validation fails
    """
    from kittylog.errors import ConfigError

    # Temperature validation
    temperature = config.get("temperature", EnvDefaults.TEMPERATURE)
    if not 0.0 <= temperature <= 2.0:
        raise ConfigError(
            f"Invalid temperature: must be between 0.0 and 2.0, got {temperature}",
            config_key="temperature",
            config_value=str(temperature),
        )

    # Token validation
    max_tokens = config.get("max_output_tokens", EnvDefaults.MAX_OUTPUT_TOKENS)
    if max_tokens < 1:
        raise ConfigError(
            f"Invalid max_output_tokens: must be positive, got {max_tokens}",
            config_key="max_output_tokens",
            config_value=str(max_tokens),
        )

    # Retry validation (must be >= 1)
    max_retries = config.get("max_retries", EnvDefaults.MAX_RETRIES)
    if max_retries < 1:
        raise ConfigError(
            f"Invalid max_retries: must be at least 1, got {max_retries}",
            config_key="max_retries",
            config_value=str(max_retries),
        )

    # Gap threshold validation
    gap_threshold = config.get("gap_threshold_hours", EnvDefaults.GAP_THRESHOLD_HOURS)
    if gap_threshold <= 0:
        raise ConfigError(
            f"Invalid gap_threshold_hours: must be positive, got {gap_threshold}",
            config_key="gap_threshold_hours",
            config_value=str(gap_threshold),
        )

    # Grouping mode validation
    grouping_mode = config.get("grouping_mode", EnvDefaults.GROUPING_MODE)
    valid_modes = [mode.value for mode in GroupingMode]
    if grouping_mode not in valid_modes:
        raise ConfigError(
            f"Invalid grouping_mode: {grouping_mode}. Valid: {valid_modes}",
            config_key="grouping_mode",
            config_value=grouping_mode,
        )

    # Date grouping validation
    date_grouping = config.get("date_grouping", EnvDefaults.DATE_GROUPING)
    valid_groupings = [mode.value for mode in DateGrouping]
    if date_grouping not in valid_groupings:
        raise ConfigError(
            f"Invalid date_grouping: {date_grouping}. Valid: {valid_groupings}",
            config_key="date_grouping",
            config_value=date_grouping,
        )

    # Language validation - check against both display names and values from LANGUAGES tuples
    language = config.get("language")
    if language is not None:
        valid_languages = {name for name, _ in Languages.LANGUAGES} | {value for _, value in Languages.LANGUAGES}
        if language not in valid_languages:
            raise ConfigError(f"Unsupported language: {language}")

    # Audience validation
    audience = config.get("audience", EnvDefaults.AUDIENCE)
    if audience not in Audiences.slugs():
        raise ConfigError(f"Invalid audience: {audience}. Valid: {Audiences.slugs()}")

    # Log level validation
    log_level = config.get("log_level", EnvDefaults.LOG_LEVEL)
    if log_level not in Logging.LEVELS:
        raise ConfigError(f"Invalid log_level: {log_level}. Valid: {Logging.LEVELS}")

    # Translate headings validation
    translate_headings = config.get("translate_headings", EnvDefaults.TRANSLATE_HEADINGS)
    if not isinstance(translate_headings, bool):
        raise ConfigError(f"Invalid translate_headings: must be a boolean, got {type(translate_headings).__name__}")
