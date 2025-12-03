"""Pytest configuration and fixtures for kittylog tests."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

try:
    from git import Repo
except ImportError:
    # Mock the git module for CI environments
    Repo = Mock()
    print("Warning: gitpython not available, using mock")

# Ensure we're in a valid directory at the start
try:
    os.getcwd()
except Exception:
    os.chdir(str(Path.home()))


@pytest.fixture(autouse=True)
def clear_caches_between_tests():
    """Automatically clear all git caches between tests."""
    # Save original cwd
    try:
        original_cwd = os.getcwd()
    except Exception:
        original_cwd = str(Path.home())

    # Clear before test
    try:
        from kittylog.git_operations import clear_all_caches

        clear_all_caches()
    except ImportError:
        pass

    yield

    # Clear after test
    try:
        from kittylog.git_operations import clear_all_caches

        clear_all_caches()
    except ImportError:
        pass

    # Restore original cwd or go to safe location
    try:
        os.chdir(original_cwd)
    except Exception:
        try:
            os.chdir(str(Path.home()))
        except Exception:
            pass


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def git_repo(temp_dir):
    """Create a temporary git repository for testing."""
    # Clear git cache before setting up new repo
    from kittylog.git_operations import clear_all_caches

    clear_all_caches()

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

    # Clear git cache after test to prevent cross-test contamination
    clear_all_caches()

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
        "model": "cerebras:qwen-3-coder-480b",
        "temperature": 0.7,
        "max_output_tokens": 1024,
        "max_retries": 3,
        "log_level": "WARNING",
        "warning_limit_tokens": 16384,
        "audience": "developers",
        "translate_headings": False,
    }


@pytest.fixture
def mock_console():
    """Mock rich console for testing."""
    with patch("kittylog.utils.console") as mock:
        yield mock


@pytest.fixture
def mock_questionary():
    """Mock questionary for testing CLI interactions."""
    with patch("kittylog.init_cli.questionary") as mock:
        # Set up default responses
        mock.select.return_value.ask.side_effect = [
            "Anthropic",
            "English",
            "developers",
        ]
        mock.text.return_value.ask.return_value = "claude-3-5-haiku-latest"
        mock.password.return_value.ask.return_value = "test-api-key"
        yield mock


@pytest.fixture(autouse=True)
def mock_api_calls():
    """Automatically mock API calls in all tests."""
    # Mock httpx.post for all providers
    with patch("httpx.post") as mock_post:
        # Create mock response for HTTP calls
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None  # Don't raise exceptions

        # Default response that works for most providers
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "### Added\n\n- Test feature\n\n### Fixed\n\n- Test bug fix"}}]
        }

        # For Anthropic provider, which has a different response format
        anthropic_response = {"content": [{"text": "### Added\n\n- Test feature\n\n### Fixed\n\n- Test bug fix"}]}

        # Configure the mock to return appropriate responses based on URL
        def side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            if "anthropic" in url:
                mock_response.json.return_value = anthropic_response
            elif "ollama" in url:
                mock_response.json.return_value = {
                    "message": {"content": "### Added\n\n- Test feature\n\n### Fixed\n\n- Test bug fix"}
                }
            else:
                mock_response.json.return_value = {
                    "choices": [{"message": {"content": "### Added\n\n- Test feature\n\n### Fixed\n\n- Test bug fix"}}]
                }
            return mock_response

        mock_post.side_effect = side_effect

        yield mock_post


@pytest.fixture
def mock_tiktoken():
    """Mock tiktoken for token counting."""
    with patch("kittylog.utils.tiktoken") as mock:
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
        patch("kittylog.git_operations.get_repo") as mock_get_repo,
        patch("kittylog.git_operations.get_all_tags") as mock_get_tags,
        patch("kittylog.git_operations.get_commits_between_tags") as mock_get_commits,
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
