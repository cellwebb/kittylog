# clog Enhancement Plan

## Goals

1. Make clog retroactive - build changelog from a given commit or from early tags like v0.0.1/v0.1.0
2. Incorporate git diffs to provide more context to the LLM
3. Rely more on LLM intelligence instead of manual commit categorization

## Current State Analysis

Let's examine what we have now:

- clog processes new git tags since the last update
- It analyzes commit messages and changed files
- It has some basic categorization logic in constants.py
- It uses AI to generate changelog content based on this analysis

## 1. Retroactive Changelog Generation

### Problem

Currently, clog only processes new tags since the last changelog update. If a project doesn't have a changelog or wants to regenerate it from scratch, there's no easy way to do this.

### Solution

Add new command-line options:

- `--from-commit <commit>` - Start from a specific commit instead of relying on tag detection
- `--regenerate` - Regenerate the entire changelog from the beginning

### Implementation Details

In cli.py, add new options to the update command:

```bash
@click.option('--from-commit', default=None, help='Start from specific commit instead of last changelog update')
@click.option('--regenerate', is_flag=True, help='Regenerate entire changelog from beginning')
```

In main.py, update the logic to:

1. Handle `--regenerate` by clearing existing changelog content (except header)
2. Handle `--from-commit` by treating it similarly to `--from-tag`
3. Ensure proper sorting and processing order
4. Possibly add a `--to-commit` option as well for completeness

The workflow should be:

- If `--regenerate` is specified, start from the first commit
- If `--from-commit` is specified, start from that commit
- If neither is specified, use existing logic to detect new tags
- Process all tags chronologically between the start point and HEAD

This may require:

- A new function to get tags in chronological order between commits
- Logic to handle cases where tags don't exist (process commits directly)
- Proper diff processing between arbitrary commits

## 2. Git Diff Integration

### Problem

Currently, clog only analyzes commit messages and file names. It doesn't look at the actual code changes, which could provide much more context for generating accurate changelog entries.

### Solution

Modify the git.py module to include actual diff content in the commit information:

### Implementation Details

In get_commits_between_tags() function:

1. Add diff content to each commit object
2. Limit diff content to avoid token explosion (maybe just diff stats or a summary)
3. Make diff inclusion configurable (full diffs vs summaries vs none)

```python
def get_commits_between_tags(from_tag: str | None, to_tag: str | None) -> list[dict]:
    # Existing code...

    for commit in commit_iter:
        # Get changed files (existing code)
        changed_files = []

        # NEW: Get diff information
        diff_content = ""
        diff_stats = {}
        if commit.parents:
            diff = commit.parents[0].diff(commit)
            # Get diff stats for high-level overview
            diff_stats = {
                "files_changed": len(diff),
                "insertions": commit.stats.total["insertions"],
                "deletions": commit.stats.total["deletions"],
            }
            # Process diff to extract meaningful information
            diff_content = _process_diff(diff)

        commits.append({
            "hash": commit.hexsha,
            "short_hash": commit.hexsha[:8],
            "message": commit.message.strip(),
            "author": str(commit.author),
            "date": datetime.fromtimestamp(commit.committed_date),
            "files": changed_files,
            "diff": diff_content,  # NEW
            "diff_stats": diff_stats,  # NEW
        })

    return commits
```

In `_process_diff()` function:

1. Extract meaningful changes from the diff
2. Limit content size to prevent token overflow
3. Focus on significant changes rather than trivial ones
4. Consider using GitPython's diff parsing capabilities

```python
def _process_diff(diff) -> str:
    """Process git diff to extract meaningful information for changelog generation."""
    # For now, focus on diff stats and file changes
    # Later: consider extracting actual code changes for more context

    diff_info = []
    for item in diff:
        # Basic file change information
        if item.a_path and item.b_path and item.a_path != item.b_path:
            diff_info.append(f"{item.a_path} -> {item.b_path} (renamed)")
        elif item.deleted_file:
            diff_info.append(f"{item.a_path} (deleted)")
        elif item.new_file:
            diff_info.append(f"{item.b_path} (added)")
        else:
            diff_info.append(f"{item.a_path or item.b_path} (modified)")

    return "\n".join(diff_info)
```

## 3. Rely More on LLM Intelligence

### Problem

Currently, clog tries to pre-categorize commits using the `categorize_commit_by_message()` function in prompt.py and keyword lists in constants.py:

This approach:

1. Is brittle and relies on specific commit message formats
2. Doesn't leverage the full intelligence of modern LLMs
3. May miss important context that an LLM could identify
4. Creates an unnecessary preprocessing step that could be handled by the AI

### Solution

Simplify commit categorization and let the LLM do most of the work:

1. Remove the `categorize_commit_by_message()` function
2. Remove the `CommitKeywords` class from constants.py
3. Send raw commit data (messages + diffs) to the LLM
4. Provide clear instructions in the prompt for the LLM to categorize changes appropriately

### Implementation Details

In prompt.py:

1. Remove the `categorize_commit_by_message()` function
2. Update the system prompt to be even clearer about the LLM's role in analysis
3. Send all commit information as-is to the LLM without preprocessing
4. Remove any references to commit categorization from the instructions

The LLM should be capable of analyzing commit messages and diffs to determine appropriate categories without our keyword-based preprocessing.

## Priority Implementation Order

1. **Git Diff Integration** - This is the foundation for providing richer context
2. **LLM Intelligence Enhancement** - Simplify our preprocessing to rely more on the LLM
3. **Retroactive Generation** - Add CLI options to build changelog from arbitrary points

## Technical Considerations

### Token Management

- Git diffs can be large; implement smart truncation
- Add configuration options for diff inclusion level
- Monitor token usage and warn when approaching limits

### Performance

- Getting full diffs for many commits may be slow
- Consider diff processing in parallel
- Cache diff analysis results when possible

### Backward Compatibility

- Keep existing behavior as default
- New features should be opt-in via CLI flags
- Maintain support for existing configuration

## Testing Strategy

1. Test retroactive generation with various starting points
2. Test diff integration with different types of changes
3. Verify LLM-generated categorization quality
4. Ensure existing functionality remains intact

## Expected Benefits

- More accurate changelog entries
- Better handling of projects without existing changelogs
- Reduced maintenance burden of categorization rules
- Enhanced LLM utilization for more intelligent analysis

---

_Plan created by prince, your loyal code puppy_ 🐕
