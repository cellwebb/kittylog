# Qwen Code Context for kittylog

## 🚨 CRITICAL: AI AGENT COMMAND REQUIREMENTS

**ALWAYS use `uv run` prefix for ALL Python-related commands. NEVER use vanilla commands.**

### ✅ CORRECT (Always use these):
```bash
uv run python script.py          # NEVER: python script.py
uv run pytest                    # NEVER: pytest
uv run python -m pytest tests/   # NEVER: python -m pytest tests/
uv run python -c "print('test')" # NEVER: python -c "print('test')"
uv run ruff check .              # NEVER: ruff check .
uv run ruff format .             # NEVER: ruff format .
uv run mypy src/                 # NEVER: mypy src/
uv run pip install package      # NEVER: pip install package
```

### ❌ FORBIDDEN (Never use these):
- `python` (any form)
- `pytest` (any form) 
- `pip` (any form)
- `ruff` (any form)
- `mypy` (any form)
- `black`, `isort`, `flake8`, or any other Python tools

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
- **Multi-provider support** for Anthropic, OpenAI, Groq, Cerebras, Ollama models
- **Smart tag detection** - automatically detects which tags need changelog entries
- **Keep a Changelog format** with proper Added/Changed/Fixed categorization
- **Unreleased section** tracking for commits since last tag
- **Interactive workflow** - review and approve content before saving
- **Intelligent version detection** - avoids duplicates by comparing with existing changelog

### Technologies Used

- Python 3.10+
- GitPython for git operations
- Direct provider SDK integrations for AI (Anthropic, OpenAI, Groq, Cerebras, Ollama, Z.AI)
- Click for CLI interface
- Pydantic for data validation
- Rich for terminal output formatting
- pytest for testing
- ruff for linting and formatting

## Project Structure

```
.
├── src/kittylog/           # Main source code
│   ├── __init__.py
│   ├── __version__.py      # Version information
│   ├── ai.py               # AI integration for changelog generation
│   ├── changelog.py        # Changelog operations and parsing
│   ├── cli.py              # CLI entry point and command definitions
│   ├── config.py           # Configuration loading and validation
│   ├── constants.py        # Application constants
│   ├── errors.py           # Error handling
│   ├── git_operations.py   # Git operations for tag-based changelog generation
│   ├── main.py             # Business logic for changelog workflow
│   ├── output.py           # Unified output management
│   ├── postprocess.py      # Changelog content post-processing
│   ├── prompt.py           # AI prompt construction
│   ├── utils.py            # Utility functions
│   └── init_changelog.py   # Changelog initialization functionality
├── tests/                  # Test suite
├── assets/                 # Documentation assets
├── .github/workflows/      # CI/CD workflows
├── README.md               # Project overview
├── USAGE.md                # Detailed usage documentation
├── CONTRIBUTING.md         # Development guidelines
├── AGENTS.md               # AI agent documentation
├── pyproject.toml          # Project configuration and dependencies
├── Makefile                # Development commands
├── CHANGELOG.md            # Project changelog (maintained by kittylog itself)
└── QWEN.md                 # This file
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
pipx install kittylog
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

The project uses direct provider SDK integrations to support multiple AI providers:

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

Configuration is handled through environment variables or the `~/.kittylog.env` file.

## Core Modules

### CLI (`src/kittylog/cli.py`)

The command-line interface that defines all available commands and options. Uses Click for argument parsing.

### Main Business Logic (`src/kittylog/main.py`)

Orchestrates the changelog update workflow including git operations, AI generation, and file updates.

### AI Integration (`src/kittylog/ai.py`)

Handles AI model integration for generating changelog entries from commit data using direct provider SDKs.

### Git Operations (`src/kittylog/git_operations.py`)

Provides Git operations specifically focused on tag-based changelog generation.

### Changelog Operations (`src/kittylog/changelog.py`)

Handles reading, parsing, and updating changelog files using AI-generated content.

### Configuration (`src/kittylog/config.py`)

Loads configuration from environment variables and .env files with proper precedence.

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