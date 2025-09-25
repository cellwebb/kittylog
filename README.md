# kittylog

[![Quality Checks](https://github.com/cellwebb/kittylog/actions/workflows/ci.yml/badge.svg)](https://github.com/cellwebb/kittylog/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/kittylog.svg)](https://badge.fury.io/py/kittylog)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue.svg)](https://www.python.org/downloads/)
[![codecov](https://codecov.io/gh/cellwebb/kittylog/branch/main/graph/badge.svg)](https://codecov.io/gh/cellwebb/kittylog)
[![Code Style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
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

## Grouping Modes

kittylog supports three different grouping strategies to accommodate various project workflows:

### 🏷️ **Tags Mode** (default)
Uses git tags as changelog boundaries. Perfect for projects with consistent release tagging.
```bash
kittylog --grouping-mode tags  # Default behavior
```

### 📅 **Date Mode**
Groups commits by date (daily/weekly/monthly). Ideal for projects without regular tags.
```bash
kittylog --grouping-mode dates --date-grouping daily    # Group by day
kittylog --grouping-mode dates --date-grouping weekly   # Group by week
kittylog --grouping-mode dates --date-grouping monthly  # Group by month
```

### ⏱️ **Gap Mode**
Groups commits by activity sessions with configurable time gaps. Great for irregular development patterns.
```bash
kittylog --grouping-mode gaps --gap-threshold 4.0  # 4-hour gaps (default)
kittylog --grouping-mode gaps --gap-threshold 24   # 24-hour gaps
```

**When to use each mode:**
- **Tags**: Formal release process with semantic versioning
- **Dates**: Regular development without formal releases
- **Gaps**: Irregular development with distinct work sessions

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
1. Detects changelog boundaries using your chosen grouping mode (tags/dates/gaps)
2. Analyzes commits and file changes between boundaries
3. Generates categorized changelog entries with AI that understands the grouping context
4. Shows preview and prompts for confirmation
5. Updates your CHANGELOG.md file with properly formatted sections

See [USAGE.md](USAGE.md) for detailed documentation.

## Requirements

- Python 3.10+
- Git repository (tags optional - can use date/gap grouping)
- AI provider API key

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. This project uses kittylog to maintain its own changelog!

## License

MIT License - see [LICENSE](LICENSE) for details.
