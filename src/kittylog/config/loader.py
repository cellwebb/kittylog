"""Configuration loading utilities for kittylog.

Handles environment variable and .env file precedence for application settings.
Configuration precedence (highest to lowest):
1. Environment variables
2. Project .kittylog.env
3. Project .env
4. User ~/.kittylog.env
5. Default values
"""

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from dotenv import load_dotenv

from kittylog.constants import Audiences, DateGrouping, EnvDefaults, GroupingMode, Languages, Logging

T = TypeVar("T")


def _load_env_files() -> None:
    """Load environment variables from .env files into os.environ.

    Files are loaded in order of priority (lowest to highest):
    1. User ~/.kittylog.env
    2. Project .env
    3. Project .kittylog.env

    Environment variables already set take highest priority.
    """
    user_config = Path.home() / ".kittylog.env"
    project_env = Path(".env")
    project_config_env = Path(".kittylog.env")

    # Load in order - load_dotenv with override=False respects existing env vars
    # Later files override earlier ones when override=True
    if user_config.exists():
        load_dotenv(user_config, override=False)

    if project_env.exists():
        load_dotenv(project_env, override=True)

    if project_config_env.exists():
        load_dotenv(project_config_env, override=True)


# Load env files at module import time so API keys are available
_load_env_files()


def _safe_float(value: str | None, default: float) -> float:
    """Safely convert a string to float with default."""
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
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
        result = int(value)
        if min_value is not None and result < min_value:
            return default
        return result
    except ValueError:
        return default


def _safe_enum(value: str | None, default: str, valid_values: list[str]) -> str:
    """Safely get an enum-like value, falling back to default if invalid."""
    if value is None:
        return default
    # Compare case-insensitively by creating a lowercase set of valid values
    valid_values_lower = {v.lower() for v in valid_values}
    if value.lower() not in valid_values_lower:
        return default
    # Return the original value from valid_values that matches (preserves original case)
    for valid_value in valid_values:
        if valid_value.lower() == value.lower():
            return valid_value
    return default  # Fallback, should never reach here


def load_config() -> dict:
    """Load configuration from environment variables and .env files.

    Returns:
        Dictionary containing configuration values
    """
    # Ensure env files are loaded (idempotent call)
    _load_env_files()

    # Valid enum values
    valid_grouping_modes = [mode.value for mode in GroupingMode]
    valid_date_groupings = [mode.value for mode in DateGrouping]
    valid_log_levels = Logging.LEVELS
    valid_audiences = Audiences.slugs()

    return {
        "model": os.getenv("KITTYLOG_MODEL") or None,  # None when not set
        "temperature": _safe_float(os.getenv("KITTYLOG_TEMPERATURE"), EnvDefaults.TEMPERATURE),
        "max_output_tokens": _safe_int(os.getenv("KITTYLOG_MAX_OUTPUT_TOKENS"), EnvDefaults.MAX_OUTPUT_TOKENS),
        "max_retries": _safe_int(os.getenv("KITTYLOG_RETRIES"), EnvDefaults.MAX_RETRIES, min_value=0),
        "log_level": _safe_enum(os.getenv("KITTYLOG_LOG_LEVEL"), EnvDefaults.LOG_LEVEL, valid_log_levels),
        "warning_limit_tokens": _safe_int(
            os.getenv("KITTYLOG_WARNING_LIMIT_TOKENS"), EnvDefaults.WARNING_LIMIT_TOKENS
        ),
        "grouping_mode": _safe_enum(
            os.getenv("KITTYLOG_GROUPING_MODE"), EnvDefaults.GROUPING_MODE, valid_grouping_modes
        ),
        "gap_threshold_hours": _safe_float(
            os.getenv("KITTYLOG_GAP_THRESHOLD_HOURS"), EnvDefaults.GAP_THRESHOLD_HOURS
        ),
        "date_grouping": _safe_enum(
            os.getenv("KITTYLOG_DATE_GROUPING"), EnvDefaults.DATE_GROUPING, valid_date_groupings
        ),
        "language": os.getenv("KITTYLOG_LANGUAGE") or None,  # None when not set
        "audience": _safe_enum(os.getenv("KITTYLOG_AUDIENCE"), EnvDefaults.AUDIENCE, valid_audiences),
        "translate_headings": (
            (os.getenv("KITTYLOG_TRANSLATE_HEADINGS") or "").lower() == "true"
            if os.getenv("KITTYLOG_TRANSLATE_HEADINGS") is not None
            else EnvDefaults.TRANSLATE_HEADINGS
        ),
    }


def apply_config_defaults(config: dict) -> dict:
    """Apply default values to configuration dictionary.

    Args:
        config: Configuration dictionary to update

    Returns:
        Updated configuration dictionary
    """
    return {
        "model": config.get("model", EnvDefaults.MODEL),
        "temperature": config.get("temperature", EnvDefaults.TEMPERATURE),
        "max_output_tokens": config.get("max_output_tokens", EnvDefaults.MAX_OUTPUT_TOKENS),
        "max_retries": config.get("max_retries", EnvDefaults.MAX_RETRIES),
        "log_level": config.get("log_level", EnvDefaults.LOG_LEVEL),
        "warning_limit_tokens": config.get("warning_limit_tokens", EnvDefaults.WARNING_LIMIT_TOKENS),
        "grouping_mode": config.get("grouping_mode", EnvDefaults.GROUPING_MODE),
        "gap_threshold_hours": config.get("gap_threshold_hours", EnvDefaults.GAP_THRESHOLD_HOURS),
        "date_grouping": config.get("date_grouping", EnvDefaults.DATE_GROUPING),
        "language": config.get("language", EnvDefaults.LANGUAGE),
        "audience": config.get("audience", EnvDefaults.AUDIENCE),
        "translate_headings": config.get("translate_headings", EnvDefaults.TRANSLATE_HEADINGS),
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
        raise ConfigError(f"Invalid {config_key} '{value}'. Valid values: {valid_str}")


def validate_config(config: dict) -> None:
    """Validate configuration dictionary.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigError: If validation fails
    """
    from kittylog.errors import ConfigError

    # Temperature validation
    temperature = config.get("temperature", EnvDefaults.TEMPERATURE)
    if not 0.0 <= temperature <= 2.0:
        raise ConfigError(f"Invalid temperature: must be between 0.0 and 2.0, got {temperature}")

    # Token validation
    max_tokens = config.get("max_output_tokens", EnvDefaults.MAX_OUTPUT_TOKENS)
    if max_tokens < 1:
        raise ConfigError(f"Invalid max_output_tokens: must be positive, got {max_tokens}")

    # Retry validation (must be >= 1)
    max_retries = config.get("max_retries", EnvDefaults.MAX_RETRIES)
    if max_retries < 1:
        raise ConfigError(f"Invalid max_retries: must be at least 1, got {max_retries}")

    # Gap threshold validation
    gap_threshold = config.get("gap_threshold_hours", EnvDefaults.GAP_THRESHOLD_HOURS)
    if gap_threshold <= 0:
        raise ConfigError(f"Invalid gap_threshold_hours: must be positive, got {gap_threshold}")

    # Grouping mode validation
    grouping_mode = config.get("grouping_mode", EnvDefaults.GROUPING_MODE)
    valid_modes = [mode.value for mode in GroupingMode]
    if grouping_mode not in valid_modes:
        raise ConfigError(f"Invalid grouping_mode: {grouping_mode}. Valid: {valid_modes}")

    # Date grouping validation
    date_grouping = config.get("date_grouping", EnvDefaults.DATE_GROUPING)
    valid_groupings = [mode.value for mode in DateGrouping]
    if date_grouping not in valid_groupings:
        raise ConfigError(f"Invalid date_grouping: {date_grouping}. Valid: {valid_groupings}")

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
