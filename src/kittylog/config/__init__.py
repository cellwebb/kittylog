"""Configuration management for kittylog.

This package provides configuration loading, validation, and secure handling
for API keys and application settings.
"""

# Data classes
# CLI commands
from kittylog.config.cli import KITTYLOG_ENV_PATH, config
from kittylog.config.data import KittylogConfigData

# Loading and validation
from kittylog.config.loader import (
    apply_config_defaults,
    load_config,
    validate_config,
    validate_config_value,
    validate_env_var,
)
from kittylog.config.options import ChangelogOptions, WorkflowOptions

# Secure configuration
from kittylog.config.secure import SecureConfig, get_api_key, inject_provider_keys

__all__ = [
    "KITTYLOG_ENV_PATH",
    "ChangelogOptions",
    "KittylogConfigData",
    "SecureConfig",
    "WorkflowOptions",
    "apply_config_defaults",
    "config",
    "get_api_key",
    "inject_provider_keys",
    "load_config",
    "validate_config",
    "validate_config_value",
    "validate_env_var",
]
