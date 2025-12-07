"""Tests for secure configuration handling."""

import os
from unittest.mock import patch

from kittylog.config.data import KittylogConfigData
from kittylog.config.secure import (
    SecureConfig,
    get_api_key,
    inject_provider_keys,
)


class TestGetApiKey:
    """Test the get_api_key function."""

    def test_get_api_key_exists(self):
        """Test getting existing API key from environment."""
        key_name = "TEST_API_KEY"
        key_value = "secret_value"

        with patch.dict(os.environ, {key_name: key_value}):
            result = get_api_key(key_name)
            assert result == key_value

    def test_get_api_key_not_exists(self):
        """Test getting non-existent API key."""
        key_name = "NONEXISTENT_API_KEY"

        with patch.dict(os.environ, {}, clear=True):
            result = get_api_key(key_name)
            assert result is None

    def test_get_api_key_with_default(self):
        """Test getting API key with default value when key doesn't exist."""
        key_name = "NONEXISTENT_API_KEY"
        default_value = "default_secret"

        with patch.dict(os.environ, {}, clear=True):
            result = get_api_key(key_name, default=default_value)
            assert result == default_value

    def test_get_api_key_with_default_exists(self):
        """Test getting API key with default when key exists."""
        key_name = "TEST_API_KEY"
        key_value = "actual_secret"
        default_value = "default_secret"

        with patch.dict(os.environ, {key_name: key_value}):
            result = get_api_key(key_name, default=default_value)
            assert result == key_value  # Should use actual value, not default

    def test_get_api_key_environment_var_override(self):
        """Test that environment variable changes are reflected."""
        key_name = "TEST_API_KEY"

        with patch.dict(os.environ, {key_name: "initial_value"}):
            assert get_api_key(key_name) == "initial_value"

            os.environ[key_name] = "changed_value"
            assert get_api_key(key_name) == "changed_value"


class TestInjectProviderKeys:
    """Test the inject_provider_keys context manager."""

    def test_inject_provider_keys_successful_injection(self):
        """Test successful injection of provider keys."""
        provider_mapping = {"OPENAI_API_KEY": "sk-test123", "CUSTOM_ENV_VAR": "custom_value"}

        # Save original values to restore manually
        original_openai = os.getenv("OPENAI_API_KEY")
        original_custom = os.getenv("CUSTOM_ENV_VAR")

        try:
            with inject_provider_keys("test_provider", provider_mapping):
                assert os.getenv("OPENAI_API_KEY") == "sk-test123"
                assert os.getenv("CUSTOM_ENV_VAR") == "custom_value"

            # After context manager, values should be restored
            assert os.getenv("OPENAI_API_KEY") == original_openai
            assert os.getenv("CUSTOM_ENV_VAR") == original_custom
        finally:
            # Clean up manually in case restore failed
            if original_openai is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = original_openai

            if original_custom is None:
                os.environ.pop("CUSTOM_ENV_VAR", None)
            else:
                os.environ["CUSTOM_ENV_VAR"] = original_custom

    def test_inject_provider_keys_restore_original_values(self):
        """Test that original values are properly restored."""
        original_values = {"OPENAI_API_KEY": "original_key", "CUSTOM_VAR": "original_custom"}

        provider_mapping = {"OPENAI_API_KEY": "new_key", "CUSTOM_VAR": "new_custom", "NEW_VAR": "brand_new"}

        with patch.dict(os.environ, original_values):
            with inject_provider_keys("test_provider", provider_mapping):
                assert os.getenv("OPENAI_API_KEY") == "new_key"
                assert os.getenv("CUSTOM_VAR") == "new_custom"
                assert os.getenv("NEW_VAR") == "brand_new"

            # Should be restored to original values
            assert os.getenv("OPENAI_API_KEY") == "original_key"
            assert os.getenv("CUSTOM_VAR") == "original_custom"
            assert os.getenv("NEW_VAR") is None

    def test_inject_provider_keys_exception_handling(self):
        """Test that original values are restored even if exception occurs."""
        original_values = {"OPENAI_API_KEY": "original_key"}

        provider_mapping = {"OPENAI_API_KEY": "new_key"}

        with patch.dict(os.environ, original_values):
            try:
                with inject_provider_keys("test_provider", provider_mapping):
                    assert os.getenv("OPENAI_API_KEY") == "new_key"
                    raise ValueError("Test exception")
            except ValueError:
                pass  # Expected

            # Should still be restored
            assert os.getenv("OPENAI_API_KEY") == "original_key"

    def test_inject_provider_keys_empty_mapping(self):
        """Test injection with empty mapping."""
        original_values = {"EXISTING_VAR": "existing_value"}

        with patch.dict(os.environ, original_values):
            with inject_provider_keys("test_provider", {}):
                assert os.getenv("EXISTING_VAR") == "existing_value"

            assert os.getenv("EXISTING_VAR") == "existing_value"

    def test_inject_provider_keys_none_values(self):
        """Test that None values are handled gracefully."""
        provider_mapping = {
            "API_KEY": ""  # Use empty string instead of None for env vars
        }

        with patch.dict(os.environ, {}, clear=True):
            with inject_provider_keys("test_provider", provider_mapping):
                # Empty string should be set
                assert os.getenv("API_KEY") == ""

            assert os.getenv("API_KEY") is None  # Should be removed


class TestSecureConfig:
    """Test the SecureConfig class."""

    def test_secure_config_init_with_dict(self):
        """Test SecureConfig initialization with dictionary."""
        config_dict = {
            "model": "gpt-4",
            "OPENAI_API_KEY": "sk-test123",
            "temperature": 0.7,
            "ANTHROPIC_API_TOKEN": "ant-test456",
        }

        secure_config = SecureConfig(config_dict)
        assert secure_config.get("model") == "gpt-4"
        assert secure_config.get("temperature") == 0.7

        # API keys should be extracted
        provider_keys = secure_config._provider_keys
        assert "OPENAI_API_KEY" in provider_keys
        assert "ANTHROPIC_API_TOKEN" in provider_keys
        assert provider_keys["OPENAI_API_KEY"] == "sk-test123"
        assert provider_keys["ANTHROPIC_API_TOKEN"] == "ant-test456"

    def test_secure_config_init_with_dataclass(self):
        """Test SecureConfig initialization with KittylogConfigData."""
        config_data = KittylogConfigData(model="claude-3", temperature=0.5)

        secure_config = SecureConfig(config_data)
        assert secure_config.get("model") == "claude-3"
        assert secure_config.get("temperature") == 0.5

        # No API keys should be extracted from clean dataclass
        provider_keys = secure_config._provider_keys
        assert provider_keys == {}

    def test_extract_provider_keys_with_various_suffixes(self):
        """Test extraction of provider keys with different suffixes."""
        config_dict = {
            "OPENAI_API_KEY": "sk-123",
            "ANTHROPIC_API_TOKEN": "ant-456",
            "CUSTOM_ACCESS_TOKEN": "custom-token",
            "SOME_OTHER_KEY": "other-value",
            "ANOTHER_VAR": "var-value",
            "EMPTY_KEY": "",
        }

        secure_config = SecureConfig(config_dict)
        provider_keys = secure_config._provider_keys

        # Should extract keys with _API_KEY, _API_TOKEN, _ACCESS_TOKEN suffixes
        assert "OPENAI_API_KEY" in provider_keys
        assert "ANTHROPIC_API_TOKEN" in provider_keys
        assert "CUSTOM_ACCESS_TOKEN" in provider_keys

        # Should not extract keys without proper suffixes
        assert "SOME_OTHER_KEY" not in provider_keys
        assert "ANOTHER_VAR" not in provider_keys

        # Should not extract empty strings
        assert "EMPTY_KEY" not in provider_keys

    def test_extract_provider_keys_non_string_values(self):
        """Test that non-string values are not extracted as API keys."""
        config_dict = {
            "STRING_KEY": "string-value",
            "INT_KEY": 123,
            "NONE_KEY": None,
            "BOOL_KEY": True,
            "OPENAI_API_KEY": "sk-123",
        }

        secure_config = SecureConfig(config_dict)
        provider_keys = secure_config._provider_keys

        # Should only extract string values with proper suffixes
        assert "STRING_KEY" not in provider_keys  # Wrong suffix
        assert "INT_KEY" not in provider_keys  # Not string
        assert "NONE_KEY" not in provider_keys  # Not string
        assert "BOOL_KEY" not in provider_keys  # Not string
        assert "OPENAI_API_KEY" in provider_keys  # Should be extracted

    def test_has_api_keys_true(self):
        """Test has_api_keys returns True when keys are present."""
        config_dict = {"OPENAI_API_KEY": "sk-123"}

        secure_config = SecureConfig(config_dict)
        assert secure_config.has_api_keys() is True

    def test_has_api_keys_false(self):
        """Test has_api_keys returns False when no keys are present."""
        config_dict = {"model": "gpt-4", "temperature": 0.7}

        secure_config = SecureConfig(config_dict)
        assert secure_config.has_api_keys() is False

    def test_has_api_keys_empty_strings(self):
        """Test has_api_keys returns False when keys are empty strings."""
        config_dict = {"OPENAI_API_KEY": "", "ANTHROPIC_API_TOKEN": None}

        secure_config = SecureConfig(config_dict)
        assert secure_config.has_api_keys() is False

    def test_get_config_value_dict_config(self):
        """Test getting values from dict configuration."""
        config_dict = {"model": "gpt-4", "temperature": 0.7}

        secure_config = SecureConfig(config_dict)
        assert secure_config.get("model") == "gpt-4"
        assert secure_config.get("temperature") == 0.7
        assert secure_config.get("nonexistent") is None
        assert secure_config.get("nonexistent", "default") == "default"

    def test_get_config_value_dataclass_config(self):
        """Test getting values from dataclass configuration."""
        config_data = KittylogConfigData(model="claude-3", temperature=0.5)

        secure_config = SecureConfig(config_data)
        assert secure_config.get("model") == "claude-3"
        assert secure_config.get("temperature") == 0.5
        assert secure_config.get("nonexistent") is None
        assert secure_config.get("nonexistent", "default") == "default"

    def test_inject_for_provider_functionality(self):
        """Test inject_for_provider context manager."""
        config_dict = {"OPENAI_API_KEY": "sk-123", "ANTHROPIC_API_TOKEN": "ant-456"}

        secure_config = SecureConfig(config_dict)

        with patch.dict(os.environ, {}, clear=True):
            with secure_config.inject_for_provider("openai"):
                assert os.getenv("OPENAI_API_KEY") == "sk-123"
                assert os.getenv("ANTHROPIC_API_TOKEN") == "ant-456"

            # Keys should be restored (removed since they didn't exist originally)
            assert os.getenv("OPENAI_API_KEY") is None
            assert os.getenv("ANTHROPIC_API_TOKEN") is None

    def test_get_provider_config(self):
        """Test getting provider configuration."""
        config_dict = {
            "OPENAI_API_KEY": "sk-123",
            "ANTHROPIC_API_TOKEN": "ant-456",
            "CUSTOM_ACCESS_TOKEN": "custom-token",
        }

        secure_config = SecureConfig(config_dict)
        provider_config = secure_config.get_provider_config("openai")

        assert provider_config["OPENAI_API_KEY"] == "sk-123"
        assert provider_config["ANTHROPIC_API_TOKEN"] == "ant-456"
        assert provider_config["CUSTOM_ACCESS_TOKEN"] == "custom-token"

        # Should return a copy, not the original dict
        assert provider_config is not secure_config._provider_keys

    def test_get_provider_config_empty(self):
        """Test getting provider config when no keys exist."""
        config_dict = {"model": "gpt-4", "temperature": 0.7}

        secure_config = SecureConfig(config_dict)
        provider_config = secure_config.get_provider_config("openai")

        assert provider_config == {}

    def test_inject_for_provider_with_exception(self):
        """Test inject_for_provider handles exceptions properly."""
        config_dict = {"OPENAI_API_KEY": "sk-123"}

        secure_config = SecureConfig(config_dict)

        with patch.dict(os.environ, {}, clear=True):
            try:
                with secure_config.inject_for_provider("openai"):
                    assert os.getenv("OPENAI_API_KEY") == "sk-123"
                    raise RuntimeError("Test exception")
            except RuntimeError:
                pass  # Expected

            # Keys should be restored even after exception
            assert os.getenv("OPENAI_API_KEY") is None

    def test_secure_config_integration_with_real_env(self):
        """Test SecureConfig integration with real environment variables."""
        config_dict = {"OPENAI_API_KEY": "environment_key"}

        with patch.dict(os.environ, {"OPENAI_API_KEY": "real_env_value"}):
            secure_config = SecureConfig(config_dict)

            # The config value should take precedence over environment
            provider_keys = secure_config._provider_keys
            assert provider_keys["OPENAI_API_KEY"] == "environment_key"

            # But injection should work based on the extracted keys
            with secure_config.inject_for_provider("openai"):
                assert os.getenv("OPENAI_API_KEY") == "environment_key"
