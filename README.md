# kittylog

[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue.svg)](https://www.python.org/downloads/)
[![Code Style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

- **AI-Powered Changelog Generation:** Automatically generates clear, comprehensive changelog entries using large language models.
- **Git Tag Integration:** Uses git tags to automatically detect version changes and generate appropriate changelog sections.
- **Unreleased Changes Support:** Automatically tracks changes since the last git tag in an "Unreleased" section.
- **Dogfooding:** This project uses `kittylog` to maintain its own `CHANGELOG.md` file!
- **Smart Change Analysis:** Analyzes commit messages, file changes, and code patterns to categorize changes appropriately.
- **Multi-Provider & Model Support:** Works with various AI providers (Anthropic, Cerebras, Groq, OpenAI, Ollama) and models.
- **Keep a Changelog Format:** Follows the [Keep a Changelog](https://keepachangelog.com/) standard format with proper categorization.
- **Intelligent Version Detection:** Automatically detects which tags need changelog entries by comparing with existing changelog content.
- **Interactive Workflow:** Review and approve generated content before updating your changelog.

## How It Works

kittylog analyzes your git tags and commits to generate changelog entries. It examines:

- **Git Tags**: Identifies version releases and their associated commits
- **Commit History**: Analyzes commit messages and changed files between versions
- **Existing Changelog**: Detects what's already documented to avoid duplicates
- **Change Categorization**: Uses AI to properly categorize changes as Added, Changed, Fixed, etc.

## Quick Start

After setting up the tool, updating your changelog is simple:

```sh
# Run from your git repository root
kittylog

# This will:
# 1. Detect new git tags since last changelog update
# 2. Analyze commits for each new version
# 3. Generate changelog entries using AI
# 4. Show preview and ask for confirmation
# 5. Update your CHANGELOG.md file
```

To create a pull request with your changelog updates:

```sh
# Create a pull request with changelog updates
kittylog -p
```

![Simple kittylog Usage](assets/kittylog-usage.png)

## Installation and Configuration

### 1. Installation

#### Quick Try with uvx (no installation)

You can try kittylog without installing it using uvx:

```sh
# Try kittylog without installation
uvx kittylog --help

# Set up configuration (creates ~/.kittylog.env)
uvx kittylog init

# Use kittylog in your git repository
cd your-project
uvx kittylog
```

#### Permanent Installation

Install system-wide using pipx:

```sh
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install kittylog
pipx install kittylog
```

Verify installation:

```sh
kittylog --version
```

### 2. Configuration

The recommended way to configure `kittylog` is using the interactive setup:

```sh
kittylog init
```

This command will guide you through selecting an AI provider, model, and securely entering your API keys. It will create or update a user-level configuration file at `$HOME/.kittylog.env`.

See [USAGE.md](USAGE.md) for detailed command information.

#### Managing Configuration

You can manage settings in your `$HOME/.kittylog.env` file using config commands:

- Show config: `kittylog config show`
- Set a value: `kittylog config set KITTYLOG_MODEL groq:meta-llama/llama-4-scout-17b-16e-instruct`
- Get a value: `kittylog config get KITTYLOG_MODEL`
- Unset a value: `kittylog config unset KITTYLOG_MODEL`

See [USAGE.md](USAGE.md) for detailed command information.

### 3. Verify Setup

Test that `kittylog` is working properly with your configuration:

```sh
# Make sure you have some git tags in your repository
git tag v0.1.0
git tag v0.2.0

# Run kittylog to generate entries
kittylog --dry-run
```

You should see an AI-generated changelog preview.

### 4. Upgrade

To upgrade `kittylog` to the latest version, run:

```sh
pipx upgrade kittylog
```

## Usage

Once installed and configured, using `kittylog` is straightforward:

1. Make sure you have git tags in your repository:

   ```sh
   git tag v1.0.0
   git tag v1.1.0
   ```

2. Run `kittylog`:

   ```sh
   kittylog
   ```

   This will detect new tags, analyze commits, and generate changelog entries for review.

### Common Commands

- Generate changelog entries: `kittylog`
- Auto-accept the generated content: `kittylog -y`
- Preview without saving: `kittylog --dry-run`
- Process specific tag range: `kittylog --from-tag v1.0.0 --to-tag v1.2.0`
- Add hints for the AI: `kittylog -h "Focus on breaking changes"`
- Use different changelog file: `kittylog -f CHANGES.md`
- Show the AI prompt: `kittylog --show-prompt`

See [USAGE.md](USAGE.md) for comprehensive usage documentation and examples.

## Best Practices

- **Tag Consistently**: Use semantic versioning for your git tags (v1.0.0, v1.1.0, etc.)
- **Write Good Commit Messages**: Clear commit messages help generate better changelog entries
- **Review Before Saving**: Always review AI-generated content before accepting
- **Keep API Keys Secure**: Use the config commands to manage API keys safely
- **Regular Updates**: Run kittylog after each release to keep your changelog current

## Requirements

- Python 3.10 or higher
- Git repository with tags
- AI provider API key (Anthropic, OpenAI, Groq, etc.)
- GitHub CLI installed and configured (required for PR creation functionality)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## AI Agents

kittylog uses AI agents to analyze git commit history and generate changelog entries. See [AGENTS.md](AGENTS.md) for detailed information about the agents and their integration points.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Community & Support

For questions, suggestions, or support, please open an issue or discussion on GitHub.
