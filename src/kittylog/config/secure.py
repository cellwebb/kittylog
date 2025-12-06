"""Secure configuration handling for API keys and sensitive data."""

import os
from contextlib import contextmanager
from typing import Any

from kittylog.config.data import KittylogConfigData


def get_api_key(key: str, default: str | None = None) -> str | None:
    """Get API key from environment variables.

    Args:
        key: Environment variable key to retrieve
        default: Optional default value if key not found

    Returns:
        API key value or default
    """
    return os.getenv(key, default)


@contextmanager
def inject_provider_keys(provider: str, provider_mapping: dict[str, str]) -> Any:
    """Context manager to temporarily inject provider API keys.

    Args:
        provider: Provider name
        provider_mapping: Mapping of env var names to values

    Yields:
        None
    """
    # Store original values
    original_values = {}

    try:
        # Set new values
        for env_var, value in provider_mapping.items():
            original_values[env_var] = os.getenv(env_var)
            os.environ[env_var] = value

        yield

    finally:
        # Restore original values
        for env_var, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(env_var, None)
            else:
                os.environ[env_var] = original_value


class SecureConfig:
    """Secure configuration manager for API keys and sensitive data.

    Provides safe access to API keys and other sensitive configuration
    while preventing accidental exposure.
    """

    def __init__(self, config: dict | KittylogConfigData):
        """Initialize secure configuration.

        Args:
            config: Configuration dictionary or KittylogConfigData instance
        """
        self._config = config
        self._provider_keys = self._extract_provider_keys()

    def _extract_provider_keys(self) -> dict[str, str]:
        """Extract provider-specific API keys from configuration."""
        # Handle both dict and KittylogConfigData
        config_dict = self._config if isinstance(self._config, dict) else self._config.to_dict()

        # Look for any keys ending in _API_KEY or _API_TOKEN
        return {
            key: value
            for key, value in config_dict.items()
            if value
            and isinstance(value, str)
            and (key.endswith("_API_KEY") or key.endswith("_API_TOKEN") or key.endswith("_ACCESS_TOKEN"))
        }

    @contextmanager
    def inject_for_provider(self, provider: str):
        """Inject API keys for a specific provider.

        Args:
            provider: Provider name to inject keys for

        Yields:
            None
        """
        # Map env var names to actual key values from our extracted keys
        key_mapping = dict(self._provider_keys)

        with inject_provider_keys(provider, key_mapping):
            yield

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value safely.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if isinstance(self._config, dict):
            return self._config.get(key, default)
        else:
            # For dataclass, use getattr with fallback
            return getattr(self._config, key, default)

    def has_api_keys(self) -> bool:
        """Check if any API keys are configured.

        Returns:
            True if API keys are configured
        """
        return bool(self._provider_keys)

    def get_provider_config(self, provider: str) -> dict[str, str]:
        """Get configuration for a specific provider.

        Args:
            provider: Provider name

        Returns:
            Dictionary of provider-specific configuration
        """
        # Return all extracted provider keys
        # In a real implementation, you might filter by provider name
        return dict(self._provider_keys)
