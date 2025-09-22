"""Configuration loading for clog.

Handles environment variable and .env file precedence for application settings.
"""

import os
from pathlib import Path

from dotenv import dotenv_values

from clog.constants import EnvDefaults, Logging
from clog.errors import ConfigError


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


def load_config() -> dict[str, str | int | float | bool | None]:
    """Load configuration from $HOME/.clog.env, then ./.clog.env or ./.env, then environment variables."""

    # Load config files in order of precedence
    # Variables in later files will override earlier ones
    config_vars: dict[str, str | None] = {}

    # Load user config file (lowest precedence)
    user_config = Path.home() / ".clog.env"
    if user_config.exists():
        config_vars.update(dotenv_values(user_config))

    # Load project .env file (medium precedence)
    project_env = Path(".env")
    if project_env.exists():
        config_vars.update(dotenv_values(project_env))

    # Load project .clog.env file (highest precedence)
    project_config_env = Path(".clog.env")
    if project_config_env.exists():
        config_vars.update(dotenv_values(project_config_env))
    api_keys = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "OLLAMA_HOST"]

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
    env_model = os.getenv("CLOG_MODEL") or os.getenv("CHANGELOG_UPDATER_MODEL")
    env_temperature = os.getenv("CLOG_TEMPERATURE") or os.getenv("CHANGELOG_UPDATER_TEMPERATURE")
    env_max_output_tokens = os.getenv("CLOG_MAX_OUTPUT_TOKENS") or os.getenv("CHANGELOG_UPDATER_MAX_OUTPUT_TOKENS")
    env_max_retries = os.getenv("CLOG_RETRIES") or os.getenv("CHANGELOG_UPDATER_RETRIES")
    env_log_level = os.getenv("CLOG_LOG_LEVEL") or os.getenv("CHANGELOG_UPDATER_LOG_LEVEL")
    env_warning_limit_tokens = os.getenv("CLOG_WARNING_LIMIT_TOKENS") or os.getenv(
        "CHANGELOG_UPDATER_WARNING_LIMIT_TOKENS"
    )
    env_replace_unreleased = os.getenv("CLOG_REPLACE_UNRELEASED") or os.getenv("CHANGELOG_UPDATER_REPLACE_UNRELEASED")

    # Apply safe conversion to environment variables WITHOUT defaults
    # For environment variables, we delay applying defaults so validate_config can catch invalid values
    config["model"] = env_model
    config["temperature"] = (
        _safe_float(env_temperature, EnvDefaults.TEMPERATURE) if env_temperature is not None else None
    )
    config["max_output_tokens"] = (
        _safe_int(env_max_output_tokens, EnvDefaults.MAX_OUTPUT_TOKENS) if env_max_output_tokens is not None else None
    )
    config["max_retries"] = _safe_int(env_max_retries, EnvDefaults.MAX_RETRIES) if env_max_retries is not None else None
    config["log_level"] = env_log_level
    config["warning_limit_tokens"] = (
        _safe_int(env_warning_limit_tokens, EnvDefaults.WARNING_LIMIT_TOKENS)
        if env_warning_limit_tokens is not None
        else None
    )
    # Convert replace_unreleased to boolean
    if env_replace_unreleased is not None:
        config["replace_unreleased"] = env_replace_unreleased.lower() in ("true", "1", "yes", "on")
    else:
        config["replace_unreleased"] = None

    # Apply stricter validation only to INVALID environment variables
    # For environment variables, we want to apply defaults for both syntactic and semantic errors
    if env_temperature is not None:
        # Try to convert environment variable
        try:
            converted_temp = float(env_temperature)
        except ValueError:
            converted_temp = None
        # If conversion failed OR value is semantically invalid, apply default
        if converted_temp is None or converted_temp < 0 or converted_temp > 2:
            config["temperature"] = EnvDefaults.TEMPERATURE

    # Max output tokens should be positive
    if env_max_output_tokens is not None:
        try:
            converted_tokens = int(env_max_output_tokens)
        except ValueError:
            converted_tokens = None
        # If conversion failed OR value is semantically invalid, apply default
        if converted_tokens is None or converted_tokens <= 0:
            config["max_output_tokens"] = EnvDefaults.MAX_OUTPUT_TOKENS

    # Max retries should be positive
    if env_max_retries is not None:
        try:
            converted_retries = int(env_max_retries)
        except ValueError:
            converted_retries = None
        # If conversion failed OR value is semantically invalid, apply default
        if converted_retries is None or converted_retries <= 0:
            config["max_retries"] = EnvDefaults.MAX_RETRIES

    # Warning limit tokens should be positive
    if env_warning_limit_tokens is not None:
        try:
            converted_warning_tokens = int(env_warning_limit_tokens)
        except ValueError:
            converted_warning_tokens = None
        # If conversion failed OR value is semantically invalid, apply default
        if converted_warning_tokens is None or converted_warning_tokens <= 0:
            config["warning_limit_tokens"] = EnvDefaults.WARNING_LIMIT_TOKENS

    # Apply file values as fallbacks (only if env vars weren't set or were None)
    # For file variables, convert them normally so validate_config can catch errors
    if config["model"] is None:
        config["model"] = config_vars.get("CLOG_MODEL") or config_vars.get("CHANGELOG_UPDATER_MODEL")

    if config["temperature"] is None:
        config_temperature_str = config_vars.get("CLOG_TEMPERATURE") or config_vars.get("CHANGELOG_UPDATER_TEMPERATURE")
        config["temperature"] = _safe_float(config_temperature_str, EnvDefaults.TEMPERATURE) or EnvDefaults.TEMPERATURE

    if config["max_output_tokens"] is None:
        config_max_output_tokens_str = config_vars.get("CLOG_MAX_OUTPUT_TOKENS") or config_vars.get(
            "CHANGELOG_UPDATER_MAX_OUTPUT_TOKENS"
        )
        config["max_output_tokens"] = (
            _safe_int(config_max_output_tokens_str, EnvDefaults.MAX_OUTPUT_TOKENS) or EnvDefaults.MAX_OUTPUT_TOKENS
        )

    if config["max_retries"] is None:
        config_max_retries_str = config_vars.get("CLOG_RETRIES") or config_vars.get("CHANGELOG_UPDATER_RETRIES")
        config["max_retries"] = _safe_int(config_max_retries_str, EnvDefaults.MAX_RETRIES) or EnvDefaults.MAX_RETRIES

    if config["log_level"] is None:
        config["log_level"] = (
            config_vars.get("CLOG_LOG_LEVEL") or config_vars.get("CHANGELOG_UPDATER_LOG_LEVEL") or Logging.DEFAULT_LEVEL
        )

    if config["warning_limit_tokens"] is None:
        config_warning_limit_tokens_str = config_vars.get("CLOG_WARNING_LIMIT_TOKENS") or config_vars.get(
            "CHANGELOG_UPDATER_WARNING_LIMIT_TOKENS"
        )
        config["warning_limit_tokens"] = (
            _safe_int(config_warning_limit_tokens_str, EnvDefaults.WARNING_LIMIT_TOKENS)
            or EnvDefaults.WARNING_LIMIT_TOKENS
        )

    # Apply file values as fallbacks for replace_unreleased (only if env vars weren't set or were None)
    if config["replace_unreleased"] is None:
        config_replace_unreleased_str = config_vars.get("CLOG_REPLACE_UNRELEASED") or config_vars.get("CHANGELOG_UPDATER_REPLACE_UNRELEASED")
        if config_replace_unreleased_str is not None:
            config["replace_unreleased"] = config_replace_unreleased_str.lower() in ("true", "1", "yes", "on")
        else:
            config["replace_unreleased"] = False

    return config


def validate_config(config: dict) -> None:
    """Validate configuration values and raise ConfigError for invalid values.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigError: If any configuration values are invalid
    """
    # Validate temperature (should be between 0 and 2)
    temp = config.get("temperature")
    if temp is not None and (temp < 0 or temp > 2):
        raise ConfigError(
            f"Invalid temperature value: {temp}. Must be between 0 and 2.", config_key="temperature", config_value=temp
        )

    # Validate max_output_tokens (should be positive)
    max_tokens = config.get("max_output_tokens")
    if max_tokens is not None and max_tokens <= 0:
        raise ConfigError(
            f"Invalid max_output_tokens value: {max_tokens}. Must be positive.",
            config_key="max_output_tokens",
            config_value=max_tokens,
        )

    # Validate max_retries (should be positive)
    retries = config.get("max_retries")
    if retries is not None and retries <= 0:
        raise ConfigError(
            f"Invalid max_retries value: {retries}. Must be positive.", config_key="max_retries", config_value=retries
        )

    # Validate log_level (should be valid)
    log_level = config.get("log_level")
    if log_level is not None and log_level not in Logging.LEVELS:
        raise ConfigError(
            f"Invalid log_level value: {log_level}. Must be one of {Logging.LEVELS}.",
            config_key="log_level",
            config_value=log_level,
        )


def apply_config_defaults(config: dict) -> dict:
    """Apply default values for invalid configuration entries.

    Args:
        config: Configuration dictionary to validate and apply defaults to

    Returns:
        dict: Configuration with defaults applied for invalid values
    """
    validated_config = config.copy()

    # Validate temperature (should be between 0 and 2)
    temp = config.get("temperature")
    if temp is not None and (temp < 0 or temp > 2):
        validated_config["temperature"] = EnvDefaults.TEMPERATURE

    # Validate max_output_tokens (should be positive)
    max_tokens = config.get("max_output_tokens")
    if max_tokens is not None and max_tokens <= 0:
        validated_config["max_output_tokens"] = EnvDefaults.MAX_OUTPUT_TOKENS

    # Validate max_retries (should be positive)
    retries = config.get("max_retries")
    if retries is not None and retries <= 0:
        validated_config["max_retries"] = EnvDefaults.MAX_RETRIES

    # Validate log_level (should be valid)
    log_level = config.get("log_level")
    if log_level is not None and log_level not in Logging.LEVELS:
        validated_config["log_level"] = Logging.DEFAULT_LEVEL

    # For replace_unreleased, ensure it's a boolean
    replace_unreleased = config.get("replace_unreleased")
    if replace_unreleased is not None and not isinstance(replace_unreleased, bool):
        validated_config["replace_unreleased"] = False

    return validated_config
