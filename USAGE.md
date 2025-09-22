# clog Usage

## Main Commands

### `clog` (default command)

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
- `tag`: Specific tag to process (optional argument)

### `clog update`

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
- `version`: Specific version to update (optional argument)

### `clog unreleased`

Generate unreleased changelog entries

**Options:**

- `--version`: Same as main command options
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

## Configuration Commands

### `clog config`

Manage clog configuration in $HOME/.clog.env

**Subcommands:**

- `show`: Display all current config values
- `set <key> <value>`: Set a config key to value
- `get <key>`: Get a config value by key
- `unset <key>`: Remove a config key

### `clog init`

Interactively set up $HOME/.clog.env for clog

No arguments or options - runs interactive setup wizard.

## Usage Examples

```bash
# Basic usage - process missing tags
clog

# Process all tags (not just missing ones)
clog --all

# Auto-accept changes without confirmation
clog -y

# Preview without saving
clog --dry-run

# Process specific tag range
clog --from-tag v1.0.0 --to-tag v1.2.0

# Update specific version
clog update v1.1.0

# Generate unreleased changes only
clog unreleased

# Replace existing unreleased content
clog

# Show AI prompt
clog --show-prompt

# Add hints for AI
clog -h "Focus on breaking changes"

# Use different changelog file
clog -f CHANGES.md

# Use different AI model
clog -m "openai:gpt-4"
```
