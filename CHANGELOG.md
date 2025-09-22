# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Add support for tracking and displaying unreleased changes since the last git tag
- Introduce automatic 'Unreleased' section generation when the current commit is not tagged
- Add comprehensive documentation for AI agent integration, including configuration examples and provider support
- Include contribution guidelines with instructions for AI provider integration and code quality standards
- Implement automated semantic versioning preparation and dependency management enhancements

### Changed

- Improve changelog formatting by removing empty sections and trailing newlines
- Refactor core logic to process both tagged releases and unreleased changes seamlessly
- Update prompt logic to better handle versions without tags
- Enhance console output to clearly indicate when unreleased changes are being processed
- Reorder and consolidate import statements across core modules and tests for improved readability
- Rename main Click group function from `main` to `cli` for clarity
- Update `update_changelog` function to accept an `existing_content` parameter for better content handling

### Removed

- Remove manual commit categorization in favor of LLM-driven analysis
- Remove unused preview functionality and redundant test setup steps
- Remove unnecessary blank lines and improve code structure in various source files

### Fixed

- Fix test stability issues related to git working directory context
- Fix parameter alignment in function signatures for better consistency
### Added

- Add support for tracking and displaying unreleased changes in changelog generation
  - Automatically detect changes since the last git tag
  - Include an 'Unreleased' section when the current commit is not tagged
  - Enhance changelog formatting to gracefully handle versions without tags
- Introduce comprehensive contribution guidelines in CONTRIBUTING.md
  - Detail development setup, code quality standards, and testing requirements
  - Provide instructions for integrating new AI providers via aisuite
- Add documentation for AI agent integration and configuration in AGENTS.md
  - Document supported AI providers: Anthropic, OpenAI, Groq, Ollama, and Cerebras
  - Explain the structured workflow used by AI agents to generate changelog entries
  - Include configuration examples using environment variables

### Changed

- Improve changelog formatting and output quality
  - Clean up trailing newlines to prevent excessive blank lines
  - Remove empty [Unreleased] sections automatically
  - Ensure consistent spacing before version sections
- Enhance core business logic to process both tagged releases and unreleased changes
- Refactor integration tests for better directory context management and cleanup
- Rename main Click group function from `main` to `cli` for improved clarity

### Fixed

- Address test stability issues related to git working directory context
- Correct parameter alignment in function signatures for better code consistency

### Removed

- Remove unused preview functionality and redundant test setup steps

## [0.1.1] - 2025-09-20

### Added

- Add support for `None` as a valid input for the `log_level` parameter in the `setup_logging` function, defaulting to `WARNING` level when unspecified
- Introduce `uv.lock` for precise dependency version tracking, enabling reproducible builds and faster installations using the `uv` package manager
- Implement `bumpversion` configuration for automated semantic version management, including rules for version bumps and release tagging

### Changed

- Rename the main Click group function in the CLI module from `main` to `cli` for improved clarity and consistency (no functional changes)
- Enhance changelog generation logic with better git tag handling and improved debug output
- Refactor integration tests to ensure proper directory context and cleanup, improving test stability and isolation
- Update the `update_changelog` function to accept an `existing_content` parameter, allowing more flexible input handling
- Improve commit display formatting with smarter truncation logic in utility functions

### Fixed

- Resolve test stability issues caused by invalid working directories during git operations by restoring original directory context
- Correct an indentation error in the `TestErrorHandlingIntegration` test case
- Remove unused preview functionality from the main business logic, reducing unnecessary code paths

### Removed

- Eliminate redundant directory creation and changelog pre-setup steps in integration tests for cleaner test execution flow

## [0.1.0] - 2025-01-01

### Added

- **Initial Release**: Core functionality for AI-powered changelog generation from git tags
- **Multi-Provider AI Support**: Integration with Anthropic, Cerebras, Groq, OpenAI, and Ollama
- **Git Tag Integration**: Automatic detection of new tags since last changelog update
- **Smart Change Analysis**: Categorizes commits into Added, Changed, Fixed, Removed, Deprecated, and Security sections
- **Interactive Configuration**: `changelog-updater init` command for easy setup
- **Configuration Management**: Commands to show, set, get, and unset configuration values
- **Keep a Changelog Format**: Proper formatting following the Keep a Changelog standard
- **Dry Run Mode**: Preview generated content without modifying files
- **Flexible Tag Processing**: Support for specific tag ranges or automatic detection
- **Command Line Interface**: Comprehensive CLI with options for customization

### Technical

- **GitPython Integration**: Robust git operations for tag and commit analysis
- **Token Counting**: Accurate token usage tracking for AI model interactions
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Logging System**: Configurable logging levels for debugging and monitoring
- **Rich Console Output**: Beautiful terminal output with styled text and panels