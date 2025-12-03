"""Secure configuration handling for API keys and sensitive data."""

import os
from contextlib import contextmanager
from typing import Any

from kittylog.providers import PROVIDER_ENV_VARS


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

    def __init__(self, config: dict):
        """Initialize secure configuration.

        Args:
            config: Configuration dictionary
        """
        self._config = config
        self._provider_keys = self._extract_provider_keys()

    def _extract_provider_keys(self) -> dict[str, str]:
        """Extract provider-specific API keys from configuration."""
        provider_keys = {}

        for env_vars in PROVIDER_ENV_VARS.values():
            for env_var in env_vars:
                value = self._config.get(env_var)
                if value:
                    provider_keys[env_var] = value

        return provider_keys

    @contextmanager
    def inject_for_provider(self, provider: str):
        """Inject API keys for a specific provider.

        Args:
            provider: Provider name to inject keys for

        Yields:
            None
        """
        # Build provider mapping directly
        from kittylog.providers import PROVIDER_ENV_VARS

        provider_mappings = {prov: {var: var for var in vars_list} for prov, vars_list in PROVIDER_ENV_VARS.items()}
        provider_mappings["azure-openai"] = {"AZURE_OPENAI_API_KEY": "AZURE_OPENAI_API_KEY"}

        provider_mapping = provider_mappings.get(provider, {})

        # Map env var names to actual key values
        key_mapping = {}
        for env_var, config_var in provider_mapping.items():
            actual_key = self._provider_keys.get(config_var)
            if actual_key:
                key_mapping[env_var] = actual_key

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
        return self._config.get(key, default)

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
        provider_config = {}
        env_vars = PROVIDER_ENV_VARS.get(provider, [])

        for env_var in env_vars:
            value = self._provider_keys.get(env_var)
            if value:
                provider_config[env_var] = value

        return provider_config
