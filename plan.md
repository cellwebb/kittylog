# CLI Consolidation Plan for kittylog

## Current State Analysis

### Existing Commands Structure
```
kittylog                          # Main command (invokes add_cli)
├── add [version]                # Full-featured, default command
├── update [version]             # Partial features, missing 8+ options
├── release <version>            # Prepare changelog release
├── config                       # Manage configuration
├── init                         # Interactive setup
├── language / lang              # Set language interactively
├── model                        # Set model/provider interactively
└── auth                         # OAuth authentication
```

### Problems with Current Structure
1. **`add`** and **`update`** do the same thing but `update` is missing options:
   - Missing: `--interactive`, `--grouping-mode`, `--gap-threshold`, `--date-grouping`
   - Missing: `--context-entries`, `--detail`, `--incremental-save`, `--include-diff`
2. **`add`** as the default is confusing—users expect to "update" a changelog
3. The default `cli()` function manually passes 20+ parameters (fragile)
4. Two separate files (`cli.py` and `update_cli.py`) with duplicated logic

## Proposed Structure
```
kittylog                          # Main command group
├── [no subcommand]              # Default: invokes `update`
├── update [version]             # Unified changelog update command
├── release <version>            # Keep as-is
├── config                       # Keep as-is
├── init                         # Keep as-is
├── language / lang              # Keep as-is
├── model                        # Keep as-is
└── auth                         # Keep as-is
```

## Implementation Plan

### Step 1: Rename `add_cli` → `update_cli` in cli.py

Rename the function and update help text:

```python
@click.command(context_settings={"ignore_unknown_options": True})
@common_options
@click.argument("version", required=False)  # Rename 'tag' to 'version' for clarity
def update_cli(version: str | None = None, **kwargs) -> None:
    """Update changelog entries.

    Without arguments: Update missing entries
    With version: Update specific version
    With --all: Update all entries
    With --from/--to: Update specific range
    """
    # ... existing add_cli logic unchanged
```

### Step 2: Fix the Default Invocation

Replace the fragile 20+ parameter manual invocation with decorator forwarding:

```python
@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show the kittylog version")
@common_options
@click.argument("version_arg", required=False)
@click.pass_context
def cli(ctx, version, version_arg, **kwargs):
    """kittylog - Generate polished changelog entries from your git history."""
    if version:
        output = get_output_manager()
        output.echo(f"kittylog version: {__version__}")
        sys.exit(0)

    if "-q" not in sys.argv and "--quiet" not in sys.argv:
        print_banner(get_output_manager())

    if ctx.invoked_subcommand is None:
        # Forward all options directly - no manual parameter passing
        ctx.invoke(update_cli, version=version_arg, **kwargs)
```

### Step 3: Delete `update_cli.py`

Remove `src/kittylog/update_cli.py` entirely. All functionality is covered by the renamed `update_cli` in `cli.py`.

### Step 4: Update Command Registration

```python
# Clean registration - no aliases, no backward compat
cli.add_command(update_cli, "update")  # Explicit subcommand
cli.add_command(release_cli, "release")
cli.add_command(config_cli, "config")
cli.add_command(init_cli, "init")
cli.add_command(language_cli, "language")
cli.add_command(lang, "lang")  # Keep alias
cli.add_command(model_cli, "model")
cli.add_command(auth_cli, "auth")

# REMOVED:
# - cli.add_command(add_cli)  # No longer exists
# - cli.add_command(update_version, "update")  # Replaced by update_cli
```

### Step 5: Update Tests

- Update imports: `from kittylog.cli import update_cli` (was `add_cli`)
- Remove tests for old `update_version` function
- Update any test that referenced `add_cli` or the `add` subcommand

### Step 6: Update Documentation

- README.md examples
- CLAUDE.md if needed
- Help text in CLI

## Files to Modify

| File | Action |
|------|--------|
| `src/kittylog/cli.py` | Rename `add_cli` → `update_cli`, fix default invocation, update registration |
| `src/kittylog/update_cli.py` | **DELETE** |
| `tests/test_cli.py` | Update imports and test names |
| `README.md` | Update usage examples |

## Command Usage After Changes

```bash
# Default behavior - update missing entries
kittylog

# Explicit subcommand
kittylog update

# Update specific version
kittylog update v1.2.0

# Update all entries
kittylog update --all

# Update range
kittylog update --from v1.0.0 --to v1.2.0

# With options
kittylog update v1.2.0 --dry-run --show-prompt
kittylog update --all --audience users --hint "Focus on breaking changes"

# Other commands unchanged
kittylog config show
kittylog init
kittylog release v1.2.0
```

## Preserved Functionality

All existing features preserved:
- All CLI options (`--dry-run`, `--quiet`, `--verbose`, `--all`, etc.)
- All grouping modes (tags, dates, gaps)
- All configuration commands
- All 25+ AI providers
- Release workflow

## Success Criteria

- [x] `kittylog` (no args) updates missing entries
- [x] `kittylog update` works identically
- [x] `kittylog update v1.0.0` updates specific version
- [x] All CLI options work
- [x] All tests pass (599 passed, 22 skipped)
- [x] `update_cli.py` deleted
- [x] No backward compatibility aliases (clean break)
