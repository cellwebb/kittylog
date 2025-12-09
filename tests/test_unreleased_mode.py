"""Test suite for unreleased mode handler."""

from unittest import mock

import pytest

from kittylog.errors import AIError, GitError
from kittylog.mode_handlers.unreleased import handle_unreleased_mode


class TestHandleUnreleasedMode:
    """Test the handle_unreleased_mode function."""

    def test_skips_when_no_unreleased(self):
        """Test that function returns early when no_unreleased is True."""
        with (
            mock.patch("kittylog.changelog.io.read_changelog") as mock_read,
            mock.patch("kittylog.output.get_output_manager") as mock_output,
        ):
            mock_read.return_value = "# Changelog\n"
            mock_output_manager = mock.Mock()
            mock_output.return_value = mock_output_manager

            result_success, _result_content = handle_unreleased_mode(
                changelog_file="CHANGELOG.md", generate_entry_func=mock.Mock(), no_unreleased=True
            )

            assert result_success is True
            assert _result_content == "# Changelog\n"
            mock_output_manager.info.assert_called_once_with("Skipping unreleased section creation as requested")
            # Should not call any other functions
            mock_read.assert_called_once_with("CHANGELOG.md")

    def test_skips_when_current_commit_tagged(self):
        """Test that function returns early when current commit is tagged."""
        with (
            mock.patch("kittylog.changelog.io.read_changelog") as mock_read,
            mock.patch("kittylog.output.get_output_manager") as mock_output,
            mock.patch("kittylog.tag_operations.is_current_commit_tagged") as mock_is_tagged,
        ):
            mock_read.return_value = "# Changelog\n"
            mock_output_manager = mock.Mock()
            mock_output.return_value = mock_output_manager
            mock_is_tagged.return_value = True

            result_success, _result_content = handle_unreleased_mode(
                changelog_file="CHANGELOG.md", generate_entry_func=mock.Mock(), no_unreleased=False
            )

            assert result_success is True
            assert _result_content == "# Changelog\n"
            mock_output_manager.info.assert_called_once_with("Current commit is tagged, no unreleased changes needed")

    def test_skips_when_no_commits_since_last_tag(self):
        """Test that function returns early when no commits since last tag."""
        with (
            mock.patch("kittylog.changelog.io.read_changelog") as mock_read,
            mock.patch("kittylog.output.get_output_manager") as mock_output,
            mock.patch("kittylog.tag_operations.is_current_commit_tagged") as mock_is_tagged,
            mock.patch("kittylog.mode_handlers.unreleased.get_latest_tag") as mock_latest_tag,
            mock.patch("kittylog.mode_handlers.unreleased.get_commits_between_tags") as mock_get_commits,
        ):
            mock_read.return_value = "# Changelog\n"
            mock_output_manager = mock.Mock()
            mock_output.return_value = mock_output_manager
            mock_is_tagged.return_value = False
            mock_latest_tag.return_value = "v1.0.0"
            mock_get_commits.return_value = []

            result_success, _result_content = handle_unreleased_mode(
                changelog_file="CHANGELOG.md", generate_entry_func=mock.Mock(), no_unreleased=False
            )

            assert result_success is True
            assert _result_content == "# Changelog\n"
            mock_output_manager.info.assert_called_once_with("No new commits since last tag")

    def test_generates_and_inserts_entry_successfully(self):
        """Test successful entry generation and insertion."""
        with (
            mock.patch("kittylog.changelog.io.read_changelog") as mock_read,
            mock.patch("kittylog.output.get_output_manager") as mock_output,
            mock.patch("kittylog.tag_operations.is_current_commit_tagged") as mock_is_tagged,
            mock.patch("kittylog.mode_handlers.unreleased.get_latest_tag") as mock_latest_tag,
            mock.patch("kittylog.mode_handlers.unreleased.get_commits_between_tags") as mock_get_commits,
            mock.patch("kittylog.mode_handlers.unreleased.limit_bullets_in_sections") as mock_limit,
            mock.patch("kittylog.mode_handlers.unreleased._insert_unreleased_entry") as mock_insert,
            mock.patch("kittylog.changelog.io.write_changelog") as mock_write,
        ):
            # Setup mocks
            mock_read.return_value = "# Changelog\n"
            mock_output_manager = mock.Mock()
            mock_output.return_value = mock_output_manager
            mock_is_tagged.return_value = False
            mock_latest_tag.return_value = "v1.0.0"
            mock_commits = [mock.Mock(), mock.Mock()]
            mock_get_commits.return_value = mock_commits
            mock_limit.return_value = ["## [Unreleased]", "", "### Added", "- New feature"]
            # Mock the actual insertion result - this should be the existing content plus the new entry
            mock_insert.return_value = "# Changelog\n\n## [Unreleased]\n\n### Added\n- New feature"

            generate_func = mock.Mock()
            generate_func.return_value = "## [Unreleased]\n\n### Added\n- New feature"

            result_success, _result_content = handle_unreleased_mode(
                changelog_file="CHANGELOG.md",
                generate_entry_func=generate_func,
                no_unreleased=False,
                quiet=False,
                dry_run=False,
                incremental_save=True,
            )

            assert result_success is True
            # The result should contain the unreleased section
            assert "## [Unreleased]" in _result_content
            assert "### Added" in _result_content
            assert "- New feature" in _result_content

            # Verify function calls
            generate_func.assert_called_once_with(commits=mock_commits, tag="Unreleased")
            mock_limit.assert_called_once()
            mock_insert.assert_called_once_with("# Changelog\n", "## [Unreleased]\n\n### Added\n- New feature")
            mock_write.assert_called_once_with("CHANGELOG.md", mock_insert.return_value)
            mock_output_manager.debug.assert_called()
            mock_output_manager.info.assert_called_with(f"Found {len(mock_commits)} commits since last tag")
            mock_output_manager.success.assert_called_once_with("✓ Saved unreleased changelog entry")

    def test_handles_empty_ai_generated_content(self):
        """Test handling when AI generates empty content."""
        with (
            mock.patch("kittylog.changelog.io.read_changelog") as mock_read,
            mock.patch("kittylog.output.get_output_manager") as mock_output,
            mock.patch("kittylog.tag_operations.is_current_commit_tagged") as mock_is_tagged,
            mock.patch("kittylog.mode_handlers.unreleased.get_latest_tag") as mock_latest_tag,
            mock.patch("kittylog.mode_handlers.unreleased.get_commits_between_tags") as mock_get_commits,
        ):
            # Setup mocks
            mock_read.return_value = "# Changelog\n"
            mock_output_manager = mock.Mock()
            mock_output.return_value = mock_output_manager
            mock_is_tagged.return_value = False
            mock_latest_tag.return_value = "v1.0.0"
            mock_commits = [mock.Mock()]
            mock_get_commits.return_value = mock_commits

            generate_func = mock.Mock()
            generate_func.return_value = "   \n\t\n  "  # Whitespace only

            result_success, _result_content = handle_unreleased_mode(
                changelog_file="CHANGELOG.md", generate_entry_func=generate_func, no_unreleased=False
            )

            assert result_success is True
            assert _result_content == "# Changelog\n"
            generate_func.assert_called_once_with(commits=mock_commits, tag="Unreleased")
            mock_output_manager.warning.assert_called_once_with("AI generated empty content for unreleased section")

    def test_handles_dry_run_mode(self):
        """Test that content is not saved in dry run mode."""
        with (
            mock.patch("kittylog.changelog.io.read_changelog") as mock_read,
            mock.patch("kittylog.output.get_output_manager") as mock_output,
            mock.patch("kittylog.tag_operations.is_current_commit_tagged") as mock_is_tagged,
            mock.patch("kittylog.mode_handlers.unreleased.get_latest_tag") as mock_latest_tag,
            mock.patch("kittylog.mode_handlers.unreleased.get_commits_between_tags") as mock_get_commits,
            mock.patch("kittylog.mode_handlers.unreleased.limit_bullets_in_sections") as mock_limit,
            mock.patch("kittylog.mode_handlers.unreleased._insert_unreleased_entry") as mock_insert,
            mock.patch("kittylog.changelog.io.write_changelog") as mock_write,
        ):
            # Setup mocks
            mock_read.return_value = "# Changelog\n"
            mock_output_manager = mock.Mock()
            mock_output.return_value = mock_output_manager
            mock_is_tagged.return_value = False
            mock_latest_tag.return_value = "v1.0.0"
            mock_commits = [mock.Mock()]
            mock_get_commits.return_value = mock_commits
            mock_limit.return_value = ["## [Unreleased]", "", "### Added", "- New feature"]
            mock_insert.return_value = "updated content"

            generate_func = mock.Mock()
            generate_func.return_value = "## [Unreleased]\n\n### Added\n- New feature"

            result_success, _result_content = handle_unreleased_mode(
                changelog_file="CHANGELOG.md",
                generate_entry_func=generate_func,
                no_unreleased=False,
                quiet=True,
                dry_run=True,  # This should prevent saving
                incremental_save=True,
            )

            assert result_success is True
            assert _result_content == "updated content"

            # Should not write in dry run mode
            mock_write.assert_not_called()

    def test_handles_incremental_save_disabled(self):
        """Test that content is not saved when incremental_save is False."""
        with (
            mock.patch("kittylog.changelog.io.read_changelog") as mock_read,
            mock.patch("kittylog.output.get_output_manager") as mock_output,
            mock.patch("kittylog.tag_operations.is_current_commit_tagged") as mock_is_tagged,
            mock.patch("kittylog.mode_handlers.unreleased.get_latest_tag") as mock_latest_tag,
            mock.patch("kittylog.mode_handlers.unreleased.get_commits_between_tags") as mock_get_commits,
            mock.patch("kittylog.mode_handlers.unreleased.limit_bullets_in_sections") as mock_limit,
            mock.patch("kittylog.mode_handlers.unreleased._insert_unreleased_entry") as mock_insert,
            mock.patch("kittylog.changelog.io.write_changelog") as mock_write,
        ):
            # Setup mocks
            mock_read.return_value = "# Changelog\n"
            mock_output_manager = mock.Mock()
            mock_output.return_value = mock_output_manager
            mock_is_tagged.return_value = False
            mock_latest_tag.return_value = "v1.0.0"
            mock_commits = [mock.Mock()]
            mock_get_commits.return_value = mock_commits
            mock_limit.return_value = ["## [Unreleased]", "", "### Added", "- New feature"]
            mock_insert.return_value = "updated content"

            generate_func = mock.Mock()
            generate_func.return_value = "## [Unreleased]\n\n### Added\n- New feature"

            result_success, _result_content = handle_unreleased_mode(
                changelog_file="CHANGELOG.md",
                generate_entry_func=generate_func,
                no_unreleased=False,
                quiet=False,
                dry_run=False,
                incremental_save=False,  # This should prevent saving
            )

            assert result_success is True
            assert _result_content == "updated content"

            # Should not write when incremental_save is False
            mock_write.assert_not_called()

    @pytest.mark.parametrize("exception_class", [AIError, OSError, TimeoutError, ValueError, GitError])
    def test_handles_exceptions(self, exception_class):
        """Test that various exceptions are handled correctly."""
        with (
            mock.patch("kittylog.changelog.io.read_changelog") as mock_read,
            mock.patch("kittylog.output.get_output_manager") as mock_output,
            mock.patch("kittylog.tag_operations.is_current_commit_tagged") as mock_is_tagged,
            mock.patch("kittylog.mode_handlers.unreleased.get_latest_tag") as mock_latest_tag,
            mock.patch("kittylog.mode_handlers.unreleased.get_commits_between_tags") as mock_get_commits,
            mock.patch("kittylog.errors.handle_error") as mock_handle_error,
        ):
            # Setup mocks
            mock_read.return_value = "# Changelog\n"
            mock_output_manager = mock.Mock()
            mock_output.return_value = mock_output_manager
            mock_is_tagged.return_value = False
            mock_latest_tag.return_value = "v1.0.0"
            mock_commits = [mock.Mock()]
            mock_get_commits.return_value = mock_commits

            generate_func = mock.Mock()
            generate_func.side_effect = exception_class("Test error")

            result_success, _result_content = handle_unreleased_mode(
                changelog_file="CHANGELOG.md", generate_entry_func=generate_func, no_unreleased=False
            )

            assert result_success is False
            assert _result_content == "# Changelog\n"
            generate_func.assert_called_once_with(commits=mock_commits, tag="Unreleased")
            mock_handle_error.assert_called_once()
            # Check that handle_error was called with the correct exception
            mock_handle_error.assert_called_with(mock.ANY)
            # Verify the exception passed to handle_error is the expected type
            called_exception = mock_handle_error.call_args[0][0]
            assert isinstance(called_exception, exception_class)
            assert str(called_exception) == "Test error"

    def test_uses_kwargs_passed_to_generate_function(self):
        """Test that additional kwargs are passed to generate function."""
        with (
            mock.patch("kittylog.changelog.io.read_changelog") as mock_read,
            mock.patch("kittylog.output.get_output_manager") as mock_output,
            mock.patch("kittylog.tag_operations.is_current_commit_tagged") as mock_is_tagged,
            mock.patch("kittylog.mode_handlers.unreleased.get_latest_tag") as mock_latest_tag,
            mock.patch("kittylog.mode_handlers.unreleased.get_commits_between_tags") as mock_get_commits,
            mock.patch("kittylog.mode_handlers.unreleased.limit_bullets_in_sections") as mock_limit,
            mock.patch("kittylog.mode_handlers.unreleased._insert_unreleased_entry") as mock_insert,
        ):
            # Setup mocks
            mock_read.return_value = "# Changelog\n"
            mock_output_manager = mock.Mock()
            mock_output.return_value = mock_output_manager
            mock_is_tagged.return_value = False
            mock_latest_tag.return_value = "v1.0.0"
            mock_commits = [mock.Mock()]
            mock_get_commits.return_value = mock_commits
            mock_limit.return_value = ["## [Unreleased]", "", "### Added", "- New feature"]
            mock_insert.return_value = "updated content"

            generate_func = mock.Mock()
            generate_func.return_value = "## [Unreleased]\n\n### Added\n- New feature"

            result_success, _result_content = handle_unreleased_mode(
                changelog_file="CHANGELOG.md",
                generate_entry_func=generate_func,
                no_unreleased=False,
                dry_run=True,  # Prevent actual saving
                custom_arg="custom_value",
                another_kwarg=42,
            )

            assert result_success is True
            generate_func.assert_called_once_with(
                commits=mock_commits, tag="Unreleased", custom_arg="custom_value", another_kwarg=42
            )
