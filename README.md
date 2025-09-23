# kittylog

[![Quality Checks](https://github.com/cellwebb/kittylog/actions/workflows/ci.yml/badge.svg)](https://github.com/cellwebb/kittylog/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/kittylog.svg)](https://badge.fury.io/py/kittylog)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue.svg)](https://www.python.org/downloads/)
[![codecov](https://codecov.io/gh/cellwebb/kittylog/branch/main/graph/badge.svg)](https://codecov.io/gh/cellwebb/kittylog)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**LLM-powered changelog generation from git tags and commits.** Automatically analyzes your repository history to create well-structured changelog entries following the [Keep a Changelog](https://keepachangelog.com/) format.

## Key Features

- **LLM-powered analysis** of commits, file changes, and code patterns to categorize changes
- **Multi-provider support** for Anthropic, OpenAI, Groq, Cerebras, Ollama models
- **Smart tag detection** - automatically detects which tags need changelog entries
- **Keep a Changelog format** with proper Added/Changed/Fixed categorization
- **Unreleased section** tracking for commits since last tag
- **Interactive workflow** - review and approve content before saving
- **Intelligent version detection** - avoids duplicates by comparing with existing changelog

## Installation

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

## Usage

```sh
# Basic usage (from git repository root)
kittylog

# Common options
kittylog --dry-run              # Preview only
kittylog -y                     # Auto-accept
kittylog -h "Breaking changes"  # Add context hint
```

![Simple kittylog Usage](assets/kittylog-usage.png)

**How it works:**
1. Detects new git tags since last changelog update
2. Analyzes commits and file changes between versions
3. Generates categorized changelog entries with AI
4. Shows preview and prompts for confirmation
5. Updates your CHANGELOG.md file

See [USAGE.md](USAGE.md) for detailed documentation.

## Requirements

- Python 3.10+
- Git repository with tags
- AI provider API key

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. This project uses kittylog to maintain its own changelog!

## License

MIT License - see [LICENSE](LICENSE) for details.
