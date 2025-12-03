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
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

from dotenv import dotenv_values

from kittylog.constants import Audiences, DateGrouping, EnvDefaults, GroupingMode, Languages, Logging
from kittylog.errors import ConfigError

T = TypeVar("T")


def _get_env_vars() -> dict[str, str | None]:
    """Get environment variables from .env files and os.environ."""
    # Start with actual environment variables (highest priority)
    env_vars: dict[str, str | None] = dict(os.environ)

    # Load config files (lower priority, will be overridden by env vars)
    user_config = Path.home() / ".kittylog.env"
    project_env = Path(".env")
    project_config_env = Path(".kittylog.env")

    # Load in order (later ones override earlier, but env vars still win)
    for config_file in [user_config, project_env, project_config_env]:
        if config_file.exists():
            file_vars = dotenv_values(config_file)
            # Only set if not already in os.environ
            env_vars.update({k: v for k, v in file_vars.items() if k not in os.environ})

    return env_vars


@dataclass
class KittylogConfigData:
    """Centralized configuration with validation.

    This dataclass replaces the TypedDict with proper validation
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

    @classmethod
    def from_env(cls) -> "KittylogConfigData":
        """Create configuration from environment variables."""
        env_vars = _get_env_vars()
        return cls(
            model=env_vars.get("KITTYLOG_MODEL") or EnvDefaults.MODEL,
            temperature=_safe_float(env_vars.get("KITTYLOG_TEMPERATURE"), EnvDefaults.TEMPERATURE),
            max_output_tokens=_safe_int(env_vars.get("KITTYLOG_MAX_OUTPUT_TOKENS"), EnvDefaults.MAX_OUTPUT_TOKENS),
            max_retries=_safe_int(env_vars.get("KITTYLOG_RETRIES"), EnvDefaults.MAX_RETRIES),
            log_level=env_vars.get("KITTYLOG_LOG_LEVEL") or EnvDefaults.LOG_LEVEL,
            warning_limit_tokens=_safe_int(
                env_vars.get("KITTYLOG_WARNING_LIMIT_TOKENS"), EnvDefaults.WARNING_LIMIT_TOKENS
            ),
            grouping_mode=env_vars.get("KITTYLOG_GROUPING_MODE") or EnvDefaults.GROUPING_MODE,
            gap_threshold_hours=_safe_float(
                env_vars.get("KITTYLOG_GAP_THRESHOLD_HOURS"), EnvDefaults.GAP_THRESHOLD_HOURS
            ),
            date_grouping=env_vars.get("KITTYLOG_DATE_GROUPING") or EnvDefaults.DATE_GROUPING,
            language=env_vars.get("KITTYLOG_LANGUAGE") or EnvDefaults.LANGUAGE,
            audience=env_vars.get("KITTYLOG_AUDIENCE") or EnvDefaults.AUDIENCE,
            translate_headings=(
                env_vars.get("KITTYLOG_TRANSLATE_HEADINGS") or str(EnvDefaults.TRANSLATE_HEADINGS)
            ).lower()
            == "true",
        )


@dataclass
class WorkflowOptions:
    """Options controlling workflow behavior and execution.

    Replaces the long parameter list in workflow functions with
    a structured, typed object.
    """

    dry_run: bool = False
    quiet: bool = False
    verbose: bool = False
    require_confirmation: bool = True
    update_all_entries: bool = False
    no_unreleased: bool = False
    include_diff: bool = False
    interactive: bool = False
    yes: bool = False  # Auto-accept changes
    audience: str = field(default_factory=lambda: EnvDefaults.AUDIENCE)
    language: str = field(default_factory=lambda: EnvDefaults.LANGUAGE)
    hint: str = ""
    show_prompt: bool = False

    def __post_init__(self) -> None:
        """Validate workflow options."""
        if self.audience not in Audiences.slugs():
            raise ValueError(f"Invalid audience: {self.audience}")
        if self.language not in [lang[1] for lang in Languages.LANGUAGES]:
            raise ValueError(f"Invalid language: {self.language}")


@dataclass
class ChangelogOptions:
    """Options controlling changelog file and boundary processing.

    Replaces the long parameter list in changelog operations with
    a structured, typed object.
    """

    file: str = "CHANGELOG.md"
    from_tag: str | None = None
    to_tag: str | None = None
    grouping_mode: str = field(default_factory=lambda: EnvDefaults.GROUPING_MODE)
    gap_threshold_hours: float = field(default_factory=lambda: EnvDefaults.GAP_THRESHOLD_HOURS)
    date_grouping: str = field(default_factory=lambda: EnvDefaults.DATE_GROUPING)
    special_unreleased_mode: bool = False

    def __post_init__(self) -> None:
        """Validate changelog options."""
        if self.grouping_mode not in [mode.value for mode in GroupingMode]:
            raise ValueError(f"Invalid grouping mode: {self.grouping_mode}")
        if self.date_grouping not in [mode.value for mode in DateGrouping]:
            raise ValueError(f"Invalid date grouping: {self.date_grouping}")
        if self.gap_threshold_hours <= 0 or self.gap_threshold_hours > 168:
            raise ValueError(f"Gap threshold hours must be between 0 and 168, got {self.gap_threshold_hours}")


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


class SecureConfig:
    """Secure configuration manager that holds API keys without global environment pollution.

    This class manages API keys securely without permanently adding them to
    os.environ, reducing the risk of key leakage and unintended exposure.
    """

    def __init__(self) -> None:
        self._keys: dict[str, str] = {}
        self._load_keys_from_files()

    def _load_keys_from_files(self) -> None:
        """Load keys from config files into secure storage."""
        # Load from user config
        self._load_from_file(Path.home() / ".kittylog.env")
        # Load from project env files
        self._load_from_file(Path(".env"))
        self._load_from_file(Path(".kittylog.env"))
        # Environment variables already take precedence
        for key in API_KEYS:
            if key in os.environ:
                self._keys[key] = os.environ[key]

    def _load_from_file(self, file_path: Path) -> None:
        """Load API keys from a specific file."""
        if not file_path.exists():
            return

        file_vars = dotenv_values(file_path)
        for key in API_KEYS:
            if key in file_vars and file_vars[key] is not None and key not in os.environ and key not in self._keys:
                self._keys[key] = str(file_vars[key])

    def get_key(self, key: str, default: str | None = None) -> str | None:
        """Get an API key securely without polluting environment.

        Args:
            key: The API key name
            default: Default value if key not found

        Returns:
            The API key value or None if not found
        """
        return self._keys.get(key, default)

    @contextmanager
    def inject_for_provider(self, provider: str, provider_mapping: dict[str, str]) -> Any:
        """Temporarily inject API keys for a specific provider call.

        This context manager temporarily sets environment variables
        for the duration of a provider call, then restores the original state.
        Prevents permanent pollution of os.environ.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            provider_mapping: Mapping from provider env vars to general key names

        Yields:
            Context with temporarily set environment variables
        """
        # Save original values
        original_values = {}
        injected_keys = []

        try:
            for provider_key, general_key in provider_mapping.items():
                value = self.get_key(general_key)
                if value:
                    # Save original value if it exists
                    if provider_key in os.environ:
                        original_values[provider_key] = os.environ[provider_key]
                    # Set the temporary value
                    os.environ[provider_key] = value
                    injected_keys.append(provider_key)

            yield

        finally:
            # Restore original values and clean up
            for key in injected_keys:
                if key in original_values:
                    os.environ[key] = original_values[key]
                else:
                    # Remove if it didn't exist before
                    os.environ.pop(key, None)

    def list_available_keys(self) -> list[str]:
        """List all available API key names (for debugging)."""
        return list(self._keys.keys())

    def has_key(self, key: str) -> bool:
        """Check if a specific API key is available."""
        return key in self._keys


# Global secure configuration instance
_secure_config = SecureConfig()


def get_api_key(key: str, default: str | None = None) -> str | None:
    """Get an API key securely without global environment pollution.

    This function replaces direct os.environ access for API keys.

    Args:
        key: API key name
        default: Default value if not found

    Returns:
        API key value or None
    """
    return _secure_config.get_key(key, default)


def inject_provider_keys(provider: str, provider_mapping: dict[str, str]) -> Any:
    """Context manager to temporarily inject API keys for a specific provider call.

    Args:
        provider: Provider name
        provider_mapping: Mapping from provider env vars to general key names

    Returns:
        Context manager that temporarily sets environment variables
    """
    return _secure_config.inject_for_provider(provider, provider_mapping)


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


# Global export removed - using SecureConfig for better security
# Keeping API_KEYS list for reference in SecureConfig


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


def load_config() -> dict:
    """Load configuration from environment and .env files.

    Precedence (highest to lowest):
    1. Environment variables
    2. Project .kittylog.env
    3. Project .env
    4. User ~/.kittylog.env
    5. Default values

    Returns:
        Configuration dictionary with all values
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

    # Update environment variables with API keys and sensitive values from config files
    # This ensures they're available via os.getenv() as expected by tests and providers
    api_key_vars = [
        "ANTHROPIC_API_KEY",
        "AZURE_OPENAI_API_KEY",
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

    # Extract API keys for secure return without polluting os.environ
    api_keys = {}
    for var in api_key_vars:
        # Check environment variables first (highest precedence)
        env_value = os.getenv(var)
        if env_value is not None:
            api_keys[var] = env_value
        # Then check config files
        elif var in config_vars and config_vars[var] is not None:
            api_keys[var] = config_vars[var]

    # Build config dictionary with proper precedence enforcement
    # Environment variables take precedence over file variables
    # But we must differentiate between invalid environment variables vs. invalid file variables
    config: dict = {}

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
            lambda x: x in [mode.value for mode in DateGrouping],
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
        config["temperature"] = _safe_float(config_temperature_str, EnvDefaults.TEMPERATURE)

    if config["max_output_tokens"] is None:
        config_max_output_tokens_str = config_vars.get("KITTYLOG_MAX_OUTPUT_TOKENS")
        config["max_output_tokens"] = _safe_int(config_max_output_tokens_str, EnvDefaults.MAX_OUTPUT_TOKENS)

    if config["max_retries"] is None:
        config_max_retries_str = config_vars.get("KITTYLOG_RETRIES")
        config["max_retries"] = _safe_int(config_max_retries_str, EnvDefaults.MAX_RETRIES)

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
        config["gap_threshold_hours"] = _safe_float(gap_threshold_str, EnvDefaults.GAP_THRESHOLD_HOURS)

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

    # Add API keys to the config dictionary for secure access
    config["api_keys"] = api_keys
    
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
        lambda x: x in [mode.value for mode in DateGrouping],
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


def apply_config_defaults(config: dict) -> dict:
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
    if date_grouping is not None and date_grouping not in [mode.value for mode in DateGrouping]:
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
