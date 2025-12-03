# Kittylog - Low-Hanging Fruit Fixes

Quick wins that improve code quality with minimal effort.

---

## 1. Consolidate Duplicate `get_repo()` Function

**Files:** `tag_operations.py:21`, `commit_analyzer.py:21`

**Problem:** Identical function defined in two files with separate caches.

**Fix:**
- Keep `get_repo()` in `tag_operations.py`
- In `commit_analyzer.py`, replace definition with: `from kittylog.tag_operations import get_repo`
- Update `conftest.py` cache clearing if needed

**Effort:** ~5 minutes

---

## 2. Add Response Structure Validation in Providers

**Files:** All `providers/*.py` files

**Problem:** Direct array indexing assumes response structure:
```python
return response_data["choices"][0]["message"]["content"]
```

**Fix:** Add defensive checks:
```python
choices = response_data.get("choices")
if not choices or not isinstance(choices, list):
    raise AIError.generation_error("Invalid response: missing choices")
content = choices[0].get("message", {}).get("content")
if content is None:
    raise AIError.generation_error("Invalid response: missing content")
return content
```

**Effort:** ~30 minutes (22 providers, but pattern is identical)

---

## 3. Catch Specific Exceptions Instead of Bare `Exception`

**Files:** All `providers/*.py` files

**Problem:**
```python
except Exception as e:
    raise AIError.generation_error(...)
```

**Fix:** Catch specific types:
```python
except httpx.HTTPStatusError as e:
    raise AIError.generation_error(f"API error: {e.response.status_code}") from e
except httpx.TimeoutException as e:
    raise AIError.generation_error("Request timed out") from e
except httpx.RequestError as e:
    raise AIError.generation_error(f"Network error: {e}") from e
except (KeyError, IndexError, TypeError) as e:
    raise AIError.generation_error(f"Invalid response format: {e}") from e
```

**Effort:** ~45 minutes

---

## 4. Fix OAuth Token Environment Pollution

**File:** `oauth/claude_code.py:371`

**Problem:** Stores token directly in `os.environ`, contradicting `SecureConfig` pattern.

**Fix:** Return the token and let caller decide storage, or use `SecureConfig`:
```python
# Instead of:
os.environ["CLAUDE_CODE_ACCESS_TOKEN"] = access_token

# Return it:
return access_token
```

**Effort:** ~15 minutes

---

## 5. Add Missing `__all__` Exports

**Files:** Various modules

**Problem:** Some modules lack explicit `__all__` definitions, making public API unclear.

**Fix:** Add `__all__` to key modules listing intended public interface.

**Effort:** ~20 minutes

---

## 6. Remove Unused Imports

**Action:** Run `ruff check --select=F401` and fix any unused imports.

**Effort:** ~5 minutes

---

## Summary

| Task | Effort | Impact |
|------|--------|--------|
| Consolidate `get_repo()` | 5 min | High - eliminates duplicate cache bug |
| Response validation | 30 min | Medium - prevents cryptic errors |
| Specific exceptions | 45 min | Medium - better error handling |
| OAuth token fix | 15 min | Low - consistency |
| Add `__all__` exports | 20 min | Low - API clarity |
| Remove unused imports | 5 min | Low - cleanliness |

**Total:** ~2 hours of focused work

---

## Not Included (Larger Refactors)

These require more planning:
- Provider base class extraction (~1400 lines of duplication)
- Resolving `SecureConfig` vs `load_config()` pattern conflict
- Eliminating `types.py` circular import workaround
