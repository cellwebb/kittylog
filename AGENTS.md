# kittylog Project Overview

## Project Type

This is a Python-based CLI tool for generating changelog entries using AI analysis of git commits and tags. The project follows the "Keep a Changelog" format and supports multiple AI providers.

## Key Technologies

- Python 3.10+
- GitPython for git operations
- aisuite for multi-provider AI integration
- Click for CLI interface
- Pydantic for data validation
- Rich for terminal output formatting
- pytest for testing

## Project Structure

```
.
├── src/kittylog/           # Main source code
├── tests/                  # Test suite
├── assets/                 # Documentation assets
├── .github/workflows/      # CI/CD workflows
├── README.md               # Project overview
├── USAGE.md                # Detailed usage documentation
├── CONTRIBUTING.md         # Development guidelines
├── AGENTS.md               # AI agent documentation
├── pyproject.toml          # Project configuration and dependencies
├── Makefile                # Development commands
└── CHANGELOG.md            # Project changelog (maintained by kittylog itself)
```

## Core Functionality

- Automatically detects git tags missing from the changelog
- Analyzes commits between tags using AI to categorize changes
- Generates changelog entries in Keep a Changelog format (Added/Changed/Fixed sections)
- Supports multiple AI providers (Anthropic, OpenAI, Groq, Cerebras, Ollama)
- Interactive workflow with preview and confirmation
- Maintains an "Unreleased" section for commits since last tag

## Building and Running

### Installation

```bash
# Try without installing
uvx kittylog init  # Set up configuration
uvx kittylog       # Generate changelog

# Install permanently
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
2. Install dependencies with `uv pip install -e ".[dev,test]"` or use `make install-dev`
3. Install pre-commit hooks with `pre-commit install` (or use `make install-dev` which does this automatically)
4. Run tests with `pytest` or `make test`

### Development Commands

```bash
# Installation
make install-dev        # Install development dependencies and pre-commit hooks

# Testing
make test               # Run tests
make test-coverage      # Run tests with coverage report
make test-integration   # Run integration tests only
make test-watch         # Run tests in watch mode

# Code Quality
make lint               # Run linting (ruff check and mypy)
make format             # Format code (ruff format)
make check              # Run both linting and tests
make pre-commit         # Run all pre-commit hooks

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

## AI Integration

The project uses the `aisuite` library to support multiple AI providers:

- Anthropic Claude
- OpenAI GPT models
- Groq
- Cerebras
- Ollama (for local models)

Configuration is handled through environment variables or the `~/.kittylog.env` file.

## Contributing

Contributions are welcome! See CONTRIBUTING.md for detailed guidelines on:

- Setting up the development environment
- Code quality standards
- Testing practices
- Adding new AI providers
- Submitting pull requests
