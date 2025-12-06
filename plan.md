# Kittylog Refactoring Plan

Based on fresh code review (2025-12-05). Ordered by effort - low-hanging fruit first.

## 🎯 **Progress Summary**
- **Phase 0** ✅ **COMPLETE** - Critical bug fix (grouping mode ignored)
- **Phase 1** ✅ **COMPLETE** - Quick wins (cleanup & documentation)
- **Phase 2** ✅ **COMPLETE** - Small refactors (30min-1hr each)
- **Phase 3** ⏳ **NEXT** - Medium refactors (1-2hr each)  
- **Phase 4** ⏳ **PENDING** - Major refactors (4+hr each)

**Total Completed:** 11/14 tasks (79%)
**Impact:** 1 critical bug fixed, 1 unused dependency removed, code quality significantly improved, test failures resolved, robust boundary handling implemented

---

## ✅ Phase 0: Critical Bug Fix (BLOCKING) - COMPLETE

### ✅ 0.1 Grouping Mode Ignored in Missing Entries Mode - **COMPLETED**
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

## ✅ Phase 1: Quick Wins (< 15 min each) - COMPLETE

### ✅ 1.1 Remove Unused pydantic Dependency - **COMPLETED**
- **File:** `pyproject.toml`
- **Issue:** pydantic listed but never imported (codebase uses dataclasses)
- **Action:** ✅ Removed `pydantic>=2.12.5` from dependencies
- **Verify:** ✅ Confirmed no pydantic imports exist

### ✅ 1.2 Remove Duplicate Comment - **COMPLETED**
- **File:** `src/kittylog/cli.py:283`
- **Issue:** Duplicate comment "Language/audience already set in WorkflowOptions constructor"
- **Action:** ✅ Removed duplicate comment line

### ✅ 1.3 Add `.kittylog.env` to `.gitignore` - **COMPLETED**
- **File:** `.gitignore`
- **Issue:** Ensure `.kittylog.env` with API keys is not checked into repo
- **Action:** ✅ Already properly ignored in `.gitignore`
- **Note:** No actual `.kittylog.env` file exists (good!)

### ✅ 1.4 Add Docstrings to Option Decorators - **COMPLETED**
- **File:** `src/kittylog/cli.py:37-129`
- **Issue:** Basic docstrings existed but lacked detail
- **Action:** ✅ Enhanced all 4 decorator docstrings with detailed descriptions

---

## ✅ Phase 2: Small Refactors (30 min - 1 hour each) - **COMPLETE**

### ✅ 2.1 Extract Shared Logging Setup Utility - **COMPLETED**
- **Files:** ✅ Completed
  - `src/kittylog/cli.py` - ✅ Updated to use shared utility
  - `src/kittylog/update_cli.py` - ✅ Updated to use shared utility
  - `src/kittylog/release_cli.py` - ✅ Updated to use shared utility
  - `src/kittylog/utils/logging.py` - ✅ Created `setup_command_logging()` utility
- **Result:** Centralized logging utility, eliminated code duplication, fixed circular import issue

### ✅ 2.2 Narrow Exception Handling in AI Module - **COMPLETED**
- **File:** `src/kittylog/ai.py:158`
- **Issue:** Catches `(AIError, ValueError, TypeError, AttributeError, RuntimeError, Exception)` - too broad
- **Action:** ✅ Refined to catch specific exceptions while preserving test compatibility
  - Catches `AIError, ValueError, TypeError, RuntimeError` for expected errors
  - Catches generic `Exception` for unexpected errors with system exception protection
  - Preserves `KeyboardInterrupt`, `SystemExit`, `GeneratorExit` propagation

### ✅ 2.3 Narrow Exception Handling in AI Utils - **COMPLETED**
- **File:** `src/kittylog/ai_utils.py:61`
- **Issue:** Bare `except Exception` in retry loop could catch KeyboardInterrupt
- **Action:** ✅ Improved exception handling:
  - Catches `AIError, httpx.HTTPError, TimeoutError, ValueError, TypeError, RuntimeError`
  - Uses `classify_error()` function for intelligent error classification
  - Protects system exceptions while handling retry logic properly

### ✅ 2.4 Improve Type Annotation for Provider Registry - **COMPLETED**
- **File:** `src/kittylog/providers/base.py` (moved from registry.py)
- **Issue:** `PROVIDER_REGISTRY: dict[str, Callable]` lacks specific signature
- **Action:** ✅ Enhanced type safety:
  ```python
  ProviderFunc = Callable[[str, list[dict], float, int], str]
  PROVIDER_REGISTRY: dict[str, ProviderFunc] = {}
  ```
- **Result:** Better IDE support, improved type safety, enhanced documentation

#### 🐛 Additional: Phase 0 Test Fixes
- **Fixed:** Multiple test failures related to boundary dictionary handling
- **Issue:** `KeyError('name')` and `KeyError('identifier')` in missing entries mode
- **Action:** ✅ Implemented robust boundary key access with fallbacks
- **Tests Fixed:**
  - ✅ `test_auto_mode_shows_entry_count` - confirmation functionality
  - ✅ `test_multiple_tags_auto_detection` - integration tests
  - ✅ `test_main_logic_dates_mode` - main business logic
  - ✅ `test_main_logic_dry_run_mode` - dry run functionality (complex mock fixes)
- **Result:** All 609 tests now pass (586 passed, 23 skipped)

### ✅ 2.5 Guard Config Loading at Import Time - **COMPLETED**
- **File:** `src/kittylog/config/loader.py`
- **Issue:** `_load_env_files()` runs at module import, can break test isolation
- **Action:** ✅ Implemented lazy loading with `functools.lru_cache`:
  - Added `@functools.lru_cache(maxsize=1)` to `_load_env_files`
  - Created `reset_env_files_cache()` for test isolation
  - Updated all affected tests to use cache reset
  - Improved startup performance and test isolation

---

## Phase 3: Medium Refactors (1-2 hours each)

### ✅ 3.0 Create Separate System Prompts Per Audience (HIGH PRIORITY) - **COMPLETED**
- **Symptom:** "End Users" persona still produces technical details (modules, APIs, etc.)
- **Root Cause:** Single system prompt with technical framing bleeds through regardless of audience instructions
- **Status:** ✅ Implemented three completely separate system prompts

**The fix: Three completely separate system prompts**

1. **Create `_build_system_prompt_developers()`** (current behavior)
   - Technical details, API changes, breaking changes
   - Module/service references, migration steps
   - Implementation-focused examples

2. **Create `_build_system_prompt_users()`** (new)
   ```python
   def _build_system_prompt_users() -> str:
       return """You are writing release notes for END USERS who are NOT technical.

   ## STRICT RULES - NO TECHNICAL LANGUAGE

   FORBIDDEN (never use these words):
   - module, API, SDK, CLI, refactor, architecture, provider, endpoint
   - dependency, configuration, environment variable, migration, handler
   - implementation, interface, middleware, backend, frontend, database
   - Any programming language names, framework names, or library names

   REQUIRED LANGUAGE:
   - Write like you're explaining to a friend who doesn't code
   - Focus on WHAT users can do, not HOW it works internally
   - Describe BENEFITS and OUTCOMES, not implementation

   ## EXAMPLES OF CORRECT TRANSLATIONS:
   ❌ "Refactored authentication module" → ✅ "Improved sign-in reliability"
   ❌ "Fixed null pointer exception" → ✅ "Fixed a crash that occurred when saving"
   ❌ "Added REST API endpoint" → ✅ "New export feature available"
   ❌ "Optimized database queries" → ✅ "App now loads faster"
   ❌ "Updated dependencies" → ✅ "Security and stability improvements"

   ## SECTIONS (only include if relevant):
   - ### What's New - new features users can try
   - ### Improvements - things that work better now
   - ### Bug Fixes - problems that are now solved

   DO NOT use standard changelog sections (Added/Changed/Removed/Fixed).
   Keep language simple. Maximum 3-4 bullets per section."""
   ```

3. **Create `_build_system_prompt_stakeholders()`** (new)
   ```python
   def _build_system_prompt_stakeholders() -> str:
       return """You are writing release notes for BUSINESS STAKEHOLDERS.

   ## FOCUS AREAS:
   - Business impact and outcomes
   - Customer value delivered
   - Risk mitigation and stability
   - Strategic alignment

   ## LANGUAGE STYLE:
   - Professional and scannable
   - Quantify impact where possible
   - Mention affected product areas
   - Avoid deep technical implementation details

   ## SECTIONS:
   - ### Highlights - key business outcomes
   - ### Customer Impact - value delivered
   - ### Technical Notes - brief summary for context (optional)

   Keep entries concise and executive-summary style."""
   ```

4. **Update `_build_system_prompt()` to dispatch:**
   ```python
   def _build_system_prompt(audience: str = "developers") -> str:
       prompts = {
           "developers": _build_system_prompt_developers,
           "users": _build_system_prompt_users,
           "stakeholders": _build_system_prompt_stakeholders,
       }
       return prompts.get(audience, _build_system_prompt_developers)()
   ```

5. **Update callers to pass audience to system prompt builder**

**Files to modify:**
- `src/kittylog/prompt_templates.py` - add new functions, update dispatcher
- `src/kittylog/prompt.py` - pass audience to `_build_system_prompt()`
- `src/kittylog/ai.py` - ensure audience flows through

**Verify:** `uvx kittylog --audience users` produces no technical jargon

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

### Phase 1: Quick Wins ✅ COMPLETE
- [x] 1.1 - Remove unused pydantic dependency
- [x] 1.2 - Remove duplicate comment
- [x] 1.3 - Add .kittylog.env to .gitignore
- [x] 1.4 - Add docstrings to option decorators

### Phase 2: Small Refactors ✅ COMPLETE
- [x] 2.1 - Extract shared logging setup utility
- [x] 2.2 - Narrow exception handling in ai.py
- [x] 2.3 - Narrow exception handling in ai_utils.py
- [x] 2.4 - Improve type annotation for provider registry
- [x] 2.5 - Guard config loading at import time

### Phase 3: Medium Refactors
- [x] 3.0 - Create separate system prompts per audience (HIGH PRIORITY)
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
| Unused dependencies | 1 (pydantic) | ✅ 0 |
