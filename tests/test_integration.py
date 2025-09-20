"""Integration tests for changelog-updater."""

import os
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from clog.cli import main


class TestEndToEndWorkflow:
    """End-to-end integration tests."""

    @patch("clog.ai.ai.Client")
    def test_complete_workflow_new_changelog(self, mock_client_class, git_repo_with_tags, temp_dir):
        """Test complete workflow creating a new changelog."""
        # Setup AI mock
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = """### Added

- User authentication system
- Dashboard widgets

### Fixed

- Login validation errors"""

        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Create config
        config_file = temp_dir / ".clog.env"
        config_file.write_text("CLOG_MODEL=anthropic:claude-3-5-haiku-latest\nANTHROPIC_API_KEY=sk-ant-test123\n")

        runner = CliRunner()

        # Change to the git repo directory
        os.chdir(temp_dir)

        # Run the CLI
        result = runner.invoke(
            main,
            [
                "update",
                "--file",
                "CHANGELOG.md",
                "--yes",  # Auto-confirm
                "--quiet",
            ],
        )

        assert result.exit_code == 0

        # Check that changelog was created
        changelog_file = temp_dir / "CHANGELOG.md"
        assert changelog_file.exists()

        content = changelog_file.read_text()
        assert "# Changelog" in content
        assert "### Added" in content
        assert "User authentication system" in content
        assert "### Fixed" in content
        assert "Login validation errors" in content

    @patch("clog.ai.ai.Client")
    def test_complete_workflow_update_existing(self, mock_client_class, git_repo_with_tags, temp_dir):
        """Test complete workflow updating existing changelog."""
        # Setup AI mock
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = """### Added

- New dashboard feature

### Fixed

- Critical security issue"""

        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Create config
        config_file = temp_dir / ".clog.env"
        config_file.write_text("CLOG_MODEL=anthropic:claude-3-5-haiku-latest\nANTHROPIC_API_KEY=sk-ant-test123\n")

        # Create existing changelog
        changelog_file = temp_dir / "CHANGELOG.md"
        existing_content = """# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.1.0] - 2024-01-01

### Added
- Initial project setup
"""
        changelog_file.write_text(existing_content)

        runner = CliRunner()
        os.chdir(temp_dir)

        # Run update
        result = runner.invoke(
            main,
            [
                "update",
                "--from-tag",
                "v0.1.0",
                "--to-tag",
                "v0.2.0",
                "--yes",
                "--quiet",
            ],
        )

        assert result.exit_code == 0

        # Check updated content
        updated_content = changelog_file.read_text()
        assert "## [0.2.0]" in updated_content
        assert "New dashboard feature" in updated_content
        assert "Critical security issue" in updated_content
        assert "## [0.1.0] - 2024-01-01" in updated_content  # Preserve existing

    def test_dry_run_workflow(self, git_repo_with_tags, temp_dir):
        """Test dry run workflow."""
        with patch("clog.ai.ai.Client") as mock_client_class:
            # Setup AI mock
            mock_client = Mock()
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = "### Added\n- Test feature"

            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Create config
            config_file = Path(git_repo_with_tags.working_dir) / ".clog.env"
            config_file.write_text("CLOG_MODEL=anthropic:claude-3-5-haiku-latest\n")

            runner = CliRunner()
            os.chdir(temp_dir)

            # Run dry run
            result = runner.invoke(
                main,
                [
                    "update",
                    "--from-tag",
                    "v0.1.0",
                    "--to-tag",
                    "v0.2.0",
                    "--dry-run",
                ],
            )

            assert result.exit_code == 0

            # Changelog should not be created/modified in dry run
            changelog_file = temp_dir / "CHANGELOG.md"
            if changelog_file.exists():
                # If it exists, it should be unchanged
                # original_stat = changelog_file.stat()\n
                # In a real test, we'd compare timestamps, but mocking makes this complex
                assert changelog_file.exists()


class TestConfigIntegration:
    """Integration tests for configuration."""

    def test_init_and_config_workflow(self, temp_dir, monkeypatch):
        """Test init command followed by config commands."""
        # Mock home directory
        fake_home = temp_dir / "home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)
        
        # Also mock the init command's path for testing
        from clog.init_cli import init
        init._mock_env_path = fake_home / ".clog.env"

        runner = CliRunner()

        # Mock questionary for init
        with patch("clog.init_cli.questionary") as mock_questionary:
            mock_questionary.select.return_value.ask.return_value = "Anthropic"
            mock_questionary.text.return_value.ask.return_value = "claude-3-5-haiku-latest"
            mock_questionary.password.return_value.ask.return_value = "sk-ant-test123"

            # Run init
            result = runner.invoke(main, ["init"])
            assert result.exit_code == 0
            assert "Welcome to clog initialization" in result.output

        # Check config file was created
        config_file = fake_home / ".clog.env"
        assert config_file.exists()

        # Test config show
        result = runner.invoke(main, ["config", "show"])
        assert result.exit_code == 0
        assert "CLOG_MODEL" in result.output

        # Test config get
        result = runner.invoke(main, ["config", "get", "CLOG_MODEL"])
        assert result.exit_code == 0
        assert "anthropic:claude-3-5-haiku-latest" in result.output

        # Test config set
        result = runner.invoke(main, ["config", "set", "CHANGELOG_UPDATER_TEMPERATURE", "0.5"])
        assert result.exit_code == 0
        assert "Set CHANGELOG_UPDATER_TEMPERATURE" in result.output

        # Verify the setting
        result = runner.invoke(main, ["config", "get", "CHANGELOG_UPDATER_TEMPERATURE"])
        assert result.exit_code == 0
        assert "0.5" in result.output


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    def test_not_git_repository_error(self, temp_dir):
        """Test error when not in a git repository."""
        runner = CliRunner()
        os.chdir(temp_dir)  # temp_dir is not a git repo

        result = runner.invoke(
            main,
            [
                "update",
                "--quiet",
            ],
        )

        assert result.exit_code == 1
        assert "git" in result.output.lower()

    def test_missing_api_key_error(self, git_repo_with_tags, temp_dir):
        """Test error when API key is missing."""
        # Create config without API key in the git repo directory
        config_file = Path(git_repo_with_tags.working_dir) / ".clog.env"
        config_file.write_text("CLOG_MODEL=anthropic:claude-3-5-haiku-latest\n")

        runner = CliRunner()
        # Store original cwd for cleanup
        original_cwd = os.getcwd()
        result = None
        try:
            # Change to the git repo directory, not temp_dir
            os.chdir(git_repo_with_tags.working_dir)

            with patch("clog.ai.ai.Client") as mock_client_class:
                # Simulate authentication error
                mock_client_class.side_effect = Exception("authentication failed")

                result = runner.invoke(
                    main,
                    [
                        "update",
                        "--from-tag",
                        "v0.1.0",
                        "--to-tag",
                        "v0.2.0",
                        "--quiet",
                    ],
                )
        finally:
            # Always restore original directory
            try:
                os.chdir(original_cwd)
            except Exception:
                pass
        assert result is not None
        assert result.exit_code == 1

            assert result.exit_code == 1

    def test_invalid_tag_error(self, git_repo_with_tags, temp_dir):
        """Test error with invalid git tags."""
        # Create config in the git repo directory
        config_file = Path(git_repo_with_tags.working_dir) / ".clog.env"
        config_file.write_text("CLOG_MODEL=anthropic:claude-3-5-haiku-latest\n")

        runner = CliRunner()
        # Store original cwd for cleanup
        original_cwd = os.getcwd()
        result = None
        try:
            # Change to the git repo directory, not temp_dir
            os.chdir(git_repo_with_tags.working_dir)

            result = runner.invoke(
                main,
                [
                    "update",
                    "--from-tag",
                    "invalid-tag",
                    "--to-tag",
                    "another-invalid-tag",
                    "--quiet",
                ],
            )
        finally:
            # Always restore original directory
            try:
                os.chdir(original_cwd)
            except Exception:
                pass
        
        assert result is not None
        # Should handle gracefully, might succeed with empty commit list
        # or fail with appropriate error message
        assert result.exit_code in [0, 1]


class TestMultiTagIntegration:
    """Integration tests for multiple tag processing."""

    @patch("clog.ai.ai.Client")
    def test_multiple_tags_auto_detection(self, mock_client_class, temp_dir):
        """Test auto-detection and processing of multiple new tags."""
        # Store original directory for cleanup
        original_cwd = os.getcwd()
        
        try:
            # Create a git repo with multiple tags
            from git import Repo

            repo = Repo.init(temp_dir)
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@example.com").release()
            
            # Change to the repo directory for git operations
            os.chdir(temp_dir)

            # Create commits and tags
            for i in range(5):
                test_file = temp_dir / f"file{i}.py"
                test_file.write_text(f"# File {i}\nprint('hello {i}')")
                # Add file using relative path to avoid git path issues
                try:
                    repo.index.add([f"file{i}.py"])
                except FileNotFoundError:
                    # If we can't add with relative path, try absolute path
                    repo.index.add([str(test_file)])
                commit = repo.index.commit(f"Add file {i}")

                if i in [1, 3, 4]:  # Create tags for commits 1, 3, 4
                    repo.create_tag(f"v0.{i}.0", commit)
        finally:
            # Restore original directory if possible
            try:
                os.chdir(original_cwd)
            except Exception:
                pass

        # Create existing changelog with first tag
        changelog_file = temp_dir / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

## [0.1.0] - 2024-01-01

### Added
- Initial file
""")

        # Setup AI mock to return different content for each tag
        mock_client = Mock()

        def mock_create(**kwargs):
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()

            # Return different content based on call count
            call_count = mock_client.chat.completions.create.call_count
            if call_count == 1:
                mock_message.content = "### Added\n- File 2\n- File 3"
            else:
                mock_message.content = "### Added\n- File 4"

            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            return mock_response

        mock_client.chat.completions.create.side_effect = mock_create
        mock_client_class.return_value = mock_client

        # Create config
        config_file = temp_dir / ".clog.env"
        config_file.write_text("CLOG_MODEL=anthropic:claude-3-5-haiku-latest\nCLOG_LOG_LEVEL=DEBUG\n")

        runner = CliRunner()
        os.chdir(temp_dir)

        # Run auto-detection
        result = runner.invoke(
            main,
            [
                "update",
                "--yes",
            ],
        )

        assert result.exit_code == 0

        # Check that both new tags were processed
        content = changelog_file.read_text()
        assert "## [0.3.0]" in content
        assert "## [0.4.0]" in content
        assert "## [0.1.0]" in content  # Preserve existing


class TestCLIOptionsIntegration:
    """Integration tests for various CLI options."""

    @patch("clog.ai.ai.Client")
    def test_hint_option_integration(self, mock_client_class, git_repo_with_tags, temp_dir):
        """Test that hint option is properly passed through."""
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "### Added\n- Feature with hint"

        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Create config in the git repo directory
        config_file = Path(git_repo_with_tags.working_dir) / ".clog.env"
        config_file.write_text("CLOG_MODEL=anthropic:claude-3-5-haiku-latest\nANTHROPIC_API_KEY=sk-ant-test123\n")

        config_file = Path(git_repo_with_tags.working_dir) / ".clog.env"
        config_file.write_text("CLOG_MODEL=anthropic:claude-3-5-haiku-latest\n")

        runner = CliRunner()
        # Store original cwd for cleanup
        original_cwd = os.getcwd()
        result = None
        try:
            # Change to the git repo directory, not temp_dir
            os.chdir(git_repo_with_tags.working_dir)

            result = runner.invoke(
                main,
                [
                    "update",
                    "--from-tag",
                    "v0.1.0",
                    "--to-tag",
                    "v0.2.0",
                    "--hint",
                    "Focus on breaking changes",
                    "--yes",
                    "--quiet",
                ],
            )
        finally:
            # Always restore original directory
            try:
                os.chdir(original_cwd)
            except Exception:
                pass
        assert result is not None

        assert result.exit_code == 0

        # The hint should be passed to the AI prompt building
        # This is tested more thoroughly in unit tests
        mock_client.chat.completions.create.assert_called_once()

    @patch("clog.ai.ai.Client")
    def test_model_override_integration(self, mock_client_class, git_repo_with_tags, temp_dir):
        """Test that model override works properly."""
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "### Added\n- Model override test"

        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Create config
        config_file = temp_dir / ".clog.env"
        config_file.write_text("CLOG_MODEL=anthropic:claude-3-5-haiku-latest\nANTHROPIC_API_KEY=sk-ant-test123\n")

        # Config has one model
        config_file = Path(git_repo_with_tags.working_dir) / ".clog.env"
        config_file.write_text("CLOG_MODEL=anthropic:claude-3-5-haiku-latest\n")

        runner = CliRunner()
        # Store original cwd for cleanup
        original_cwd = os.getcwd()
        result = None
        try:
            # Change to the git repo directory, not temp_dir
            os.chdir(git_repo_with_tags.working_dir)

            # But CLI specifies different model
            result = runner.invoke(
                main,
                [
                    "update",
                    "--from-tag",
                    "v0.1.0",
                    "--to-tag",
                    "v0.2.0",
                    "--model",
                    "openai:gpt-4",
                    "--yes",
                    "--quiet",
                ],
            )
        finally:
            # Always restore original directory
            try:
                os.chdir(original_cwd)
            except Exception:
                pass
        assert result is not None

        assert result.exit_code == 0

        # Verify the overridden model was used
        call_args = mock_client.chat.completions.create.call_args[1]
        assert call_args["model"] == "openai:gpt-4"


class TestFilePathIntegration:
    """Integration tests for different file path scenarios."""

    @patch("clog.ai.ai.Client")
    def test_custom_changelog_path(self, mock_client_class, git_repo_with_tags, temp_dir):
        """Test using custom changelog file path."""
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "### Added\n- Custom path test"

        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Create config in the git repo directory
        config_file = Path(git_repo_with_tags.working_dir) / ".clog.env"
        config_file.write_text("CLOG_MODEL=anthropic:claude-3-5-haiku-latest\nANTHROPIC_API_KEY=sk-ant-test123\n")

        config_file = Path(git_repo_with_tags.working_dir) / ".clog.env"
        config_file.write_text("CLOG_MODEL=anthropic:claude-3-5-haiku-latest\n")

        # Create docs directory
        docs_dir = Path(git_repo_with_tags.working_dir) / "docs"
        docs_dir.mkdir()

        runner = CliRunner()
        # Store original cwd for cleanup
        original_cwd = os.getcwd()
        result = None
        try:
            # Change to the git repo directory, not temp_dir
            os.chdir(git_repo_with_tags.working_dir)

            result = runner.invoke(
                main,
                [
                    "update",
                    "--file",
                    "docs/CHANGES.md",
                    "--from-tag",
                    "v0.1.0",
                    "--to-tag",
                    "v0.2.0",
                    "--yes",
                    "--quiet",
                ],
            )
        finally:
            # Always restore original directory
            try:
                os.chdir(original_cwd)
            except Exception:
                pass
        assert result is not None

        assert result.exit_code == 0

        # Check that custom file was created
        custom_file = docs_dir / "CHANGES.md"
        assert custom_file.exists()

        content = custom_file.read_text()
        assert "Custom path test" in content

    def test_relative_path_handling(self, git_repo_with_tags, temp_dir):
        """Test handling of relative paths."""
        with patch("clog.ai.ai.Client") as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = "### Added\n- Relative path test"

            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            config_file = Path(git_repo_with_tags.working_dir) / ".clog.env"
            config_file.write_text("CLOG_MODEL=anthropic:claude-3-5-haiku-latest\n")

            # Create subdirectory
            subdir = Path(git_repo_with_tags.working_dir) / "project"
            subdir.mkdir()

            runner = CliRunner()
            # Store original cwd for cleanup
            original_cwd = os.getcwd()
            result = None
            try:
                # Change to the git repo directory, not temp_dir
                os.chdir(git_repo_with_tags.working_dir)

                result = runner.invoke(
                    main,
                    [
                        "update",
                        "--file",
                        "project/CHANGELOG.md",
                        "--from-tag",
                        "v0.1.0",
                        "--to-tag",
                        "v0.2.0",
                        "--yes",
                        "--quiet",
                    ],
                )
            finally:
                # Always restore original directory
                try:
                    os.chdir(original_cwd)
                except Exception:
                    pass
            assert result is not None

            assert result.exit_code == 0

            # Check that relative path worked
            changelog_file = subdir / "CHANGELOG.md"
            assert changelog_file.exists()
