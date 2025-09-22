# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Add `clog init-changelog` command to create missing changelog files and populate placeholder entries for unreleased tags
- Add `clog update ` command to generate changelog entries for specific versions
### Changed
- Refactor default CLI behavior to properly invoke the update_version command
- Improve git tag processing logic to handle None values and ensure proper string conversions
- Enhance main business logic to process all tags with AI-generated content
- Remove outdated `AGENTS.md` documentation file
- Update implementation status tracking to reflect completed tasks and current command overview
### Fixed
- Fix issues in CHANGELOG.md formatting and structure to align with Keep a Changelog standards

## [0.1.4] - 2025-09-21
### Added
- Add support for generating changelog entries for specific tags with automatic detection of the previous tag when no range is provided
- Introduce functionality to process missing tags and unreleased changes, allowing seamless integration of tagged releases and unreleased entries
### Changed
- Improve changelog generation workflow to prioritize handling of missing tags over full retroactive processing
- Refactor core logic to more accurately handle both tagged releases and unreleased changes using LLM-driven analysis
- Enhance console output and logging for better visibility during tag processing and changelog updates
### Fixed
- Resolve formatting inconsistencies in changelog output
- Fix handling of large prompts and improve reliability of AI content generation and section boundary detection

## [0.1.3] - 2025-09-21
### Added
- Add support for tracking and generating "Unreleased" changelog sections automatically when the current commit is not tagged
- Introduce `--replace-unreleased` CLI option to replace existing Unreleased content instead of appending
- Add `CLOG_REPLACE_UNRELEASED` configuration option to control Unreleased section behavior via environment variables or config files
- Implement bullet point limiting (max 6 items per section) and deduplication for AI-generated changelog entries
- Add comprehensive documentation for AI agent integration, including provider-specific usage examples
- Support retroactive processing of all git tags by default, improving accuracy of changelog updates
### Changed
- Make replace mode the default and only behavior for Unreleased sections, removing the `--replace-unreleased` flag
- Improve changelog formatting by automatically removing empty sections and excessive newlines
- Refactor core logic to seamlessly handle both tagged releases and unreleased changes
- Update AI prompt instructions to emphasize quality over quantity and enforce the 6-bullet limit
- Enhance console output to clearly indicate when unreleased changes are being processed
- Rename `git.py` module to `git_operations.py` for better clarity
### Fixed
- Resolve issues with duplicate Unreleased section headers during changelog generation
- Fix type handling where None values were causing errors in changelog content merging
- Correctly insert unreleased content as individual lines instead of a single string to prevent formatting issues
- Improve extraction and merging logic to skip section headers and empty lines for clean content integration
- Address test stability issues related to git working directory context and global configuration interference
- Ensure proper spacing and formatting before version sections for consistent changelog structure

## [0.1.1] - 2025-09-20
### Added
- Add support for `None` as a valid input for the `log_level` parameter in `setup_logging`, defaulting to `WARNING` level when unset
- Introduce `uv.lock` for precise dependency version tracking and reproducible builds using the `uv` package manager
- Implement bumpversion configuration for automated semantic version management with defined rules for major, minor, and patch increments
### Changed
- Refactor the main Click group function in `cli.py` from `main` to `cli` for improved clarity and consistency
- Enhance `update_changelog` function to accept an optional `existing_content` parameter, allowing more flexible changelog input handling
- Improve git tag processing logic with better debug output and logging to assist troubleshooting
- Update `init_cli` to use a constant path for `.clog.env` and improve monkeypatching support for testing
- Modify commit display formatting in utils with smarter truncation logic for better readability
### Fixed
- Improve test stability by ensuring valid working directory context during git operations and restoring original directories after tests
- Fix indentation error in `TestErrorHandlingIntegration` test case
- Add comprehensive integration test coverage for multi-tag changelog updates with proper validation and cleanup

## [0.1.0] - 2025-09-20
### Added
- Introduce AI-powered changelog generation with support for multiple providers (Anthropic, Cerebras, Groq, OpenAI, Ollama)
- Add automatic detection of new git tags since the last changelog update
- Implement interactive CLI configuration using questionary for user-friendly setup
- Create structured prompt system to generate well-formatted, standardized changelog entries
- Add comprehensive test suite covering unit, integration, and CLI functionality
- Include token counting and logging utilities for better AI interaction transparency
### Changed
- Refactor project structure and development workflow with updated pyproject.toml, mypy configuration, and Makefile
- Improve console output formatting with rich text support for better user experience
- Enhance error handling with retry logic and more descriptive feedback
- Optimize internal modules for git operations, AI integration, and changelog management
- Establish consistent versioning workflow using bump2version configuration
- Update README and documentation to reflect new AI-driven changelog capabilities
### Fixed
- Resolve issues in git tag processing logic for more accurate version tracking
- Address stability concerns in integration tests related to directory context and cleanup
- Fix commit message truncation formatting for improved readability in changelog entries
- Correct handling of None values in logging setup to prevent type-related errors
- Stabilize dependency management and build reproducibility with uv.lock integration
- Improve content extraction logic to ensure clean merges and formatting consistency