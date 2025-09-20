"""Tests for configuration module."""

import os

import pytest

from clog.config import load_config, validate_config
from clog.errors import ConfigError


class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_defaults(self, isolated_config_test):
        """Test loading config with default values."""
        config = load_config()

        # Check defaults
        assert config["model"] is None  # Should be None if not set
        assert config["temperature"] == 0.7
        assert config["max_output_tokens"] == 1024
        assert config["max_retries"] == 3
        assert config["log_level"] == "WARNING"
        assert config["warning_limit_tokens"] == 16384

    def test_load_config_from_env_vars(self, isolated_config_test, monkeypatch):
        """Test loading config from environment variables."""
        # Set environment variables
        monkeypatch.setenv("CHANGELOG_UPDATER_MODEL", "anthropic:claude-3-5-haiku-latest")
        monkeypatch.setenv("CHANGELOG_UPDATER_TEMPERATURE", "0.5")
        monkeypatch.setenv("CHANGELOG_UPDATER_MAX_OUTPUT_TOKENS", "2048")
        monkeypatch.setenv("CHANGELOG_UPDATER_RETRIES", "5")
        monkeypatch.setenv("CHANGELOG_UPDATER_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("CHANGELOG_UPDATER_WARNING_LIMIT_TOKENS", "8192")

        config = load_config()

        assert config["model"] == "anthropic:claude-3-5-haiku-latest"
        assert config["temperature"] == 0.5
        assert config["max_output_tokens"] == 2048
        assert config["max_retries"] == 5
        assert config["log_level"] == "DEBUG"
        assert config["warning_limit_tokens"] == 8192

    def test_load_config_from_user_env_file(self, isolated_config_test):
        """Test loading config from user-level .env file."""
        home_dir = isolated_config_test["home"]
        user_env_file = home_dir / ".clog.env"

        user_env_file.write_text("""CHANGELOG_UPDATER_MODEL=openai:gpt-4
CHANGELOG_UPDATER_TEMPERATURE=0.3
OPENAI_API_KEY=sk-test123
""")

        config = load_config()

        assert config["model"] == "openai:gpt-4"
        assert config["temperature"] == 0.3
        # API key should be available in environment
        assert os.getenv("OPENAI_API_KEY") == "sk-test123"

    def test_load_config_from_project_env_file(self, isolated_config_test):
        """Test loading config from project-level .env file."""
        cwd = isolated_config_test["cwd"]
        project_env_file = cwd / ".clog.env"

        project_env_file.write_text("""CHANGELOG_UPDATER_MODEL=groq:llama-4
CHANGELOG_UPDATER_MAX_OUTPUT_TOKENS=512
""")

        config = load_config()

        assert config["model"] == "groq:llama-4"
        assert config["max_output_tokens"] == 512

    def test_load_config_precedence(self, isolated_config_test, monkeypatch):
        """Test configuration precedence: env vars > project .env > user .env > defaults."""
        home_dir = isolated_config_test["home"]
        cwd = isolated_config_test["cwd"]

        # Create user-level config
        user_env_file = home_dir / ".clog.env"
        user_env_file.write_text("""CHANGELOG_UPDATER_MODEL=anthropic:claude-3-5-haiku-latest
CHANGELOG_UPDATER_TEMPERATURE=0.3
CHANGELOG_UPDATER_MAX_OUTPUT_TOKENS=1024
""")

        # Create project-level config (should override user config)
        project_env_file = cwd / ".clog.env"
        project_env_file.write_text("""CHANGELOG_UPDATER_MODEL=openai:gpt-4
CHANGELOG_UPDATER_TEMPERATURE=0.5
""")

        # Set environment variable (should override everything)
        monkeypatch.setenv("CHANGELOG_UPDATER_MODEL", "groq:llama-4")

        config = load_config()

        # Environment variable wins
        assert config["model"] == "groq:llama-4"
        # Project file overrides user file
        assert config["temperature"] == 0.5
        # User file provides value not overridden
        assert config["max_output_tokens"] == 1024

    def test_load_config_invalid_values(self, isolated_config_test, monkeypatch):
        """Test handling of invalid configuration values."""
        # Set invalid values
        monkeypatch.setenv("CHANGELOG_UPDATER_TEMPERATURE", "invalid")
        monkeypatch.setenv("CHANGELOG_UPDATER_MAX_OUTPUT_TOKENS", "not_a_number")
        monkeypatch.setenv("CHANGELOG_UPDATER_RETRIES", "-1")

        config = load_config()

        # Should fall back to defaults for invalid values
        assert config["temperature"] == 0.7  # default
        assert config["max_output_tokens"] == 1024  # default
        assert config["max_retries"] == 3  # default

    def test_load_config_with_nonexistent_files(self, isolated_config_test):
        """Test loading config when .env files don't exist."""
        # This should not raise an error
        config = load_config()

        # Should get defaults
        assert config["temperature"] == 0.7
        assert config["max_output_tokens"] == 1024


class TestValidateConfig:
    """Test validate_config function."""

    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        config = {
            "model": "anthropic:claude-3-5-haiku-latest",
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "max_retries": 3,
            "log_level": "INFO",
            "warning_limit_tokens": 16384,
        }

        # Should not raise any exception
        validate_config(config)

    def test_validate_config_invalid_temperature(self):
        """Test validation of invalid temperature."""
        config = {
            "model": "anthropic:claude-3-5-haiku-latest",
            "temperature": 5.0,  # Invalid: > 2.0
            "max_output_tokens": 1024,
            "max_retries": 3,
            "log_level": "INFO",
            "warning_limit_tokens": 16384,
        }

        with pytest.raises(ConfigError) as exc_info:
            validate_config(config)
        assert "temperature" in str(exc_info.value).lower()

    def test_validate_config_invalid_max_tokens(self):
        """Test validation of invalid max_output_tokens."""
        config = {
            "model": "anthropic:claude-3-5-haiku-latest",
            "temperature": 0.7,
            "max_output_tokens": -100,  # Invalid: negative
            "max_retries": 3,
            "log_level": "INFO",
            "warning_limit_tokens": 16384,
        }

        with pytest.raises(ConfigError) as exc_info:
            validate_config(config)
        assert "max_output_tokens" in str(exc_info.value).lower()

    def test_validate_config_invalid_retries(self):
        """Test validation of invalid max_retries."""
        config = {
            "model": "anthropic:claude-3-5-haiku-latest",
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "max_retries": 0,  # Invalid: must be >= 1
            "log_level": "INFO",
            "warning_limit_tokens": 16384,
        }

        with pytest.raises(ConfigError) as exc_info:
            validate_config(config)
        assert "max_retries" in str(exc_info.value).lower()

    def test_validate_config_invalid_log_level(self):
        """Test validation of invalid log_level."""
        config = {
            "model": "anthropic:claude-3-5-haiku-latest",
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "max_retries": 3,
            "log_level": "INVALID",  # Invalid log level
            "warning_limit_tokens": 16384,
        }

        with pytest.raises(ConfigError) as exc_info:
            validate_config(config)
        assert "log_level" in str(exc_info.value).lower()

    def test_validate_config_boundary_values(self):
        """Test validation of boundary values."""
        # Test minimum valid values
        config = {
            "model": "test:model",
            "temperature": 0.0,
            "max_output_tokens": 1,
            "max_retries": 1,
            "log_level": "DEBUG",
            "warning_limit_tokens": 1,
        }
        validate_config(config)

        # Test maximum valid values
        config = {
            "model": "test:model",
            "temperature": 2.0,
            "max_output_tokens": 999999,
            "max_retries": 100,
            "log_level": "CRITICAL",
            "warning_limit_tokens": 999999,
        }
        validate_config(config)


class TestConfigurationIntegration:
    """Integration tests for configuration loading and validation."""

    def test_full_config_workflow(self, isolated_config_test, monkeypatch):
        """Test complete configuration workflow."""
        home_dir = isolated_config_test["home"]
        cwd = isolated_config_test["cwd"]

        # Create user config
        user_env_file = home_dir / ".clog.env"
        user_env_file.write_text("""# User configuration
CHANGELOG_UPDATER_MODEL=anthropic:claude-3-5-haiku-latest
CHANGELOG_UPDATER_TEMPERATURE=0.3
ANTHROPIC_API_KEY=sk-ant-user123
""")

        # Create project config
        project_env_file = cwd / ".clog.env"
        project_env_file.write_text("""# Project overrides
CHANGELOG_UPDATER_TEMPERATURE=0.7
CHANGELOG_UPDATER_MAX_OUTPUT_TOKENS=2048
""")

        # Load and validate config
        config = load_config()
        validate_config(config)

        # Check final values
        assert config["model"] == "anthropic:claude-3-5-haiku-latest"  # from user
        assert config["temperature"] == 0.7  # from project (overrides user)
        assert config["max_output_tokens"] == 2048  # from project
        assert config["max_retries"] == 3  # default

        # Check API key is available
        assert os.getenv("ANTHROPIC_API_KEY") == "sk-ant-user123"

    def test_config_error_handling(self, isolated_config_test):
        """Test configuration error handling."""
        cwd = isolated_config_test["cwd"]

        # Create config with invalid values
        project_env_file = cwd / ".clog.env"
        project_env_file.write_text("""CHANGELOG_UPDATER_TEMPERATURE=10.0
CHANGELOG_UPDATER_MAX_OUTPUT_TOKENS=-1
""")

        # Load config (should handle invalid values gracefully)
        config = load_config()

        # Validation should catch the issues
        with pytest.raises(ConfigError):
            validate_config(config)

    def test_config_with_comments_and_empty_lines(self, isolated_config_test):
        """Test configuration files with comments and empty lines."""
        home_dir = isolated_config_test["home"]

        user_env_file = home_dir / ".clog.env"
        user_env_file.write_text("""# Changelog Updater Configuration
# AI Provider Settings

CHANGELOG_UPDATER_MODEL=anthropic:claude-3-5-haiku-latest

# Generation Settings
CHANGELOG_UPDATER_TEMPERATURE=0.5
CHANGELOG_UPDATER_MAX_OUTPUT_TOKENS=1024

# API Keys
ANTHROPIC_API_KEY=sk-ant-test123

# Empty line above
""")

        config = load_config()

        assert config["model"] == "anthropic:claude-3-5-haiku-latest"
        assert config["temperature"] == 0.5
        assert config["max_output_tokens"] == 1024
        assert os.getenv("ANTHROPIC_API_KEY") == "sk-ant-test123"


class TestConfigUtils:
    """Test configuration utility functions."""

    def test_model_parsing(self):
        """Test that model configuration is properly parsed."""
        test_models = [
            "anthropic:claude-3-5-haiku-latest",
            "openai:gpt-4",
            "groq:llama-4-scout-17b",
            "ollama:gemma3",
        ]

        for model in test_models:
            config = {"model": model}
            validate_config(config)  # Should not raise

    def test_config_type_conversion(self, isolated_config_test, monkeypatch):
        """Test that string values from env are properly converted to correct types."""
        # Set string values that should be converted
        monkeypatch.setenv("CHANGELOG_UPDATER_TEMPERATURE", "0.8")
        monkeypatch.setenv("CHANGELOG_UPDATER_MAX_OUTPUT_TOKENS", "2048")
        monkeypatch.setenv("CHANGELOG_UPDATER_RETRIES", "5")
        monkeypatch.setenv("CHANGELOG_UPDATER_WARNING_LIMIT_TOKENS", "32768")

        config = load_config()

        # Check types
        assert isinstance(config["temperature"], float)
        assert isinstance(config["max_output_tokens"], int)
        assert isinstance(config["max_retries"], int)
        assert isinstance(config["warning_limit_tokens"], int)

        # Check values
        assert config["temperature"] == 0.8
        assert config["max_output_tokens"] == 2048
        assert config["max_retries"] == 5
        assert config["warning_limit_tokens"] == 32768
