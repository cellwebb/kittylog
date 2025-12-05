# Kittylog Unified Refactoring Plan

Consolidated from plan.md, plan2.md, and plan3.md. Organized by effort (lowest hanging fruit first).

---

## Phase 1: Quick Wins (< 1 hour each)

### 1.1 Extract Magic Numbers to Constants
**Effort:** 15 min | **Impact:** Maintainability

Files to update:
- `src/kittylog/ai.py` - `max_diff_length = 5000`
- `src/kittylog/workflow.py` - `gap_threshold_hours > 168` (1 week)
- `src/kittylog/workflow.py` - `preview_lines[:50]`
- `src/kittylog/changelog_parser.py` - `max_bullets = 6`

Add to `constants.py`:
```python
class Limits:
    MAX_DIFF_LENGTH = 5000
    MAX_GAP_THRESHOLD_HOURS = 168  # 1 week
    PREVIEW_LINE_COUNT = 50
    MAX_BULLETS_PER_SECTION = 6
```

### 1.2 Add Error Context to Exception Raises
**Effort:** 20 min | **Impact:** Debugging

Search for `raise ChangelogError` and `raise GitError` without context params.

```python
# Before
raise ChangelogError(f"To boundary not found: {to_tag}")

# After
raise ChangelogError(
    f"To boundary not found: {to_tag}",
    file_path=changelog_file,
)
```

### 1.3 Move Module-Level Config to Lazy Loading
**Effort:** 30 min | **Impact:** Testability

Files: `workflow.py:27`, `ai.py`, `main.py`

```python
# Before (module level)
config = load_config()

# After (inside functions)
def validate_and_setup_workflow(...):
    config = load_config()
    ...
```

### 1.4 Delete or Use `KittylogConfigData` Dataclass
**Effort:** 15 min | **Impact:** Reduces confusion

File: `src/kittylog/config/data.py`

Either:
- A) Delete if unused (verify with `grep -r "KittylogConfigData" src/`)
- B) Use throughout codebase (see Phase 3.4)

---

## Phase 2: Safety & Exception Handling (1-2 hours each)

### 2.1 Replace Broad `except Exception` with Specific Types
**Effort:** 2 hours | **Impact:** Debugging, error handling

**Files with `except Exception` (34 instances):**
- `src/kittylog/commit_analyzer.py` - 10 occurrences
- `src/kittylog/tag_operations.py` - 7 occurrences
- `src/kittylog/workflow.py` - 4 occurrences
- `src/kittylog/changelog_io.py` - 3 occurrences
- `src/kittylog/changelog.py` - 2 occurrences
- `src/kittylog/ai.py` - 1 occurrence
- `tests/conftest.py` - 7 instances

```python
# Before
except Exception as e:
    logger.error(f"Failed: {e}")

# After
except (OSError, TimeoutError, ValueError) as e:
    logger.error(f"Failed: {e}")
```

### 2.2 Standardize Provider Error Handling with Decorator
**Effort:** 2 hours | **Impact:** Consistency across 24 providers

Create `src/kittylog/providers/error_handler.py`:

```python
from functools import wraps
import httpx
from kittylog.errors import AIError

def handle_provider_errors(provider_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except httpx.ConnectError as e:
                raise AIError.connection_error(f"{provider_name}: {e}")
            except httpx.TimeoutException as e:
                raise AIError.timeout_error(f"{provider_name}: {e}")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise AIError.authentication_error(f"{provider_name}: Invalid API key")
                elif e.response.status_code == 429:
                    raise AIError.rate_limit_error(f"{provider_name}: Rate limit exceeded")
                raise AIError.generation_error(f"{provider_name}: HTTP {e.response.status_code}")
        return wrapper
    return decorator
```

Apply to all 24 provider functions.

### 2.3 Convert CLI Warnings to Validation Errors
**Effort:** 1 hour | **Impact:** User experience

File: `src/kittylog/cli.py`

Current: conflicting options produce warnings but continue.
Target: validate early and fail fast.

```python
# Add validation before WorkflowOptions creation
if grouping_mode != GroupingMode.TAGS.value and (from_tag or to_tag):
    raise click.UsageError(
        f"--from-tag and --to-tag require --grouping-mode tags, got {grouping_mode}"
    )
```

---

## Phase 3: Code Organization (2-4 hours each)

### 3.1 Break Up `workflow.py` (498 lines)
**Effort:** 3 hours | **Impact:** Maintainability

**Target structure:**
```
src/kittylog/
├── workflow.py          # Keep: main_business_logic(), process_workflow_modes()
├── workflow_validation.py  # Extract: validate_workflow_prereqs(), validate_and_setup_workflow()
└── workflow_ui.py          # Extract: handle_dry_run_and_confirmation()
```

### 3.2 Break Up `prompt.py` (~500 lines)
**Effort:** 2 hours | **Impact:** Easier prompt debugging

**Target structure:**
```
src/kittylog/
├── prompt.py               # Keep: build_changelog_prompt() public interface
├── prompt_templates.py     # Extract: _build_system_prompt(), _build_user_prompt()
└── prompt_cleaning.py      # Extract: clean_changelog_content(), categorize_commit_by_message()
```

### 3.3 Consolidate Changelog Modules
**Effort:** 2 hours | **Impact:** Clear responsibilities

**Current (confusing):**
- `changelog.py` - update logic
- `changelog_parser.py` - parsing
- `changelog_io.py` - read/write

**Target (package):**
```
src/kittylog/changelog/
├── __init__.py     # Public API exports
├── io.py           # read, write, create header
├── parser.py       # find boundaries, insertion points, extract entries
└── updater.py      # update logic
```

### 3.4 Stop Unpacking Dataclasses
**Effort:** 2 hours | **Impact:** Maintainability

Pass `WorkflowOptions` and `ChangelogOptions` directly instead of unpacking into 16+ individual params.

Files affected:
- `workflow.py` - `process_workflow_modes()` signature (16 params → 2 dataclasses)
- `workflow.py` - `validate_and_setup_workflow()` signature
- `mode_handlers/*.py` - handler signatures

### 3.5 Split Constants into Focused Modules
**Effort:** 1 hour | **Impact:** Organization

**Target structure:**
```
src/kittylog/constants/
├── __init__.py         # Re-exports for backwards compat
├── languages.py        # Languages class
├── audiences.py        # Audiences class
├── env_defaults.py     # EnvDefaults class
└── enums.py            # GroupingMode, DateGrouping, FileStatus, etc.
```

### 3.6 Remove Deprecated Backwards Compatibility Shims
**Effort:** 1 hour | **Impact:** Reduced confusion, smaller codebase

**Pure backwards compatibility shims to delete:**

| Module | Re-exports from | Action |
|--------|----------------|--------|
| `src/kittylog/changelog.py` | `changelog/` package | Delete |
| `src/kittylog/changelog_io.py` | `changelog.io` | Delete |
| `src/kittylog/changelog_parser.py` | `changelog.parser` | Delete |

**Steps:**
1. Search codebase for imports from deprecated modules:
   ```bash
   uv run grep -r "from kittylog.changelog import" src/ tests/
   uv run grep -r "from kittylog.changelog_io import" src/ tests/
   uv run grep -r "from kittylog.changelog_parser import" src/ tests/
   uv run grep -r "from kittylog import.*changelog" src/ tests/
   ```

2. Update all imports to use the package structure:
   ```python
   # Before
   from kittylog.changelog import update_changelog
   from kittylog.changelog_io import read_changelog
   from kittylog.changelog_parser import find_insertion_point

   # After
   from kittylog.changelog import update_changelog  # From package __init__.py
   from kittylog.changelog.io import read_changelog
   from kittylog.changelog.parser import find_insertion_point
   ```

3. Delete the three deprecated shim files

4. Update `src/kittylog/__init__.py` if it imports from deleted modules

**Package `__init__.py` aggregators to keep:**
These follow standard Python patterns and should remain:
- `changelog/__init__.py` - Public API for changelog operations
- `config/__init__.py` - Public API for configuration
- `constants/__init__.py` - Public API for constants
- `mode_handlers/__init__.py` - Public API for mode handlers
- `utils/__init__.py` - Public API for utilities

**Thin wrappers to evaluate:**
- `main.py` - Consider merging into `workflow.py` or keeping as stable entry point
- `prompt.py` - Keep as public interface, but verify re-exports are still needed

---

## Phase 4: Provider Consolidation (4-8 hours)

### 4.1 Create Provider Base Class with Shared Logic
**Effort:** 4 hours | **Impact:** -500 lines, consistency

Current: 24 providers with duplicated httpx calls, error handling, response parsing.

Create `src/kittylog/providers/base_configured.py`:

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class ProviderConfig:
    name: str
    api_key_env: str
    base_url: str
    timeout: int = 120

class BaseConfiguredProvider(ABC):
    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    def _build_request_body(self, messages: list, temperature: float, max_tokens: int) -> dict:
        pass

    @abstractmethod
    def _parse_response(self, response: dict) -> str:
        pass

    @handle_provider_errors  # From 2.2
    def generate(self, model: str, messages: list, temperature: float, max_tokens: int) -> str:
        body = self._build_request_body(messages, temperature, max_tokens)
        response = httpx.post(self.config.base_url, json=body, ...)
        return self._parse_response(response.json())
```

### 4.2 Consolidate into 3-4 Base Implementations
**Effort:** 4 hours | **Impact:** Major code reduction

**Target:**
- `OpenAICompatibleProvider` - OpenAI, Azure, Groq, Cerebras, Together, custom OpenAI
- `AnthropicCompatibleProvider` - Anthropic, custom Anthropic
- `OllamaProvider` - Local Ollama
- `GenericHTTPProvider` - Replicate, Z.AI, etc.

Each provider becomes thin config:

```python
# providers/groq.py
class GroqProvider(OpenAICompatibleProvider):
    config = ProviderConfig(
        name="groq",
        api_key_env="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1/chat/completions",
    )
```

### 4.3 Provider Auto-Registration with Decorators
**Effort:** 2 hours | **Impact:** Maintainability

Replace manual registry in `providers/__init__.py`:

```python
# providers/registry.py
PROVIDER_REGISTRY = {}

def register_provider(name: str, env_vars: list[str]):
    def decorator(cls):
        PROVIDER_REGISTRY[name] = {
            "class": cls,
            "env_vars": env_vars,
        }
        return cls
    return decorator

# providers/groq.py
@register_provider("groq", ["GROQ_API_KEY"])
class GroqProvider(OpenAICompatibleProvider):
    ...
```

Delete manual imports and dictionaries from `providers/__init__.py`.

---

## Phase 5: Type Safety & Configuration (2-4 hours each)

### 5.1 Use Config Dataclass Throughout
**Effort:** 4 hours | **Impact:** Type safety, IDE autocomplete

Replace `load_config() -> dict` with `load_config() -> KittylogConfigData`.

```python
# Before
config = load_config()
model = config.get("model")  # No type info, KeyError risk

# After
config = load_config()
model = config.model  # Type-checked, autocomplete works
```

### 5.2 Add Protocol for Provider Contract
**Effort:** 2 hours | **Impact:** Type safety

```python
from typing import Protocol

class ProviderProtocol(Protocol):
    def __call__(
        self,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> str: ...
```

### 5.3 Simplify Configuration Precedence
**Effort:** 1 hour | **Impact:** User experience

**Current (5 layers - confusing):**
1. Environment variables
2. Project .kittylog.env
3. Project .env ← **REMOVE** (generic, conflicts with other tools)
4. User ~/.kittylog.env
5. Default values

**Target (4 layers - clear):**
1. CLI arguments (highest)
2. Environment variables
3. Config files (project .kittylog.env → user ~/.kittylog.env)
4. Default values (lowest)

**Changes:**
- Remove `load_dotenv()` call for project `.env` file
- Keep project `.kittylog.env` for project-specific overrides
- Keep user `~/.kittylog.env` for global defaults

---

## Phase 6: Testing & Polish (Nice to Have)

### 6.1 Simplify Test Mocking
**Effort:** 3 hours | **Impact:** Faster test development

Current: 4+ layers of mocking for simple tests.
Target: Reduce to 1-2 layers, focus on behavior not implementation.

### 6.2 Add Error Path Test Coverage
**Effort:** 4 hours | **Impact:** Reliability

Add tests for:
- Provider authentication failures
- Rate limiting
- Timeout handling
- Invalid config values
- Git operation failures

### 6.3 Add Structured Logging
**Effort:** 2 hours | **Impact:** Debugging

```python
logger.info(
    "Generating changelog entry",
    extra={"tag": tag, "commit_count": len(commits), "provider": provider}
)
```

---

## Checklist

### Phase 1: Quick Wins
- [x] 1.1 - Magic numbers to constants ✅
- [x] 1.2 - Add error context to raises ✅
- [x] 1.3 - Lazy config loading ✅
- [x] 1.4 - Delete/use KittylogConfigData ✅

### Phase 2: Safety & Exception Handling
- [x] 2.1 - Replace broad `except Exception` ✅
- [x] 2.2 - Provider error handling decorator ✅
- [x] 2.3 - Validation errors instead of warnings ✅

### Phase 3: Code Organization
- [x] 3.1 - Break up workflow.py ✅
- [x] 3.2 - Break up prompt.py ✅
- [x] 3.3 - Consolidate changelog modules ✅
- [x] 3.4 - Stop unpacking dataclasses ✅
- [x] 3.5 - Split constants into modules ✅
- [x] 3.6 - Remove deprecated backwards compatibility shims ✅

### Phase 4: Provider Consolidation
- [x] 4.1 - Create provider base class ✅
- [x] 4.2 - Consolidate to 3-4 base implementations ✅
- [x] 4.3 - Provider auto-registration ✅

### Phase 5: Type Safety & Configuration
- [x] 5.1 - Config dataclass throughout ✅
- [x] 5.2 - Provider protocol ✅
- [x] 5.3 - Simplify config precedence ✅

### Phase 6: Testing & Polish
- [x] 6.1 - Simplify test mocking ✅
- [x] 6.2 - Error path test coverage ✅
- [x] 6.3 - Structured logging ✅

---

## Expected Impact

| Metric | Before | After |
|--------|--------|-------|
| Provider files | 24 separate | 4 base + 24 configs |
| Duplicated provider code | ~1500 lines | ~200 lines |
| `except Exception` instances | 34+ | < 5 |
| `workflow.py` size | 498 lines | ~150 lines |
| `prompt.py` size | ~500 lines | ~150 lines |
| Magic numbers | 15+ | 0 |
| Function params (max) | 23 | < 5 |

---

## Estimated Timeline

**Week 1:** Phase 1 + Phase 2 (Quick wins + Safety)
**Week 2:** Phase 3 (Code organization)
**Week 3:** Phase 4 (Provider consolidation)
**Week 4:** Phase 5 + Phase 6 (Type safety + Polish)

**Total effort:** ~40-50 hours
