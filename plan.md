# Plan: Refactor kittylog CLI to match gac's modular structure

## Overview

This plan outlines how to refactor kittylog's CLI modules to follow the patterns established in the sister project `gac` (../gac/). The goal is to create a more modular, maintainable CLI structure with reusable configuration functions.

## Key Patterns from gac

### 1. Separation of Concerns
gac separates CLI modules into distinct files with clear responsibilities:
- `init_cli.py` - Orchestrates the full init workflow, delegating to other modules
- `model_cli.py` - Model/provider configuration (reusable function + standalone command)
- `language_cli.py` - Language selection (reusable function + standalone command)
- `auth_cli.py` - OAuth authentication as a standalone command
- `config_cli.py` - Configuration management (show/get/set/unset)

### 2. Reusable Internal Functions
Each CLI module exposes reusable functions that can be called from `init_cli.py`:
- `model_cli._configure_model(existing_env)` - Returns `bool` for success/failure
- `language_cli.configure_language_init_workflow(env_path)` - Returns `bool`

### 3. Standalone Commands
Each module also provides a Click command for direct CLI usage:
- `gac model` - Interactive model configuration
- `gac language` (or `gac lang`) - Interactive language selection
- `gac auth` - OAuth re-authentication

### 4. Clean Init Orchestration
gac's `init_cli.py` is very simple (~70 lines):
```python
def init():
    existing_env = _load_existing_env()
    if not _configure_model(existing_env):
        return
    _configure_language(existing_env)
    click.echo("Setup complete!")
```

## Current kittylog Structure (Problems)

1. **`init_cli.py`** (288 lines): Contains ALL model configuration logic embedded directly
   - Cannot run model configuration standalone
   - Provider list and selection logic is duplicated
   - Hard to maintain and test

2. **`language_cli.py`** (78 lines): Simpler than gac's, missing:
   - No `configure_language_init_workflow()` for init integration
   - No audience configuration (unique to kittylog)

3. **No `model_cli.py`**: Model configuration cannot be run independently

4. **`config_cli.py`**: Has `reauth` command that should be in `auth_cli.py`

## Proposed Changes

### Phase 1: Create model_cli.py

Create a new `src/kittylog/model_cli.py` that:

1. Extracts model configuration logic from `init_cli.py`:
   - Provider list definition
   - `_configure_model(existing_env: dict) -> bool` reusable function
   - Provider-specific configuration (custom URLs, OAuth, etc.)
   - API key handling with existing key detection

2. Adds a standalone `model` command:
   ```python
   @click.command()
   def model() -> None:
       """Interactively update provider/model/API key."""
       existing_env = _load_existing_env()
       if not _configure_model(existing_env):
           return
       click.echo("Model configuration complete.")
   ```

3. Handles existing configuration gracefully (like gac does):
   - Detect existing API key and offer "Keep existing" / "Enter new"
   - Detect existing token and offer re-auth options

### Phase 2: Refactor language_cli.py

Update `src/kittylog/language_cli.py` to:

1. Add `configure_language_init_workflow(env_path: Path) -> bool`:
   - Called from `init_cli.py` during init
   - Handles existing language detection
   - Offers "Keep existing" / "Select new" options

2. Add `_run_language_selection_flow(env_path: Path) -> str | None`:
   - Internal helper for the actual language selection
   - Returns selected language or None if cancelled

3. Add audience configuration (kittylog-specific):
   - `_configure_audience(env_path: Path) -> str | None`
   - Could be in `language_cli.py` or a new `audience_cli.py`

4. Keep the standalone `language` command but have it use internal helpers

### Phase 3: Create auth_cli.py

Create a new `src/kittylog/auth_cli.py` that:

1. Moves `reauth` command from `config_cli.py`
2. Provides a standalone `auth` command for OAuth authentication
3. Pattern matches gac's `auth_cli.py`:
   ```python
   @click.command()
   def auth(quiet: bool = False, log_level: str = "INFO") -> None:
       """Authenticate Claude Code OAuth token."""
       # Check existing token, perform OAuth, save
   ```

### Phase 4: Simplify init_cli.py

Refactor `src/kittylog/init_cli.py` to be a thin orchestrator:

1. Import configuration functions from other modules:
   ```python
   from kittylog.model_cli import _configure_model
   from kittylog.language_cli import configure_language_init_workflow
   ```

2. Simplify `init()` command to ~50 lines:
   ```python
   @click.command()
   def init() -> None:
       """Interactively set up $HOME/.kittylog.env."""
       click.echo("Welcome to kittylog initialization!\n")
       existing_env = _load_existing_env()

       if not _configure_model(existing_env):
           click.echo("Model configuration cancelled. Exiting.")
           return

       configure_language_init_workflow(KITTYLOG_ENV_PATH)

       click.echo("\nkittylog setup complete!")
   ```

### Phase 5: Update cli.py

Update `src/kittylog/cli.py` to:

1. Add new command imports:
   ```python
   from kittylog.auth_cli import auth as auth_cli
   from kittylog.model_cli import model as model_cli
   ```

2. Register new commands:
   ```python
   cli.add_command(auth_cli)
   cli.add_command(model_cli)
   ```

3. Remove `reauth` from config group (now in auth_cli)

## File Changes Summary

| File | Action |
|------|--------|
| `src/kittylog/model_cli.py` | **CREATE** - New file with model configuration |
| `src/kittylog/auth_cli.py` | **CREATE** - New file with auth command |
| `src/kittylog/init_cli.py` | **SIMPLIFY** - Thin orchestrator, import from other modules |
| `src/kittylog/language_cli.py` | **ENHANCE** - Add reusable workflow functions |
| `src/kittylog/config_cli.py` | **MODIFY** - Remove `reauth` command |
| `src/kittylog/cli.py` | **MODIFY** - Add new command imports |

## New CLI Commands After Refactor

```
kittylog                    # Main command (existing)
kittylog add                # Add changelog entries (existing)
kittylog init               # Full interactive setup (simplified)
kittylog model              # Standalone model configuration (NEW)
kittylog language           # Standalone language configuration (existing, enhanced)
kittylog lang               # Alias for language (existing)
kittylog auth               # OAuth authentication (NEW)
kittylog config show        # Show config (existing)
kittylog config get KEY     # Get config value (existing)
kittylog config set KEY VAL # Set config value (existing)
kittylog config unset KEY   # Remove config value (existing)
kittylog update             # Update specific version (existing)
kittylog init-changelog     # Initialize changelog file (existing)
```

## Testing Considerations

1. Existing tests for `init_cli.py` need to be updated to work with new structure
2. Add tests for new `model_cli.py` functions
3. Add tests for new `auth_cli.py` command
4. Ensure `language_cli.py` enhancements are tested

## Benefits

1. **Modularity**: Each concern in its own file
2. **Reusability**: Configuration functions can be called from multiple places
3. **Testability**: Smaller, focused functions are easier to test
4. **Maintainability**: Changes to model config don't touch init logic
5. **User Experience**: Users can update just model or language without full init
6. **Consistency**: Same patterns as gac for developers working on both projects

## Implementation Order

1. Create `model_cli.py` (largest change, most value)
2. Create `auth_cli.py` (simple extraction)
3. Enhance `language_cli.py` (add workflow function)
4. Simplify `init_cli.py` (depends on 1, 2, 3)
5. Update `cli.py` (final wiring)
6. Update tests
