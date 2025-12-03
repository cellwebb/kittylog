"""Configuration loading for kittylog.

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
from typing import Any, TypedDict, TypeVar

from dotenv import dotenv_values

from kittylog.constants import Audiences, EnvDefaults, Logging
from kittylog.errors import ConfigError

T = TypeVar("T")


class KittylogConfig(TypedDict, total=False):
    """Type definition for kittylog configuration.

    All fields are optional (total=False) since they may be None
    before defaults are applied.
    """

    model: str | None
    temperature: float | None
    max_output_tokens: int | None
    max_retries: int | None
    log_level: str | None
    warning_limit_tokens: int | None
    grouping_mode: str | None
    gap_threshold_hours: float | None
    date_grouping: str | None
    language: str | None
    audience: str | None
    translate_headings: bool | None


# API keys that should be exported to environment
API_KEYS = [
    "ANTHROPIC_API_KEY",
    "CEREBRAS_API_KEY",
    "CHUTES_API_KEY",
    "CHUTES_BASE_URL",
    "CLAUDE_CODE_ACCESS_TOKEN",
    "CUSTOM_ANTHROPIC_API_KEY",
    "CUSTOM_ANTHROPIC_BASE_URL",
    "CUSTOM_ANTHROPIC_VERSION",
    "CUSTOM_OPENAI_API_KEY",
    "CUSTOM_OPENAI_BASE_URL",
    "DEEPSEEK_API_KEY",
    "FIREWORKS_API_KEY",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "LMSTUDIO_API_KEY",
    "LMSTUDIO_API_URL",
    "MINIMAX_API_KEY",
    "MISTRAL_API_KEY",
    "OLLAMA_API_URL",
    "OLLAMA_HOST",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "STREAMLAKE_API_KEY",
    "SYNTHETIC_API_KEY",
    "SYN_API_KEY",
    "TOGETHER_API_KEY",
    "VC_API_KEY",
    "ZAI_API_KEY",
]


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


def _export_api_keys_from_file(file_path: Path) -> None:
    """Export API keys from a .env file to environment, without overwriting existing values.

    Args:
        file_path: Path to the .env file to read from
    """
    if not file_path.exists():
        return

    file_vars = dotenv_values(file_path)
    for key in API_KEYS:
        if key in file_vars and key not in os.environ:
            value = file_vars[key]
            if value is not None:
                os.environ[key] = value


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


def load_config() -> KittylogConfig:
    """Load configuration from environment and .env files.

    Precedence (highest to lowest):
    1. Environment variables
    2. Project .kittylog.env
    3. Project .env
    4. User ~/.kittylog.env
    5. Default values

    Returns:
        KittylogConfig dictionary with all configuration values
    """
    # Define config file paths
    user_config = Path.home() / ".kittylog.env"
    project_env = Path(".env")
    project_config_env = Path(".kittylog.env")

    # Load config files in order of precedence (later files override earlier)
    config_vars: dict[str, str | None] = {}
    if user_config.exists():
        config_vars.update(dotenv_values(user_config))
    if project_env.exists():
        config_vars.update(dotenv_values(project_env))
    if project_config_env.exists():
        config_vars.update(dotenv_values(project_config_env))

    # Export API keys to environment (respecting existing env vars)
    _export_api_keys_from_file(user_config)
    _export_api_keys_from_file(project_env)
    _export_api_keys_from_file(project_config_env)

    # Build config dictionary with proper precedence enforcement
    # Environment variables take precedence over file variables
    # But we must differentiate between invalid environment variables vs. invalid file variables
    config: KittylogConfig = {}

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
    env_audience = os.getenv("KITTYLOG_AUDIENCE")
    env_language = os.getenv("KITTYLOG_LANGUAGE")
    env_translate_headings = os.getenv("KITTYLOG_TRANSLATE_HEADINGS")

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

    config["language"] = env_language
    config["audience"] = Audiences.resolve(env_audience) if env_audience is not None else None
    config["translate_headings"] = (
        env_translate_headings.lower() in ("true", "1", "yes", "on") if env_translate_headings is not None else None
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

    if config["language"] is None:
        config["language"] = config_vars.get("KITTYLOG_LANGUAGE")

    if config["audience"] is None:
        audience_value = config_vars.get("KITTYLOG_AUDIENCE")
        config["audience"] = Audiences.resolve(audience_value) if audience_value is not None else EnvDefaults.AUDIENCE
    else:
        # Ensure env-derived audience is normalized
        config["audience"] = Audiences.resolve(str(config["audience"]))

    if config["translate_headings"] is None:
        translate_headings_value = config_vars.get("KITTYLOG_TRANSLATE_HEADINGS")
        if translate_headings_value is not None:
            config["translate_headings"] = translate_headings_value.lower() in ("true", "1", "yes", "on")
        else:
            config["translate_headings"] = EnvDefaults.TRANSLATE_HEADINGS

    return config


def validate_config(config: KittylogConfig) -> None:
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

    validate_config_value(
        config.get("translate_headings"),
        lambda x: isinstance(x, bool),
        "translate_headings",
        "Must be a boolean value",
    )

    validate_config_value(
        config.get("audience"),
        lambda x: x in Audiences.slugs(),
        "audience",
        f"Must be one of {Audiences.slugs()}",
    )


def apply_config_defaults(config: KittylogConfig) -> KittylogConfig:
    """Apply default values for invalid configuration entries.

    Args:
        config: Configuration dictionary to validate and apply defaults to

    Returns:
        dict: Configuration with defaults applied for invalid values
    """
    validated_config = config.copy()

    # Apply temperature defaults
    temperature = config.get("temperature")
    if temperature is not None and not (0 <= temperature <= 2):
        validated_config["temperature"] = EnvDefaults.TEMPERATURE

    # Apply max_output_tokens defaults
    max_output_tokens = config.get("max_output_tokens")
    if max_output_tokens is not None and not (max_output_tokens > 0):
        validated_config["max_output_tokens"] = EnvDefaults.MAX_OUTPUT_TOKENS

    # Apply max_retries defaults
    max_retries = config.get("max_retries")
    if max_retries is not None and not (max_retries > 0):
        validated_config["max_retries"] = EnvDefaults.MAX_RETRIES

    # Apply log_level defaults
    log_level = config.get("log_level")
    if log_level is not None and log_level not in Logging.LEVELS:
        validated_config["log_level"] = Logging.DEFAULT_LEVEL

    # Apply grouping_mode defaults
    grouping_mode = config.get("grouping_mode")
    if grouping_mode is not None and grouping_mode not in ["tags", "dates", "gaps"]:
        validated_config["grouping_mode"] = EnvDefaults.GROUPING_MODE

    # Apply gap_threshold_hours defaults
    gap_threshold_hours = config.get("gap_threshold_hours")
    if gap_threshold_hours is not None and not (gap_threshold_hours > 0):
        validated_config["gap_threshold_hours"] = EnvDefaults.GAP_THRESHOLD_HOURS

    # Apply date_grouping defaults
    date_grouping = config.get("date_grouping")
    if date_grouping is not None and date_grouping not in ["daily", "weekly", "monthly"]:
        validated_config["date_grouping"] = EnvDefaults.DATE_GROUPING

    # Apply translate_headings defaults
    translate_headings = config.get("translate_headings")
    if translate_headings is not None and not isinstance(translate_headings, bool):
        validated_config["translate_headings"] = EnvDefaults.TRANSLATE_HEADINGS

    # Apply audience defaults
    audience = config.get("audience")
    if audience is not None and audience not in Audiences.slugs():
        validated_config["audience"] = Audiences.resolve(EnvDefaults.AUDIENCE)

    return validated_config
