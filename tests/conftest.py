"""Pytest configuration and fixtures for clog tests."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from git import Repo

# Ensure we're in a valid directory at the start
try:
    os.getcwd()
except Exception:
    os.chdir(str(Path.home()))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def git_repo(temp_dir):
    """Create a temporary git repository for testing."""
    repo = Repo.init(temp_dir)

    # Configure git user (required for commits)
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Store original directory
    try:
        original_cwd = os.getcwd()
    except Exception:
        original_cwd = str(Path.home())

    # Change to the repo directory for git operations
    os.chdir(str(temp_dir))

    # Create initial commit
    test_file = Path("README.md")
    test_file.write_text("# Test Project\n")
    # Add file using relative path
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    yield repo

    # Restore original directory or change to a safe one
    try:
        os.chdir(original_cwd)
    except Exception:
        os.chdir(str(Path.home()))

    # Additional safety: make sure we're in a valid directory
    try:
        os.getcwd()
    except Exception:
        os.chdir(str(Path.home()))


@pytest.fixture
def git_repo_with_tags(git_repo):
    """Create a git repository with sample tags and commits."""
    repo = git_repo

    # Create some commits and tags
    commits_and_tags = [
        ("Add user authentication", "v0.1.0"),
        ("Fix login bug", None),
        ("Add dashboard feature", "v0.2.0"),
        ("Update documentation", None),
        ("Fix security issue", "v0.2.1"),
    ]

    for commit_msg, tag in commits_and_tags:
        # Create a file change
        test_file = Path(repo.working_dir) / f"file_{len(list(repo.iter_commits()))}.py"
        test_file.write_text(f"# {commit_msg}\nprint('hello')\n")
        repo.index.add([str(test_file)])
        commit = repo.index.commit(commit_msg)

        if tag:
            repo.create_tag(tag, commit)

    return repo


@pytest.fixture
def sample_changelog():
    """Sample changelog content for testing."""
    return """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-01-01

### Added

- Initial project setup
- Basic authentication system

### Fixed

- Login validation errors
"""


@pytest.fixture
def sample_commits():
    """Sample commit data for testing."""
    from datetime import datetime

    return [
        {
            "hash": "abc123def456",
            "short_hash": "abc123d",
            "message": "feat: add user authentication system",
            "author": "Test User <test@example.com>",
            "date": datetime(2024, 1, 15),
            "files": ["auth.py", "users.py", "requirements.txt"],
        },
        {
            "hash": "def456ghi789",
            "short_hash": "def456g",
            "message": "fix: resolve login validation bug",
            "author": "Test User <test@example.com>",
            "date": datetime(2024, 1, 16),
            "files": ["auth.py", "tests/test_auth.py"],
        },
        {
            "hash": "ghi789jkl012",
            "short_hash": "ghi789j",
            "message": "docs: update README with installation instructions",
            "author": "Test User <test@example.com>",
            "date": datetime(2024, 1, 17),
            "files": ["README.md", "docs/installation.md"],
        },
    ]


@pytest.fixture
def mock_ai_client():
    """Mock AI client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_choice = Mock()
    mock_message = Mock()

    mock_message.content = """### Added

- New user authentication system with OAuth2 support
- Dashboard widgets for real-time monitoring

### Fixed

- Fixed issue where users couldn't save preferences
- Resolved login validation errors"""

    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    return mock_client


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "model": "anthropic:claude-3-5-haiku-latest",
        "temperature": 0.7,
        "max_output_tokens": 1024,
        "max_retries": 3,
        "log_level": "WARNING",
        "warning_limit_tokens": 16384,
    }


@pytest.fixture
def mock_console():
    """Mock rich console for testing."""
    with patch("clog.utils.console") as mock:
        yield mock


@pytest.fixture
def mock_questionary():
    """Mock questionary for testing CLI interactions."""
    with patch("clog.init_cli.questionary") as mock:
        # Set up default responses
        mock.select.return_value.ask.return_value = "Anthropic"
        mock.text.return_value.ask.return_value = "claude-3-5-haiku-latest"
        mock.password.return_value.ask.return_value = "test-api-key"
        yield mock


@pytest.fixture(autouse=True)
def mock_api_calls():
    """Automatically mock API calls in all tests."""
    with patch("clog.ai.ai.Client") as mock_client_class:
        mock_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()

        mock_message.content = "### Added\n\n- Test feature\n\n### Fixed\n\n- Test bug fix"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_client_class.return_value = mock_client

        yield mock_client


@pytest.fixture
def mock_tiktoken():
    """Mock tiktoken for token counting."""
    with patch("clog.utils.tiktoken") as mock:
        mock_encoding = Mock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock.encoding_for_model.return_value = mock_encoding
        mock.get_encoding.return_value = mock_encoding
        yield mock


# Utility fixtures for common mock combinations
@pytest.fixture
def mock_all_git_operations():
    """Mock all git operations for isolated testing."""
    with (
        patch("clog.git_operations.get_repo") as mock_get_repo,
        patch("clog.git_operations.get_all_tags") as mock_get_tags,
        patch("clog.git_operations.get_commits_between_tags") as mock_get_commits,
    ):
        # Set up defaults
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        mock_get_tags.return_value = ["v0.1.0", "v0.2.0"]
        mock_get_commits.return_value = []

        yield {
            "get_repo": mock_get_repo,
            "get_tags": mock_get_tags,
            "get_commits": mock_get_commits,
        }


@pytest.fixture
def isolated_config_test(temp_dir, monkeypatch):
    """Create isolated environment for config testing."""
    # Mock home directory
    fake_home = temp_dir / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    # Clear environment variables
    env_vars_to_clear = [
        "CHANGELOG_UPDATER_MODEL",
        "CHANGELOG_UPDATER_TEMPERATURE",
        "CHANGELOG_UPDATER_MAX_OUTPUT_TOKENS",
        "CHANGELOG_UPDATER_RETRIES",
        "CHANGELOG_UPDATER_LOG_LEVEL",
        "CHANGELOG_UPDATER_WARNING_LIMIT_TOKENS",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GROQ_API_KEY",
        "OLLAMA_HOST",
    ]

    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)

    # Change to temp directory
    original_cwd = os.getcwd()
    os.chdir(str(temp_dir))

    yield {
        "home": fake_home,
        "cwd": temp_dir,
    }

    try:
        os.chdir(original_cwd)
    except Exception:
        # If the directory no longer exists, just stay where we are
        pass
