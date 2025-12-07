# Contributing to kittylog

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Setup

1. Clone the repo
2. Install dependencies with `uv pip install -e ".[dev,test]"` or use `make install-dev`
3. Install pre-commit hooks with `uv run pre-commit install` (or use `make install-dev` which does this automatically)
4. Run tests with `uv run pytest` or `make test`

For a quick setup, you can run `make quickstart` which will install dependencies, set up pre-commit hooks, and run initial tests.

> **Important:** Always use `uv run` prefix for all Python commands (pytest, ruff, mypy, etc.) to ensure proper environment isolation.

## Code Quality

- All code should be formatted with `ruff format` (replaces black and isort)
- Code should pass `ruff check` linting
- Type checking should pass `mypy src/kittylog`

You can run all code quality checks with:

- `make lint` - runs ruff check and mypy
- `make format` - formats code with ruff
- `make pre-commit` - runs all pre-commit hooks
- `make check` - runs both linting and tests

## Testing

- All new features should include tests
- Run the full test suite before submitting PRs
- Use `uv run pytest` for testing
- Tests are isolated from global configuration files
- Configuration-related tests mock the KITTYLOG_ENV_PATH constant to prevent interference from existing global config files
- Error path tests cover provider failures, rate limiting, timeouts, and invalid configs

Run tests with:

- `make test` - runs pytest
- `make test-coverage` - runs tests with coverage report
- `make test-integration` - runs integration tests only
- `make test-watch` - runs tests in watch mode

## Project Structure

```
src/kittylog/
├── cli.py                  # Click-based CLI entry point
├── main.py                 # Business logic orchestration
├── ai.py                   # AI generation coordination
├── workflow.py             # Main workflow logic
├── workflow_validation.py  # Workflow prerequisite validation
├── workflow_ui.py          # Dry-run and confirmation UI
├── postprocess.py          # Postprocessing public interface
├── prompt.py               # Prompt building public interface
├── prompt_templates.py     # System and user prompt templates
├── changelog/              # Changelog operations package
│   ├── __init__.py         # Public API exports
│   ├── io.py               # Read, write, create header
│   ├── parser.py           # Find boundaries, insertion points, extract entries
│   └── updater.py          # Update logic
├── constants/              # Configuration constants package
│   ├── __init__.py         # Re-exports for backwards compat
│   ├── languages.py        # Languages class
│   ├── audiences.py        # Audiences class
│   ├── env_defaults.py     # EnvDefaults and Limits classes
│   └── enums.py            # GroupingMode, DateGrouping, FileStatus, etc.
├── config/                 # Configuration management
│   └── __init__.py         # Config loading with KittylogConfigData dataclass
├── providers/              # AI provider implementations
│   ├── __init__.py         # Provider registry and auto-discovery
│   ├── base.py             # BaseConfiguredProvider ABC
│   ├── openai_compat.py    # OpenAI-compatible providers (OpenAI, Groq, Cerebras, etc.)
│   ├── anthropic_compat.py # Anthropic-compatible providers
│   ├── ollama.py           # Ollama local models
│   └── error_handler.py    # Provider error handling decorator
├── git_operations.py       # Git tag and commit utilities
└── errors.py               # Custom exception classes

tests/
├── conftest.py             # Test configuration and fixtures
└── test_*.py               # Unit and integration tests
```

## Adding New AI Providers

Providers use a base class architecture with automatic registration. To add a new provider:

### 1. Choose the appropriate base class

- **OpenAI-compatible APIs**: Extend `OpenAICompatibleProvider` (for Groq, Cerebras, Together, etc.)
- **Anthropic-compatible APIs**: Extend `AnthropicCompatibleProvider`
- **Custom APIs**: Extend `BaseConfiguredProvider` and implement `_build_request_body()` and `_parse_response()`

### 2. Create a minimal provider class

```python
# src/kittylog/providers/my_provider.py
from kittylog.providers.base import ProviderConfig
from kittylog.providers.openai_compat import OpenAICompatibleProvider
from kittylog.providers.registry import register_provider

@register_provider("myprovider", ["MYPROVIDER_API_KEY"])
class MyProvider(OpenAICompatibleProvider):
    config = ProviderConfig(
        name="myprovider",
        api_key_env="MYPROVIDER_API_KEY",
        base_url="https://api.myprovider.com/v1/chat/completions",
    )
```

### 3. Add dependencies (if needed)

If your provider requires a specific SDK, add it to `pyproject.toml` dependencies.

### 4. Update documentation

Add the provider to the supported providers list in `README.md`.

## Configuration Precedence

Configuration values are resolved in this order (highest to lowest priority):

1. **CLI arguments** - Flags like `--model`, `--language`, `--audience`
2. **Environment variables** - `KITTYLOG_MODEL`, `OPENAI_API_KEY`, etc.
3. **Config files** - Project `.kittylog.env` → User `~/.kittylog.env`
4. **Default values** - Built-in defaults from `EnvDefaults`

## Pull Request Process

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. Ensure the test suite passes
4. Make sure your code follows the style guidelines (`make format` and `make lint`)
5. Issue the pull request!

All PRs will automatically run pre-commit hooks and tests. Make sure to run `make check` locally to verify everything passes before submitting.
