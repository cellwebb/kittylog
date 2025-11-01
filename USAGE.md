# kittylog Usage

## Main Commands

### `kittylog` (default command)

Process git history to generate changelog entries. Defaults to interactive mode for guided setup.

**Options:**

- `-d, --dry-run`: Preview changes without modifying the changelog file
- `-y, --yes`: Skip confirmation prompts
- `-a, --all`: Update all entries (not just missing ones)
- `-f, --file`: Path to changelog file (default: CHANGELOG.md)
- `-s, --from-tag`: Start from specific tag
- `-t, --to-tag`: Update up to specific tag
- `-p, --show-prompt`: Show the prompt sent to the LLM
- `-h, --hint`: Additional context for the prompt
- `-l, --language`: Override the generated changelog language (name or locale code)
- `-u, --audience`: Choose tone for developers, users, or stakeholders
- `-m, --model`: Override default model
- `-q, --quiet`: Suppress non-error output
- `-v, --verbose`: Increase output verbosity to INFO
- `--log-level`: Set log level (DEBUG, INFO, WARNING, ERROR)
- `--no-unreleased`: Skip creating unreleased section
- `--include-diff`: Append git diff context (higher token usage warning)
- `-i/--interactive` or `--no-interactive`: Toggle guided configuration prompts
- `--grouping-mode {tags,dates,gaps}`: Choose how boundaries are detected
- `--gap-threshold FLOAT`: Hours of inactivity to split sections when using gap mode
- `--date-grouping {daily,weekly,monthly}`: Period length when grouping by dates
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
- `-l, --language`: Override the generated changelog language (name or locale code)
- `-u, --audience`: Choose tone for developers, users, or stakeholders
- `-m, --model`: Override default model
- `-q, --quiet`: Suppress non-error output
- `-v, --verbose`: Increase output verbosity to INFO
- `--log-level`: Set log level (DEBUG, INFO, WARNING, ERROR)
- `--no-unreleased`: Skip creating unreleased section
- `--include-diff`: Append git diff context (higher token usage warning)
- `-i/--interactive` or `--no-interactive`: Toggle guided configuration prompts
- `--grouping-mode {tags,dates,gaps}`: Choose how boundaries are detected
- `--gap-threshold FLOAT`: Hours of inactivity to split sections when using gap mode
- `--date-grouping {daily,weekly,monthly}`: Period length when grouping by dates
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

### `kittylog language`

Interactively select the default language and optional translated headings for changelog output.

### `kittylog init-changelog`

Create a starter `CHANGELOG.md` that follows Keep a Changelog conventions.

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

# Generate in Spanish for stakeholders
kittylog --language es --audience stakeholders

# Use date-based grouping with weekly sections
kittylog --grouping-mode dates --date-grouping weekly

# Include git diff context and auto-accept entries
kittylog --include-diff -y

# Add hints for AI
kittylog -h "Focus on breaking changes"

# Use different changelog file
kittylog -f CHANGES.md

# Use different AI model
kittylog -m "openai:gpt-4"
```
