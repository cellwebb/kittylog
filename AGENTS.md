# Qwen Code Context for kittylog

## 🚨 CRITICAL: AI AGENT COMMAND REQUIREMENTS

**ALWAYS use `uv run` prefix for ALL Python-related commands. NEVER use vanilla commands.**

### CORRECT (Always use these):
```bash
✅ uv run python script.py          # NEVER: python script.py
✅ uv run pytest                    # NEVER: pytest
✅ uv run python -m pytest tests/   # NEVER: python -m pytest tests/
✅ uv run python -c "print('test')" # NEVER: python -c "print('test')"
✅ uv run ruff check .              # NEVER: ruff check .
✅ uv run ruff format .             # NEVER: ruff format .
✅ uv run mypy src/                 # NEVER: mypy src/
✅ uv run pip install package      # NEVER: pip install package
```

### FORBIDDEN (Never use these):
❌ `python` (any form)
❌ `pytest` (any form) 
❌ `pip` (any form)
❌ `ruff` (any form)
❌ `mypy` (any form)
❌ `black`, `isort`, `flake8`, or any other Python tools

**Why?** All development tools must go through `uv run` to ensure:
- Proper environment isolation
- Consistent dependency resolution
- No interference with global Python installations
- Reliable tool execution across different systems

**This requirement is NON-NEGOTIABLE for AI agents working with this project.**

---

## Project Overview

**kittylog** is an AI-powered changelog generator that automatically analyzes git tags and commits to create well-structured changelog entries following the [Keep a Changelog](https://keepachangelog.com/) format. The tool uses multiple AI providers to categorize changes into sections like Added, Changed, Fixed, etc.

### Key Features

- **LLM-powered analysis** of commits, file changes, and code patterns to categorize changes
- **Multi-provider support** for 18+ AI providers (Anthropic, OpenAI, Groq, Cerebras, Ollama, and more)
- **Flexible boundary detection** - tags, dates, or time gaps for changelog grouping
- **Keep a Changelog format** with proper Added/Changed/Fixed categorization
- **Unreleased section** tracking for commits since last tag
- **Interactive workflow** - review and approve content before saving
- **Intelligent version detection** - avoids duplicates by comparing with existing changelog
- **Multilingual support** - 25+ languages with optional translated section headings
- **Audience presets** - tailor tone for developers, users, or stakeholders

### Technologies Used

- Python 3.10+
- GitPython for git operations
- Direct provider SDK integrations and httpx for AI (Anthropic, OpenAI, Groq, Cerebras, Ollama, etc.)
- Click for CLI interface
- Pydantic for data validation
- Rich for terminal output formatting
- pytest for testing
- ruff for linting and formatting

## Project Structure

```
.
├── src/kittylog/               # Main source code
│   ├── __init__.py
│   ├── __version__.py          # Version information
│   ├── ai.py                   # AI generation coordination
│   ├── ai_utils.py             # AI utility functions
│   ├── auth_cli.py             # Authentication CLI commands
│   ├── cache.py                # Caching functionality
│   ├── cli.py                  # Main CLI entry point and command definitions
│   ├── commit_analyzer.py      # Commit analysis and parsing
│   ├── errors.py               # Custom exception classes with context
│   ├── init_cli.py             # Initialization CLI commands
│   ├── language_cli.py         # Language management CLI
│   ├── main.py                 # Business logic orchestration
│   ├── model_cli.py            # Model management CLI
│   ├── output.py               # Unified output management
│   ├── postprocess.py          # Content post-processing
│   ├── prompt_cleaning.py      # Content cleaning and commit categorization
│   ├── release_cli.py          # Release management CLI
│   ├── tag_operations.py       # Tag-based git operations
│   ├── utils.py                # Utility functions
│   ├── workflow.py             # Main workflow logic
│   ├── workflow_ui.py          # Dry-run and confirmation UI handling
│   ├── workflow_validation.py  # Workflow prerequisite validation
│   ├── changelog/              # Changelog operations package
│   │   ├── __init__.py         # Public API exports
│   │   ├── boundaries.py       # Boundary detection logic
│   │   ├── content.py          # Changelog content handling
│   │   ├── insertion.py        # Changelog insertion logic
│   │   ├── io.py               # Read, write, create header
│   │   └── updater.py          # Update logic
│   ├── config/                 # Configuration management
│   │   ├── __init__.py         # Configuration exports
│   │   ├── cli.py              # Configuration CLI options
│   │   ├── data.py             # Configuration data structures
│   │   ├── loader.py           # Configuration loading logic
│   │   ├── options.py          # Configuration options
│   │   └── secure.py           # Secure configuration handling
│   ├── constants/              # Configuration constants package
│   │   ├── __init__.py         # Constants re-exports
│   │   ├── audiences.py        # Audience definitions
│   │   ├── changelog_sections.py # Changelog section constants
│   │   ├── commit_keywords.py  # Commit parsing keywords
│   │   ├── enums.py            # Enum definitions
│   │   ├── env_defaults.py     # Environment defaults
│   │   ├── languages.py        # Language definitions (25+ supported)
│   │   ├── limits.py           # Various limits and constraints
│   │   ├── logging.py          # Logging configuration
│   │   └── utility.py          # Utility constants
│   ├── mode_handlers/          # Processing mode handlers
│   │   ├── __init__.py         # Mode handler exports
│   │   ├── boundary.py         # Boundary mode processing
│   │   ├── missing.py          # Missing entries mode processing
│   │   └── unreleased.py       # Unreleased section processing
│   ├── oauth/                  # OAuth and authentication
│   │   ├── __init__.py         # OAuth exports
│   │   ├── claude_code.py      # Claude Code OAuth implementation
│   │   ├── qwen_oauth.py       # Qwen OAuth implementation
│   │   └── token_store.py      # Token storage and retrieval
│   ├── prompt/                 # Prompt generation and templates
│   │   ├── __init__.py         # Prompt module exports
│   │   ├── detail_limits.py    # Prompt detail limitation
│   │   ├── system.py           # Base system prompts
│   │   ├── system_developers.py # Developer-focused system prompts
│   │   ├── system_stakeholders.py # Stakeholder-focused system prompts
│   │   ├── system_users.py     # User-focused system prompts
│   │   └── user.py             # User prompt generation
│   ├── providers/              # AI provider implementations (25+ providers)
│   │   ├── README.md           # Provider development documentation
│   │   ├── __init__.py         # Provider registry and auto-discovery
│   │   ├── base.py             # Base provider ABC and configuration
│   │   ├── error_handler.py    # Provider error handling decorator
│   │   ├── protocol.py         # Provider protocol definitions
│   │   ├── registry.py         # Provider registry
│   │   ├── [25+ provider files] # Individual providers (OpenAI, Claude, Groq, etc.)
│   │   └── [custom providers]   # Custom endpoint implementations
│   ├── ui/                     # User interface components
│   │   ├── __init__.py         # UI exports
│   │   ├── banner.py           # Terminal banner display
│   │   └── prompts.py          # Interactive prompt handling
│   └── utils/                  # Utility functions
│       ├── __init__.py         # Utils exports
│       ├── commit.py           # Commit utility functions
│       ├── logging.py          # Logging utilities
│       ├── system.py           # System utility functions
│       └── text.py             # Text processing utilities
├── tests/                      # Comprehensive test suite (200+ tests)
│   ├── __init__.py
│   ├── conftest.py             # pytest configuration and fixtures
│   ├── fixtures.py             # Test fixtures and helpers
│   ├── oauth/                  # OAuth-related tests
│   │   ├── __init__.py
│   │   ├── test_claude_code_oauth.py
│   │   ├── test_qwen_oauth.py
│   │   ├── test_reauth.py
│   │   └── test_token_store.py
│   ├── providers/              # Provider-specific tests
│   │   ├── __init__.py
│   │   ├── conftest.py         # Provider test configuration
│   │   └── [test files for each provider] # Individual provider test files
│   ├── test_ai.py              # AI generation tests
│   ├── test_boundary_filtering_integration.py
│   ├── test_boundary_insertion_order.py
│   ├── test_bullet_limiting.py
│   ├── test_changelog.py       # Changelog operation tests
│   ├── test_changelog_discovery.py
│   ├── test_cli.py             # CLI tests
│   ├── test_config.py          # Configuration tests
│   ├── test_confirmation_functionality.py
│   ├── test_context_entries.py
│   ├── test_edge_cases.py
│   ├── test_error_paths.py
│   ├── test_errors.py
│   ├── test_git.py             # Git operation tests
│   ├── test_integration.py     # Integration tests
│   ├── test_language_cli.py
│   ├── test_language_codes.py
│   ├── test_main.py            # Main workflow tests
│   ├── test_missing_entries_mode.py
│   ├── test_postprocess.py
│   └── test_utils.py           # Utility function tests
├── assets/                     # Documentation assets
│   └── kittylog-usage.png      # Usage demonstration image
├── README.md                   # Project overview
├── USAGE.md                    # Detailed usage documentation
├── CONTRIBUTING.md             # Development guidelines
├── AGENTS.md                   # AI agent documentation (this file)
├── pyproject.toml              # Project configuration and dependencies
├── uv.lock                     # UV package manager lockfile
├── mypy.ini                    # MyPy type checking configuration
└── CHANGELOG.md                # Project changelog (maintained by kittylog itself)
```

## Building and Running

### Installation

**Try without installing:**

```sh
uvx kittylog init  # Set up configuration
uvx kittylog       # Generate changelog
```

**Install permanently:**

```sh
uv tool install kittylog
kittylog init  # Interactive setup
```

### Usage Examples

```bash
# Basic usage - process missing tags
kittylog

# Process all tags (not just missing ones)
kittylog --all

# Auto-accept changes without confirmation
kittylog -y

# Preview without saving
kittylog --dry-run

# Process specific tag range
kittylog --from-tag v1.0.0 --to-tag v1.2.0

# Update specific version
kittylog update v1.1.0

# Skip creating unreleased section
kittylog --no-unreleased

# Show AI prompt
kittylog --show-prompt

# Add hints for AI
kittylog -h "Focus on breaking changes"

# Use different changelog file
kittylog -f CHANGES.md

# Use different AI model
kittylog -m "openai:gpt-4"

# Grouping modes (alternative to tags)
kittylog --grouping-mode dates --date-grouping weekly
kittylog --grouping-mode gaps --gap-threshold 6

# Multilingual and audience options
kittylog --language es --audience stakeholders
kittylog --language ja --translate-headings

# Include git diff for deeper analysis
kittylog --include-diff -y
```

## Development Setup

1. Clone the repo
2. Install dependencies with `uv run pip install -e ".[dev,test]"` or use `make install-dev`
3. Install pre-commit hooks with `uv run pre-commit install` (or use `make install-dev` which does this automatically)
4. Run tests with `uv run pytest` or `make test`

**🚨 REMINDER FOR AI AGENTS:** ALL Python commands MUST use `uv run` prefix:
- Use `uv run python` instead of `python`
- Use `uv run pytest` instead of `pytest`
- Use `uv run python -m pytest` for specific test modules
- Use `uv run python -c "..."` for inline Python execution
- Use `uv run ruff check/format` instead of `ruff check/format`
- Use `uv run pip install` instead of `pip install`
- Use `uv run pre-commit install` instead of `pre-commit install`

**NO EXCEPTIONS!**

### Development Commands

```bash
# Installation
make install-dev        # Install development dependencies and pre-commit hooks

# Testing
make test               # Run tests
make test-coverage      # Run tests with coverage report
make test-integration   # Run integration tests only
make test-watch         # Run tests in watch mode
# Agent-specific commands:
uv run pytest                               # Run tests directly
uv run python -m pytest tests/module.py    # Run specific test module
uv run python -m pytest tests/module.py::test_name  # Run specific test

# Code Quality
make lint               # Run linting (ruff check and mypy)
make format             # Format code (ruff format)
make check              # Run both linting and tests
make pre-commit         # Run all pre-commit hooks
# Agent-specific commands:
uv run ruff check .                        # Run linting directly
uv run ruff format .                       # Format code directly
uv run mypy src/                          # Run type checking directly

# Other
make clean              # Clean build artifacts
make build              # Build distribution packages
make quickstart         # Quick setup for new contributors
```

## Development Conventions

- Code formatting with `ruff format` (replaces black and isort)
- Linting with `ruff check`
- Type checking with `mypy`
- Tests written with `pytest`
- All new features should include tests
- Follow Keep a Changelog format for changelog entries
- Use conventional commit messages
- All code quality checks are run through pre-commit hooks
- Use `uv` or `uvx` for package management and tool execution instead of `pip` when possible, including for tools like `ruff`
- **For AI agents:** ALWAYS use `uv run` prefix for executing Python, pytest, ruff, mypy, and other development tools to ensure proper environment isolation and dependency management

## AI Integration

The project uses a base class architecture with automatic provider registration:

### Provider Base Classes

- **`OpenAICompatibleProvider`** - For OpenAI-compatible APIs (OpenAI, Groq, Cerebras, Together, Fireworks, etc.)
- **`AnthropicCompatibleProvider`** - For Anthropic and custom Anthropic endpoints
- **`OllamaProvider`** - For local Ollama models

### Adding New Providers

New providers are added via the `@register_provider` decorator:

```python
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

### Supported Providers

- Anthropic Claude
- Cerebras
- Chutes.ai
- Custom Anthropic-compatible endpoints
- Custom OpenAI-compatible endpoints (Azure/proxies)
- DeepSeek
- Fireworks AI
- Gemini
- Groq
- LM Studio
- MiniMax
- Mistral
- Ollama (for local models)
- OpenAI GPT models
- OpenRouter
- StreamLake (Vanchin)
- Synthetic.new
- Together AI
- Z.AI (standard and coding APIs)

### Configuration Precedence

Configuration values are resolved in this order (highest to lowest priority):

1. **CLI arguments** - `--model`, `--language`, `--audience`, etc.
2. **Environment variables** - `KITTYLOG_MODEL`, `OPENAI_API_KEY`, etc.
3. **Config files** - Project `.kittylog.env` → User `~/.kittylog.env`
4. **Default values** - Built-in defaults from `EnvDefaults`

## Core Modules

### CLI (`src/kittylog/cli.py`)

The command-line interface that defines all available commands and options. Uses Click for argument parsing with shared option decorators (`workflow_options`, `changelog_options`, `model_options`).

### Main Business Logic (`src/kittylog/main.py`)

Orchestrates the changelog update workflow including git operations, AI generation, and file updates.

### Workflow Modules

- **`workflow.py`** - Main workflow logic and processing
- **`workflow_validation.py`** - Workflow prerequisite validation
- **`workflow_ui.py`** - Dry-run and confirmation UI handling

### AI Integration (`src/kittylog/ai.py`)

Coordinates AI generation for changelog entries, delegating to the providers package.

### Prompt Modules

- **`prompt.py`** - Public interface for building prompts
- **`prompt_templates.py`** - System and user prompt templates
- **`prompt_cleaning.py`** - Content cleaning and commit categorization

### Git Operations (`src/kittylog/git_operations.py`)

Provides Git operations specifically focused on tag-based changelog generation.

### Changelog Package (`src/kittylog/changelog/`)

- **`io.py`** - Read, write, create header operations
- **`parser.py`** - Find boundaries, insertion points, extract entries
- **`updater.py`** - Update logic

### Constants Package (`src/kittylog/constants/`)

- **`languages.py`** - Languages class (25+ supported languages)
- **`audiences.py`** - Audiences class (developers, users, stakeholders)
- **`env_defaults.py`** - EnvDefaults and Limits classes
- **`enums.py`** - GroupingMode, DateGrouping, FileStatus, etc.

### Configuration (`src/kittylog/config/`)

Loads configuration using `KittylogConfigData` dataclass with type-safe access. Handles environment variables and .env files with proper precedence.

### Providers Package (`src/kittylog/providers/`)

- **`base.py`** - `BaseConfiguredProvider` ABC with `ProviderConfig` dataclass
- **`openai_compat.py`** - OpenAI-compatible providers
- **`anthropic_compat.py`** - Anthropic-compatible providers
- **`ollama.py`** - Ollama local models
- **`error_handler.py`** - `@handle_provider_errors` decorator for consistent error handling

## Contributing

Contributions are welcome! See CONTRIBUTING.md for detailed guidelines on:

- Setting up the development environment
- Code quality standards
- Testing practices
- Adding new AI providers
- Submitting pull requests

## Environment Variables

The tool can be configured through environment variables or a `~/.kittylog.env` file:

- `KITTYLOG_MODEL` - AI model to use (e.g., "openai:gpt-4", "anthropic:claude-3-5-sonnet-latest")
- `KITTYLOG_TEMPERATURE` - AI model temperature (0.0-2.0, default: 0.7)
- `KITTYLOG_MAX_OUTPUT_TOKENS` - Maximum output tokens (default: 1024)
- `KITTYLOG_RETRIES` - Maximum retry attempts (default: 3)
- `KITTYLOG_LOG_LEVEL` - Log level (DEBUG, INFO, WARNING, ERROR, default: WARNING)

API keys and related settings for different providers:

- `ANTHROPIC_API_KEY`
- `CEREBRAS_API_KEY`
- `CHUTES_API_KEY`
- `CHUTES_BASE_URL`
- `CUSTOM_ANTHROPIC_API_KEY`
- `CUSTOM_ANTHROPIC_BASE_URL`
- `CUSTOM_ANTHROPIC_VERSION`
- `CUSTOM_OPENAI_API_KEY`
- `CUSTOM_OPENAI_BASE_URL`
- `DEEPSEEK_API_KEY`
- `FIREWORKS_API_KEY`
- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `LMSTUDIO_API_KEY`
- `LMSTUDIO_API_URL`
- `MINIMAX_API_KEY`
- `MISTRAL_API_KEY`
- `OLLAMA_API_URL`
- `OLLAMA_HOST` (legacy compatibility)
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`
- `STREAMLAKE_API_KEY` (alias: `VC_API_KEY`)
- `SYNTHETIC_API_KEY` or `SYN_API_KEY`
- `TOGETHER_API_KEY`
- `ZAI_API_KEY`
- Provider-specific keys as required

## Testing

The project has comprehensive test coverage with 200+ tests. Tests are written using pytest and can be run with:

```bash
make test
# or (for agents)
uv run pytest
# or (for specific modules)
uv run python -m pytest tests/test_config.py
# or (for specific tests)
uv run python -m pytest tests/test_config.py::TestLoadConfig::test_load_config_from_user_env_file
```

**🚨 CRITICAL FOR AI AGENTS:**
- **ALWAYS** use `uv run pytest` instead of `pytest`
- **ALWAYS** use `uv run python -m pytest` for specific modules
- **ALWAYS** use full module path format for individual tests
- **NEVER** use any form of testing command without `uv run` prefix
- All test execution MUST go through `uv run` to maintain consistency

Tests are isolated from global configuration files to prevent side effects during execution.
