# Kittylog Refactoring Plan

## 1. Resolve SecureConfig vs load_config() Pattern Conflict

### Problem

Two contradictory patterns exist for API key management:

**Pattern A - SecureConfig** (`config.py:199-288`):
- Well-designed class with `inject_for_provider()` context manager
- Temporarily injects keys, then cleans up
- Prevents permanent environment pollution

**Pattern B - load_config()** (`config.py:463-466`):
```python
for var in api_key_vars:
    if var in config_vars and config_vars[var] is not None and os.getenv(var) is None:
        os.environ[var] = config_vars[var]
```
- Permanently pollutes `os.environ`
- Contradicts SecureConfig philosophy

### Current Usage

`load_config()` is called from:
- `workflow.py:26` - module-level
- `cli.py:121` - inside function
- `ai.py:47` - module-level
- `update_cli.py:19` - module-level
- `ui/prompts.py:24,96` - inside functions

`SecureConfig` has a global instance at `config.py:295` but is underutilized.

### Solution

**Option A: Remove env pollution from load_config()** (Recommended)
1. Delete lines 463-466 in `config.py` (the `os.environ[var] = ...` loop)
2. Have `load_config()` return API keys in the dict without setting env vars
3. Update providers to get keys from the returned config dict or use `SecureConfig.get_key()`

**Option B: Deprecate SecureConfig entirely**
- Remove SecureConfig class
- Accept environment pollution as the pattern
- Simpler but less secure

### Implementation Steps (Option A)

1. **Modify load_config()** (`config.py`):
   - Remove lines 463-466 (env pollution loop)
   - Return API keys in the config dict under a `"api_keys"` sub-dict

2. **Update provider calls** to pass API keys explicitly or use SecureConfig:
   ```python
   # Before (relies on os.environ)
   api_key = os.getenv("GROQ_API_KEY")

   # After (explicit passing)
   api_key = config.get("api_keys", {}).get("GROQ_API_KEY")
   ```

3. **Update ai.py** to use SecureConfig's `inject_for_provider()` context manager for SDK-based providers that require env vars

4. **Update tests** - remove any reliance on env var pollution

### Files to Modify

- `config.py` - Remove pollution, restructure return value
- `ai.py` - Use SecureConfig for provider calls
- All `providers/*.py` - Accept api_key as parameter instead of reading os.environ
- Test files - Update fixtures

---

## 2. Eliminate types.py Circular Import Workaround

### Problem

`types.py` exists solely to break a circular import between `ai.py` and `ai_utils.py`:

```
ai.py imports ai_utils.py
ai_utils.py needs classify_error() from ai.py → circular!
```

Current workaround: `classify_error()` lives in `types.py` (37 lines).

### Current Usage

Single import at `ai_utils.py:84`:
```python
from kittylog.types import classify_error
```

This is a lazy import inside a function, which is already a workaround pattern.

### Solution

**Move `classify_error()` to `errors.py`** (Recommended)

This makes semantic sense - error classification belongs with error definitions.

### Implementation Steps

1. **Move function** from `types.py` to `errors.py`:
   ```python
   # errors.py (add at bottom)
   def classify_error(error: Exception) -> str:
       """Classify an error for retry logic."""
       error_str = str(error).lower()
       # ... rest of function
   ```

2. **Update import** in `ai_utils.py:84`:
   ```python
   # Before
   from kittylog.types import classify_error

   # After
   from kittylog.errors import classify_error
   ```

3. **Delete `types.py`** entirely

4. **Update `__init__.py`** if `types` is exported

5. **Run tests** to verify no circular import issues

### Files to Modify

- `errors.py` - Add `classify_error()` function
- `ai_utils.py` - Update import
- `types.py` - Delete
- `__init__.py` - Remove types export if present

### Risk Assessment

**Low risk** - `classify_error()` has no dependencies on `ai.py` or `ai_utils.py`, so moving it to `errors.py` won't create new circular imports.

---

## Summary

| Task | Effort | Impact | Risk |
|------|--------|--------|------|
| SecureConfig resolution | 2-3 hrs | High - security, consistency | Medium |
| Eliminate types.py | 15 min | Low - code cleanliness | Low |

**Recommended order**: Do #2 first (quick win), then #1 (more involved).
