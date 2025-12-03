"""Pytest configuration and fixtures for provider tests."""

from unittest.mock import Mock

import pytest

# Dummy messages used across all provider tests
DUMMY_MESSAGES = [{"role": "user", "content": "test"}]
DUMMY_MESSAGES_WITH_SYSTEM = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Test message"},
]
DUMMY_CONVERSATION = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "How are you?"},
]


@pytest.fixture
def dummy_messages():
    """Provide standard dummy messages for testing."""
    return DUMMY_MESSAGES.copy()


@pytest.fixture
def dummy_messages_with_system():
    """Provide dummy messages with system prompt."""
    return DUMMY_MESSAGES_WITH_SYSTEM.copy()


@pytest.fixture
def dummy_conversation():
    """Provide a sample conversation history."""
    return DUMMY_CONVERSATION.copy()


class MockResponseFactory:
    """Factory for creating consistent mock responses."""

    @staticmethod
    def create_anthropic_response(text: str = "Test response") -> dict:
        """Create Anthropic-compatible mock response."""
        return {"content": [{"text": text}]}

    @staticmethod
    def create_openai_response(text: str = "Test response") -> dict:
        """Create OpenAI-compatible mock response."""
        return {"choices": [{"message": {"content": text}}]}

    @staticmethod
    def create_ollama_response(text: str = "Test response") -> dict:
        """Create Ollama-compatible mock response."""
        return {"message": {"content": text}}


@pytest.fixture
def mock_response_factory():
    """Provide factory for creating mock responses."""
    return MockResponseFactory()


class MockHTTPResponseFactory:
    """Factory for creating mock HTTP response objects."""

    @staticmethod
    def create_success_response(response_data: dict) -> Mock:
        """Create a successful HTTP response mock."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = response_data
        mock_response.status_code = 200
        return mock_response

    @staticmethod
    def create_error_response(status_code: int = 429, error_message: str = "Rate limit exceeded") -> Mock:
        """Create an error HTTP response mock."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.text = error_message
        mock_response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
        return mock_response


@pytest.fixture
def mock_http_response_factory():
    """Provide factory for creating mock HTTP responses."""
    return MockHTTPResponseFactory()


# Markers for provider-specific tests
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
    )
    config.addinivalue_line(
        "markers",
        "provider_specific: marks tests as provider-specific (may not apply to all providers)",
    )


# Helper fixture for common API key validation pattern
@pytest.fixture
def api_key_env_key():
    """Provide the API key environment variable name for the test."""
    # This should be overridden in individual test modules
    return "API_KEY"


@pytest.fixture
def api_base_url_env_key():
    """Provide the API base URL environment variable name (if applicable)."""
    # This should be overridden in individual test modules for custom providers
    return None


@pytest.fixture(params=[0.5, 0.7, 1.0])
def temperature_values(request):
    """Parametrize common temperature values for testing."""
    return request.param


@pytest.fixture(params=[32, 100, 1024])
def max_token_values(request):
    """Parametrize common max token values for testing."""
    return request.param


# Provider model fixtures
@pytest.fixture
def anthropic_models():
    """Anthropic models for testing."""
    return ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"]


@pytest.fixture
def openai_models():
    """OpenAI models for testing."""
    return ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"]


@pytest.fixture
def groq_models():
    """Groq models for testing."""
    return ["llama3-8b-8192", "mixtral-8x7b-32768", "gemma-7b-it"]


@pytest.fixture
def ollama_models():
    """Ollama models for testing."""
    return ["llama2", "mistral", "neural-chat"]


@pytest.fixture
def cerebras_models():
    """Cerebras models for testing."""
    return ["llama-3.1-70b"]


class APITestHelper:
    """Helper class for common API testing patterns."""

    @staticmethod
    def verify_bearer_token_header(headers: dict, api_key: str) -> bool:
        """Verify Bearer token is present in headers."""
        return "Authorization" in headers and f"Bearer {api_key}" in headers["Authorization"]

    @staticmethod
    def verify_api_key_header(headers: dict, api_key: str, header_name: str = "x-api-key") -> bool:
        """Verify API key is present in headers."""
        return header_name in headers and headers[header_name] == api_key

    @staticmethod
    def extract_call_data(mock_post_call) -> dict:
        """Extract JSON data from a mock POST call."""
        call_args = mock_post_call.call_args
        return call_args[1]["json"] if call_args else {}

    @staticmethod
    def extract_call_headers(mock_post_call) -> dict:
        """Extract headers from a mock POST call."""
        call_args = mock_post_call.call_args
        return call_args[1]["headers"] if call_args else {}

    @staticmethod
    def extract_call_url(mock_post_call) -> str:
        """Extract URL from a mock POST call."""
        call_args = mock_post_call.call_args
        return call_args[0][0] if call_args and call_args[0] else ""


@pytest.fixture
def api_test_helper():
    """Provide helper for API testing patterns."""
    return APITestHelper()


class MessageValidator:
    """Helper for validating message formatting in API calls."""

    @staticmethod
    def validate_messages(messages: list, expected_roles: list) -> bool:
        """Validate message structure and roles."""
        if len(messages) != len(expected_roles):
            return False
        return all(msg["role"] == expected_role for msg, expected_role in zip(messages, expected_roles, strict=True))

    @staticmethod
    def extract_system_message(messages: list) -> str | None:
        """Extract system message from messages list."""
        for msg in messages:
            if msg.get("role") == "system":
                return msg.get("content")
        return None

    @staticmethod
    def get_non_system_messages(messages: list) -> list:
        """Get all non-system messages."""
        return [msg for msg in messages if msg.get("role") != "system"]


@pytest.fixture
def message_validator():
    """Provide helper for message validation."""
    return MessageValidator()


@pytest.fixture(autouse=True)
def reset_provider_caches():
    """Reset all provider singleton caches before each test.

    This ensures that API key checks work correctly even when running
    tests in sequence, since providers cache their API keys.
    """
    # Import providers and reset their cached API keys
    try:
        import importlib
        import importlib.util

        # Just check if provider modules exist
        provider_names = [
            "anthropic",
            "azure_openai",
            "cerebras",
            "deepseek",
            "fireworks",
            "groq",
            "minimax",
            "mistral",
            "moonshot",
            "ollama",
            "openai",
            "openrouter",
            "streamlake",
            "synthetic",
            "together",
            "zai",
        ]

        for name in provider_names:
            importlib.util.find_spec(f"kittylog.providers.{name}")

        # Reset all provider singletons
        providers_to_reset = [
            ("anthropic", "_anthropic_provider"),
            ("cerebras", "_cerebras_provider"),
            ("deepseek", "_deepseek_provider"),
            ("fireworks", "_fireworks_provider"),
            ("groq", "_groq_provider"),
            ("minimax", "_minimax_provider"),
            ("mistral", "_mistral_provider"),
            ("moonshot", "_moonshot_provider"),
            ("ollama", "_ollama_provider"),
            ("openai", "_openai_provider"),
            ("openrouter", "_openrouter_provider"),
            ("streamlake", "_streamlake_provider"),
            ("synthetic", "_synthetic_provider"),
            ("together", "_together_provider"),
            ("zai", "_zai_provider"),
            ("zai", "_zai_coding_provider"),
            ("azure_openai", "_azure_openai_provider"),
        ]

        import kittylog.providers as providers_module

        for module_name, provider_name in providers_to_reset:
            try:
                module = getattr(providers_module, module_name)
                provider = getattr(module, provider_name, None)
                if provider and hasattr(provider, "_api_key"):
                    provider._api_key = None
                # Also reset Azure-specific cached properties
                if hasattr(provider, "api_endpoint"):
                    provider.api_endpoint = None
                if hasattr(provider, "api_version"):
                    provider.api_version = None
            except (AttributeError, ImportError):
                pass
    except ImportError:
        pass

    yield
