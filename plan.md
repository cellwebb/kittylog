# Kittylog Refactoring Plan

## Phase 1: Quick Wins (Low Effort, High Impact)

### 1.1 Move Repeated Imports to Module Level
**File:** `src/kittylog/mode_handlers.py`
**Lines:** 147, 161, 229, 243

Move these duplicate imports to the top of the file:
```python
from kittylog.git_operations import generate_boundary_identifier, get_all_boundaries, get_previous_boundary
```

### 1.2 Fix Silent Token Counting Failure
**File:** `src/kittylog/utils.py:172`

Instead of returning 0 on failure, either:
- Raise a specific exception
- Return a sentinel value that callers check
- Log a warning (not just debug) so failures are visible

### 1.3 Extract Changelog Header Creation Helper
**File:** `src/kittylog/mode_handlers.py`
**Lines:** 55-57, 137-140, 269-271, 353-356

Create a helper function to reduce duplication:
```python
def _ensure_changelog_exists(changelog_file: str, title: str = "Changelog") -> str:
    """Create changelog with header if it doesn't exist, return content."""
```

---

## Phase 2: Naming Consistency (Medium Effort)

### 2.1 Standardize Parameter Names
**Decision:** Use `from_boundary`/`to_boundary` everywhere (more generic than tag-specific)

**Files to update:**
- `src/kittylog/changelog.py` - rename `from_tag`/`to_tag` parameters
- `src/kittylog/mode_handlers.py` - already uses boundary naming
- Update all callers accordingly

### 2.2 Standardize Content Variable Names
Pick one: `content`, `changelog_content`, or `existing_content` and use consistently.

---

## Phase 3: Error Handling Improvements (Medium Effort)

### 3.1 Replace Broad Exception Catching
**Files:**
- `src/kittylog/cli.py:292, 456`
- `src/kittylog/workflow.py:360-362`
- `src/kittylog/ai_utils.py:81`
- `src/kittylog/tag_operations.py:69, 95, 115, 160`
- `src/kittylog/update_cli.py:169`

Replace `except Exception as e:` with specific exception types:
- `GitError` for git operations
- `ConfigError` for configuration issues
- `AIError` for provider failures
- `ChangelogError` for file operations

### 3.2 Add Early Validation
**File:** `src/kittylog/workflow.py`

Add validation at workflow start:
- Check changelog file is writable
- Validate git repository exists and is valid
- Validate gap threshold bounds early

---

## Phase 4: Function Decomposition (Higher Effort)

### 4.1 Refactor `interactive_configuration()`
**File:** `src/kittylog/cli.py` (173 lines)

Extract into:
- `ui/prompts.py` - questionary prompt logic
- Keep orchestration in cli.py
- Separate fallback handling

### 4.2 Refactor `load_config()`
**File:** `src/kittylog/config.py` (249 lines)

Extract:
- `_load_env_file(path: str, keys: list) -> dict` helper
- Consolidate the 3-fold duplication in env loading
- Separate validation from loading

### 4.3 Extract Boundary-Finding Logic
**File:** `src/kittylog/mode_handlers.py:242-263`

Create shared helper:
```python
def _find_boundary_index(boundaries: list, target: str) -> int | None:
    """Find index of target boundary in list."""
```

---

## Phase 5: Type Safety (Higher Effort)

### 5.1 Create Config TypedDict
**File:** `src/kittylog/config.py`

Define explicit types for config values:
```python
class KittylogConfig(TypedDict):
    api_key: str | None
    model: str
    gap_threshold: float
    # ... etc
```

### 5.2 Remove isinstance() Checks
Once TypedDict is in place, remove scattered `isinstance()` checks throughout codebase.

---

## Phase 6: Documentation (Low Priority)

### 6.1 Add Module Docstrings
- `src/kittylog/workflow.py` - explain orchestration flow
- `src/kittylog/git_operations.py` - document facade pattern

### 6.2 Provider System Documentation
Add `src/kittylog/providers/README.md` explaining how to add new providers.

---

## Checklist

- [x] Phase 1.1: Move repeated imports
- [x] Phase 1.2: Fix silent token failure
- [x] Phase 1.3: Extract changelog header helper
- [x] Phase 2.1: Standardize boundary parameter names
- [x] Phase 2.2: Standardize content variable names
- [x] Phase 3.1: Replace broad exception catching
- [x] Phase 3.2: Add early validation
- [x] Phase 4.1: Refactor interactive_configuration()
- [x] Phase 4.2: Refactor load_config()
- [x] Phase 4.3: Extract boundary-finding logic
- [x] Phase 5.1: Create Config TypedDict
- [x] Phase 5.2: Remove isinstance() checks
- [x] Phase 6.1: Add module docstrings
- [x] Phase 6.2: Provider system documentation
