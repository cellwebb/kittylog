# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.8] - 2025-09-21

### Added

- Add exclusion of changelog files (CHANGELOG.md, changelog.md) from git diff operations
- Enhance AI analysis accuracy by filtering out changelog-related changes

### Changed

- Modify `get_git_diff` function to use pathspecs for excluding specific files
- Update diff command to prevent changelog updates from being included in future changelog generation

### Fixed

- Fix issue where changelog file modifications were incorrectly included in diff analysis
- Resolve potential noise in AI-generated changelog by focusing only on relevant code changes

## [0.1.7] - 2025-09-21

### Added

- Dynamically control the "Unreleased" section in changelogs based on whether the current commit is tagged
- Automatic removal of "Unreleased" sections when generating tagged releases
- Post-processing utilities to ensure Keep a Changelog compliance and proper formatting

### Changed

- Refactored changelog generation logic to improve handling of tagged and untagged commits
- Updated AI prompt formatting with stricter rules and bullet point limits for clearer output
- Improved deduplication and section management to prevent common changelog formatting errors
- Made replace mode the default behavior for updating "Unreleased" sections to avoid duplication

### Fixed

- Resolved issues with None value handling during git tag processing and content merging
- Eliminated redundant checks and streamlined tag validation in postprocessing steps

## [0.1.6] - 2025-09-21

### Added

- Add post-processing utilities to clean and format AI-generated changelog content
- Add automatic "Unreleased" section generation for commits that are not tagged
- Add `remove_unreleased_sections()` function to clean up changelog content for tagged releases

### Changed

- Improve AI prompt instructions with stricter formatting requirements and bullet point limits
- Enhance changelog content deduplication and section handling to prevent duplicates and formatting errors
- Update core logic to seamlessly process both tagged releases and unreleased changes
- Make replace mode the default behavior for Unreleased sections to maintain clean structure
- Ensure proper spacing around section headers for Keep a Changelog compliance

### Fixed

- Fix issues with None values in tag processing and content merging
- Remove empty sections, excessive newlines, and misplaced headers from generated changelogs

## [0.1.5] - 2025-09-21

### Added

- Add `clog init-changelog` command to automatically create and initialize missing changelog files with proper Keep a Changelog structure
- Introduce `clog update ` command for generating changelog entries for specific versions
- Implement post-processing utilities to clean and format AI-generated changelog content, ensuring compliance with Keep a Changelog standards

### Changed

- Refactor CLI logic to correctly handle tag processing and invocation of update commands
- Enhance AI prompt instructions with stricter formatting rules and bullet point limits for more consistent output
- Improve content deduplication and section handling to prevent duplicate headers and formatting issues
- Update core changelog generation workflow to seamlessly support both tagged releases and unreleased changes
- Make replace mode the default behavior for Unreleased sections to ensure fresh content generation
- Integrate post-processing steps directly into the AI generation pipeline for automatic cleanup

### Fixed

- Fix issues with None values during git tag processing and content merging
- Resolve formatting errors caused by empty sections, excessive newlines, and misplaced headers
- Correct CLI default behavior to properly invoke the update_version command

### Removed

- Remove outdated AGENTS.md documentation file in favor of updated implementation tracking and README improvements

## [0.1.4] - 2025-09-21

### Added

- Add support for generating changelog entries for specific tags with automatic detection of the previous tag when no range is provided
- Introduce functionality to process missing git tags and seamlessly integrate them with existing unreleased changes
- Add `unreleased` CLI command for dedicated handling of unreleased changelog entries
- Implement `find_existing_tags` function to parse and identify already documented tags in the changelog

### Changed

- Improve changelog generation workflow to prioritize processing missing tags over full retroactive updates
- Enhance AI prompt logic to include git diff content (up to 5000 characters) for better context-aware changelog entries
- Increase AI API timeout to 120 seconds to accommodate larger prompts and prevent failures
- Refactor section boundary detection to correctly handle sub-section headers in AI-generated content

### Fixed

- Fix formatting inconsistencies in changelog output
- Address issues with handling large prompts by truncating excessive diff content and increasing timeout tolerance
- Improve error classification to properly handle Cerebras SDK-related errors without unnecessary retries

## [0.1.3] - 2025-09-21

### Added

- Add support for tracking and automatically including an "Unreleased" section in the changelog when the current commit is not tagged
- Introduce `--replace-unreleased` CLI option to replace existing unreleased content instead of appending to it
- Add `CLOG_REPLACE_UNRELEASED` configuration option to control unreleased section behavior via environment variables or config files
- Implement bullet point limiting (maximum 6 items per section) and deduplication for AI-generated changelog entries
- Add comprehensive documentation for AI agent integration, including supported providers and configuration examples
- Include contribution guidelines with instructions for adding new AI providers and development setup

### Changed

- Change default behavior for unreleased sections to always replace content instead of appending, preventing duplicate entries and ensuring accuracy when commits are rolled back
- Improve changelog formatting by removing empty sections, excessive newlines, and trailing whitespace
- Refactor core logic to seamlessly handle both tagged releases and unreleased changes
- Update AI prompt instructions to emphasize quality over quantity and enforce the 6-bullet limit
- Rename `git.py` module to `git_operations.py` for better clarity
- Simplify bullet limiting logic and remove complex legacy deduplication code

### Fixed

- Fix duplicate section headers issue when processing unreleased changes by improving content extraction and merging logic
- Resolve formatting issues caused by inserting unreleased content as a single string instead of individual lines
- Address type issues where None values were passed to functions expecting non-nullable types
- Improve test stability related to git working directory context and global configuration interference
- Fix excessive blank lines and improper spacing in changelog output formatting

## [0.1.1] - 2025-09-20

### Added

- Add support for None log level parameter in setup_logging function, defaulting to WARNING level when unset
- Introduce uv.lock file for precise dependency version tracking and reproducible builds
- Add bumpversion configuration for automated semantic version management
- Implement multi-tag processing integration tests with changelog update validation

### Changed

- Rename main Click group function to cli for better clarity and consistency in command-line interface
- Improve changelog update logic with enhanced tag handling and debug output
- Refactor init_cli to use a constant path for .clog.env, enabling easier monkeypatching during tests
- Enhance commit display formatting in utils with smarter truncation logic

### Fixed

- Improve test stability by ensuring valid working directory context during git operations
- Fix indentation error in TestErrorHandlingIntegration test case
- Remove unused preview functionality from main business logic
- Ensure proper directory handling and cleanup in integration tests for better isolation

## [0.1.0] - 2025-09-20

### Added

- Add AI-powered changelog generation capability with support for multiple providers (Anthropic, Cerebras, Groq, OpenAI, Ollama)
- Add automatic detection and processing of git tags to structure changelog entries
- Add "Unreleased" section tracking for commits that occur between official releases
- Add interactive CLI configuration using questionary for easy setup
- Add dry-run preview mode to show changelog updates without writing to file
- Add command-line options for flexible usage including `-f`, `-s`, `-t`, `-p`, `-m`, and `--replace-unreleased`

### Changed

- Implement structured prompt system for more consistent and accurate changelog formatting
- Improve error handling with user-friendly messages and retry logic
- Enhance console output with rich formatting for better readability
- Refactor project structure to support modular AI provider integration via aisuite
- Update development workflow with comprehensive tooling (black, isort, ruff, pytest)
- Isolate tests from global configuration files to prevent side effects during execution

### Fixed

- Fix version tracking logic to correctly identify new tags since last changelog update
- Fix token counting and logging utilities to provide accurate usage feedback
- Fix git operations module to handle edge cases in tag detection and commit analysis
- Fix configuration loading to respect environment variables and local settings

### Security

- Add secure handling of API keys and configuration through environment variable isolation
- Implement proper logging level controls to prevent accidental exposure of sensitive data

## [0.1.0] - 2025-09-20

### Added

- Introduce AI-powered changelog generation with support for multiple providers (Anthropic, Cerebras, Groq, OpenAI, Ollama)
- Add `clog init-changelog` command to automatically create and structure missing changelog files
- Add `clog update` command to generate changelog entries for specific versions or tags
- Implement automatic detection of new git tags since the last changelog update
- Add interactive CLI configuration using questionary for streamlined setup
- Include post-processing utilities to ensure Keep a Changelog compliance and clean formatting

### Changed

- Refactor CLI logic to properly handle tag processing and command invocation
- Improve AI prompt structure with stricter formatting rules and bullet point limits
- Enhance changelog content deduplication and section management to prevent duplicates
- Update core logic to seamlessly process both tagged releases and unreleased changes
- Change default behavior to replace Unreleased section content instead of appending
- Optimize handling of large AI prompts and git history for more stable generation

### Fixed

- Resolve issues with None values in tag processing and content merging
- Remove empty sections, excessive newlines, and malformed headers from output
- Ensure correct spacing around section headers for consistent markdown formatting
- Fix directory and file path handling for more robust changelog file updates
