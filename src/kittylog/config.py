"""Configuration loading for kittylog.

Handles environment variable and .env file precedence for application settings.
"""

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from dotenv import dotenv_values

from kittylog.constants import EnvDefaults, Logging
from kittylog.errors import ConfigError

T = TypeVar("T")


def _safe_float(value: str | None, default: float) -> float:
    """Safely convert a string to float, returning default on error."""
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _safe_int(value: str | None, default: int) -> int:
    """Safely convert a string to int, returning default on error."""
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def validate_env_var(
    env_value: str | None,
    converter: Callable[[str], T],
    validator: Callable[[T], bool],
    default: T,
    config_key: str,
    description: str = "",
) -> T:
    """Generic environment variable validation with consistent error handling.

    Args:
        env_value: Raw environment variable value (string or None)
        converter: Function to convert string to target type (e.g., float, int)
        validator: Function to validate converted value (returns True if valid)
        default: Default value to use if conversion or validation fails
        config_key: Configuration key name for error reporting
        description: Human-readable description for error messages

    Returns:
        Validated value or default if validation fails
    """
    if env_value is None:
        return default

    try:
        converted_value = converter(env_value)
    except (ValueError, TypeError):
        return default

    if not validator(converted_value):
        return default

    return converted_value


def validate_config_value(value: Any, validator: Callable[[Any], bool], config_key: str, description: str = "") -> None:
    """Validate a configuration value and raise ConfigError if invalid.

    Args:
        value: Value to validate
        validator: Function that returns True if value is valid
        config_key: Configuration key name for error reporting
        description: Human-readable description for error messages

    Raises:
        ConfigError: If validation fails
    """
    if value is not None and not validator(value):
        raise ConfigError(
            f"Invalid {config_key} value: {value}. {description}", config_key=config_key, config_value=value
        )


def load_config() -> dict[str, str | int | float | bool | None]:
    """Load configuration from $HOME/.kittylog.env, then ./.kittylog.env or ./.env, then environment variables."""

    # Load config files in order of precedence
    # Variables in later files will override earlier ones
    config_vars: dict[str, str | None] = {}

    # Load user config file (lowest precedence)
    user_config = Path.home() / ".kittylog.env"
    if user_config.exists():
        config_vars.update(dotenv_values(user_config))

    # Load project .env file (medium precedence)
    project_env = Path(".env")
    if project_env.exists():
        config_vars.update(dotenv_values(project_env))

    # Load project .kittylog.env file (highest precedence)
    project_config_env = Path(".kittylog.env")
    if project_config_env.exists():
        config_vars.update(dotenv_values(project_config_env))
    api_keys = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "CEREBRAS_API_KEY", "OLLAMA_HOST", "ZAI_API_KEY"]

    if user_config.exists():
        user_vars = dotenv_values(user_config)
        for key in api_keys:
            if key in user_vars:
                value = user_vars[key]
                if value is not None:
                    os.environ[key] = value

    if project_env.exists():
        project_vars = dotenv_values(project_env)
        for key in api_keys:
            if key in project_vars:
                value = project_vars[key]
                if value is not None:
                    os.environ[key] = value

    if project_config_env.exists():
        project_config_vars = dotenv_values(project_config_env)
        for key in api_keys:
            if key in project_config_vars:
                value = project_config_vars[key]
                if value is not None:
                    os.environ[key] = value

    # Build config dictionary with proper precedence enforcement
    # Environment variables take precedence over file variables
    # But we must differentiate between invalid environment variables vs. invalid file variables
    config: dict[str, str | int | float | bool | None] = {}

    # Read environment variables (these have highest precedence)
    env_model = os.getenv("KITTYLOG_MODEL")
    env_temperature = os.getenv("KITTYLOG_TEMPERATURE")
    env_max_output_tokens = os.getenv("KITTYLOG_MAX_OUTPUT_TOKENS")
    env_max_retries = os.getenv("KITTYLOG_RETRIES")
    env_log_level = os.getenv("KITTYLOG_LOG_LEVEL")
    env_warning_limit_tokens = os.getenv("KITTYLOG_WARNING_LIMIT_TOKENS")
    env_grouping_mode = os.getenv("KITTYLOG_GROUPING_MODE")
    env_gap_threshold_hours = os.getenv("KITTYLOG_GAP_THRESHOLD_HOURS")
    env_date_grouping = os.getenv("KITTYLOG_DATE_GROUPING")

    # Apply validated environment variables with defaults for invalid values
    config["model"] = env_model
    config["temperature"] = (
        validate_env_var(
            env_temperature,
            float,
            lambda x: 0 <= x <= 2,
            EnvDefaults.TEMPERATURE,
            "temperature",
            "Must be between 0 and 2",
        )
        if env_temperature is not None
        else None
    )

    config["max_output_tokens"] = (
        validate_env_var(
            env_max_output_tokens,
            int,
            lambda x: x > 0,
            EnvDefaults.MAX_OUTPUT_TOKENS,
            "max_output_tokens",
            "Must be positive",
        )
        if env_max_output_tokens is not None
        else None
    )

    config["max_retries"] = (
        validate_env_var(
            env_max_retries, int, lambda x: x > 0, EnvDefaults.MAX_RETRIES, "max_retries", "Must be positive"
        )
        if env_max_retries is not None
        else None
    )

    config["log_level"] = env_log_level
    config["warning_limit_tokens"] = (
        validate_env_var(
            env_warning_limit_tokens,
            int,
            lambda x: x > 0,
            EnvDefaults.WARNING_LIMIT_TOKENS,
            "warning_limit_tokens",
            "Must be positive",
        )
        if env_warning_limit_tokens is not None
        else None
    )

    # New environment variables for boundary detection
    config["grouping_mode"] = (
        validate_env_var(
            env_grouping_mode,
            str,
            lambda x: x in ["tags", "dates", "gaps"],
            EnvDefaults.GROUPING_MODE,
            "grouping_mode",
            "Must be one of 'tags', 'dates', or 'gaps'",
        )
        if env_grouping_mode is not None
        else None
    )

    config["gap_threshold_hours"] = (
        validate_env_var(
            env_gap_threshold_hours,
            float,
            lambda x: x > 0,
            EnvDefaults.GAP_THRESHOLD_HOURS,
            "gap_threshold_hours",
            "Must be positive",
        )
        if env_gap_threshold_hours is not None
        else None
    )

    config["date_grouping"] = (
        validate_env_var(
            env_date_grouping,
            str,
            lambda x: x in ["daily", "weekly", "monthly"],
            EnvDefaults.DATE_GROUPING,
            "date_grouping",
            "Must be one of 'daily', 'weekly', or 'monthly'",
        )
        if env_date_grouping is not None
        else None
    )

    # Apply file values as fallbacks (only if env vars weren't set or were None)
    # For file variables, convert them normally so validate_config can catch errors
    if config["model"] is None:
        config["model"] = config_vars.get("KITTYLOG_MODEL")

    if config["temperature"] is None:
        config_temperature_str = config_vars.get("KITTYLOG_TEMPERATURE")
        config["temperature"] = _safe_float(config_temperature_str, EnvDefaults.TEMPERATURE) or EnvDefaults.TEMPERATURE

    if config["max_output_tokens"] is None:
        config_max_output_tokens_str = config_vars.get("KITTYLOG_MAX_OUTPUT_TOKENS")
        config["max_output_tokens"] = (
            _safe_int(config_max_output_tokens_str, EnvDefaults.MAX_OUTPUT_TOKENS) or EnvDefaults.MAX_OUTPUT_TOKENS
        )

    if config["max_retries"] is None:
        config_max_retries_str = config_vars.get("KITTYLOG_RETRIES")
        config["max_retries"] = _safe_int(config_max_retries_str, EnvDefaults.MAX_RETRIES) or EnvDefaults.MAX_RETRIES

    if config["log_level"] is None:
        config["log_level"] = config_vars.get("KITTYLOG_LOG_LEVEL") or Logging.DEFAULT_LEVEL

    if config["warning_limit_tokens"] is None:
        config_warning_limit_tokens_str = config_vars.get("KITTYLOG_WARNING_LIMIT_TOKENS")
        config["warning_limit_tokens"] = (
            _safe_int(config_warning_limit_tokens_str, EnvDefaults.WARNING_LIMIT_TOKENS)
            or EnvDefaults.WARNING_LIMIT_TOKENS
        )

    # Apply file values for new environment variables
    if config["grouping_mode"] is None:
        config["grouping_mode"] = config_vars.get("KITTYLOG_GROUPING_MODE") or EnvDefaults.GROUPING_MODE

    if config["gap_threshold_hours"] is None:
        gap_threshold_str = config_vars.get("KITTYLOG_GAP_THRESHOLD_HOURS")
        config["gap_threshold_hours"] = (
            _safe_float(gap_threshold_str, EnvDefaults.GAP_THRESHOLD_HOURS) or EnvDefaults.GAP_THRESHOLD_HOURS
        )

    if config["date_grouping"] is None:
        config["date_grouping"] = config_vars.get("KITTYLOG_DATE_GROUPING") or EnvDefaults.DATE_GROUPING

    return config


def validate_config(config: dict) -> None:
    """Validate configuration values and raise ConfigError for invalid values.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigError: If any configuration values are invalid
    """
    validate_config_value(config.get("temperature"), lambda x: 0 <= x <= 2, "temperature", "Must be between 0 and 2")

    validate_config_value(config.get("max_output_tokens"), lambda x: x > 0, "max_output_tokens", "Must be positive")

    validate_config_value(config.get("max_retries"), lambda x: x > 0, "max_retries", "Must be positive")

    validate_config_value(
        config.get("log_level"), lambda x: x in Logging.LEVELS, "log_level", f"Must be one of {Logging.LEVELS}"
    )

    # Validate new configuration values for boundary detection
    validate_config_value(
        config.get("grouping_mode"),
        lambda x: x in ["tags", "dates", "gaps"],
        "grouping_mode",
        "Must be one of 'tags', 'dates', or 'gaps'",
    )

    validate_config_value(
        config.get("gap_threshold_hours"),
        lambda x: x > 0,
        "gap_threshold_hours",
        "Must be positive",
    )

    validate_config_value(
        config.get("date_grouping"),
        lambda x: x in ["daily", "weekly", "monthly"],
        "date_grouping",
        "Must be one of 'daily', 'weekly', or 'monthly'",
    )


def apply_config_defaults(config: dict) -> dict:
    """Apply default values for invalid configuration entries.

    Args:
        config: Configuration dictionary to validate and apply defaults to

    Returns:
        dict: Configuration with defaults applied for invalid values
    """
    validated_config = config.copy()

    def apply_default_if_invalid(key: str, validator: Callable[[Any], bool], default: Any) -> None:
        """Apply default value if the config value is invalid."""
        value = config.get(key)
        if value is not None and not validator(value):
            validated_config[key] = default

    apply_default_if_invalid("temperature", lambda x: 0 <= x <= 2, EnvDefaults.TEMPERATURE)
    apply_default_if_invalid("max_output_tokens", lambda x: x > 0, EnvDefaults.MAX_OUTPUT_TOKENS)
    apply_default_if_invalid("max_retries", lambda x: x > 0, EnvDefaults.MAX_RETRIES)
    apply_default_if_invalid("log_level", lambda x: x in Logging.LEVELS, Logging.DEFAULT_LEVEL)

    # Apply defaults for new configuration values
    apply_default_if_invalid("grouping_mode", lambda x: x in ["tags", "dates", "gaps"], EnvDefaults.GROUPING_MODE)
    apply_default_if_invalid("gap_threshold_hours", lambda x: x > 0, EnvDefaults.GAP_THRESHOLD_HOURS)
    apply_default_if_invalid("date_grouping", lambda x: x in ["daily", "weekly", "monthly"], EnvDefaults.DATE_GROUPING)

    return validated_config
