# kittylog: Date-Based and Gap-Based Commit Grouping Implementation Plan

## Overview
Add alternatives to git tag-based changelog generation by implementing date-based and gap-based commit grouping for projects that don't use consistent git tagging.

---

## Phase 1: Core Boundary Detection Functions

### 1.1 New Functions in `git_operations.py`
- [ ] **1.1.1** Implement `get_all_commits_chronological()` - Get all commits sorted by commit date
  - [ ] **1.1.1.1** Unit tests for `get_all_commits_chronological()`
- [ ] **1.1.2** Implement `get_commits_by_date_boundaries(grouping='daily'|'weekly'|'monthly')`
  - [ ] **1.1.2.1** Group commits by calendar day (handle timezone considerations)
  - [ ] **1.1.2.2** For each day with commits, identify the last commit as boundary
  - [ ] **1.1.2.3** Handle edge cases (commits spanning midnight)
  - [ ] **1.1.2.4** Support weekly and monthly grouping options
  - [ ] **1.1.2.5** Unit tests for `get_commits_by_date_boundaries()`
- [ ] **1.1.3** Implement `get_commits_by_gap_boundaries(gap_threshold_hours=4)`
  - [ ] **1.1.3.1** Calculate time gaps between consecutive commits
  - [ ] **1.1.3.2** Identify gaps larger than threshold
  - [ ] **1.1.3.3** Mark commits after significant gaps as boundaries
  - [ ] **1.1.3.4** Handle configurable gap thresholds
  - [ ] **1.1.3.5** Unit tests for `get_commits_by_gap_boundaries()`
- [ ] **1.1.4** Implement `get_all_boundaries(mode='tags'|'dates'|'gaps', **kwargs)` - Unified interface
  - [ ] **1.1.4.1** Route to appropriate boundary detection method
  - [ ] **1.1.4.2** Return consistent boundary format regardless of mode
  - [ ] **1.1.4.3** Include boundary metadata (date, commit hash, etc.)
  - [ ] **1.1.4.4** Unit tests for `get_all_boundaries()`

### 1.2 Generalized Commit Range Functions
- [ ] **1.2.1** Implement `get_commits_between_boundaries(from_boundary, to_boundary, mode)`
  - [ ] **1.2.1.1** Handle tag boundaries (existing logic)
  - [ ] **1.2.1.2** Handle date boundaries (commit hash ranges)
  - [ ] **1.2.1.3** Handle gap boundaries (commit hash ranges)
  - [ ] **1.2.1.4** Unit tests for `get_commits_between_boundaries()`
- [ ] **1.2.2** Add `get_previous_boundary(target_boundary, mode)`
  - [ ] **1.2.2.1** Generalized version of `get_previous_tag()`
  - [ ] **1.2.2.2** Unit tests for `get_previous_boundary()`
- [ ] **1.2.3** Add `get_latest_boundary(mode)`
  - [ ] **1.2.3.1** Generalized version of `get_latest_tag()`
  - [ ] **1.2.3.2** Unit tests for `get_latest_boundary()`

### 1.3 Boundary Identifier Generation
- [ ] **1.3.1** Implement `generate_boundary_identifier(boundary, mode)`
  - [ ] **1.3.1.1** For tags: return tag name (existing)
  - [ ] **1.3.1.2** For dates: return formatted date (e.g., "2024-01-15")
  - [ ] **1.3.1.3** For gaps: return formatted date + short hash (e.g., "2024-01-15-abc123de")
  - [ ] **1.3.1.4** Unit tests for `generate_boundary_identifier()`
- [ ] **1.3.2** Implement `generate_boundary_display_name(boundary, mode)`
  - [ ] **1.3.2.1** For tags: return version format (e.g., "[1.0.0]")
  - [ ] **1.3.2.2** For dates: return date format (e.g., "[2024-01-15] - January 15, 2024")
  - [ ] **1.3.2.3** For gaps: return descriptive format (e.g., "[Gap-2024-01-15] - Development session")
  - [ ] **1.3.2.4** Unit tests for `generate_boundary_display_name()`

---

## Phase 2: Configuration and CLI Updates

### 2.1 Configuration Support in `config.py`
- [ ] **2.1.1** Add `KITTYLOG_GROUPING_MODE` environment variable support
  - [ ] **2.1.1.1** Default to 'tags' for backward compatibility
  - [ ] **2.1.1.2** Support 'dates', 'gaps', 'tags' values
  - [ ] **2.1.1.3** Unit tests for environment variable support
- [ ] **2.1.2** Add `KITTYLOG_GAP_THRESHOLD_HOURS` environment variable support
  - [ ] **2.1.2.1** Default to 4 hours
  - [ ] **2.1.2.2** Validate numeric input
  - [ ] **2.1.2.3** Unit tests for gap threshold validation
- [ ] **2.1.3** Add `KITTYLOG_DATE_GROUPING` environment variable support
  - [ ] **2.1.3.1** Default to 'daily'
  - [ ] **2.1.3.2** Support 'daily', 'weekly', 'monthly' values
  - [ ] **2.1.3.3** Unit tests for date grouping options
- [ ] **2.1.4** Update config validation and error handling
  - [ ] **2.1.4.1** Unit tests for config validation

### 2.2 CLI Updates in `cli.py`
- [ ] **2.2.1** Add `--grouping-mode` option to `changelog_options`
  - [ ] **2.2.1.1** Add click.Choice(['tags', 'dates', 'gaps'])
  - [ ] **2.2.1.2** Default to config value or 'tags'
  - [ ] **2.2.1.3** Update help text with examples
  - [ ] **2.2.1.4** Unit tests for CLI option
- [ ] **2.2.2** Add `--gap-threshold` option
  - [ ] **2.2.2.1** Accept numeric value in hours
  - [ ] **2.2.2.2** Default to config value or 4.0
  - [ ] **2.2.2.3** Add validation for positive values
  - [ ] **2.2.2.4** Unit tests for gap threshold CLI option
- [ ] **2.2.3** Add `--date-grouping` option
  - [ ] **2.2.3.1** Add click.Choice(['daily', 'weekly', 'monthly'])
  - [ ] **2.2.3.2** Default to config value or 'daily'
  - [ ] **2.2.3.3** Unit tests for date grouping CLI option
- [ ] **2.2.4** Update CLI help documentation
  - [ ] **2.2.4.1** Add examples for each grouping mode
  - [ ] **2.2.4.2** Explain when to use each mode
  - [ ] **2.2.4.3** Update command descriptions
  - [ ] **2.2.4.4** Unit tests for CLI help documentation

### 2.3 Backward Compatibility
- [ ] **2.3.1** Ensure existing `--from-tag`/`--to-tag` options work with new system
  - [ ] **2.3.1.1** Unit tests for backward compatibility
- [ ] **2.3.2** Add deprecation warnings for conflicting options (e.g., `--from-tag` with `--grouping-mode dates`)
  - [ ] **2.3.2.1** Unit tests for deprecation warnings
- [ ] **2.3.3** Update error messages to guide users toward appropriate options
  - [ ] **2.3.3.1** Unit tests for error messages

---

## Phase 3: Core Business Logic Updates

### 3.1 Workflow Function Updates in `main.py`
- [ ] **3.1.1** Update `handle_auto_mode()` to support boundary modes
  - [ ] **3.1.1.1** Replace `get_all_tags()` calls with `get_all_boundaries(mode)`
  - [ ] **3.1.1.2** Update existing tag detection logic
  - [ ] **3.1.1.3** Handle boundary-based filtering for missing entries
  - [ ] **3.1.1.4** Unit tests for updated auto mode
- [ ] **3.1.2** Update `handle_single_tag_mode()` to `handle_single_boundary_mode()`
  - [ ] **3.1.2.1** Accept boundary identifiers instead of just tags
  - [ ] **3.1.2.2** Update boundary resolution logic
  - [ ] **3.1.2.3** Unit tests for single boundary mode
- [ ] **3.1.3** Update `handle_tag_range_mode()` to `handle_boundary_range_mode()`
  - [ ] **3.1.3.1** Support boundary range specifications
  - [ ] **3.1.3.2** Handle mixed boundary types if needed
  - [ ] **3.1.3.3** Unit tests for boundary range mode
- [ ] **3.1.4** Update `handle_unreleased_mode()` to work with all boundary types
  - [ ] **3.1.4.1** Find latest boundary regardless of type
  - [ ] **3.1.4.2** Calculate unreleased changes from latest boundary
  - [ ] **3.1.4.3** Unit tests for unreleased mode with boundaries

### 3.2 Main Business Logic Function Updates
- [ ] **3.2.1** Update `main_business_logic()` function signature
  - [ ] **3.2.1.1** Add `grouping_mode`, `gap_threshold`, `date_grouping` parameters
  - [ ] **3.2.1.2** Pass parameters through to workflow functions
  - [ ] **3.2.1.3** Update parameter validation
  - [ ] **3.2.1.4** Unit tests for updated business logic function
- [ ] **3.2.2** Update workflow routing logic
  - [ ] **3.2.2.1** Route to appropriate workflow based on boundary mode
  - [ ] **3.2.2.2** Handle parameter conflicts and validation
  - [ ] **3.2.2.3** Unit tests for routing logic
- [ ] **3.2.3** Update error handling for new boundary modes
  - [ ] **3.2.3.1** Unit tests for error handling

### 3.3 Edge Case Handling
- [ ] **3.3.1** Handle repositories with no boundaries (no tags, sparse commits)
  - [ ] **3.3.1.1** Provide helpful error messages
  - [ ] **3.3.1.2** Suggest appropriate grouping modes
  - [ ] **3.3.1.3** Unit tests for no boundary handling
- [ ] **3.3.2** Handle timezone considerations for date boundaries
  - [ ] **3.3.2.1** Unit tests for timezone handling
- [ ] **3.3.3** Handle very active repositories (many commits per day) with date grouping
  - [ ] **3.3.3.1** Unit tests for active repositories
- [ ] **3.3.4** Handle repositories with irregular commit patterns for gap grouping
  - [ ] **3.3.4.1** Unit tests for irregular commit patterns

---

## Phase 4: Changelog Generation Updates

### 4.1 Updates in `changelog.py`
- [ ] **4.1.1** Update `update_changelog()` function
  - [ ] **4.1.1.1** Accept boundary mode parameters
  - [ ] **4.1.1.2** Use generalized boundary functions instead of tag-specific ones
  - [ ] **4.1.1.3** Generate appropriate section headers for each boundary type
  - [ ] **4.1.1.4** Unit tests for updated changelog function
- [ ] **4.1.2** Update `find_existing_tags()` to `find_existing_boundaries()`
  - [ ] **4.1.2.1** Parse date-based section headers
  - [ ] **4.1.2.2** Parse gap-based section headers
  - [ ] **4.1.2.3** Maintain backward compatibility with tag headers
  - [ ] **4.1.2.4** Unit tests for existing boundaries parsing
- [ ] **4.1.3** Update section header generation
  - [ ] **4.1.3.1** Format tag boundaries: `## [1.0.0] - 2024-01-15`
  - [ ] **4.1.3.2** Format date boundaries: `## [2024-01-15] - January 15, 2024`
  - [ ] **4.1.3.3** Format gap boundaries: `## [Gap-2024-01-15] - Development Session`
  - [ ] **4.1.3.4** Unit tests for section header generation

### 4.2 AI Prompt Updates in `ai.py`
- [ ] **4.2.1** Update prompts to handle non-tag boundaries
  - [ ] **4.2.1.1** Explain date-based grouping context to AI
  - [ ] **4.2.1.2** Explain gap-based grouping context to AI
  - [ ] **4.2.1.3** Adjust prompt expectations for different boundary types
  - [ ] **4.2.1.4** Unit tests for AI prompt updates
- [ ] **4.2.2** Update commit context generation
  - [ ] **4.2.2.1** Include boundary reasoning in commit descriptions
  - [ ] **4.2.2.2** Help AI understand the grouping logic
  - [ ] **4.2.2.3** Unit tests for commit context generation

---

## Phase 5: Integration Testing and Documentation

### 5.1 Integration Tests
- [ ] **5.1.1** Test end-to-end workflows with date grouping
- [ ] **5.1.2** Test end-to-end workflows with gap grouping
- [ ] **5.1.3** Test mixed scenarios (existing tag-based changelog + new boundary modes)
- [ ] **5.1.4** Test backward compatibility with existing tag-based workflows

### 5.2 Documentation Updates
- [ ] **5.2.1** Update README.md
  - [ ] **5.2.1.1** Add section explaining new grouping modes
  - [ ] **5.2.1.2** Provide examples for each mode
  - [ ] **5.2.1.3** Explain when to use each approach
- [ ] **5.2.2** Update CLAUDE.md with new commands and options
- [ ] **5.2.3** Add inline documentation to new functions
- [ ] **5.2.4** Create migration guide for users switching from tag-only workflows

---

## Phase 6: Polish and Optimization

### 6.1 Performance Optimization
- [ ] **6.1.1** Optimize commit retrieval for large repositories
- [ ] **6.1.2** Cache boundary calculations appropriately
- [ ] **6.1.3** Add progress indicators for long-running boundary detection

### 6.2 User Experience Improvements
- [ ] **6.2.1** Add helpful suggestions when no boundaries are found
- [ ] **6.2.2** Provide preview mode for boundary detection
- [ ] **6.2.3** Add warnings for potentially suboptimal grouping choices

### 6.3 Error Handling and Validation
- [ ] **6.3.1** Comprehensive error messages for all failure modes
- [ ] **6.3.2** Input validation for all new parameters
- [ ] **6.3.3** Graceful degradation when git operations fail

---

## Completion Criteria
- [ ] **All phases completed and tested**
- [ ] **Backward compatibility maintained**
- [ ] **Documentation updated**
- [ ] **Integration tests passing**
- [ ] **Ready for production use**

---

*Last updated: [Date will be updated as work progresses]*