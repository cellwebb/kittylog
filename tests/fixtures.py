"""Simplified test fixtures for kittylog.

These fixtures reduce the number of mocking layers needed in tests
by providing pre-configured, behavior-focused mocks.
"""

from contextlib import contextmanager
from unittest.mock import Mock, patch

import pytest


class MockAIResponse:
    """Builder for AI response mocks."""

    def __init__(self, content: str = "### Added\n\n- Test feature"):
        self.content = content

    def as_openai(self) -> dict:
        """Format as OpenAI-compatible response."""
        return {"choices": [{"message": {"content": self.content}}]}

    def as_anthropic(self) -> dict:
        """Format as Anthropic response."""
        return {"content": [{"text": self.content}]}

    def as_gemini(self) -> dict:
        """Format as Gemini response."""
        return {"candidates": [{"content": {"parts": [{"text": self.content}]}}]}

    def as_ollama(self) -> dict:
        """Format as Ollama response."""
        return {"message": {"content": self.content}}


class MockProviderBuilder:
    """Builder for provider mocks with fluent interface."""

    def __init__(self):
        self._response = MockAIResponse()
        self._should_fail = False
        self._error_type = None
        self._status_code = 200

    def with_response(self, content: str) -> "MockProviderBuilder":
        """Set the response content."""
        self._response = MockAIResponse(content)
        return self

    def with_auth_error(self) -> "MockProviderBuilder":
        """Configure to raise authentication error."""
        self._should_fail = True
        self._error_type = "auth"
        self._status_code = 401
        return self

    def with_rate_limit(self) -> "MockProviderBuilder":
        """Configure to raise rate limit error."""
        self._should_fail = True
        self._error_type = "rate_limit"
        self._status_code = 429
        return self

    def with_timeout(self) -> "MockProviderBuilder":
        """Configure to raise timeout error."""
        self._should_fail = True
        self._error_type = "timeout"
        return self

    def with_connection_error(self) -> "MockProviderBuilder":
        """Configure to raise connection error."""
        self._should_fail = True
        self._error_type = "connection"
        return self

    def build(self) -> Mock:
        """Build the configured mock."""
        import httpx

        mock_response = Mock()
        mock_response.status_code = self._status_code

        if self._should_fail:
            if self._error_type == "timeout":
                mock_post = Mock(side_effect=httpx.TimeoutException("Request timed out"))
            elif self._error_type == "connection":
                mock_post = Mock(side_effect=httpx.ConnectError("Connection failed"))
            else:
                # HTTP status error
                mock_response.text = f"Error {self._status_code}"
                error = httpx.HTTPStatusError(
                    f"HTTP {self._status_code}",
                    request=Mock(),
                    response=mock_response,
                )
                mock_post = Mock()
                mock_post.return_value.raise_for_status.side_effect = error
        else:
            mock_response.json.return_value = self._response.as_openai()
            mock_response.raise_for_status.return_value = None
            mock_post = Mock(return_value=mock_response)

        return mock_post


@contextmanager
def mock_provider(builder: MockProviderBuilder | None = None):
    """Context manager for mocking provider HTTP calls.

    Usage:
        with mock_provider() as mock:
            result = call_some_api()
            assert mock.called

        # With custom response:
        builder = MockProviderBuilder().with_response("Custom content")
        with mock_provider(builder) as mock:
            result = call_some_api()
    """
    if builder is None:
        builder = MockProviderBuilder()

    with patch("httpx.post", builder.build()) as mock:
        yield mock


@contextmanager
def mock_git_repo(tags: list[str] | None = None, commits: list[dict] | None = None):
    """Context manager for mocking git operations.

    Usage:
        with mock_git_repo(tags=["v1.0.0", "v1.1.0"]) as git:
            tags = get_all_tags()
    """
    if tags is None:
        tags = ["v0.1.0", "v0.2.0"]
    if commits is None:
        commits = []

    with (
        patch.multiple(
            "kittylog.tag_operations",
            get_all_tags=Mock(return_value=tags),
            get_tag_date=Mock(return_value=None),
            get_latest_tag=Mock(return_value=tags[-1] if tags else None),
        ),
        patch(
            "kittylog.commit_analyzer.get_commits_between_tags",
            Mock(return_value=commits),
        ),
    ):
        yield


@contextmanager
def mock_changelog(content: str = "# Changelog\n\n## [Unreleased]\n"):
    """Context manager for mocking changelog file operations.

    Usage:
        with mock_changelog("# Changelog\n\n## [1.0.0]\n"):
            result = read_changelog("CHANGELOG.md")
    """
    with patch.multiple(
        "kittylog.changelog.io",
        read_changelog=Mock(return_value=content),
        write_changelog=Mock(),
    ):
        yield


# Pytest fixtures using the builders


@pytest.fixture
def provider_mock():
    """Fixture providing a MockProviderBuilder for custom configuration."""
    return MockProviderBuilder()


@pytest.fixture
def ai_response():
    """Fixture providing a MockAIResponse builder."""
    return MockAIResponse()


@pytest.fixture
def sample_commits():
    """Fixture providing sample commit data for testing."""
    from datetime import datetime

    return [
        {
            "short_hash": "abc123d",
            "message": "feat: add new authentication feature",
            "author": "John Doe <john@example.com>",
            "date": datetime(2024, 1, 15, 10, 30),
            "files": ["src/auth.py", "tests/test_auth.py"],
        },
        {
            "short_hash": "def456g",
            "message": "fix: resolve memory leak in cache",
            "author": "Jane Smith <jane@example.com>",
            "date": datetime(2024, 1, 16, 14, 22),
            "files": ["src/cache.py"],
        },
        {
            "short_hash": "ghi789h",
            "message": "docs: update API documentation",
            "author": "Bob Wilson <bob@example.com>",
            "date": datetime(2024, 1, 17, 9, 15),
            "files": ["docs/api.md"],
        },
    ]


@pytest.fixture
def mock_config():
    """Fixture providing a mock configuration object for testing."""
    from kittylog.config.data import KittylogConfigData

    return KittylogConfigData(
        model="openai:gpt-4",
        temperature=0.7,
        max_output_tokens=1024,
        max_retries=3,
        log_level="WARNING",
        warning_limit_tokens=16384,
        grouping_mode="tags",
        gap_threshold_hours=4.0,
        date_grouping="daily",
        language=None,
        translate_headings=False,
        audience="developers",
    )
