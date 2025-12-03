# Kittylog Refactoring Plan

Ordered by effort (low-hanging fruit first).

---

## Phase 1: Quick Fixes (< 1 hour each)

### 1.1 Add explanatory comments to bare `pass` statements
- `src/kittylog/config/cli.py:15` ✅ (comment added during refactor)
- `src/kittylog/tag_operations.py:362`

### 1.2 Fix bare `except: pass` blocks
- `src/kittylog/language_cli.py:87, 114, 194`
- Replace with specific exceptions or add logging

### 1.3 Add missing return type hints
Priority files:
- `src/kittylog/cli.py` (9 functions)
- `src/kittylog/errors.py` (5 functions)
- `src/kittylog/constants.py` (2 functions)
- `src/kittylog/tag_operations.py` (1 function)
- `src/kittylog/cache.py` (1 function)
- `src/kittylog/output.py` (1 function)

---

## Phase 2: Configuration Cleanup (1-2 hours)

### 2.1 Consolidate API_KEYS definitions ✅ DONE
- ~~Remove duplication between `config.py:167-196` and `ai_utils.py:34-64`~~
- API_KEYS now comes from single source: `providers/__init__.py` registry

### 2.2 Fix module-level config loading
- `src/kittylog/ai.py:21` - move `load_config()` inside functions
- Consider `@functools.lru_cache` for repeated calls

---

## Phase 3: Exception Handling (2-4 hours)

### 3.1 Replace broad `except Exception` with specific types
Files to address (34 instances total):
- `src/kittylog/commit_analyzer.py` - 10 occurrences
- `src/kittylog/tag_operations.py` - 7 occurrences
- `src/kittylog/workflow.py` - 4 occurrences
- `src/kittylog/changelog_io.py` - 3 occurrences
- `src/kittylog/changelog.py` - 2 occurrences

Strategy:
1. Identify actual exceptions that can be raised
2. Replace with specific exception types
3. Remove redundant catch-all blocks where first catch is comprehensive

---

## Phase 4: Provider Refactoring (4-8 hours)

### 4.1 Create base provider class
Extract common pattern from 25 provider implementations:
```python
class BaseAPIProvider:
    API_URL: str
    API_KEY_ENV: str
    TIMEOUT: int = 120

    def call(self, model: str, messages: list, temperature: float, max_tokens: int) -> str:
        # Common implementation
```

### 4.2 Refactor existing providers to inherit from base
- Reduces ~1500 lines of duplicated code
- Centralizes error handling, retries, timeouts

---

## Phase 5: Module Decomposition (8+ hours)

### 5.1 Break down large modules ✅ DONE
- ~~`config.py` (762 lines) → split into `config_data.py`, `config_loader.py`, `secure_config.py`~~
- Refactored into `src/kittylog/config/` package:
  - `config/data.py` - dataclasses (ChangelogOptions, WorkflowOptions, KittylogConfigData)
  - `config/loader.py` - load_config, validate_config, etc.
  - `config/secure.py` - SecureConfig, inject_provider_keys
  - `config/cli.py` - config CLI commands
  - `config/__init__.py` - public API exports
- `utils.py` (580 lines) → identify logical groupings
- `mode_handlers.py` (534 lines) → one module per handler type

### 5.2 Modularize prompt template
- `prompt.py` (~150 lines of prompt text)
- Split into composable sections: system rules, section rules, examples
- Consider external template files for easier editing

---

## Phase 6: Architecture Improvements (future)

### 6.1 Dependency injection for output manager
- Replace global singleton pattern in `output.py`
- Pass output manager to CLI commands

### 6.2 Add validation layer
- Validate CLI options before passing to main code
- Centralize validation logic

### 6.3 Improve error classification
- Replace fragile string matching in `errors.py:286-310`
- Use exception type hierarchies instead
