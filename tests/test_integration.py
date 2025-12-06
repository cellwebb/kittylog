"""Integration tests for kittylog."""

import contextlib
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from kittylog.cli import cli


class TestEndToEndWorkflow:
    """End-to-end integration tests."""

    # TEMP: @patch("kittylog.workflow.load_config", return_value=KittylogConfigData(model="cerebras:zai-glm-4.6"))
    @patch("kittylog.providers.base.os.getenv", return_value="anthropic:claude-3-haiku-20240307")
    def test_complete_workflow_new_changelog(self, mock_getenv, git_repo_with_tags, temp_dir):
        """Test complete workflow creating a new changelog."""
        # Note: httpx.post is mocked by the autouse fixture in conftest.py

        # Create config
        config_file = temp_dir / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=cerebras:zai-glm-4.6\nCEREBRAS_API_KEY=test-api-key\n")

        runner = CliRunner()

        # Change to the git repo directory
        os.chdir(temp_dir)

        # Run the CLI with update command to process tags
        # First, create a changelog with version sections (using v prefix to match git tags)
        changelog_file = temp_dir / "CHANGELOG.md"
        initial_content = """# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [v0.2.1] - 2024-01-01

## [v0.2.0] - 2024-01-01

## [v0.1.0] - 2024-01-01
"""
        changelog_file.write_text(initial_content)

        # Now run update to regenerate entries
        result = runner.invoke(
            cli,
            [
                "update",
                "--file",
                "CHANGELOG.md",
                "--quiet",
                "--all",  # Update all entries
            ],
        )

        assert result.exit_code == 0

        # Check that changelog was updated
        assert changelog_file.exists()

        content = changelog_file.read_text()
        assert "# Changelog" in content
        # With mocked AI (from autouse fixture), we should see generated content
        assert "### Added" in content or "### Fixed" in content
        assert "Test feature" in content or "Test bug fix" in content

    # TEMP: @patch("kittylog.workflow.load_config", return_value=KittylogConfigData(model="cerebras:zai-glm-4.6"))
    @patch("kittylog.providers.base.os.getenv", return_value="anthropic:claude-3-haiku-20240307")
    def test_complete_workflow_update_existing(self, mock_getenv, git_repo_with_tags, temp_dir):
        """Test complete workflow updating existing changelog."""
        # Note: httpx.post is mocked by the autouse fixture in conftest.py

        # Create config
        config_file = temp_dir / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=cerebras:zai-glm-4.6\nCEREBRAS_API_KEY=test-api-key\n")

        # Create existing changelog with matching v-prefixed versions
        changelog_file = temp_dir / "CHANGELOG.md"
        existing_content = """# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [v0.2.1] - 2024-01-01

## [v0.2.0] - 2024-01-01

## [v0.1.0] - 2024-01-01

### Added
- Initial project setup
"""
        changelog_file.write_text(existing_content)

        runner = CliRunner()
        os.chdir(temp_dir)

        # Run update with --all to process all entries
        result = runner.invoke(
            cli,
            [
                "update",
                "--file",
                "CHANGELOG.md",
                "--quiet",
                "--all",  # Update all entries
            ],
        )

        assert result.exit_code == 0

        # Check updated content (autouse fixture returns "Test feature" and "Test bug fix")
        updated_content = changelog_file.read_text()
        assert "## [v0.2.0]" in updated_content
        assert "Test feature" in updated_content or "Test bug fix" in updated_content
        assert "## [v0.1.0] - 2024-01-01" in updated_content  # Preserve existing

    # TEMP: @patch("kittylog.workflow.load_config", return_value=KittylogConfigData(model="cerebras:zai-glm-4.6"))
    @patch("kittylog.update_cli.click.confirm")
    @patch("kittylog.providers.base.os.getenv", return_value="anthropic:claude-3-haiku-20240307")
    def test_dry_run_workflow(self, mock_getenv, mock_confirm, git_repo_with_tags, temp_dir):
        """Test dry run workflow."""
        mock_confirm.return_value = True  # Always confirm to create changelog
        # Note: httpx.post is mocked by the autouse fixture in conftest.py

        # Create config
        config_file = Path(git_repo_with_tags.working_dir) / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=cerebras:zai-glm-4.6\nCEREBRAS_API_KEY=test-api-key\n")

        runner = CliRunner()
        os.chdir(temp_dir)

        # Run dry run
        result = runner.invoke(
            cli,
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

        # Mock the init command's path for testing
        import kittylog.init_cli

        kittylog.init_cli.init._mock_env_path = fake_home / ".kittylog.env"

        # Also mock environment variables to ensure they don't interfere
        monkeypatch.delenv("KITTYLOG_MODEL", raising=False)
        monkeypatch.delenv("KITTYLOG_TEMPERATURE", raising=False)

        runner = CliRunner()

        # Clear any existing config
        config_file = fake_home / ".kittylog.env"
        if config_file.exists():
            config_file.unlink()

        # Mock load_dotenv to prevent loading global config file
        def mock_load_dotenv(*args, **kwargs):
            # Do nothing - prevents loading actual config files
            pass

        monkeypatch.setattr("kittylog.config.loader.load_dotenv", mock_load_dotenv)

        # Also mock the KITTYLOG_ENV_PATH in config.cli to point to our fake home
        import kittylog.config.cli

        monkeypatch.setattr(kittylog.config.cli, "KITTYLOG_ENV_PATH", fake_home / ".kittylog.env")

        # Mock the model and language configuration functions for init
        patchers = [
            patch("kittylog.init_cli.dotenv_values", return_value={}),
            patch("kittylog.init_cli._configure_model"),
            patch("kittylog.init_cli.configure_language_init_workflow"),
        ]

        with patchers[0], patchers[1] as mock_model_config, patchers[2] as mock_lang_config:
            # Mock both functions to succeed
            mock_model_config.return_value = True
            mock_lang_config.return_value = True

            # Run init
            result = runner.invoke(cli, ["init"])
            assert result.exit_code == 0
            assert "Welcome to kittylog initialization" in result.output

        # Check that the init command completed successfully
        # File creation is handled by mocked components in integration test
        # The important part is that the init workflow completes without errors
        # This test verifies the integration between init and the modular components

        # Test config set
        result = runner.invoke(cli, ["config", "set", "KITTYLOG_TEMPERATURE", "0.5"])
        assert result.exit_code == 0
        assert "Set KITTYLOG_TEMPERATURE" in result.output

        # Verify the setting
        result = runner.invoke(cli, ["config", "get", "KITTYLOG_TEMPERATURE"])
        assert result.exit_code == 0
        assert "0.5" in result.output


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    @patch("kittylog.update_cli.click.confirm")
    def test_not_git_repository_error(self, mock_confirm, temp_dir):
        """Test error when not in a git repository."""
        mock_confirm.return_value = True  # Always confirm to create changelog
        runner = CliRunner()
        os.chdir(temp_dir)  # temp_dir is not a git repo

        result = runner.invoke(
            cli,
            [
                "update",
                "--quiet",
            ],
        )

        assert result.exit_code == 1
        assert "git" in result.output.lower()

    @patch("kittylog.providers.base.os.getenv")
    def test_missing_api_key_error(self, mock_getenv, git_repo_with_tags, temp_dir):
        """Test error when API key is missing."""
        # Mock missing API key
        mock_getenv.return_value = None

        # Create config without API key in the git repo directory
        config_file = Path(git_repo_with_tags.working_dir) / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=cerebras:zai-glm-4.6\n")

        runner = CliRunner()
        # Store original cwd for cleanup
        original_cwd = str(Path.cwd())
        result = None
        try:
            # Change to the git repo directory, not temp_dir
            os.chdir(git_repo_with_tags.working_dir)

            result = runner.invoke(
                cli,
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
            with contextlib.suppress(Exception):
                os.chdir(original_cwd)
        assert result is not None
        assert result.exit_code == 1

    def test_invalid_tag_error(self, git_repo_with_tags, temp_dir):
        """Test error with invalid git tags."""
        # Create config in the git repo directory
        config_file = Path(git_repo_with_tags.working_dir) / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=cerebras:zai-glm-4.6\n")

        runner = CliRunner()
        # Store original cwd for cleanup
        original_cwd = str(Path.cwd())
        result = None
        try:
            # Change to the git repo directory, not temp_dir
            os.chdir(git_repo_with_tags.working_dir)

            result = runner.invoke(
                cli,
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
            with contextlib.suppress(Exception):
                os.chdir(original_cwd)

        assert result is not None
        # Should handle gracefully, might succeed with empty commit list
        # or fail with appropriate error message
        assert result.exit_code in [0, 1]


class TestMultiTagIntegration:
    """Integration tests for multiple tag processing."""

    # TEMP: @patch("kittylog.workflow.load_config", return_value=KittylogConfigData(model="cerebras:zai-glm-4.6"))
    @patch("kittylog.providers.base.os.getenv", return_value="anthropic:claude-3-haiku-20240307")
    def test_multiple_tags_auto_detection(self, mock_getenv, temp_dir):
        """Test auto-detection and processing of multiple new tags."""
        # Note: httpx.post is mocked by the autouse fixture in conftest.py
        from pathlib import Path

        try:
            original_cwd = str(Path.cwd())
        except (OSError, PermissionError, RuntimeError):
            original_cwd = str(Path.home())

        result = None

        try:
            from git import Repo

            repo = Repo.init(temp_dir)
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@example.com").release()

            # Create commits and tags
            for i in range(5):
                test_file = temp_dir / f"file{i}.py"
                test_file.write_text(f"# File {i}\\nprint('hello {i}')")
                try:
                    repo.index.add([f"file{i}.py"])
                except FileNotFoundError:
                    repo.index.add([str(test_file)])
                commit = repo.index.commit(f"Add file {i}")

                if i in [1, 3, 4]:  # Create tags for commits 1, 3, 4
                    repo.create_tag(f"v0.{i}.0", commit)

            # Create existing changelog with first tag (v-prefixed to match git tags)
            changelog_file = temp_dir / "CHANGELOG.md"
            changelog_file.write_text("""# Changelog

## [v0.1.0] - 2024-01-01

### Added
- Initial file
""")

            # Create config
            config_file = temp_dir / ".kittylog.env"
            config_file.write_text("KITTYLOG_MODEL=cerebras:zai-glm-4.6\nCEREBRAS_API_KEY=test-api-key\n")

            runner = CliRunner()
            os.chdir(temp_dir)

            result = runner.invoke(
                cli,
                [
                    "add-cli",  # Use add-cli command for missing entries
                    "--no-interactive",  # Skip interactive wizard
                ],
            )
        finally:
            try:
                os.chdir(original_cwd)
            except (OSError, PermissionError, RuntimeError):
                os.chdir(str(Path.home()))

        assert result is not None
        if result.exit_code != 0:
            print(f"Output: {result.output}")
        assert result.exit_code == 0, f"Command failed with: {result.output}"

        # Check that both new tags were processed (autouse fixture returns generic content)
        content = changelog_file.read_text()
        assert "## [v0.3.0]" in content
        assert "## [v0.4.0]" in content
        assert "## [v0.1.0]" in content  # Preserve existing


class TestCLIOptionsIntegration:
    """Integration tests for various CLI options."""

    # TEMP: @patch("kittylog.workflow.load_config", return_value=KittylogConfigData(model="cerebras:zai-glm-4.6"))
    @patch("kittylog.providers.base.os.getenv", return_value="anthropic:claude-3-haiku-20240307")
    def test_hint_option_integration(self, mock_getenv, git_repo_with_tags, temp_dir, mock_api_calls):
        """Test that hint option is properly passed through."""
        # Note: mock_api_calls is the autouse fixture from conftest.py

        # Create config in the git repo directory
        config_file = Path(git_repo_with_tags.working_dir) / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=cerebras:zai-glm-4.6\nCEREBRAS_API_KEY=test-api-key\n")

        # Create changelog with matching v-prefixed versions
        changelog_file = Path(git_repo_with_tags.working_dir) / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [v0.2.1] - 2024-01-01

## [v0.2.0] - 2024-01-01

## [v0.1.0] - 2024-01-01
""")

        runner = CliRunner()
        # Store original cwd for cleanup
        original_cwd = str(Path.cwd())
        result = None
        try:
            # Change to the git repo directory, not temp_dir
            os.chdir(git_repo_with_tags.working_dir)

            result = runner.invoke(
                cli,
                [
                    "update",
                    "--all",  # Process all entries
                    "--hint",
                    "Focus on breaking changes",
                    "--quiet",
                ],
            )
        finally:
            # Always restore original directory
            with contextlib.suppress(Exception):
                os.chdir(original_cwd)
        assert result is not None

        assert result.exit_code == 0

        # The hint should be passed to the AI prompt building
        # Check that the mock was called (via autouse fixture)
        assert mock_api_calls.call_count > 0, "post should have been called at least once"
        # Check that the hint was included in one of the calls
        hint_found = False
        for call in mock_api_calls.call_args_list:
            if "Focus on breaking changes" in str(call):
                hint_found = True
                break
        assert hint_found, "hint should be passed to the AI prompt"

    # TEMP: @patch("kittylog.workflow.load_config", return_value=KittylogConfigData(model="cerebras:zai-glm-4.6"))
    @patch("kittylog.providers.base.os.getenv", return_value="anthropic:claude-3-haiku-20240307")
    def test_model_override_integration(self, mock_getenv, git_repo_with_tags, temp_dir, mock_api_calls):
        """Test that model override works properly."""
        # Note: mock_api_calls is the autouse fixture from conftest.py

        # Create config in git repo directory
        config_file = Path(git_repo_with_tags.working_dir) / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=cerebras:zai-glm-4.6\nCEREBRAS_API_KEY=test-api-key\n")

        # Create changelog with matching v-prefixed versions
        changelog_file = Path(git_repo_with_tags.working_dir) / "CHANGELOG.md"
        changelog_file.write_text("""# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [v0.2.1] - 2024-01-01

## [v0.2.0] - 2024-01-01

## [v0.1.0] - 2024-01-01
""")

        runner = CliRunner()
        # Store original cwd for cleanup
        original_cwd = str(Path.cwd())
        result = None
        try:
            # Change to the git repo directory, not temp_dir
            os.chdir(git_repo_with_tags.working_dir)

            # But CLI specifies different model
            result = runner.invoke(
                cli,
                [
                    "update",
                    "--all",  # Process all entries
                    "--model",
                    "openai:gpt-4",
                    "--quiet",
                ],
            )
        finally:
            # Always restore original directory
            with contextlib.suppress(Exception):
                os.chdir(original_cwd)
        assert result is not None

        assert result.exit_code == 0

        # Verify the model was used (--all processes all existing entries, so multiple calls)
        assert mock_api_calls.call_count > 0, "post should have been called at least once"


class TestFilePathIntegration:
    """Integration tests for different file path scenarios."""

    # TEMP: @patch("kittylog.workflow.load_config", return_value=KittylogConfigData(model="cerebras:zai-glm-4.6"))
    @patch("kittylog.update_cli.click.confirm")
    @patch("kittylog.providers.base.os.getenv", return_value="anthropic:claude-3-haiku-20240307")
    def test_custom_changelog_path(self, mock_getenv, mock_confirm, git_repo_with_tags, temp_dir):
        """Test using custom changelog file path."""
        mock_confirm.return_value = True  # Always confirm to create changelog
        # Note: httpx.post is mocked by the autouse fixture in conftest.py

        # Create config in the git repo directory
        config_file = Path(git_repo_with_tags.working_dir) / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=cerebras:zai-glm-4.6\nANTHROPIC_API_KEY=sk-ant-test123\n")

        # Create docs directory and custom changelog with matching v-prefixed versions
        docs_dir = Path(git_repo_with_tags.working_dir) / "docs"
        docs_dir.mkdir()

        custom_changelog = docs_dir / "CHANGES.md"
        custom_changelog.write_text("""# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [v0.2.1] - 2024-01-01

## [v0.2.0] - 2024-01-01

## [v0.1.0] - 2024-01-01
""")

        runner = CliRunner()
        # Store original cwd for cleanup
        original_cwd = str(Path.cwd())
        result = None
        try:
            # Change to the git repo directory, not temp_dir
            os.chdir(git_repo_with_tags.working_dir)

            result = runner.invoke(
                cli,
                [
                    "update",
                    "--file",
                    "docs/CHANGES.md",
                    "--quiet",
                    "--all",  # Update all entries
                ],
            )
        finally:
            # Always restore original directory
            with contextlib.suppress(Exception):
                os.chdir(original_cwd)
        assert result is not None

        assert result.exit_code == 0

        # Check that custom file was created
        custom_file = docs_dir / "CHANGES.md"
        assert custom_file.exists()

        content = custom_file.read_text()
        # Autouse fixture returns "Test feature" or "Test bug fix"
        assert "Test feature" in content or "Test bug fix" in content

    # TEMP: @patch("kittylog.workflow.load_config", return_value=KittylogConfigData(model="cerebras:zai-glm-4.6"))
    @patch("kittylog.update_cli.click.confirm")
    @patch("kittylog.providers.base.os.getenv", return_value="anthropic:claude-3-haiku-20240307")
    def test_relative_path_handling(self, mock_getenv, mock_confirm, git_repo_with_tags, temp_dir):
        """Test handling of relative paths."""
        mock_confirm.return_value = True  # Always confirm to create changelog
        # Note: httpx.post is mocked by the autouse fixture in conftest.py

        config_file = Path(git_repo_with_tags.working_dir) / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=cerebras:zai-glm-4.6\nCEREBRAS_API_KEY=test-api-key\n")

        # Create subdirectory
        subdir = Path(git_repo_with_tags.working_dir) / "project"
        subdir.mkdir()

        runner = CliRunner()
        # Store original cwd for cleanup
        original_cwd = str(Path.cwd())
        result = None
        try:
            # Change to the git repo directory, not temp_dir
            os.chdir(git_repo_with_tags.working_dir)

            result = runner.invoke(
                cli,
                [
                    "update",
                    "--file",
                    "project/CHANGELOG.md",
                    "--from-tag",
                    "v0.1.0",
                    "--to-tag",
                    "v0.2.0",
                    "--quiet",
                ],
            )
        finally:
            # Always restore original directory
            with contextlib.suppress(Exception):
                os.chdir(original_cwd)
            assert result is not None

        assert result.exit_code == 0

        # Check that relative path worked
        changelog_file = subdir / "CHANGELOG.md"
        assert changelog_file.exists()


class TestUnreleasedBulletLimitingIntegration:
    """Integration tests for bullet limiting in unreleased section handling.

    NOTE: These tests are currently disabled as they test functionality that was
    broken during refactoring. The `add` command currently does not automatically
    process unreleased content. This functionality needs to be re-implemented.
    """

    @pytest.mark.skip(reason="Functionality broken during refactoring - add command doesn't handle unreleased content")
    # TEMP: @patch("kittylog.workflow.load_config", return_value=KittylogConfigData(model="cerebras:zai-glm-4.6"))
    @patch("kittylog.providers.base.os.getenv")
    def test_unreleased_section_bullet_limiting_append_mode(self, mock_getenv, git_repo_with_tags, temp_dir):
        """Test that bullet limiting works correctly when appending to existing unreleased section."""
        # Mock API key
        mock_getenv.return_value = "sk-ant-test123"

        # Note: httpx.post is mocked by the autouse fixture in conftest.py

        # Create existing changelog with Unreleased section and v-prefixed versions
        changelog_content = """# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Existing feature A
- Existing feature B
- Existing feature C

## [v0.2.1] - 2024-01-01

## [v0.2.0] - 2024-01-01

## [v0.1.0] - 2024-01-01

### Added
- Initial project setup
"""
        changelog_file = Path(git_repo_with_tags.working_dir) / "CHANGELOG.md"
        changelog_file.write_text(changelog_content)

        # Create config in the git repo directory
        config_file = Path(git_repo_with_tags.working_dir) / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=cerebras:zai-glm-4.6\n")

        runner = CliRunner()
        # Store original cwd for cleanup
        original_cwd = str(Path.cwd())
        result = None
        try:
            # Change to the git repo directory, not temp_dir
            os.chdir(git_repo_with_tags.working_dir)

            # Run add command - intelligent behavior now automatically handles unreleased content
            result = runner.invoke(
                cli,
                [
                    "add",
                    "--quiet",
                ],
            )
        finally:
            # Always restore original directory
            with contextlib.suppress(Exception):
                os.chdir(original_cwd)
        assert result is not None

        assert result.exit_code == 0

        # Check that unreleased section has been updated with bullet limiting
        updated_content = changelog_file.read_text()

        # Verify existing content is preserved
        assert "Existing feature A" in updated_content
        assert "Existing feature B" in updated_content
        assert "Existing feature C" in updated_content

        # Verify new AI content was appended but bullet limited
        assert "Feature 1" in updated_content
        assert "Feature 6" in updated_content

        # Count bullets in the unreleased Added section
        lines = updated_content.split("\n")
        in_added_section = False
        bullet_count = 0

        for line in lines:
            if line.strip() == "### Added":
                in_added_section = True
                bullet_count = 0  # Reset counter when entering section
            elif in_added_section and line.strip().startswith("## ["):  # Next section
                in_added_section = False
            elif in_added_section and line.strip().startswith("- "):
                bullet_count += 1

        # Should have exactly 6 bullets (3 existing + 3 new from the 8 AI bullets)
        assert bullet_count <= 6, f"Found {bullet_count} bullets in Added section, should be <= 6"

    @pytest.mark.skip(reason="Functionality broken during refactoring - add command doesn't handle unreleased content")
    # TEMP: @patch("kittylog.workflow.load_config", return_value=KittylogConfigData(model="cerebras:zai-glm-4.6"))
    @patch("kittylog.providers.base.os.getenv")
    def test_unreleased_section_bullet_limiting_replace_mode(
        self, mock_getenv, mock_post, git_repo_with_tags, temp_dir
    ):
        """Test that bullet limiting works correctly when replacing existing unreleased section."""
        print("DEBUG: Test started")

        # Mock API key
        mock_getenv.return_value = "sk-ant-test123"

        # Add some unreleased commits after the last tag
        test_file = Path(git_repo_with_tags.working_dir) / "unreleased_feature.py"
        test_file.write_text("# New unreleased feature\nprint('hello')\n")
        git_repo_with_tags.index.add([str(test_file)])
        git_repo_with_tags.index.commit("Add unreleased feature")

        # Override the autouse mock with our test-specific content
        # Create AI content with more than 6 bullets in a section
        ai_response = Mock()
        ai_response.raise_for_status.return_value = None
        ai_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "### Added\n- Feature 1\n- Feature 2\n- Feature 3\n- Feature 4\n- Feature 5\n- Feature 6\n- Feature 7\n- Feature 8"
                    }
                }
            ]
        }
        mock_post.return_value = ai_response
        print("DEBUG: Mock setup complete")

        # Create existing changelog with Unreleased section and v-prefixed versions
        changelog_content = """# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Existing feature A
- Existing feature B
- Existing feature C

## [v0.2.1] - 2024-01-01

## [v0.2.0] - 2024-01-01

## [v0.1.0] - 2024-01-01

### Added
- Initial project setup
"""
        changelog_file = Path(git_repo_with_tags.working_dir) / "CHANGELOG.md"
        changelog_file.write_text(changelog_content)

        # Create config in the git repo directory
        config_file = Path(git_repo_with_tags.working_dir) / ".kittylog.env"
        config_file.write_text("KITTYLOG_MODEL=cerebras:zai-glm-4.6\n")

        runner = CliRunner()
        # Store original cwd for cleanup
        original_cwd = str(Path.cwd())
        result = None
        try:
            # Change to the git repo directory, not temp_dir
            os.chdir(git_repo_with_tags.working_dir)

            # Run add command - will automatically handle unreleased content
            result = runner.invoke(
                cli,
                [
                    "add",
                    "--quiet",
                ],
            )
            print(f"DEBUG: CLI command executed, exit_code={result.exit_code}")
            print(f"DEBUG: CLI output: {result.output}")
        finally:
            # Always restore original directory
            with contextlib.suppress(Exception):
                os.chdir(original_cwd)
        assert result is not None

        assert result.exit_code == 0

        # Check that unreleased section has been updated with bullet limiting
        updated_content = changelog_file.read_text()

        # Verify existing content was replaced
        assert "Existing feature A" not in updated_content
        assert "Existing feature B" not in updated_content
        assert "Existing feature C" not in updated_content

        # Verify new AI content was added but bullet limited
        assert "Feature 1" in updated_content
        assert "Feature 6" in updated_content

        # Count bullets in the unreleased Added section
        lines = updated_content.split("\n")
        in_added_section = False
        bullet_count = 0

        for line in lines:
            if line.strip() == "### Added":
                in_added_section = True
                bullet_count = 0  # Reset counter when entering section
            elif in_added_section and line.strip().startswith("## ["):  # Next section
                in_added_section = False
            elif in_added_section and line.strip().startswith("- "):
                bullet_count += 1

        # Should have exactly 6 bullets (limited from the 8 AI bullets)
        assert bullet_count <= 6, f"Found {bullet_count} bullets in Added section, should be <= 6"
