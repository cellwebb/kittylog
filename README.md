# clog

[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue.svg)](https://www.python.org/downloads/)
[![Code Style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

- **AI-Powered Changelog Generation:** Automatically generates clear, comprehensive changelog entries using large language models.
- **Git Tag Integration:** Uses git tags to automatically detect version changes and generate appropriate changelog sections.
- **Unreleased Changes Support:** Automatically tracks changes since the last git tag in an "Unreleased" section.
- **Dogfooding:** This project uses `clog` to maintain its own `CHANGELOG.md` file!
- **Smart Change Analysis:** Analyzes commit messages, file changes, and code patterns to categorize changes appropriately.
- **Multi-Provider & Model Support:** Works with various AI providers (Anthropic, Cerebras, Groq, OpenAI, Ollama) and models.
- **Keep a Changelog Format:** Follows the [Keep a Changelog](https://keepachangelog.com/) standard format with proper categorization.
- **Intelligent Version Detection:** Automatically detects which tags need changelog entries by comparing with existing changelog content.
- **Interactive Workflow:** Review and approve generated content before updating your changelog.


## How It Works

clog analyzes your git tags and commits to generate changelog entries. It examines:

- **Git Tags**: Identifies version releases and their associated commits
- **Commit History**: Analyzes commit messages and changed files between versions
- **Existing Changelog**: Detects what's already documented to avoid duplicates
- **Change Categorization**: Uses AI to properly categorize changes as Added, Changed, Fixed, etc.

### Technical Architecture

- **Smart Tag Detection**: Automatically finds new tags since the last changelog update
- **Commit Analysis**: Examines commit messages, file changes, and code patterns
- **AI-Powered Generation**: Uses structured prompts to generate well-organized changelog entries
- **Format Compliance**: Ensures output follows Keep a Changelog standards

## How to Use

After setting up the tool, updating your changelog is simple:

```sh
# Run from your git repository root
clog

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
clog -p

# This will:
# 1. Detect new git tags (or specified range)
# 2. Analyze commits for each new version
# 3. Generate changelog entries using AI
# 4. Show preview and ask for confirmation
# 5. Create a new branch with the changelog updates
# 6. Commit the changes
# 7. Push the branch to origin
# 8. Create a pull request using GitHub CLI
```

![Simple clog Usage](assets/clog-usage.png)

## Installation and Configuration

### 1. Installation

#### Quick Try with uvx (no installation)

You can try clog without installing it using uvx:

```sh
# Try clog without installation
uvx clog --help

# Set up configuration (creates ~/.clog.env)
uvx clog init

# Use clog in your git repository
cd your-project
uvx clog
```

#### Permanent Installation

Install system-wide using pipx:

```sh
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install clog
pipx install clog
```

Verify installation:

```sh
clog --version
```

### 2. Configuration

The recommended way to configure `clog` is using the interactive setup:

```sh
clog init
```

This command will guide you through selecting an AI provider, model, and securely entering your API keys. It will create or update a user-level configuration file at `$HOME/.clog.env`.

Example `$HOME/.clog.env` output:

```env
CLOG_MODEL=anthropic:claude-3-5-haiku-latest
ANTHROPIC_API_KEY=your_anthropic_key_here
```

#### Managing Configuration with `clog config`

You can manage settings in your `$HOME/.clog.env` file using config commands:

- Show config: `clog config show`
- Set a value: `clog config set CLOG_MODEL groq:meta-llama/llama-4-scout-17b-16e-instruct`
- Get a value: `clog config get CLOG_MODEL`
- Unset a value: `clog config unset CLOG_MODEL`

### 3. Verify Setup

Test that `clog` is working properly with your configuration:

```sh
# Make sure you have some git tags in your repository
git tag v0.1.0
git tag v0.2.0

# Run clog to generate entries
clog --dry-run
```

You should see an AI-generated changelog preview.

### Command Line Options

The `clog update` command supports several options:

- `-d, --dry-run`: Preview changes without modifying the changelog file
- `-y, --yes`: Skip confirmation prompts
- `-f, --file`: Specify a different changelog file path (default: CHANGELOG.md)
- `-s, --from-tag`: Specify the starting tag for changelog generation
- `-t, --to-tag`: Specify the ending tag for changelog generation
- `-p, --show-prompt`: Display the prompt sent to the AI model
- `-h, --hint`: Provide additional context to guide the AI model
- `-m, --model`: Override the configured AI model
- `-q, --quiet`: Suppress non-error output messages
- `-v, --verbose`: Increase output verbosity to INFO
- `--log-level`: Set a specific logging level
- `--replace-unreleased`: Replace existing unreleased content instead of appending to it

### 4. Upgrade

To upgrade `clog` to the latest version, run:

```sh
pipx upgrade clog
```

## Basic Usage

Once installed and configured, using `clog` is straightforward:

1. Make sure you have git tags in your repository:

   ```sh
   git tag v1.0.0
   git tag v1.1.0
   ```

2. Run `clog`:

   ```sh
   clog
   ```

   This will detect new tags, analyze commits, and generate changelog entries for review.

### Common Commands

- Generate changelog entries: `clog`
- Auto-accept the generated content: `clog -y`
- Preview without saving: `clog --dry-run`
- Process specific tag range: `clog --from-tag v1.0.0 --to-tag v1.2.0`
- Add hints for the AI: `clog -h "Focus on breaking changes"`
- Use different changelog file: `clog -f CHANGES.md`
- Show the AI prompt: `clog --show-prompt`

### Unreleased Changes

When you have commits that haven't been tagged yet, clog will automatically include them in
an "Unreleased" section at the top of your changelog. This is useful for tracking ongoing
changes between official releases.

By default, clog will append new unreleased changes to any existing unreleased section. If you
want to replace the existing unreleased content entirely (useful when you've made significant
changes and want a fresh AI-generated summary), use the `--replace-unreleased` option:

```bash
clog --replace-unreleased
```

This will replace everything in your current unreleased section with a new AI-generated summary
based on all commits since your last tag.

### Advanced Usage Examples

```sh
# Process only new tags since last update
clog

# Process specific version range
clog --from-tag v1.0.0 --to-tag v1.2.0

# Dry run with AI hints
clog --dry-run -h "Focus on user-facing changes"

# Use different model
clog -m "openai:gpt-4"

# Different changelog file location
clog -f docs/CHANGELOG.md

# Create a pull request with changelog updates
clog -p
```

## Configuration Options

clog loads configuration from two locations (in order of precedence):

1. User-level `$HOME/.clog.env` (applies to all projects for the user)
2. Project-level `.clog.env` (in the project root, overrides user config)

Environment variables always take final precedence over both files.

### Available Configuration Variables

- `CLOG_MODEL`: AI model to use (e.g., "anthropic:claude-3-5-haiku-latest")
- `CLOG_TEMPERATURE`: Model temperature (0.0-2.0, default: 0.7)
- `CLOG_MAX_OUTPUT_TOKENS`: Maximum tokens for AI response (default: 1024)
- `CLOG_WARNING_LIMIT_TOKENS`: Warn when prompt exceeds this limit (default: 16384)
- `CLOG_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Best Practices

- **Tag Consistently**: Use semantic versioning for your git tags (v1.0.0, v1.1.0, etc.)
- **Write Good Commit Messages**: Clear commit messages help generate better changelog entries
- **Review Before Saving**: Always review AI-generated content before accepting
- **Keep API Keys Secure**: Use the config commands to manage API keys safely
- **Regular Updates**: Run clog after each release to keep your changelog current

## Requirements

- Python 3.10 or higher
- Git repository with tags
- AI provider API key (Anthropic, OpenAI, Groq, etc.)
- GitHub CLI installed and configured (required for PR creation functionality)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

For information about AI agent integrations, see [AGENTS.md](AGENTS.md).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Community & Support

For questions, suggestions, or support, please open an issue or discussion on GitHub.