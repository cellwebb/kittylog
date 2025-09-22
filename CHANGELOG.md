# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Add `clog init-changelog` command to automatically create and initialize missing changelog files with proper structure
- Add `clog update ` command to generate changelog entries for specific versions
- Introduce post-processing utilities to clean and format AI-generated changelog content
- Add support for automatic "Unreleased" section generation when current commit is not tagged
### Changed
- Refactor CLI logic to correctly invoke update commands and handle tag processing
- Improve AI prompt instructions with stricter formatting requirements and bullet point limits
- Enhance changelog content deduplication and section handling to prevent duplicates and formatting errors
- Update core logic to seamlessly process both tagged releases and unreleased changes
### Fixed
- Fix issues with None values in tag processing and content merging
- Remove empty sections, excessive newlines, and misplaced headers from generated changelogs
- Ensure proper spacing around section headers for Keep a Changelog compliance
- Make replace mode the default behavior for Unreleased sections to maintain clean structure

## [0.1.5] - 2025-09-21
### Added
- Add `clog init-changelog` command to automatically create and initialize missing changelog files with proper structure
- Add `clog update ` command to generate or update changelog entries for specific versions
- Introduce post-processing utilities to clean and format AI-generated changelog content for Keep a Changelog compliance
### Changed
- Improve AI prompt instructions with stricter formatting rules and limits on bullet points per section
- Refactor CLI logic to correctly handle tag processing and ensure proper invocation of update commands
- Enhance changelog generation workflow to better manage unreleased sections and version updates
### Fixed
- Fix issues with None values in git tag processing and content merging logic
- Remove duplicate section headers and ensure proper spacing around markdown headers
- Automatically remove empty sections, excessive newlines, and malformed changelog entries

## [0.1.4] - 2025-09-21
### Added
- Add support for generating changelog entries for specific tags with automatic detection of the previous tag when no range is provided
- Introduce functionality to process missing git tags and seamlessly integrate them with unreleased changes in the changelog
### Changed
- Improve changelog generation workflows by overwriting unreleased content when targeting specific tags, ensuring up-to-date and accurate entries
- Refactor core logic to prioritize processing missing tags over full retroactive changelog generation, enhancing efficiency and reliability
### Fixed
- Resolve formatting inconsistencies in changelog output and improve handling of large AI prompts for more stable generation
- Fix issues with directory handling, file paths, and edge cases in changelog updates to ensure robust file processing

## [0.1.3] - 2025-09-21
### Added
- Add support for tracking and generating "Unreleased" changelog sections automatically when the current commit is not tagged
- Introduce `--replace-unreleased` CLI option to replace existing Unreleased content instead of appending to it
- Implement `find_version_section()` function to locate and manage specific version sections in the changelog
- Add `CLOG_REPLACE_UNRELEASED` configuration option to control Unreleased section behavior via environment variables or config files
- Support bullet point limiting (maximum 6 items per section) and deduplication for AI-generated changelog entries
- Document AI agent integration and configuration in new `AGENTS.md` file, including supported providers and usage examples
### Changed
- Change default behavior to replace Unreleased section content instead of appending, preventing duplicate entries and ensuring accuracy when commits are rolled back
- Improve changelog formatting by removing empty sections, trailing newlines, and excessive spacing
- Refactor core logic to seamlessly handle both tagged releases and unreleased changes
- Update AI prompt instructions to prioritize quality over quantity and enforce a 6-bullet limit per section
- Rename `git.py` module to `git_operations.py` for better clarity
- Simplify bullet limiting logic and remove complex deduplication mechanisms
### Fixed
- Fix issue where Unreleased content was being inserted as a single string instead of individual lines, causing formatting problems
- Resolve duplicate section headers and entries when appending or replacing Unreleased content
- Correct type handling issues where None values were passed to functions expecting non-nullable types
- Improve extraction and merging of AI-generated content to prevent duplicate headers and ensure clean formatting
- Stabilize integration tests by fixing git working directory context and global configuration interference
- Enhance changelog generation logic to gracefully handle cases where no git tags exist

## [0.1.1] - 2025-09-20
### Added
- Add support for `None` as a valid input for the `log_level` parameter in the `setup_logging` function, defaulting to `WARNING` level when unset
- Introduce `uv.lock` for precise dependency version tracking, enabling reproducible builds and faster installations with the `uv` package manager
- Implement `bumpversion` configuration for automated semantic version management, including rules for major, minor, and patch increments
### Changed
- Rename the main Click group function from `main` to `cli` in the CLI module for improved clarity and consistency
- Enhance changelog generation logic with better git tag handling, debug logging, and support for multi-tag processing
- Refactor integration tests to improve directory handling, test stability, and isolation during git operations
### Fixed
- Improve test stability by ensuring valid working directory context during git operations and restoring original paths after execution
- Fix an indentation error in the `TestErrorHandlingIntegration` test case
- Remove unused preview functionality from the main changelog business logic to reduce complexity
### Security
- No security-related changes included in this version

## [0.1.0] - 2025-09-20
### Added
- Add core functionality for AI-powered changelog generation from git commit history
- Introduce support for multiple AI providers including Anthropic, Cerebras, Groq, OpenAI, and Ollama
- Implement automatic detection of new git tags since the last changelog update
- Add interactive CLI setup using questionary for easy configuration management
- Include comprehensive test suite covering unit, integration, and CLI functionality
- Add dry-run mode to preview generated changelog content without modifying files
### Changed
- Refactor CLI logic to correctly invoke update commands and process git tags
- Improve AI prompt instructions with stricter formatting rules for consistent output
- Enhance changelog content deduplication and section handling to prevent duplicates
- Update core logic to seamlessly handle both tagged releases and unreleased changes
- Improve formatting utilities to ensure compliance with Keep a Changelog standard
- Optimize tag processing workflow to prioritize missing tags over full retroactive generation
### Fixed
- Fix handling of None values in tag processing and content merging logic
- Remove empty sections, excessive newlines, and malformed headers from output
- Correct issues related to large prompt handling and improve AI integration robustness
- Ensure proper spacing around section headers for consistent markdown formatting