"""Tests for main module - cleaned up version.

This file has been cleaned up to remove broken legacy tests.
Comprehensive test coverage is provided by:
- test_main_fixed.py - Working tests with proper mocks
- test_edge_cases.py - Edge case handling tests
"""

from unittest.mock import Mock, patch

from kittylog.main import main_business_logic


class TestMainBusinessLogic:
    """Minimal working tests for main business logic."""

    @patch("kittylog.main.get_output_manager")
    @patch("kittylog.git_operations.get_repo")
    def test_main_logic_no_model_error(self, mock_get_repo, mock_output_manager, temp_dir):
        """Test error handling when no model is specified."""
        # Mock repository
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo

        # Mock output manager
        mock_output = Mock()
        mock_output_manager.return_value = mock_output

        config_without_model = {
            "model": None,
            "temperature": 0.7,
            "log_level": "INFO",
            "max_output_tokens": 1024,
            "max_retries": 3,
        }

        with patch("kittylog.main.config", config_without_model):
            success, token_usage = main_business_logic(
                changelog_file=str(temp_dir / "CHANGELOG.md"),
                model=None,
                quiet=True
            )

        assert success is False
        assert token_usage is None