"""Tests for configuration module."""

import os

import pytest

from kittylog.config import load_config, validate_config
from kittylog.errors import ConfigError


class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_defaults(self, isolated_config_test):
        """Test loading config with default values."""
        config = load_config()

        # Check defaults
        assert config["model"] is None  # Should be None if not set
        assert config["temperature"] == 1.0
        assert config["max_output_tokens"] == 1024
        assert config["max_retries"] == 3
        assert config["log_level"] == "WARNING"
        assert config["warning_limit_tokens"] == 16384
        # Check new defaults
        assert config["grouping_mode"] == "tags"
        assert config["gap_threshold_hours"] == 4.0
        assert config["date_grouping"] == "daily"

    def test_load_config_from_env_vars(self, isolated_config_test, monkeypatch):
        """Test loading config from environment variables."""
        # Set environment variables
        monkeypatch.setenv("KITTYLOG_MODEL", "cerebras:qwen-3-coder-480b")
        monkeypatch.setenv("KITTYLOG_TEMPERATURE", "0.5")
        monkeypatch.setenv("KITTYLOG_MAX_OUTPUT_TOKENS", "2048")
        monkeypatch.setenv("KITTYLOG_RETRIES", "5")
        monkeypatch.setenv("KITTYLOG_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("KITTYLOG_WARNING_LIMIT_TOKENS", "8192")
        # Set new environment variables
        monkeypatch.setenv("KITTYLOG_GROUPING_MODE", "dates")
        monkeypatch.setenv("KITTYLOG_GAP_THRESHOLD_HOURS", "2.5")
        monkeypatch.setenv("KITTYLOG_DATE_GROUPING", "weekly")

        config = load_config()

        assert config["model"] == "cerebras:qwen-3-coder-480b"
        assert config["temperature"] == 0.5
        assert config["max_output_tokens"] == 2048
        assert config["max_retries"] == 5
        assert config["log_level"] == "DEBUG"
        assert config["warning_limit_tokens"] == 8192
        # Check new environment variables
        assert config["grouping_mode"] == "dates"
        assert config["gap_threshold_hours"] == 2.5
        assert config["date_grouping"] == "weekly"

    def test_load_config_from_user_env_file(self, isolated_config_test):
        """Test loading config from user-level .env file."""
        home_dir = isolated_config_test["home"]
        user_env_file = home_dir / ".kittylog.env"

        user_env_file.write_text("""KITTYLOG_MODEL=openai:gpt-4
KITTYLOG_TEMPERATURE=0.3
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
        project_env_file = cwd / ".kittylog.env"

        project_env_file.write_text("""KITTYLOG_MODEL=groq:llama-4
KITTYLOG_MAX_OUTPUT_TOKENS=512
KITTYLOG_GROUPING_MODE=gaps
KITTYLOG_GAP_THRESHOLD_HOURS=6.0
KITTYLOG_DATE_GROUPING=monthly
""")

        config = load_config()

        assert config["model"] == "groq:llama-4"
        assert config["max_output_tokens"] == 512
        # Check new project-level environment variables
        assert config["grouping_mode"] == "gaps"
        assert config["gap_threshold_hours"] == 6.0
        assert config["date_grouping"] == "monthly"

    def test_load_config_precedence(self, isolated_config_test, monkeypatch):
        """Test configuration precedence: env vars > project .env > user .env > defaults."""
        home_dir = isolated_config_test["home"]
        cwd = isolated_config_test["cwd"]

        # Create user-level config
        user_env_file = home_dir / ".kittylog.env"
        user_env_file.write_text("""KITTYLOG_MODEL=cerebras:qwen-3-coder-480b
KITTYLOG_TEMPERATURE=0.3
KITTYLOG_MAX_OUTPUT_TOKENS=1024
KITTYLOG_GROUPING_MODE=tags
KITTYLOG_GAP_THRESHOLD_HOURS=1.0
KITTYLOG_DATE_GROUPING=daily
""")

        # Create project-level config (should override user config)
        project_env_file = cwd / ".kittylog.env"
        project_env_file.write_text("""KITTYLOG_MODEL=openai:gpt-4
KITTYLOG_TEMPERATURE=0.5
KITTYLOG_GROUPING_MODE=gaps
KITTYLOG_GAP_THRESHOLD_HOURS=2.0
""")

        # Set environment variable (should override everything)
        monkeypatch.setenv("KITTYLOG_MODEL", "groq:llama-4")

        config = load_config()

        # Environment variable wins
        assert config["model"] == "groq:llama-4"
        # Project file overrides user file
        assert config["temperature"] == 0.5
        assert config["grouping_mode"] == "gaps"
        assert config["gap_threshold_hours"] == 2.0
        # User file provides value not overridden
        assert config["max_output_tokens"] == 1024
        assert config["date_grouping"] == "daily"

    @pytest.mark.xfail(reason="File-based config currently overwrites exported API keys", strict=True)
    def test_load_config_preserves_exported_api_key(self, isolated_config_test, monkeypatch):
        """Environment secrets should not be clobbered by project config files."""
        home_dir = isolated_config_test["home"]
        user_env_file = home_dir / ".kittylog.env"
        user_env_file.write_text("OPENAI_API_KEY=from-file\n")

        monkeypatch.setenv("OPENAI_API_KEY", "from-env")

        load_config()

        assert os.getenv("OPENAI_API_KEY") == "from-env"

    @pytest.mark.xfail(reason="Zero values are coerced back to defaults", strict=True)
    def test_load_config_allows_zero_temperature(self, isolated_config_test, monkeypatch):
        """A temperature of zero is valid and should survive validation."""
        monkeypatch.setenv("KITTYLOG_TEMPERATURE", "0")

        config = load_config()

        assert config["temperature"] == 0.0

    def test_load_config_invalid_values(self, isolated_config_test, monkeypatch):
        """Test handling of invalid configuration values."""
        # Set invalid values
        monkeypatch.setenv("KITTYLOG_TEMPERATURE", "invalid")
        monkeypatch.setenv("KITTYLOG_MAX_OUTPUT_TOKENS", "not_a_number")
        monkeypatch.setenv("KITTYLOG_RETRIES", "-1")
        # Set invalid values for new environment variables
        monkeypatch.setenv("KITTYLOG_GROUPING_MODE", "invalid_mode")
        monkeypatch.setenv("KITTYLOG_GAP_THRESHOLD_HOURS", "invalid_number")
        monkeypatch.setenv("KITTYLOG_DATE_GROUPING", "invalid_grouping")

        config = load_config()

        # Should fall back to defaults for invalid values
        assert config["temperature"] == 1.0  # default
        assert config["max_output_tokens"] == 1024  # default
        assert config["max_retries"] == 3  # default
        # Should fall back to defaults for invalid new values
        assert config["grouping_mode"] == "tags"  # default
        assert config["gap_threshold_hours"] == 4.0  # default
        assert config["date_grouping"] == "daily"  # default

    def test_load_config_with_nonexistent_files(self, isolated_config_test):
        """Test loading config when .env files don't exist."""
        # This should not raise an error
        config = load_config()

        # Should get defaults
        assert config["temperature"] == 1.0
        assert config["max_output_tokens"] == 1024
        # Should get new defaults
        assert config["grouping_mode"] == "tags"
        assert config["gap_threshold_hours"] == 4.0
        assert config["date_grouping"] == "daily"


class TestValidateConfig:
    """Test validate_config function."""

    def test_validate_config_valid(self):
        """Test validation of valid configuration."""
        config = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "max_retries": 3,
            "log_level": "INFO",
            "warning_limit_tokens": 16384,
            "grouping_mode": "dates",
            "gap_threshold_hours": 4.0,
            "date_grouping": "weekly",
        }

        # Should not raise any exception
        validate_config(config)

    def test_validate_config_invalid_temperature(self):
        """Test validation of invalid temperature."""
        config = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 5.0,  # Invalid: > 2.0
            "max_output_tokens": 1024,
            "max_retries": 3,
            "log_level": "INFO",
            "warning_limit_tokens": 16384,
            "grouping_mode": "tags",
            "gap_threshold_hours": 4.0,
            "date_grouping": "daily",
        }

        with pytest.raises(ConfigError) as exc_info:
            validate_config(config)
        assert "temperature" in str(exc_info.value).lower()

    def test_validate_config_invalid_max_tokens(self):
        """Test validation of invalid max_output_tokens."""
        config = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "max_output_tokens": -100,  # Invalid: negative
            "max_retries": 3,
            "log_level": "INFO",
            "warning_limit_tokens": 16384,
            "grouping_mode": "tags",
            "gap_threshold_hours": 4.0,
            "date_grouping": "daily",
        }

        with pytest.raises(ConfigError) as exc_info:
            validate_config(config)
        assert "max_output_tokens" in str(exc_info.value).lower()

    def test_validate_config_invalid_retries(self):
        """Test validation of invalid max_retries."""
        config = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "max_retries": 0,  # Invalid: must be >= 1
            "log_level": "INFO",
            "warning_limit_tokens": 16384,
            "grouping_mode": "tags",
            "gap_threshold_hours": 4.0,
            "date_grouping": "daily",
        }

        with pytest.raises(ConfigError) as exc_info:
            validate_config(config)
        assert "max_retries" in str(exc_info.value).lower()

    def test_validate_config_invalid_log_level(self):
        """Test validation of invalid log_level."""
        config = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "max_retries": 3,
            "log_level": "INVALID",  # Invalid log level
            "warning_limit_tokens": 16384,
            "grouping_mode": "tags",
            "gap_threshold_hours": 4.0,
            "date_grouping": "daily",
        }

        with pytest.raises(ConfigError) as exc_info:
            validate_config(config)
        assert "log_level" in str(exc_info.value).lower()

    def test_validate_config_invalid_grouping_mode(self):
        """Test validation of invalid grouping_mode."""
        config = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "max_retries": 3,
            "log_level": "INFO",
            "warning_limit_tokens": 16384,
            "grouping_mode": "invalid_mode",  # Invalid grouping mode
            "gap_threshold_hours": 4.0,
            "date_grouping": "daily",
        }

        with pytest.raises(ConfigError) as exc_info:
            validate_config(config)
        assert "grouping_mode" in str(exc_info.value).lower()

    def test_validate_config_invalid_gap_threshold(self):
        """Test validation of invalid gap_threshold_hours."""
        config = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "max_retries": 3,
            "log_level": "INFO",
            "warning_limit_tokens": 16384,
            "grouping_mode": "gaps",
            "gap_threshold_hours": -1.0,  # Invalid: negative
            "date_grouping": "daily",
        }

        with pytest.raises(ConfigError) as exc_info:
            validate_config(config)
        assert "gap_threshold_hours" in str(exc_info.value).lower()

    def test_validate_config_invalid_date_grouping(self):
        """Test validation of invalid date_grouping."""
        config = {
            "model": "cerebras:qwen-3-coder-480b",
            "temperature": 0.7,
            "max_output_tokens": 1024,
            "max_retries": 3,
            "log_level": "INFO",
            "warning_limit_tokens": 16384,
            "grouping_mode": "dates",
            "gap_threshold_hours": 4.0,
            "date_grouping": "invalid_grouping",  # Invalid date grouping
        }

        with pytest.raises(ConfigError) as exc_info:
            validate_config(config)
        assert "date_grouping" in str(exc_info.value).lower()

    def test_validate_config_boundary_values(self):
        """Test validation of boundary values."""
        # Test minimum valid values
        config = {
            "model": "openai:gpt-4o-mini",
            "temperature": 0.0,
            "max_output_tokens": 1,
            "max_retries": 1,
            "log_level": "DEBUG",
            "warning_limit_tokens": 1,
            "grouping_mode": "tags",
            "gap_threshold_hours": 0.1,  # minimum positive value
            "date_grouping": "daily",
        }
        validate_config(config)

        # Test maximum valid values
        config = {
            "model": "openai:gpt-4o-mini",
            "temperature": 2.0,
            "max_output_tokens": 999999,
            "max_retries": 100,
            "log_level": "CRITICAL",
            "warning_limit_tokens": 999999,
            "grouping_mode": "gaps",
            "gap_threshold_hours": 999999.0,
            "date_grouping": "monthly",
        }
        validate_config(config)


class TestConfigurationIntegration:
    """Integration tests for configuration loading and validation."""

    def test_full_config_workflow(self, isolated_config_test, monkeypatch):
        """Test complete configuration workflow."""
        home_dir = isolated_config_test["home"]
        cwd = isolated_config_test["cwd"]

        # Create user config
        user_env_file = home_dir / ".kittylog.env"
        user_env_file.write_text("""# User configuration
KITTYLOG_MODEL=cerebras:qwen-3-coder-480b
KITTYLOG_TEMPERATURE=0.3
ANTHROPIC_API_KEY=sk-ant-user123
""")

        # Create project config
        project_env_file = cwd / ".kittylog.env"
        project_env_file.write_text("""# Project overrides
KITTYLOG_TEMPERATURE=0.7
KITTYLOG_MAX_OUTPUT_TOKENS=2048
KITTYLOG_GROUPING_MODE=dates
KITTYLOG_DATE_GROUPING=weekly
""")

        # Load and validate config
        config = load_config()
        validate_config(config)

        # Check final values
        assert config["model"] == "cerebras:qwen-3-coder-480b"  # from user
        assert config["temperature"] == 0.7  # from project (overrides user)
        assert config["max_output_tokens"] == 2048  # from project
        assert config["max_retries"] == 3  # default
        assert config["grouping_mode"] == "dates"  # from project
        assert config["date_grouping"] == "weekly"  # from project

        # Check API key is available
        assert os.getenv("ANTHROPIC_API_KEY") == "sk-ant-user123"

    def test_config_error_handling(self, isolated_config_test):
        """Test configuration error handling."""
        cwd = isolated_config_test["cwd"]

        # Create config with invalid values
        project_env_file = cwd / ".kittylog.env"
        project_env_file.write_text("""KITTYLOG_TEMPERATURE=10.0
KITTYLOG_MAX_OUTPUT_TOKENS=-1
KITTYLOG_GROUPING_MODE=invalid
KITTYLOG_GAP_THRESHOLD_HOURS=-2.0
""")

        # Load config (should handle invalid values gracefully)
        config = load_config()

        # Validation should catch the issues
        with pytest.raises(ConfigError):
            validate_config(config)

    def test_config_with_comments_and_empty_lines(self, isolated_config_test):
        """Test configuration files with comments and empty lines."""
        home_dir = isolated_config_test["home"]

        user_env_file = home_dir / ".kittylog.env"
        user_env_file.write_text("""# Changelog Updater Configuration
# AI Provider Settings

KITTYLOG_MODEL=cerebras:qwen-3-coder-480b

# Generation Settings
KITTYLOG_TEMPERATURE=0.5
KITTYLOG_MAX_OUTPUT_TOKENS=1024

# API Keys
ANTHROPIC_API_KEY=sk-ant-test123

# Boundary Detection Settings
KITTYLOG_GROUPING_MODE=gaps
KITTYLOG_GAP_THRESHOLD_HOURS=3.5
KITTYLOG_DATE_GROUPING=monthly

# Empty line above
""")

        config = load_config()

        assert config["model"] == "cerebras:qwen-3-coder-480b"
        assert config["temperature"] == 0.5
        assert config["max_output_tokens"] == 1024
        assert os.getenv("ANTHROPIC_API_KEY") == "sk-ant-test123"
        assert config["grouping_mode"] == "gaps"
        assert config["gap_threshold_hours"] == 3.5
        assert config["date_grouping"] == "monthly"


class TestConfigUtils:
    """Test configuration utility functions."""

    def test_model_parsing(self):
        """Test that model configuration is properly parsed."""
        test_models = [
            "cerebras:qwen-3-coder-480b",
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
        monkeypatch.setenv("KITTYLOG_TEMPERATURE", "0.8")
        monkeypatch.setenv("KITTYLOG_MAX_OUTPUT_TOKENS", "2048")
        monkeypatch.setenv("KITTYLOG_RETRIES", "5")
        monkeypatch.setenv("KITTYLOG_WARNING_LIMIT_TOKENS", "32768")
        # Set string values for new environment variables
        monkeypatch.setenv("KITTYLOG_GAP_THRESHOLD_HOURS", "3.2")

        config = load_config()

        # Check types
        assert isinstance(config["temperature"], float)
        assert isinstance(config["max_output_tokens"], int)
        assert isinstance(config["max_retries"], int)
        assert isinstance(config["warning_limit_tokens"], int)
        # Check new types
        assert isinstance(config["gap_threshold_hours"], float)

        # Check values
        assert config["temperature"] == 0.8
        assert config["max_output_tokens"] == 2048
        assert config["max_retries"] == 5
        assert config["warning_limit_tokens"] == 32768
        # Check new values
        assert config["gap_threshold_hours"] == 3.2
