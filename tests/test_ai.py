"""Tests for AI integration module."""

from unittest.mock import Mock, patch

import pytest

from kittylog.ai import generate_changelog_entry
from kittylog.errors import AIError
from kittylog.providers import PROVIDER_REGISTRY, SUPPORTED_PROVIDERS


class TestGenerateChangelogEntry:
    """Test generate_changelog_entry function."""

    @patch("kittylog.ai.build_changelog_prompt")
    @patch("kittylog.ai.count_tokens")
    @patch("kittylog.ai.generate_with_retries")
    @patch("kittylog.ai.clean_changelog_content")
    def test_generate_changelog_entry_success(
        self, mock_clean, mock_generate, mock_count_tokens, mock_build_prompt, sample_commits, mock_config
    ):
        """Test successful changelog entry generation."""
        # Setup mocks
        mock_build_prompt.return_value = ("system prompt", "user prompt")
        mock_count_tokens.side_effect = [100, 50, 75]  # system prompt, user prompt, completion tokens
        mock_generate.return_value = "Raw AI content"
        mock_clean.return_value = "Cleaned AI content"

        with patch("kittylog.ai.config", mock_config):
            result = generate_changelog_entry(
                commits=sample_commits,
                tag="v1.0.0",
                model="cerebras:zai-glm-4.6",
                quiet=True,
            )

        assert result[0] == "Cleaned AI content"
        mock_build_prompt.assert_called_once()
        assert "audience" in mock_build_prompt.call_args.kwargs
        assert mock_build_prompt.call_args.kwargs["audience"] is None
        mock_generate.assert_called_once()
        mock_clean.assert_called_once_with("Raw AI content", False)

    @patch("kittylog.ai.build_changelog_prompt")
    @patch("kittylog.ai.count_tokens")
    def test_generate_changelog_entry_with_defaults(
        self, mock_count_tokens, mock_build_prompt, sample_commits, mock_config
    ):
        """Test changelog entry generation with default parameters."""
        mock_build_prompt.return_value = ("system prompt", "user prompt")
        mock_count_tokens.return_value = 100

        with (
            patch("kittylog.ai.config", mock_config),
            patch("kittylog.ai.generate_with_retries") as mock_generate,
            patch("kittylog.ai.clean_changelog_content") as mock_clean,
        ):
            mock_generate.return_value = "AI content"
            mock_clean.return_value = "Clean content"

            generate_changelog_entry(
                commits=sample_commits,
                tag="v1.0.0",
            )

        # Should use config defaults
        mock_generate.assert_called_once()
        call_kwargs = mock_generate.call_args[1]
        assert call_kwargs["model"] == mock_config["model"]
        assert call_kwargs["temperature"] == mock_config["temperature"]
        assert call_kwargs["max_tokens"] == mock_config["max_output_tokens"]
        assert call_kwargs["max_retries"] == mock_config["max_retries"]

    def test_generate_changelog_entry_no_model(self, sample_commits):
        """Test error when no model is specified."""
        with patch("kittylog.ai.config", {"model": None}):
            with pytest.raises(AIError) as exc_info:
                generate_changelog_entry(
                    commits=sample_commits,
                    tag="v1.0.0",
                    model=None,
                )
            assert "No model specified" in str(exc_info.value)

    @patch("kittylog.ai.build_changelog_prompt")
    @patch("kittylog.ai.count_tokens")
    @patch("kittylog.ai.generate_with_retries")
    def test_generate_changelog_entry_ai_error(
        self, mock_generate, mock_count_tokens, mock_build_prompt, sample_commits, mock_config
    ):
        """Test handling of AI generation errors."""
        mock_build_prompt.return_value = ("system prompt", "user prompt")
        mock_count_tokens.return_value = 100
        mock_generate.side_effect = Exception("AI service error")

        with patch("kittylog.ai.config", mock_config), pytest.raises(AIError):
            generate_changelog_entry(
                commits=sample_commits,
                tag="v1.0.0",
            )


class TestGenerateWithRetries:
    """Test generate_with_retries function."""

    @patch("httpx.post")
    @patch("os.getenv")
    def testgenerate_with_retries_success(self, mock_getenv, mock_post):
        """Test successful generation on first try."""
        # Import here to avoid ImportError during test collection
        from kittylog.ai import generate_with_retries
        from kittylog.providers import call_openai_api

        # Mock API key
        mock_getenv.return_value = "test-api-key"

        # Setup mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": [{"message": {"content": "Generated content"}}]}
        mock_post.return_value = mock_response

        result = generate_with_retries(
            provider_funcs={"openai": call_openai_api},
            model="openai:test-model",
            system_prompt="System prompt",
            user_prompt="User prompt",
            temperature=0.7,
            max_tokens=1024,
            max_retries=3,
            quiet=True,
        )

        assert result == "Generated content"
        mock_post.assert_called_once()

    def testgenerate_with_retries_empty_response(self):
        """Test handling of empty response."""
        # Import here to avoid ImportError during test collection
        from kittylog.ai import generate_with_retries

        with pytest.raises(AIError):
            generate_with_retries(
                provider_funcs={"openai": Mock(return_value="")},
                model="openai:test-model",
                system_prompt="System prompt",
                user_prompt="User prompt",
                temperature=0.7,
                max_tokens=1024,
                max_retries=1,
                quiet=True,
            )

    @patch("kittylog.ai_utils.time.sleep")
    def testgenerate_with_retries_retry_logic(self, mock_sleep):
        """Test retry logic with transient errors."""
        # Import here to avoid ImportError during test collection
        from kittylog.ai import generate_with_retries

        # Create a mock provider function that fails the first time and succeeds the second time
        mock_provider_func = Mock()
        mock_provider_func.side_effect = [
            Exception("Temporary error"),  # First call fails
            "Success",  # Second call succeeds
        ]

        result = generate_with_retries(
            provider_funcs={"openai": mock_provider_func},
            model="openai:test-model",
            system_prompt="System prompt",
            user_prompt="User prompt",
            temperature=0.7,
            max_tokens=1024,
            max_retries=3,
            quiet=True,
        )

        assert result == "Success"
        assert mock_provider_func.call_count == 2
        mock_sleep.assert_called_once_with(1)  # 2^0 = 1 second wait

    def testgenerate_with_retries_non_retryable_error(self):
        """Test handling of non-retryable errors."""
        # Import here to avoid ImportError during test collection
        from kittylog.ai import generate_with_retries

        mock_provider_func = Mock(side_effect=Exception("authentication failed"))

        with pytest.raises(AIError):
            generate_with_retries(
                provider_funcs={"openai": mock_provider_func},
                model="openai:test-model",
                system_prompt="System prompt",
                user_prompt="User prompt",
                temperature=0.7,
                max_tokens=1024,
                max_retries=3,
                quiet=True,
            )

        # Should not retry authentication errors
        assert mock_provider_func.call_count == 1

    @patch("kittylog.ai_utils.time.sleep")
    def testgenerate_with_retries_max_retries_exceeded(self, mock_sleep):
        """Test when max retries is exceeded."""
        # Import here to avoid ImportError during test collection
        from kittylog.ai import generate_with_retries

        mock_provider_func = Mock(side_effect=Exception("Rate limit"))

        with pytest.raises(AIError):
            generate_with_retries(
                provider_funcs={"openai": mock_provider_func},
                model="openai:test-model",
                system_prompt="System prompt",
                user_prompt="User prompt",
                temperature=0.7,
                max_tokens=1024,
                max_retries=2,
                quiet=True,
            )

        assert mock_provider_func.call_count == 2
        assert mock_sleep.call_count == 1  # Only sleep between retries


class TestClassifyError:
    """Test classify_error function."""

    def test_classify_authentication_error(self):
        """Test classification of authentication errors."""
        from kittylog.errors import classify_error

        errors = [
            Exception("authentication failed"),
            Exception("unauthorized access"),
            Exception("invalid api key"),
        ]

        for error in errors:
            assert classify_error(error) == "authentication"

    def test_classify_model_error(self):
        """Test classification of model errors."""
        from kittylog.errors import classify_error

        errors = [
            Exception("model not found"),
            Exception("model does not exist"),
        ]

        for error in errors:
            assert classify_error(error) == "model_not_found"

    def test_classify_rate_limit_error(self):
        """Test classification of rate limit errors."""
        from kittylog.errors import classify_error

        errors = [
            Exception("rate limit exceeded"),
            Exception("quota exceeded"),
        ]

        for error in errors:
            assert classify_error(error) == "rate_limit"

    def test_classify_timeout_error(self):
        """Test classification of timeout errors."""
        from kittylog.errors import classify_error

        error = Exception("request timeout")
        assert classify_error(error) == "timeout"

    def test_classify_context_length_error(self):
        """Test classification of context length errors."""
        from kittylog.errors import classify_error

        errors = [
            Exception("context too long"),
            Exception("context length exceeded"),
        ]

        for error in errors:
            assert classify_error(error) == "context_length"

    def test_classify_unknown_error(self):
        """Test classification of unknown errors."""
        from kittylog.errors import classify_error

        error = Exception("some random error")
        assert classify_error(error) == "unknown"


class TestAIIntegration:
    """Integration tests for AI operations."""

    @patch("httpx.post")
    @patch("kittylog.ai.build_changelog_prompt")
    @patch("kittylog.ai.count_tokens")
    @patch("kittylog.ai.clean_changelog_content")
    def test_full_ai_workflow(
        self, mock_clean, mock_count_tokens, mock_build_prompt, mock_post, sample_commits, mock_config
    ):
        """Test complete AI generation workflow."""
        # Setup mocks
        mock_build_prompt.return_value = ("System: Generate changelog", "User: Analyze these commits")
        mock_count_tokens.side_effect = [150, 100, 75]  # system prompt, user prompt, completion tokens

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": """### Added

- User authentication system with OAuth2 support
- Dashboard widgets for real-time monitoring

### Fixed

- Fixed issue where users couldn't save preferences
- Resolved login validation errors"""
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        mock_clean.return_value = mock_response.json.return_value["choices"][0]["message"]["content"]

        with patch("kittylog.ai.config", mock_config):
            result = generate_changelog_entry(
                commits=sample_commits,
                tag="v1.0.0",
                from_boundary="v0.9.0",
                hint="Focus on user-facing changes",
                show_prompt=False,
                quiet=True,
            )

        # Verify the workflow
        assert "### Added" in result[0]
        assert "User authentication system" in result[0]
        assert "### Fixed" in result[0]
        assert "login validation errors" in result[0]

        # Verify prompt building was called correctly
        mock_build_prompt.assert_called_once_with(
            commits=sample_commits,
            tag="v1.0.0",
            from_boundary="v0.9.0",
            hint="Focus on user-facing changes",
            boundary_mode="tags",
            language=None,
            translate_headings=False,
            audience=None,
        )

        # Verify AI client was called
        mock_post.assert_called_once()

    def test_ai_error_propagation(self, sample_commits):
        """Test that AI errors are properly propagated."""
        with patch("kittylog.ai.config", {"model": None}):
            with pytest.raises(AIError) as exc_info:
                generate_changelog_entry(
                    commits=sample_commits,
                    tag="v1.0.0",
                )

            assert exc_info.value.error_type == "model"
            assert "No model specified" in str(exc_info.value)


class TestProviderRegistry:
    """Tests for the centralized provider registry."""

    def test_provider_registry_and_supported_providers_consistency(self):
        """Test that SUPPORTED_PROVIDERS contains exactly the keys from PROVIDER_REGISTRY."""
        registry_keys = set(PROVIDER_REGISTRY.keys())
        supported_providers_set = set(SUPPORTED_PROVIDERS)

        assert registry_keys == supported_providers_set, (
            f"PROVIDER_REGISTRY keys and SUPPORTED_PROVIDERS are not identical:\n"
            f"Registry keys not in supported: {registry_keys - supported_providers_set}\n"
            f"Supported providers not in registry: {supported_providers_set - registry_keys}"
        )

    def test_provider_registry_functions_exist(self):
        """Test that all functions in PROVIDER_REGISTRY are callable."""
        for provider_name, provider_func in PROVIDER_REGISTRY.items():
            assert callable(provider_func), f"Provider function for '{provider_name}' is not callable"

    def test_supported_providers_is_sorted(self):
        """Test that SUPPORTED_PROVIDERS is sorted alphabetically."""
        assert SUPPORTED_PROVIDERS == sorted(PROVIDER_REGISTRY.keys()), (
            "SUPPORTED_PROVIDERS should be sorted alphabetically"
        )

    def test_provider_registry_complete(self):
        """Test that PROVIDER_REGISTRY contains all expected providers."""
        expected_providers = {
            "anthropic",
            "azure-openai",
            "cerebras",
            "chutes",
            "claude-code",
            "custom-anthropic",
            "custom-openai",
            "deepseek",
            "fireworks",
            "gemini",
            "groq",
            "kimi-coding",
            "lm-studio",
            "minimax",
            "mistral",
            "moonshot",
            "ollama",
            "openai",
            "openrouter",
            "replicate",
            "streamlake",
            "synthetic",
            "together",
            "zai",
            "zai-coding",
        }

        actual_providers = set(PROVIDER_REGISTRY.keys())

        assert actual_providers == expected_providers, (
            f"Provider registry is missing expected providers or has extra ones:\n"
            f"Missing: {expected_providers - actual_providers}\n"
            f"Extra: {actual_providers - expected_providers}"
        )
