# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.7] - 2025-09-21
### Added
- Introduce post-processing utilities to clean and format AI-generated changelog content for Keep a Changelog compliance
- Add support for automatic "Unreleased" section generation when the current commit is not tagged
- Add `clog update ` command to generate or update changelog entries for specific versions
### Changed
- Improve AI prompt instructions with stricter formatting requirements and limits on bullet points per section
- Refactor CLI logic to correctly handle tag processing and ensure proper invocation of update commands
- Enhance content deduplication and section management to prevent duplicate headers and formatting errors
- Update core logic to seamlessly process both tagged releases and unreleased changes
- Make replace mode the default behavior for updating Unreleased sections to maintain clean structure
- Automatically remove empty sections, excessive newlines, and malformed entries during post-processing
### Fixed
- Fix issues with None values in git tag processing and content merging logic
- Remove duplicate section headers and ensure proper spacing around markdown headers
- Resolve formatting inconsistencies in changelog output for more stable AI-driven generation
- Ensure robust handling of large AI prompts and improve overall generation stability

## [0.1.6] - 2025-09-21
### Added
- Introduce post-processing utilities to clean and format AI-generated changelog content for Keep a Changelog compliance
- Add support for automatic "Unreleased" section generation when the current commit is not tagged
### Changed
- Improve AI prompt instructions with stricter formatting requirements and limits on bullet points per section
- Enhance changelog content deduplication and section handling to prevent duplicates and formatting errors
- Refactor CLI logic to correctly invoke update commands and handle tag processing
- Update core logic to seamlessly process both tagged releases and unreleased changes
### Fixed
- Fix issues with None values in tag processing and content merging
- Remove empty sections, excessive newlines, and misplaced headers from generated changelogs
- Ensure proper spacing around section headers for Keep a Changelog compliance
- Make replace mode the default behavior for Unreleased sections to maintain clean structure

## [0.1.5] - 2025-09-21
### Added
- Add `clog init-changelog` command to automatically create and initialize missing changelog files with proper structure
- Introduce `clog update ` command for generating changelog entries for specific versions
- Implement post-processing utilities to clean and format AI-generated changelog content according to Keep a Changelog standards
### Changed
- Improve AI prompt instructions with stricter formatting requirements and bullet point limits for clearer output
- Refactor CLI logic to correctly handle tag processing and ensure seamless integration between commands
- Enhance content deduplication and section handling to prevent duplicate headers and formatting issues
- Update core changelog generation workflow to better support both tagged releases and unreleased changes
### Fixed
- Fix issues with None values in git tag processing and content merging to ensure stability
- Resolve formatting errors related to empty sections, excessive newlines, and misplaced headers
### Removed
- Remove outdated `AGENTS.md` documentation file (functionality now covered in README and implementation status)

## [0.1.4] - 2025-09-21
### Added
- Add support for generating changelog entries for specific tags with automatic detection of the previous tag when no range is provided
- Introduce dedicated `unreleased` CLI command to handle unreleased changes separately, improving workflow flexibility
### Changed
- Improve changelog generation logic to seamlessly integrate tagged releases and unreleased entries
- Refactor main workflow to prioritize processing missing tags over full retroactive changelog generation
- Enhance AI content logging and section boundary detection for more reliable parsing and formatting
### Fixed
- Resolve formatting inconsistencies in changelog output
- Fix handling of large prompts to prevent generation issues
- Address edge cases in changelog updates for better robustness and reliability

## [0.1.3] - 2025-09-21
### Added
- Add support for tracking and automatically generating "Unreleased" changelog sections based on commits since the last git tag
- Implement `--replace-unreleased` CLI option and `CLOG_REPLACE_UNRELEASED` environment variable to control whether unreleased content replaces or appends to existing entries
- Introduce bullet point limiting (maximum 6 items per section) and deduplication logic for AI-generated changelog entries
- Add comprehensive AI agent integration documentation and support for multiple providers including Anthropic, OpenAI, Groq, Ollama, and Cerebras
- Include `uv.lock` for reproducible builds and improve dependency management
### Changed
- Change default behavior for unreleased sections to always replace content instead of appending, ensuring accuracy when commits are rolled back
- Improve changelog formatting by removing empty sections, excessive newlines, and trailing whitespace
- Refactor core logic to seamlessly handle both tagged releases and unreleased changes
- Update AI prompt instructions to emphasize quality over quantity and enforce the 6-bullet limit per section
- Rename internal module `git.py` to `git_operations.py` for better clarity
- Remove manual commit categorization in favor of LLM-driven analysis
### Fixed
- Resolve duplicate entries issue in unreleased sections by properly inserting content as individual lines
- Fix type handling problems where None values were passed to functions expecting non-nullable types
- Correct extraction and merging of unreleased content to prevent duplicate section headers
- Improve test stability related to git working directory context and global configuration interference
- Enhance integration test reliability and clean up redundant test setup steps
### Deprecated
- Deprecate the `--replace-unreleased` CLI flag as it's now the default and only behavior for unreleased sections
### Removed
- Remove unused preview functionality that was redundant or no longer needed
- Eliminate manual commit categorization mode in favor of AI-based classification
### Security
- No security-related changes in this release

## [0.1.1] - 2025-09-20
### Added
- Add support for `None` as a valid input for the `log_level` parameter in `setup_logging`, defaulting to `WARNING` level when unset
- Introduce `uv.lock` for precise dependency version tracking and reproducible builds using the `uv` package manager
- Implement bumpversion configuration for automated semantic version management with customizable bump behaviors
### Changed
- Refactor the main Click CLI function from `main` to `cli` for improved clarity and naming consistency
- Enhance `update_changelog` function to accept an optional `existing_content` parameter, allowing more flexible changelog input handling
- Improve git tag processing logic with better debug output and logging for troubleshooting changelog updates
- Optimize test suite directory handling to ensure stability during git operations and improve test isolation
- Remove unused preview functionality from the core changelog business logic
- Update integration tests to handle multiple tag processing scenarios and validate changelog updates more comprehensively
### Fixed
- Fix indentation error in `TestErrorHandlingIntegration` test case
- Resolve issues with temporary directory cleanup affecting test stability during git operations
- Address potential runtime errors in tag retrieval by adding fallback sorting mechanism based on commit date

## [0.1.0] - 2025-09-20
### Added
- Implement AI-powered changelog generation with support for multiple providers (Anthropic, Cerebras, Groq, OpenAI, Ollama)
- Add automatic detection of new git tags since the last changelog update
- Introduce structured prompt system for generating well-formatted changelog entries
- Build interactive configuration CLI using questionary for user-friendly setup
- Include comprehensive error handling with retry logic and token counting utilities
- Add rich console output formatting and dry-run preview mode for safer updates
### Changed
- Refactor core modules to improve organization and separation of concerns
- Enhance development workflow with updated pyproject.toml, mypy configuration, and Makefile
- Improve AI prompt instructions to ensure consistent changelog formatting
- Optimize CLI logic for more reliable tag processing and command invocation
- Strengthen changelog content deduplication and section management to prevent errors
- Update versioning configuration to use bump2version for automated version management
### Fixed
- Resolve issues with None values in git tag processing and content merging
- Correct formatting inconsistencies and malformed changelog entries
- Address edge cases in tag detection and version range handling
- Stabilize large prompt processing for more accurate AI-driven analysis

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