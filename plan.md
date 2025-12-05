# Kittylog Refactoring Plan

Based on fresh code review (2025-12-05). Ordered by effort - low-hanging fruit first.

---

## Phase 0: Critical Bug Fix (BLOCKING)

### 0.1 Grouping Mode Ignored in Missing Entries Mode
- **Symptom:** User selects "Dates - Weekly" in interactive mode, but kittylog still processes by git tags
- **Root Cause:** `handle_missing_entries_mode` ignores `grouping_mode` entirely

**Files affected:**
- `src/kittylog/workflow.py:183-195` - doesn't pass `grouping_mode` to handler
- `src/kittylog/mode_handlers/missing.py:32` - hardcodes `get_all_tags()` instead of using mode
- `src/kittylog/mode_handlers/missing.py:38` - function signature lacks `mode` parameter

**The fix:**

1. **Update `workflow.py:183-195`** - pass `grouping_mode` to handler:
   ```python
   _, content = handle_missing_entries_mode(
       changelog_file=changelog_file,
       generate_entry_func=generate_entry_func,
       mode=grouping_mode,  # ADD THIS
       date_grouping=changelog_opts.date_grouping,  # ADD THIS for dates mode
       gap_threshold=changelog_opts.gap_threshold_hours,  # ADD THIS for gaps mode
       quiet=quiet,
       yes=yes,
       dry_run=dry_run,
       incremental_save=incremental_save,
   )
   ```

2. **Update `missing.py:38`** - add mode parameters:
   ```python
   def handle_missing_entries_mode(
       changelog_file: str,
       generate_entry_func,
       mode: str = "tags",  # ADD
       date_grouping: str = "daily",  # ADD
       gap_threshold: float = 4.0,  # ADD
       quiet: bool = False,
       ...
   ```

3. **Update `missing.py:10-35`** - use `get_all_boundaries` instead of `get_all_tags`:
   ```python
   def determine_missing_entries(changelog_file: str, mode: str = "tags", **kwargs) -> list[dict]:
       """Determine which boundaries have missing changelog entries."""
       from kittylog.tag_operations import get_all_boundaries

       # Get all boundaries based on mode
       all_boundaries = get_all_boundaries(mode=mode, **kwargs)

       # ... rest of logic using boundary dicts instead of tag strings
   ```

4. **Update `missing.py:87-93`** - use boundary-aware commit fetching:
   ```python
   from kittylog.commit_analyzer import get_commits_between_boundaries

   commits = get_commits_between_boundaries(
       from_boundary=None,
       to_boundary=boundary,  # Now a dict, not a string
       mode=mode,
   )
   ```

**Verify:** `uv run pytest tests/test_missing_entries.py -v`

---

## Phase 1: Quick Wins (< 15 min each)

### 1.1 Remove Unused pydantic Dependency
- **File:** `pyproject.toml`
- **Issue:** pydantic listed but never imported (codebase uses dataclasses)
- **Action:** Remove `pydantic` from dependencies
- **Verify:** `uv run grep -r "import pydantic\|from pydantic" src/`

### 1.2 Remove Duplicate Comment
- **File:** `src/kittylog/cli.py:281`
- **Issue:** Duplicate comment "Language/audience already set in WorkflowOptions constructor"
- **Action:** Delete the duplicate line

### 1.3 Add `.kittylog.env` to `.gitignore`
- **File:** `.gitignore`
- **Issue:** `.kittylog.env` with `OPENAI_API_KEY` is checked into repo
- **Action:** Add to `.gitignore`, run `git rm --cached .kittylog.env`
- **Note:** Keep `.kittylog.env.example` as reference

### 1.4 Add Docstrings to Option Decorators
- **File:** `src/kittylog/cli.py:37-129`
- **Issue:** `workflow_options()`, `changelog_options()`, `model_options()`, `logging_options()` lack docstrings
- **Action:** Add brief docstrings explaining each decorator's purpose

---

## Phase 2: Small Refactors (30 min - 1 hour each)

### 2.1 Extract Shared Logging Setup Utility
- **Files:**
  - `src/kittylog/cli.py:132-139`
  - `src/kittylog/update_cli.py:63-70`
  - `src/kittylog/release_cli.py:49-56`
- **Issue:** Identical verbose logging setup logic in 3 places
- **Action:** Create utility function in `src/kittylog/utils/logging.py`:
  ```python
  def setup_command_logging(verbose: bool, log_level: str | None) -> str:
      effective_log_level = log_level or "WARNING"
      if verbose and effective_log_level not in ("DEBUG", "INFO"):
          effective_log_level = "INFO"
      return effective_log_level
  ```

### 2.2 Narrow Exception Handling in AI Module
- **File:** `src/kittylog/ai.py:158`
- **Issue:** Catches `(AIError, ValueError, TypeError, AttributeError, RuntimeError, Exception)` - too broad
- **Action:** Catch only `AIError` and let unexpected exceptions propagate for debugging

### 2.3 Narrow Exception Handling in AI Utils
- **File:** `src/kittylog/ai_utils.py:61`
- **Issue:** Bare `except Exception` in retry loop could catch KeyboardInterrupt
- **Action:** Change to `except (AIError, httpx.HTTPError, TimeoutError)` or re-raise system exceptions

### 2.4 Improve Type Annotation for Provider Registry
- **File:** `src/kittylog/providers/registry.py:6`
- **Issue:** `PROVIDER_REGISTRY: dict[str, Callable]` lacks specific signature
- **Action:**
  ```python
  ProviderFunc = Callable[[str, list[dict], float, int], str]
  PROVIDER_REGISTRY: dict[str, ProviderFunc] = {}
  ```

### 2.5 Guard Config Loading at Import Time
- **File:** `src/kittylog/config/loader.py:52-53`
- **Issue:** `_load_env_files()` runs at module import, can break test isolation
- **Action:** Use lazy loading with `functools.lru_cache` or explicit init function

---

## Phase 3: Medium Refactors (1-2 hours each)

### 3.1 Refactor CLI Parameter Object Construction
- **File:** `src/kittylog/cli.py:252-277`
- **Issue:** Manual construction of WorkflowOptions/ChangelogOptions from 26 raw parameters
- **Action:** Move parameter object construction into decorator layer:
  ```python
  def common_options(func):
      @workflow_options
      @changelog_options
      @model_options
      @logging_options
      @functools.wraps(func)
      def wrapper(**kwargs):
          opts = build_options_from_kwargs(kwargs)  # New helper
          return func(workflow_opts=opts.workflow, changelog_opts=opts.changelog, **opts.remaining)
      return wrapper
  ```

### 3.2 Add Type Hints to Weak Areas
- **Files:**
  - `src/kittylog/ai_utils.py:15-24` - use `dict[str, Callable[..., str]]`
  - `src/kittylog/mode_handlers/boundary.py` - add type hints throughout
  - `src/kittylog/commit_analyzer.py` - add type hints
- **Verify:** `uv run mypy --strict src/kittylog/ai_utils.py`

---

## Phase 4: Major Refactors (4+ hours)

### 4.1 Provider Factory to Eliminate Duplication
- **Files:** All 30+ files in `src/kittylog/providers/`
- **Issue:** ~800 lines of duplicated getter/API function boilerplate
- **Current pattern repeated 30+ times:**
  ```python
  def _get_<provider>_provider() -> Provider:
      return Provider(Provider.config)

  @handle_provider_errors("<Provider>")
  def call_<provider>_api(model, messages, temperature, max_tokens) -> str:
      provider = _get_<provider>_provider()
      return provider.generate(model, messages, temperature, max_tokens)
  ```

- **Option A: Factory function**
  ```python
  # providers/factory.py
  def create_provider_api(provider_class: type[BaseConfiguredProvider]) -> ProviderFunc:
      @handle_provider_errors(provider_class.config.name)
      def call_api(model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
          return provider_class(provider_class.config).generate(model, messages, temperature, max_tokens)
      return call_api

  # providers/openai.py (reduced to ~10 lines)
  class OpenAIProvider(OpenAICompatibleProvider):
      config = ProviderConfig(name="openai", ...)

  call_openai_api = create_provider_api(OpenAIProvider)
  ```

- **Option B: Auto-registration in base class**
  ```python
  class BaseConfiguredProvider(ABC):
      def __init_subclass__(cls, **kwargs):
          super().__init_subclass__(**kwargs)
          if hasattr(cls, 'config'):
              register_provider(cls.config.name, cls)
  ```

### 4.2 Reduce CLI Command Parameter Count
- **File:** `src/kittylog/cli.py:207-277`
- **Issue:** `add()` command accepts 26 parameters from stacked decorators
- **Target:** Reduce to ≤6 parameters by passing option objects
- **Depends on:** 3.1 must be completed first

---

## Verification After Each Change

```bash
uv run pytest
uv run ruff check .
uv run mypy src/
```

---

## Checklist

### Phase 0: Critical Bug Fix
- [x] 0.1 - Fix grouping mode ignored in missing entries mode

### Phase 1: Quick Wins
- [ ] 1.1 - Remove unused pydantic dependency
- [ ] 1.2 - Remove duplicate comment
- [ ] 1.3 - Add .kittylog.env to .gitignore
- [ ] 1.4 - Add docstrings to option decorators

### Phase 2: Small Refactors
- [ ] 2.1 - Extract shared logging setup utility
- [ ] 2.2 - Narrow exception handling in ai.py
- [ ] 2.3 - Narrow exception handling in ai_utils.py
- [ ] 2.4 - Improve type annotation for provider registry
- [ ] 2.5 - Guard config loading at import time

### Phase 3: Medium Refactors
- [ ] 3.1 - Refactor CLI parameter object construction
- [ ] 3.2 - Add type hints to weak areas

### Phase 4: Major Refactors
- [ ] 4.1 - Provider factory to eliminate duplication
- [ ] 4.2 - Reduce CLI command parameter count

---

## Expected Impact

| Metric | Current | After |
|--------|---------|-------|
| Provider boilerplate | ~800 lines | ~100 lines |
| CLI function params | 26 | ≤6 |
| Duplicate logging setup | 3 instances | 1 utility |
| Broad `except Exception` | Multiple | Specific types |
| Unused dependencies | 1 (pydantic) | 0 |
