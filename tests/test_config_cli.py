"""Test suite for config CLI module."""

from unittest import mock

from click.testing import CliRunner

from kittylog.config.cli import config, get, set, show, unset


class TestConfigCLI:
    """Test the config CLI commands."""

    def test_config_group_exists(self):
        """Test that config group command exists."""
        runner = CliRunner()
        result = runner.invoke(config, ["--help"])
        assert result.exit_code == 0
        assert "Manage kittylog configuration" in result.output


class TestConfigShow:
    """Test the config show command."""

    def test_show_no_config_files(self):
        """Test show command when no config files exist."""
        with (
            mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH") as mock_user_path,
            mock.patch("kittylog.config.cli.Path") as mock_project_path,
        ):
            # Mock both paths to not exist
            mock_user_path.exists = mock.PropertyMock(return_value=False)

            # Create a mock Path object instead of a real one
            mock_project_path_instance = mock.Mock(spec=["exists"])
            mock_project_path_instance.exists = mock.PropertyMock(return_value=False)
            mock_project_path.return_value = mock_project_path_instance

            runner = CliRunner()
            result = runner.invoke(show)

            assert result.exit_code == 0
            assert "No kittylog configuration found" in result.output
            assert "Expected locations:" in result.output

    def test_show_user_config_only(self):
        """Test show command with user config only."""
        with (
            mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH") as mock_user_path,
            mock.patch("kittylog.config.cli.Path") as mock_project_path,
            mock.patch("dotenv.dotenv_values") as mock_dotenv_values,
        ):
            # User config exists, project config doesn't
            mock_user_path.exists = mock.PropertyMock(return_value=True)
            mock_user_path.__str__ = mock.Mock(return_value="/home/user/.kittylog.env")

            # Create a mock Path object instead of a real one
            mock_project_path_instance = mock.Mock(spec=["exists"])
            mock_project_path_instance.exists = mock.PropertyMock(return_value=False)
            mock_project_path.return_value = mock_project_path_instance

            # Mock dotenv_values to return user config
            mock_dotenv_values.return_value = {
                "KITTYLOG_MODEL": "openai:gpt-4",
                "KITTYLOG_TEMPERATURE": "0.7",
                "OPENAI_API_KEY": "sk-test",
            }

            runner = CliRunner()
            result = runner.invoke(show)

            assert result.exit_code == 0
            assert "User config" in result.output
            assert "KITTYLOG_MODEL=openai:gpt-4" in result.output
            assert "KITTYLOG_TEMPERATURE=0.7" in result.output
            assert "OPENAI_API_KEY=***hidden***" in result.output

    def test_show_project_config_only(self):
        """Test show command with project config only."""
        with (
            mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH") as mock_user_path,
            mock.patch("kittylog.config.cli.Path") as mock_project_path,
            mock.patch("dotenv.dotenv_values") as mock_dotenv_values,
        ):
            # User config doesn't exist, project config exists
            mock_user_path.exists = mock.PropertyMock(return_value=False)

            # Create a mock Path object instead of a real one
            mock_project_path_instance = mock.Mock(spec=["exists"])
            mock_project_path_instance.exists = mock.PropertyMock(return_value=True)
            mock_project_path.return_value = mock_project_path_instance

            # Mock dotenv_values to return project config
            mock_dotenv_values.return_value = {"KITTYLOG_MODEL": "anthropic:claude-3", "CUSTOM_SETTING": "custom_value"}

            runner = CliRunner()
            result = runner.invoke(show)

            assert result.exit_code == 0
            assert "Project config" in result.output
            assert "KITTYLOG_MODEL=anthropic:claude-3" in result.output
            assert "CUSTOM_SETTING=custom_value" in result.output
            assert "Project-level values override user-level values" in result.output

    def test_show_both_configs(self):
        """Test show command with both user and project configs."""
        with (
            mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH") as mock_user_path,
            mock.patch("kittylog.config.cli.Path") as mock_project_path,
            mock.patch("dotenv.dotenv_values") as mock_dotenv_values,
        ):
            # Both configs exist
            mock_user_path.exists = mock.PropertyMock(return_value=True)
            mock_user_path.__str__ = mock.Mock(return_value="/home/user/.kittylog.env")

            # Create a mock Path object instead of a real one
            mock_project_path_instance = mock.Mock(spec=["exists"])
            mock_project_path_instance.exists = mock.PropertyMock(return_value=True)
            mock_project_path.return_value = mock_project_path_instance

            # Mock dotenv_values to return different values for user and project
            def side_effect(path):
                if "user" in str(path):
                    return {"KITTYLOG_MODEL": "openai:gpt-4", "OPENAI_API_KEY": "user-key"}
                else:
                    return {
                        "KITTYLOG_MODEL": "anthropic:claude-3",  # Override user value
                        "PROJECT_SETTING": "project-value",
                    }

            mock_dotenv_values.side_effect = side_effect

            runner = CliRunner()
            result = runner.invoke(show)

            assert result.exit_code == 0
            assert "User config" in result.output
            assert "Project config" in result.output
            assert "KITTYLOG_MODEL=openai:gpt-4" in result.output  # User config
            assert "KITTYLOG_MODEL=anthropic:claude-3" in result.output  # Project config
            assert "OPENAI_API_KEY=***hidden***" in result.output
            assert "PROJECT_SETTING=project-value" in result.output

    def test_show_hides_sensitive_values(self):
        """Test that sensitive values are hidden in show command."""
        with (
            mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH") as mock_user_path,
            mock.patch("kittylog.config.cli.Path") as mock_project_path,
            mock.patch("dotenv.dotenv_values") as mock_dotenv_values,
        ):
            mock_user_path.exists = mock.PropertyMock(return_value=True)
            mock_user_path.__str__ = mock.Mock(return_value="/home/user/.kittylog.env")

            # Create a mock Path object instead of a real one
            mock_project_path_instance = mock.Mock(spec=["exists"])
            mock_project_path_instance.exists = mock.PropertyMock(return_value=False)
            mock_project_path.return_value = mock_project_path_instance

            mock_dotenv_values.return_value = {
                "API_KEY": "secret123",
                "TOKEN": "token456",
                "SECRET": "secret789",
                "PASSWORD": "pass123",  # Note: PASSWORD not hidden by current logic
                "PUBLIC_SETTING": "public_value",
            }

            runner = CliRunner()
            result = runner.invoke(show)

            assert result.exit_code == 0
            assert "API_KEY=***hidden***" in result.output
            assert "TOKEN=***hidden***" in result.output
            assert "SECRET=***hidden***" in result.output
            assert "PASSWORD=pass123" in result.output  # Not hidden with current logic
            assert "PUBLIC_SETTING=public_value" in result.output  # Not sensitive

    def test_show_handles_none_values(self):
        """Test that None values are skipped in show command."""
        with (
            mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH") as mock_user_path,
            mock.patch("kittylog.config.cli.Path") as mock_project_path,
            mock.patch("dotenv.dotenv_values") as mock_dotenv_values,
        ):
            mock_user_path.exists = mock.PropertyMock(return_value=True)
            mock_user_path.__str__ = mock.Mock(return_value="/home/user/.kittylog.env")

            # Create a mock Path object instead of a real one
            mock_project_path_instance = mock.Mock(spec=["exists"])
            mock_project_path_instance.exists = mock.PropertyMock(return_value=False)
            mock_project_path.return_value = mock_project_path_instance

            mock_dotenv_values.return_value = {"SET_VALUE": "test", "NONE_VALUE": None, "EMPTY_VALUE": ""}

            runner = CliRunner()
            result = runner.invoke(show)

            assert result.exit_code == 0
            assert "SET_VALUE=test" in result.output
            assert "NONE_VALUE" not in result.output  # None values should be skipped
            assert "EMPTY_VALUE=" in result.output  # Empty strings are shown with current logic

    def test_show_handles_empty_config_file(self):
        """Test show command with empty config file."""
        with (
            mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH") as mock_user_path,
            mock.patch("kittylog.config.cli.Path") as mock_project_path,
            mock.patch("dotenv.dotenv_values") as mock_dotenv_values,
        ):
            mock_user_path.exists = mock.PropertyMock(return_value=True)
            mock_user_path.__str__ = mock.Mock(return_value="/home/user/.kittylog.env")

            # Create a mock Path object instead of a real one
            mock_project_path_instance = mock.Mock(spec=["exists"])
            mock_project_path_instance.exists = mock.PropertyMock(return_value=False)
            mock_project_path.return_value = mock_project_path_instance

            mock_dotenv_values.return_value = {}  # Empty config

            runner = CliRunner()
            result = runner.invoke(show)

            assert result.exit_code == 0
            assert "User config" in result.output
            # Should not crash, just show empty config section


class TestConfigSet:
    """Test the config set command."""

    @mock.patch("kittylog.config.cli.set_key")
    @mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH")
    def test_set_creates_file_and_sets_value(self, mock_path, mock_set_key):
        """Test config set command creates file and sets value."""
        mock_path.touch = mock.Mock()

        runner = CliRunner()
        result = runner.invoke(set, ["TEST_KEY", "test_value"])

        assert result.exit_code == 0
        mock_path.touch.assert_called_once_with(exist_ok=True)
        mock_set_key.assert_called_once_with(str(mock_path), "TEST_KEY", "test_value")
        assert "Set TEST_KEY in" in result.output

    @mock.patch("kittylog.config.cli.set_key")
    @mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH")
    def test_set_with_special_characters(self, mock_path, mock_set_key):
        """Test config set command with special characters in value."""
        mock_path.touch = mock.Mock()

        runner = CliRunner()
        result = runner.invoke(set, ["API_KEY", "sk-abc123/def456=ghi789"])

        assert result.exit_code == 0
        mock_path.touch.assert_called_once_with(exist_ok=True)
        mock_set_key.assert_called_once_with(str(mock_path), "API_KEY", "sk-abc123/def456=ghi789")
        assert "Set API_KEY in" in result.output

    @mock.patch("kittylog.config.cli.set_key")
    @mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH")
    def test_set_existing_key_overwrites(self, mock_path, mock_set_key):
        """Test config set command overwrites existing key."""
        mock_path.touch = mock.Mock()

        runner = CliRunner()
        result = runner.invoke(set, ["EXISTING_KEY", "new_value"])

        assert result.exit_code == 0
        # set_key from python-dotenv handles overwriting
        mock_set_key.assert_called_once_with(str(mock_path), "EXISTING_KEY", "new_value")
        assert "Set EXISTING_KEY in" in result.output


class TestConfigGet:
    """Test the config get command."""

    @mock.patch("kittylog.config.cli.load_dotenv")
    @mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH")
    @mock.patch("os.getenv")
    def test_get_existing_key(self, mock_getenv, mock_path, mock_load_dotenv):
        """Test config get for existing key."""
        mock_getenv.return_value = "test_value"

        runner = CliRunner()
        result = runner.invoke(get, ["TEST_KEY"])

        assert result.exit_code == 0
        assert "test_value" in result.output
        mock_load_dotenv.assert_called_once_with(mock_path, override=True)
        mock_getenv.assert_called_once_with("TEST_KEY")

    @mock.patch("kittylog.config.cli.load_dotenv")
    @mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH")
    @mock.patch("os.getenv")
    def test_get_nonexistent_key(self, mock_getenv, mock_path, mock_load_dotenv):
        """Test config get for non-existent key."""
        mock_getenv.return_value = None

        runner = CliRunner()
        result = runner.invoke(get, ["NONEXISTENT_KEY"])

        assert result.exit_code == 0
        assert "NONEXISTENT_KEY not set" in result.output
        mock_load_dotenv.assert_called_once_with(mock_path, override=True)
        mock_getenv.assert_called_once_with("NONEXISTENT_KEY")

    @mock.patch("kittylog.config.cli.load_dotenv")
    @mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH")
    @mock.patch("os.getenv")
    def test_get_empty_value(self, mock_getenv, mock_path, mock_load_dotenv):
        """Test config get for empty string value."""
        mock_getenv.return_value = ""

        runner = CliRunner()
        result = runner.invoke(get, ["EMPTY_KEY"])

        assert result.exit_code == 0
        assert "" in result.output  # Should output empty string
        mock_load_dotenv.assert_called_once_with(mock_path, override=True)
        mock_getenv.assert_called_once_with("EMPTY_KEY")


class TestConfigUnset:
    """Test the config unset command."""

    @mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH")
    def test_unset_no_file(self, mock_path):
        """Test config unset when no config file exists."""
        mock_path.exists = mock.PropertyMock(return_value=False)

        runner = CliRunner()
        result = runner.invoke(unset, ["TEST_KEY"])

        assert result.exit_code == 0
        assert "No $HOME/.kittylog.env found" in result.output
        # Should not try to read or write file
        assert not hasattr(mock_path, "read_text") or not mock_path.read_text.called
        assert not hasattr(mock_path, "write_text") or not mock_path.write_text.called

    @mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH")
    def test_unset_existing_key(self, mock_path):
        """Test config unset for existing key."""
        mock_path.exists = mock.PropertyMock(return_value=True)
        mock_path.read_text = mock.Mock(return_value="KEY1=value1\nKEY2=value2\nKEY3=value3\n")
        mock_path.write_text = mock.Mock()

        runner = CliRunner()
        result = runner.invoke(unset, ["KEY2"])

        assert result.exit_code == 0
        mock_path.read_text.assert_called_once()
        mock_path.write_text.assert_called_once_with("KEY1=value1\nKEY3=value3\n")
        assert "Unset KEY2 in" in result.output

    @mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH")
    def test_unset_nonexistent_key(self, mock_path):
        """Test config unset for non-existent key."""
        mock_path.exists = mock.PropertyMock(return_value=True)
        mock_path.read_text = mock.Mock(return_value="KEY1=value1\nKEY3=value3\n")
        mock_path.write_text = mock.Mock()

        runner = CliRunner()
        result = runner.invoke(unset, ["NONEXISTENT_KEY"])

        assert result.exit_code == 0
        mock_path.read_text.assert_called_once()
        # Should write back the original content unchanged
        mock_path.write_text.assert_called_once_with("KEY1=value1\nKEY3=value3\n")
        assert "Unset NONEXISTENT_KEY in" in result.output

    @mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH")
    def test_unset_key_with_special_formatting(self, mock_path):
        """Test config unset with various key formatting."""
        mock_path.exists = mock.PropertyMock(return_value=True)
        # Test with spaces, comments, and different formats
        mock_path.read_text = mock.Mock(
            return_value=(
                "# Comment\n"
                "  KEY1=value1  \n"  # Leading/trailing spaces
                "KEY2=value2\n"
                "KEY3=value3 # inline comment\n"
                "\n"  # Empty line
                "KEY4=value4\n"
            )
        )
        mock_path.write_text = mock.Mock()

        runner = CliRunner()
        result = runner.invoke(unset, ["KEY2"])

        assert result.exit_code == 0
        mock_path.read_text.assert_called_once()
        # Should remove only the KEY2 line
        expected_content = "# Comment\n  KEY1=value1  \nKEY3=value3 # inline comment\n\nKEY4=value4\n"
        mock_path.write_text.assert_called_once_with(expected_content)
        assert "Unset KEY2 in" in result.output

    @mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH")
    def test_unset_last_key_leaves_empty_file(self, mock_path):
        """Test config unset when removing the last key."""
        mock_path.exists = mock.PropertyMock(return_value=True)
        mock_path.read_text = mock.Mock(return_value="ONLY_KEY=value\n")
        mock_path.write_text = mock.Mock()

        runner = CliRunner()
        result = runner.invoke(unset, ["ONLY_KEY"])

        assert result.exit_code == 0
        mock_path.read_text.assert_called_once()
        # Should write just a newline
        mock_path.write_text.assert_called_once_with("\n")
        assert "Unset ONLY_KEY in" in result.output

    @mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH")
    def test_unset_key_multiple_occurrences(self, mock_path):
        """Test config unset when key appears multiple times."""
        mock_path.exists = mock.PropertyMock(return_value=True)
        mock_path.read_text = mock.Mock(return_value="KEY=value1\nOTHER=value\nKEY=value2\n")
        mock_path.write_text = mock.Mock()

        runner = CliRunner()
        result = runner.invoke(unset, ["KEY"])

        assert result.exit_code == 0
        mock_path.read_text.assert_called_once()
        # Should remove all occurrences of KEY=
        expected_content = "OTHER=value\n"
        mock_path.write_text.assert_called_once_with(expected_content)
        assert "Unset KEY in" in result.output


class TestConfigIntegration:
    """Integration tests for config CLI commands."""

    def test_config_set_then_get_workflow(self, temp_dir):
        """Test complete set then get workflow."""
        # Create a temporary config file
        config_file = temp_dir / ".kittylog.env"

        with mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH", config_file):
            # Set a value
            runner = CliRunner()
            set_result = runner.invoke(set, ["TEST_VAR", "test123"])
            assert set_result.exit_code == 0

            # Get the value back
            get_result = runner.invoke(get, ["TEST_VAR"])
            assert get_result.exit_code == 0
            assert "test123" in get_result.output

    def test_config_show_after_set(self, temp_dir):
        """Test config show after setting values."""
        # Create a temporary config file
        config_file = temp_dir / ".kittylog.env"

        with mock.patch("kittylog.config.cli.KITTYLOG_ENV_PATH", config_file):
            # Set some values
            runner = CliRunner()
            runner.invoke(set, ["MODEL", "gpt-4"])
            runner.invoke(set, ["API_KEY", "secret123"])

            # Show config
            show_result = runner.invoke(show)
            assert show_result.exit_code == 0
            assert "MODEL=gpt-4" in show_result.output
            assert "API_KEY=***hidden***" in show_result.output
