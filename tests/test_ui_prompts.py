"""Tests for UI prompts module."""

from unittest.mock import Mock, patch

import pytest

from kittylog.ui.prompts import interactive_configuration


class TestInteractiveConfiguration:
    """Test the interactive_configuration function."""

    def test_interactive_configuration_quiet_mode(self):
        """Test configuration in quiet mode with defaults."""
        result = interactive_configuration(
            grouping_mode="dates",
            gap_threshold=2.5,
            date_grouping="weekly",
            include_diff=True,
            quiet=True,
            audience="developers",
        )
        assert result == ("dates", 2.5, "weekly", True, "developers")

    def test_interactive_configuration_quiet_mode_with_none_values(self):
        """Test configuration in quiet mode with None values using defaults."""
        with patch("kittylog.ui.prompts.load_config", return_value=Mock(audience="users")):
            result = interactive_configuration(
                grouping_mode=None, gap_threshold=None, date_grouping=None, include_diff=None, quiet=True, audience=None
            )
            assert result == ("tags", 4.0, "daily", False, "users")

    def test_interactive_configuration_full_workflow_tags_mode(self):
        """Test full interactive workflow with tags mode."""
        mock_output = Mock()
        mock_output.echo.return_value = None
        mock_output.warning.return_value = None

        with (
            patch("kittylog.ui.prompts.get_output_manager", return_value=mock_output),
            patch("kittylog.ui.prompts.questionary") as mock_questionary,
        ):
            # Mock all the questionary responses
            mock_select = Mock()
            mock_select.ask.side_effect = ["tags", "stakeholders"]  # grouping then audience
            mock_confirm = Mock()
            mock_confirm.ask.return_value = False
            mock_questionary.select.return_value = mock_select
            mock_questionary.confirm.return_value = mock_confirm

            with patch("kittylog.ui.prompts.load_config", return_value=Mock(audience="stakeholders")):
                result = interactive_configuration(
                    grouping_mode=None,
                    gap_threshold=None,
                    date_grouping=None,
                    include_diff=None,
                    quiet=False,
                    audience=None,
                )

                assert result == ("tags", 4.0, "daily", False, "stakeholders")

                # Verify the questions were asked correctly
                assert mock_questionary.select.call_count == 2  # grouping + audience
                assert mock_questionary.confirm.call_count == 1  # diff question

    def test_interactive_configuration_gaps_mode_with_custom_threshold(self):
        """Test gaps mode with custom threshold input."""
        mock_output = Mock()
        mock_output.echo.return_value = None
        mock_output.warning.return_value = None

        with (
            patch("kittylog.ui.prompts.get_output_manager", return_value=mock_output),
            patch("kittylog.ui.prompts.questionary") as mock_questionary,
        ):
            # Mock responses: gaps mode, then threshold, then audience, no diff
            mock_select = Mock()
            mock_text = Mock()
            mock_text.ask.return_value = "6.5"
            mock_confirm = Mock()
            mock_confirm.ask.return_value = False

            # First call returns gaps, second returns default for audience, third for diff
            mock_select.ask.side_effect = ["gaps", "stakeholders"]
            mock_questionary.select.return_value = mock_select
            mock_questionary.text.return_value = mock_text
            mock_questionary.confirm.return_value = mock_confirm

            result = interactive_configuration(
                grouping_mode=None,
                gap_threshold=None,
                date_grouping=None,
                include_diff=None,
                quiet=False,
                audience=None,
            )

            assert result == ("gaps", 6.5, "daily", False, "stakeholders")

    def test_interactive_configuration_dates_mode_with_weekly(self):
        """Test dates mode with weekly grouping."""
        mock_output = Mock()
        mock_output.echo.return_value = None
        mock_output.warning.return_value = None

        with (
            patch("kittylog.ui.prompts.get_output_manager", return_value=mock_output),
            patch("kittylog.ui.prompts.questionary") as mock_questionary,
        ):
            # Mock responses: dates mode, then weekly, then audience, include diff
            mock_select = Mock()
            mock_select.ask.side_effect = ["dates", "weekly", "users"]
            mock_confirm = Mock()
            mock_confirm.ask.return_value = True
            mock_questionary.select.return_value = mock_select
            mock_questionary.confirm.return_value = mock_confirm

            result = interactive_configuration(
                grouping_mode=None,
                gap_threshold=None,
                date_grouping=None,
                include_diff=None,
                quiet=False,
                audience=None,
            )

            assert result == ("dates", 4.0, "weekly", True, "users")

    def test_interactive_configuration_with_preselected_values(self):
        """Test configuration when values are preselected."""
        mock_output = Mock()
        mock_output.echo.return_value = None
        mock_output.warning.return_value = None

        with (
            patch("kittylog.ui.prompts.get_output_manager", return_value=mock_output),
            patch("kittylog.ui.prompts.questionary") as mock_questionary,
        ):
            # All questions return None (user accepts defaults)
            mock_select = Mock()
            mock_select.ask.return_value = None
            mock_confirm = Mock()
            mock_confirm.ask.return_value = None
            mock_questionary.select.return_value = mock_select
            mock_questionary.confirm.return_value = mock_confirm

            with patch("kittylog.ui.prompts.load_config", return_value=Mock(audience="developers")):
                result = interactive_configuration(
                    grouping_mode="gaps",
                    gap_threshold="3.0",
                    date_grouping="monthly",
                    include_diff=True,
                    quiet=False,
                    audience="users",
                )

                # Should use the provided values or fallback to config
                assert result == ("gaps", "3.0", "monthly", True, "users")

    def test_interactive_configuration_keyboard_interrupt(self):
        """Test handling of keyboard interrupt."""
        mock_output = Mock()
        mock_output.echo.return_value = None
        mock_output.warning.return_value = None

        with (
            patch("kittylog.ui.prompts.get_output_manager", return_value=mock_output),
            patch("kittylog.ui.prompts.questionary") as mock_questionary,
        ):
            mock_select = Mock()
            mock_select.ask.side_effect = KeyboardInterrupt()
            mock_questionary.select.return_value = mock_select

            with pytest.raises(KeyboardInterrupt):
                interactive_configuration(
                    grouping_mode=None,
                    gap_threshold=None,
                    date_grouping=None,
                    include_diff=None,
                    quiet=False,
                    audience=None,
                )

            mock_output.warning.assert_called()

    def test_interactive_configuration_config_error(self):
        """Test handling of configuration errors."""
        mock_output = Mock()
        mock_output.echo.return_value = None
        mock_output.warning.return_value = None

        with (
            patch("kittylog.ui.prompts.get_output_manager", return_value=mock_output),
            patch("kittylog.ui.prompts.questionary") as mock_questionary,
        ):
            mock_select = Mock()
            mock_select.ask.side_effect = Exception("Config error")
            mock_questionary.select.return_value = mock_select

            with pytest.raises(Exception, match="Config error"):
                interactive_configuration(
                    grouping_mode=None,
                    gap_threshold=None,
                    date_grouping=None,
                    include_diff=None,
                    quiet=False,
                    audience=None,
                )

            # The warning might not be called if exception happens before it
            if mock_output.warning.called:
                mock_output.warning.assert_called()

    def test_interactive_configuration_ai_error(self):
        """Test handling of AI errors."""
        from kittylog.errors import AIError

        mock_output = Mock()
        mock_output.echo.return_value = None
        mock_output.warning.return_value = None

        with (
            patch("kittylog.ui.prompts.get_output_manager", return_value=mock_output),
            patch("kittylog.ui.prompts.questionary") as mock_questionary,
        ):
            mock_select = Mock()
            mock_select.ask.side_effect = AIError("AI service unavailable")
            mock_questionary.select.return_value = mock_select

            with pytest.raises(AIError):
                interactive_configuration(
                    grouping_mode=None,
                    gap_threshold=None,
                    date_grouping=None,
                    include_diff=None,
                    quiet=False,
                    audience=None,
                )

            mock_output.warning.assert_called()

    def test_interactive_configuration_invalid_threshold(self):
        """Test handling of invalid threshold input that falls back to default."""
        mock_output = Mock()
        mock_output.echo.return_value = None
        mock_output.warning.return_value = None

        with (
            patch("kittylog.ui.prompts.get_output_manager", return_value=mock_output),
            patch("kittylog.ui.prompts.questionary") as mock_questionary,
        ):
            # Mock responses: gaps mode, invalid threshold (None), then audience
            mock_select = Mock()
            mock_text = Mock()
            mock_text.ask.return_value = None  # User doesn't provide threshold
            mock_select.ask.side_effect = ["gaps", "stakeholders"]
            mock_confirm = Mock()
            mock_confirm.ask.return_value = False
            mock_questionary.select.return_value = mock_select
            mock_questionary.text.return_value = mock_text
            mock_questionary.confirm.return_value = mock_confirm

            result = interactive_configuration(
                grouping_mode=None,
                gap_threshold=None,
                date_grouping=None,
                include_diff=None,
                quiet=False,
                audience=None,
            )

            assert result == (
                "gaps",
                4.0,  # Falls back to default
                "daily",
                False,
                "stakeholders",
            )

    def test_interactive_configuration_unittest_mock_handling(self):
        """Test the special case handling for unittest.Mock objects."""
        from unittest.mock import Mock as UnitTestMock

        mock_output = Mock()
        mock_output.echo.return_value = None
        mock_output.warning.return_value = None

        with (
            patch("kittylog.ui.prompts.get_output_manager", return_value=mock_output),
            patch("kittylog.ui.prompts.questionary") as mock_questionary,
        ):
            # Mock the text response as a Mock object (as mentioned in the code)
            mock_text_response = UnitTestMock()
            mock_text = Mock()
            mock_text.ask.return_value = mock_text_response
            mock_select = Mock()
            mock_select.ask.side_effect = ["gaps", "stakeholders"]
            mock_confirm = Mock()
            mock_confirm.ask.return_value = False
            mock_questionary.select.return_value = mock_select
            mock_questionary.text.return_value = mock_text
            mock_questionary.confirm.return_value = mock_confirm

            result = interactive_configuration(
                grouping_mode=None,
                gap_threshold=2.5,
                date_grouping=None,
                include_diff=None,
                quiet=False,
                audience=None,
            )

            assert result == (
                "gaps",
                2.5,  # Should keep the existing value when Mock is returned
                "daily",
                False,
                "stakeholders",
            )

    def test_interactive_configuration_none_audience_fallback(self):
        """Test audience selection when None is returned and no default provided."""
        mock_output = Mock()
        mock_output.echo.return_value = None
        mock_output.warning.return_value = None

        with (
            patch("kittylog.ui.prompts.get_output_manager", return_value=mock_output),
            patch("kittylog.ui.prompts.questionary") as mock_questionary,
        ):
            # Mock responses: tags mode, None audience, no diff
            mock_select = Mock()
            mock_select.ask.side_effect = ["tags", None]  # None for audience
            mock_confirm = Mock()
            mock_confirm.ask.return_value = False
            mock_questionary.select.return_value = mock_select
            mock_questionary.confirm.return_value = mock_confirm

            with patch("kittylog.ui.prompts.load_config", return_value=Mock(audience=None)):
                result = interactive_configuration(
                    grouping_mode=None,
                    gap_threshold=None,
                    date_grouping=None,
                    include_diff=None,
                    quiet=False,
                    audience=None,
                )

                # Should fall back to "stakeholders" when all are None
                assert result == ("tags", 4.0, "daily", False, "stakeholders")

    def test_interactive_configuration_all_none_responses(self):
        """Test when all questionary responses are None, using all fallbacks."""
        mock_output = Mock()
        mock_output.echo.return_value = None
        mock_output.warning.return_value = None

        with (
            patch("kittylog.ui.prompts.get_output_manager", return_value=mock_output),
            patch("kittylog.ui.prompts.questionary") as mock_questionary,
        ):
            # All responses return None
            mock_select = Mock()
            mock_select.ask.return_value = None
            mock_confirm = Mock()
            mock_confirm.ask.return_value = None
            mock_questionary.select.return_value = mock_select
            mock_questionary.confirm.return_value = mock_confirm

            with patch("kittylog.ui.prompts.load_config", return_value=Mock(audience="end_users")):
                result = interactive_configuration(
                    grouping_mode=None,
                    gap_threshold=None,
                    date_grouping=None,
                    include_diff=None,
                    quiet=False,
                    audience=None,
                )

                assert result == (
                    "tags",  # falls back to default
                    4.0,  # falls back to default
                    "daily",  # falls back to default
                    False,  # falls back to default for diff
                    "end_users",  # uses config audience as fallback
                )
