# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.6] - 2025-09-21
### Added
- Introduce post-processing utilities to clean and format AI-generated changelog content for Keep a Changelog compliance
- Add support for automatic "Unreleased" section generation when the current commit is not tagged
- Add `clog init-changelog` command to automatically create and initialize missing changelog files with proper structure
- Add `clog update ` command to generate or update changelog entries for specific versions
### Changed
- Improve AI prompt instructions with stricter formatting requirements and limits on bullet points per section
- Refactor CLI logic to correctly handle tag processing and ensure proper invocation of update commands
- Enhance changelog content deduplication and section handling to prevent duplicates and formatting errors
- Update core logic to seamlessly process both tagged releases and unreleased changes
- Improve changelog generation workflow to overwrite unreleased content when targeting specific tags
### Fixed
- Fix issues with None values in git tag processing and content merging logic
- Remove duplicate section headers and ensure proper spacing around markdown headers
- Automatically remove empty sections, excessive newlines, and malformed changelog entries
- Resolve formatting inconsistencies in changelog output and improve handling of large AI prompts for more stable generation

## [0.1.5] - 2025-09-21
### Added
- Add `clog init-changelog` command to automatically create and initialize missing changelog files with proper structure
- Add `clog update ` command to generate or update changelog entries for specific versions
- Introduce post-processing utilities to clean and format AI-generated changelog content for Keep a Changelog compliance
### Changed
- Refactor CLI logic to correctly handle changelog initialization and version update workflows
- Improve AI prompt instructions with stricter formatting rules and a maximum of 6 bullets per section
- Enhance content deduplication and section handling to prevent formatting errors and duplicate headers
- Update core changelog generation logic to seamlessly support both tagged releases and unreleased changes
- Make replace mode the default behavior for updating Unreleased sections to ensure fresh content
- Automatically remove empty sections, excessive newlines, and misplaced headers during post-processing
### Fixed
- Fix issues with None values in git tag processing and content merging to ensure robust version handling

## [0.1.4] - 2025-09-21
### Added
- Add support for generating changelog entries for specific tags with automatic detection of the previous tag when no range is provided
- Introduce dedicated `unreleased` CLI command to handle unreleased changes separately, improving workflow flexibility
### Changed
- Refactor main changelog workflow to prioritize processing missing tags over full retroactive generation
- Improve formatting logic to ensure consistent output and prevent duplication or malformed sections
- Enhance AI content logging and section boundary detection for more reliable parsing and generation
- Update changelog generation to seamlessly integrate tagged releases with unreleased entries
### Fixed
- Resolve formatting inconsistencies in generated changelog entries
- Fix handling of large prompts that previously caused issues in AI-driven analysis
- Correct edge cases in tag detection and changelog updating logic
- Improve robustness when processing git tags and version ranges
- Address issues with directory handling and file paths across multiple modules
- Stabilize unreleased section merging to prevent duplication and ensure proper overwrite behavior

## [0.1.3] - 2025-09-21
### Added
- Add support for tracking and generating "Unreleased" changelog sections automatically when the current commit is not tagged
- Introduce `--replace-unreleased` CLI flag to replace existing Unreleased content instead of appending to it
- Add `CLOG_REPLACE_UNRELEASED` configuration option to control Unreleased section behavior via environment variables or config files
- Implement bullet point limiting (maximum 6 items per section) and deduplication for AI-generated changelog entries
- Add support for retroactive processing of all git tags by default, improving changelog generation accuracy
- Include documentation for AI agent integration, supported providers, and configuration examples
### Changed
- Change default behavior of Unreleased section handling to always replace content instead of appending
- Improve changelog formatting by removing empty sections and excessive blank lines automatically
- Simplify AI prompt instructions to emphasize quality over quantity and enforce 6-bullet limit
- Refactor core changelog logic to seamlessly handle both tagged releases and unreleased changes
- Update console output to clearly indicate when unreleased changes are being processed
- Enhance git tag detection and changelog insertion logic for better reliability and formatting
### Fixed
- Resolve issue where unreleased section content was being inserted as a single string instead of individual lines
- Fix duplicate section headers and empty line issues when merging AI-generated content with existing changelog entries
- Address type handling problems where None values were passed to functions expecting non-nullable types
- Correct test stability issues related to git working directory context and global configuration interference
- Improve changelog cleanup logic to remove trailing newlines and prevent malformed output
### Removed
- Remove the `--replace-unreleased` CLI flag as replace mode is now the default and only behavior for Unreleased sections
- Eliminate manual commit categorization in favor of LLM-driven analysis
- Remove unused preview functionality and redundant test setup steps

## [0.1.1] - 2025-09-20
### Added
- Add support for `None` as a valid input for the `log_level` parameter in `setup_logging`, defaulting to `WARNING` level when unset
- Introduce `uv.lock` for precise dependency version tracking and reproducible builds
- Add bumpversion configuration for automated semantic version management
### Changed
- Refactor the main Click CLI function from `main` to `cli` for improved clarity and consistency
- Enhance changelog generation logic with better git tag handling and additional debug output
- Improve commit display formatting in utilities with smarter truncation
- Update `update_changelog` function signature to accept `existing_content` parameter, allowing more flexible content input
- Modify integration tests to ensure proper directory context and cleanup during execution
### Fixed
- Improve test stability by ensuring valid working directory handling during git operations
- Fix indentation error in `TestErrorHandlingIntegration` test case
- Remove unused preview functionality from main business logic to reduce clutter

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