# kittylog Usage

## Main Commands

### `kittylog` (default command)

Process git tags to generate changelog entries

**Options:**

- `-d, --dry-run`: Preview changes without modifying the changelog file
- `-y, --yes`: Skip confirmation prompts
- `-a, --all`: Update all entries (not just missing ones)
- `-f, --file`: Path to changelog file (default: CHANGELOG.md)
- `-s, --from-tag`: Start from specific tag
- `-t, --to-tag`: Update up to specific tag
- `-p, --show-prompt`: Show the prompt sent to the LLM
- `-h, --hint`: Additional context for the prompt
- `-m, --model`: Override default model
- `-q, --quiet`: Suppress non-error output
- `-v, --verbose`: Increase output verbosity to INFO
- `--log-level`: Set log level (DEBUG, INFO, WARNING, ERROR)
- `--no-unreleased`: Skip creating unreleased section
- `tag`: Specific tag to process (optional argument)

### `kittylog update`

Update changelog for a specific version or all missing tags

**Options:**

- `-d, --dry-run`: Preview changes without modifying the changelog file
- `-y, --yes`: Skip confirmation prompts
- `-a, --all`: Update all entries (not just missing ones)
- `-f, --file`: Path to changelog file (default: CHANGELOG.md)
- `-s, --from-tag`: Start from specific tag
- `-t, --to-tag`: Update up to specific tag
- `-p, --show-prompt`: Show the prompt sent to the LLM
- `-h, --hint`: Additional context for the prompt
- `-m, --model`: Override default model
- `-q, --quiet`: Suppress non-error output
- `-v, --verbose`: Increase output verbosity to INFO
- `--log-level`: Set log level (DEBUG, INFO, WARNING, ERROR)
- `--no-unreleased`: Skip creating unreleased section
- `version`: Specific version to update (optional argument)

## Configuration Commands

### `kittylog config`

Manage kittylog configuration in $HOME/.kittylog.env

**Subcommands:**

- `show`: Display all current config values
- `set <key> <value>`: Set a config key to value
- `get <key>`: Get a config value by key
- `unset <key>`: Remove a config key

### `kittylog init`

Interactively set up $HOME/.kittylog.env for kittylog

No arguments or options - runs interactive setup wizard.

## Usage Examples

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
