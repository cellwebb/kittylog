# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).




## [2.4.0] - 2025-12-04

### Added

- Qwen AI provider with OAuth device flow and API key authentication support
- Secure token storage system for OAuth providers with atomic writes and proper file permissions
- Structured logging system with contextual information throughout the application
- Version style detection and formatting utilities for consistent changelog version handling

### Changed

- Replace normalize_tag with style-aware version formatting across changelog modules
- Simplify test fixtures with MockAIResponse builder and fluent MockProviderBuilder interface
- Enhance OAuth authentication CLI with Qwen support and improved provider status display
- Update documentation with visual indicators for correct uv run command usage

### Fixed

- Correct version prefix stripping tests to use proper string literal formatting
- Fix import order in boundary and missing mode handlers following PEP 8 guidelines

## [2.3.4] - 2025-12-04

### Added

- Comprehensive version tag normalization support across all changelog modes

### Fixed

- Resolve boundary filtering bug causing incorrect reprocessing of changelog entries
- Fix tag recognition issues by implementing proper version normalization

## [2.3.3] - 2025-12-04

### Added

- Implement proper unreleased section insertion logic for automated changelog updates

## [2.3.2] - 2025-12-04

### Added

- Enable unreleased mode for changelog generation with special_unreleased_mode flag to process commits since last tag
- Add --context-entries CLI option to control preceding entries count for style reference during AI generation
- Add support for extracting preceding changelog entries with extract_preceding_entries() function

### Changed

- Update default model configurations to latest versions (gpt-5-mini, claude-haiku-4-5, gpt-oss-20b)
- Change processing order to chronological for boundaries and missing tags to provide AI with historical context
- Fix tag recognition issues by normalizing 'v' prefix when comparing with existing boundaries
- Refactor configuration system to use KittylogConfigData dataclass with improved validation and error handling
- Centralize provider implementations using standardized base classes with consistent error handling
- Split monolithic modules into focused packages (constants, changelog, config, prompt, providers, utils, workflow)

### Fixed

- Resolve tag recognition and changelog ordering issues with proper version normalization and semantic ordering
- Fix token counting fallback estimation to use character-based approximation instead of zero fallback
- Correct boundary filtering bug causing all boundaries to be reprocessed instead of only missing ones
- Fix configuration precedence and API key loading to prevent environment pollution

## [2.3.1] - 2025-12-04

### Changed

- Change processing order to chronological for boundaries and missing tags to provide AI with historical context
- Update default model configurations to latest versions (gpt-5-mini, claude-haiku-4-5, gpt-oss-20b)
- Update documentation examples to reflect current supported model versions

### Fixed

- Resolve tag recognition issues by normalizing 'v' prefix when comparing with existing boundaries
- Fix changelog ordering to process tags in reverse order (newest first) with proper date formatting
- Implement semantic version ordering for entry insertion with comprehensive test coverage

## [2.3.0] - 2025-12-04

### Added

- Add --context-entries CLI option to include preceding changelog entries for style reference
- Support for extracting and using preceding changelog entries as style context in AI generation
- Add extract_preceding_entries() function to retrieve N most recent changelog entries
- Add release command with comprehensive options for automated changelog preparation
- Add prepare_release function to convert Unreleased sections to versioned releases
- Add comprehensive test coverage for provider registry validation and consistency

### Changed

- Refactor configuration system with dataclass-based validation and improved error handling
- Refactor all 24 AI providers to use standardized base classes and reduce code duplication
- Refactor core modules into focused packages (config, changelog, constants, utils)
- Update configuration precedence to load environment variables directly into os.environ
- Refactor workflow modules to use structured parameter objects instead of argument explosion
- Update API endpoints across multiple providers to current specifications
- Replace bump-my-version with custom version management system
- Improve token counting fallback estimation with character-based approximation
- Reorganize utility modules into package structure for better code organization

### Fixed

- Resolve tag recognition and changelog ordering issues in missing entries mode
- Fix critical boundary filtering bug causing all boundaries to be reprocessed
- Update API key loading to use environment variables with proper override behavior
- Correct version normalization and semantic version ordering in changelog insertion
- Fix response validation and specific exception handling across all AI providers
- Resolve environment pollution in OAuth token storage and configuration loading

## [2.2.0] - 2025-12-03

### Added

- Support for project-level configuration files (.kittylog.env) with precedence over user-level configs
- Robust encoding fallback system for subprocess execution supporting international locales
- Keyboard shortcuts in interactive prompts for faster navigation and improved user experience
- Automatic sensitive value hiding in configuration display for enhanced security
- Support for multiple configuration sources with clear precedence indication

### Changed

- Simplify test suite by removing complex integration tests and focusing on unit tests
- Refactor init command from 288 to 50 lines using modular components for better maintainability
- Replace XML configuration with YAML format for improved readability and consistency
- Extract error classification function to resolve circular imports and improve module organization
- Consolidate duplicate get_repo() function to prevent cache inconsistency issues

### Fixed

- Resolve memory leak causing application crashes in subprocess handling
- Correct timezone handling in date calculations across boundary detection
- Fix parser logic for proper handling of unreleased-only sections and version normalization
- Resolve circular import by moving remove_unreleased_sections import to correct location

### Security

- Remove environment pollution from OAuth token storage to prevent unintended exposure
- Implement SecureConfig pattern for API key management without global pollution
- Add specific exception handling for HTTPStatusError, TimeoutException, and RequestError across providers


## [2.1.0] - 2025-12-03

### Added

- Add standalone model configuration command supporting 20+ providers with interactive setup
- Add Claude Code OAuth authentication with PKCE flow and automatic token refresh
- Create standalone authentication command for Claude Code with browser auto-open
- Support modular CLI commands with 'kittylog auth' and 'kittylog model' standalone operations
- Add audience configuration workflow for changelog targeting in interactive setup

### Changed

- Refactor CLI architecture into modular components with dedicated auth, model, and language modules
- Eliminate environment pollution in API key management using SecureConfig context manager
- Resolve circular imports by consolidating classify_error function in errors module
- Simplify init command from 288 to 50 lines by delegating to specialized modules
- Enhance error handling across all AI providers with response validation and specific exception handling
- Replace parameter explosion in workflow with structured ChangelogOptions and WorkflowOptions objects
- Modernize configuration system using validated dataclasses and centralized cache management
- Standardize provider response validation using defensive .get() methods and proper exception chaining

### Removed

- Remove deprecated reauth command from config group
- Remove types.py module entirely after consolidating functions
- Remove redundant environment variable pollution from OAuth token storage
- Eliminate duplicate get_repo() function by consolidating git repository access logic

### Fixed

- Resolve memory leak causing application crashes in provider error handling
- Correct timezone handling in date-based boundary detection
- Fix OAuth token storage to stop polluting os.environ after saving
- Resolve circular import issues between ai.py and ai_utils.py modules
- Fix boundary filtering bug causing all boundaries to be reprocessed instead of missing ones only
- Correct token counting fallback to use character-based estimation instead of zero

## [2.0.0] - 2025-12-02

### Added

- Introduce interactive configuration mode with questionary prompts for guided setup
- Add optional git diff inclusion in AI context with cost warning notifications
- Implement environment variable precedence over config files for API key handling

### Changed

- Enhance changelog boundary detection to support nested brackets in date headings
- Propagate all configuration parameters through the complete call chain
- Improve provider modules by removing trailing whitespace for cleaner code

### Fixed

- Resolve parameter propagation issues causing test failures
- Correct config precedence problems to ensure proper environment variable handling


## [1.6.0] - 2025-11-01

### Added

- Support for audience targeting allowing customization of changelog tone for developers, users, or stakeholders
- Comprehensive multilingual support with 30+ predefined languages and custom language options
- Intelligent version detection that automatically determines semantic version bumps based on commit analysis

### Changed

- Refactor documentation with comprehensive README rewrite featuring improved structure and visual design
- Update configuration system to persist language and audience preferences in environment files
- Extend AI prompt generation throughout pipeline to include audience-specific instructions and context

### Fixed

- Resolve boundary filtering bug causing all boundaries to be reprocessed instead of only missing ones
- Correct parameter propagation issues that were causing test failures
- Fix trailing whitespace in provider modules for code cleanliness


## [1.5.0] - 2025-11-01

### Added

- Multilingual support for changelog generation with 30+ predefined languages and interactive language selection CLI
- Intelligent semantic version detection based on commit analysis for unreleased changes
- Comprehensive documentation rewrite with modern badge layout, quick start guide, and visual hierarchy

### Changed

- Refactor AI provider architecture into modular system supporting 11 new providers including Chutes, DeepSeek, Fireworks, Gemini, LM Studio, MiniMax, Mistral, StreamLake, Synthetic, and Together AI
- Implement interactive configuration mode with guided setup using questionary prompts and context-aware defaults for grouping modes
- Replace openai-specific client with generic httpx.post calls for unified multi-provider interface
- Update all dependencies to latest stable versions and bump core dependencies for improved stability

### Fixed

- Resolve critical boundary filtering bug causing all boundaries to be reprocessed due to prefix mismatch between tag extraction and identifier generation
- Fix test isolation issues and git repository context problems causing order-dependent test failures
- Correct timezone handling in date calculations and ensure consistent timezone usage throughout boundary-aware changelog processing


## [1.4.0] - 2025-10-31

### Added

- Interactive configuration mode with guided setup using questionary prompts and comprehensive explanations for grouping modes
- Optional git diff inclusion in AI context with clear cost warnings for enhanced changelog generation
- Intelligent version detection that automatically calculates semantic version bump based on commit analysis
- Support for 11 new AI providers: Chutes, Custom Anthropic/OpenAI, DeepSeek, Fireworks, Gemini, LM Studio, MiniMax, Mistral, StreamLake, Synthetic, and Together AI

### Changed

- Enhanced boundary detection to handle nested brackets in date headings for improved changelog parsing
- Updated configuration system with environment variable precedence to preserve API keys over config files
- Improved boundary filtering logic to prevent reprocessing all boundaries by normalizing identifier prefixes
- Refactored AI integration to use direct provider SDK implementations instead of external abstraction layer

### Fixed

- Parameter propagation issues causing test failures in AI module and configuration handling
- Boundary filtering bug where prefix mismatch between "v0.1.0" and "0.1.0" caused all boundaries to be reprocessed
- Critical changelog boundary detection that was incorrectly processing ALL boundaries instead of only missing ones

### Deprecated

- Legacy XML configuration format (use YAML instead)

### Removed

- Obsolete aisuite mypy configuration and associated dependencies

## [1.3.0] - 2025-10-31

### Added

- Support for 11 new AI providers including Chutes, DeepSeek, Fireworks, Gemini, LM Studio, MiniMax, Mistral, StreamLake, Synthetic, Together AI, and custom Anthropic/OpenAI endpoints
- Interactive CLI setup for new AI providers with custom endpoint configuration
- Special handling for local providers like LM Studio and Ollama with optional API keys and default URLs
- Expanded environment variable configuration support for new providers

### Changed

- Enhance provider registry system to integrate new AI provider implementations
- Improve provider integration tests with centralized configuration loading
- Update documentation to include expanded provider support and configuration guidelines

### Removed

- Monolithic provider file replaced by individual provider modules

### Fixed

- Unit test coverage for new providers including API key validation and error handling scenarios

### Security

- No security vulnerabilities addressed in this release

## [1.2.0] - 2025-10-04

### Added

- Dedicated Z.AI coding provider with distinct API endpoint support
- Comprehensive test coverage for new Z.AI coding provider

### Changed

- Refactor Z.AI provider implementation into shared internal function
- Modify CLI initialization to include Z.AI Coding as provider option
- Update documentation and contributing guides to reflect direct SDK integration approach over aisuite

### Removed

- Obsolete aisuite mypy configuration
- Implementation plan document (plan.md)
- Deprecated KITTYLOG_ZAI_USE_CODING_PLAN environment variable option

## [1.1.0] - 2025-10-03

### Added

- Add Z.AI as a new supported AI provider with coding plan API endpoint support
- Include comprehensive test coverage for new Z.AI provider functionality
- Add Z.AI-specific environment configuration options including API key and coding plan toggle

### Changed

- Update supported providers list to include Z.AI in AI utilities
- Apply code formatting improvements using ruff across prompt and provider modules
- Enhance error handling for Z.AI API responses with null/empty content validation

## [1.0.2] - 2025-10-01

### Added

- Add OpenRouter provider support with dedicated API integration
- Add Z.AI provider support with dedicated API client implementation
- Add new dependencies: bracex, pydantic-settings, rich-click, tomlkit, wcmatch
- Add ZAI_API_KEY and OPENROUTER_API_KEY to environment variable configuration loading

### Changed

- Update default temperature value from 0.7 to 1.0 in tests and configuration
- Adjust provider key normalization in CLI initialization to handle dot characters
- Replace bumpversion dependency with bump-my-version
- Upgrade httpx dependency to version 0.28.1

### Removed

- Remove bumpversion dependency in favor of bump-my-version

## [1.0.1] - 2025-09-29

### Changed

- Improve changelog generation with stricter content rules and anti-redundancy measures
- Update system prompt to enforce precise formatting and single-mention policy for changes
- Modify OpenAI API temperature handling and increase default temperature for flexibility
- Allow optional tag parameter in changelog prompt building function

## [1.0.0] - 2025-09-28

### Added

- Support for Cerebras provider integration with existing modular approach

### Changed

- Refactor AI provider integrations into separate modules for improved organization and extensibility
- Replace bumpversion with bump-my-version for version management with enhanced tagging and safety checks
- Update dependencies to enforce specific versions for greater compatibility

### Removed

- Eliminate monolithic ai_providers.py in favor of individual provider modules
- Remove unused code formatting dependencies: black and isort

### Fixed

- No bug fixes implemented in this release

### Security

- No security vulnerabilities addressed in this release

## [0.6.0] - 2025-09-27

### Added

- Introduce confirmation prompts before AI changelog generation to prevent accidental API calls
- Add `--yes` flag to automatically bypass all confirmation prompts for scripting/automation

### Changed

- Replace `bump-my-version` with the original `bumpversion` tool due to reliability issues

### Fixed

- Resolve AttributeError bug with `bump-my-version` that caused failures in version bumping process

### Security

- Ensure version management tool is secure and maintained by switching to a reliable alternative

## [0.5.1] - 2025-09-25

### Added

- Support for flexible changelog grouping modes: tags, dates, and gaps, enabling users to customize how commits are organized.

### Changed

- Update CLI to include new options for grouping modes, gap thresholds, and date-based grouping, improving usability and configurability.

### Fixed

- Resolve critical boundary filtering bug in the `kittylog add` command that caused all boundaries to be reprocessed instead of only missing ones due to a prefix mismatch.

### Security

- No security vulnerabilities were identified or addressed in this release.

## [0.4.0] - 2025-09-24

### Added

- Add multi-provider AI support for changelog generation, including Anthropic, OpenAI, Groq, Cerebras, and Ollama
- Implement environment variable loading from `.kittylog.env` files with a clear precedence hierarchy
- Introduce retry logic and utility functions for robust AI provider API interactions
- Add new integration tests for actual provider API calls (excluded by default in CI)

### Changed

- Replace `aisuite` dependency with direct HTTP-based API calls to AI providers for better control and lower overhead
- Refactor AI module to use `httpx.post` calls and provider-specific configurations while maintaining backward compatibility
- Update project documentation (`AGENTS.md`) with comprehensive usage examples, project structure, and AI integration details
- Streamline changelog header generation logic in `changelog.py`
- Improve error classification and handling for different AI provider error types
- Update installation instructions to prioritize `uv/uvx` over `pipx` in documentation and README

### Fixed

- Remove outdated and redundant documentation sections to avoid confusion
- Exclude agent-specific files and directories from git tracking while retaining user-facing documentation like `AGENTS.md`

## [0.3.3] - 2025-09-22

### Added

- Add intelligent handling of the "Unreleased" changelog section that automatically replaces existing content with newly generated entries
- Implement token usage tracking for AI operations, returning statistics for prompt, completion, and total tokens consumed during changelog generation

### Changed

- Rename project references from "changelog-updater" to "kittylog" across the entire codebase, including CLI output, error classes, and documentation
- Refactor README installation and usage sections for improved clarity and streamlined presentation
- Simplify CI workflow by removing unnecessary paths-ignore configuration for push triggers, ensuring consistent quality checks on all pushes
- Improve changelog generation logic with better section boundary detection and content insertion
- Enhance error handling and validation in changelog processing operations
- Update Makefile commands and help text to reflect the new kittylog naming convention

### Removed

- Remove redundant CLI commands and streamline the changelog update workflow
- Eliminate extensive paths-ignore list from CI push triggers for simpler workflow logic

## [0.3.2] - 2025-09-22

### Added

- Add `--no-unreleased` flag to skip creation or removal of Unreleased sections in changelog updates
- Introduce visual usage diagram in documentation to illustrate kittylog workflow and module interaction

### Changed

- Modify `update_changelog` function to accept a `no_unreleased` parameter for conditional section handling
- Adjust CLI commands (`add`, `update_compat`, `unreleased`) to support the new `--no-unreleased` flag
- Improve formatting logic to conditionally remove Unreleased sections when `no_unreleased` is enabled
- Update internal content filtering to prevent duplicate Unreleased headers during entry generation

### Fixed

- Fix excessive blank line cleanup in changelog formatting to ensure proper spacing
- Resolve issue where empty Unreleased sections were not consistently removed during processing

## [0.3.1] - 2025-09-22

### Changed

- Replace "AI-Powered" terminology with "LLM-Powered" for greater technical accuracy in changelog feature description
- Remove redundant pull request creation example from documentation to avoid duplication
- Reorder and update README badges to improve project visibility and visual hierarchy

### Fixed

- Update badge links and formatting in README to ensure proper display and functionality

## [0.3.0] - 2025-09-22

### Added

- Add GitHub Actions workflows for continuous integration and automated PyPI publishing
- Introduce Codecov configuration with project and patch coverage settings

### Changed

- Rename project from `clog` to `kittylog`, including all module references, environment variables, and configuration files
- Update AI model references in tests from `anthropic:claude-3-5-haiku-latest` to `cerebras:qwen-3-coder-480b`
- Improve readability by reformatting test function parameter lists and method signatures
- Modify CI workflow to exclude documentation, example, and metadata files from triggering builds

### Fixed

- Correct environment variable name in error messages from `CHANGELOG_UPDATER_MODEL` to `KITTYLOG_MODEL`

## [0.2.3] - 2025-09-22

### Added

- Implement unified output interface with new `OutputManager` class for consistent messaging across the application
- Add standardized methods for info, success, warning, error, and debug messages
- Introduce global output management supporting quiet and verbose modes

### Changed

- Replace direct Rich console usage with the new unified output interface throughout the codebase
- Update CLI and error handling modules to use centralized output management
- Improve output consistency and overall maintainability of user-facing messages

## [0.2.2] - 2025-09-22

### Added

- Add caching for git operations (`get_repo`, `get_all_tags`, `get_current_commit_hash`) to improve performance
- Expand changelog file discovery to include the `docs/` directory with proper priority ordering
- Introduce reusable CLI option decorators (`workflow_options`, `changelog_options`, `model_options`, `logging_options`) to reduce duplication
- Add `common_options` decorator that combines all shared options for consistent command interfaces
- Implement standardized environment variable validation using a new `validate_env_var` function
- Add `setup_command_logging` function to unify verbosity and logging level handling across CLI commands

### Changed

- Remove `--replace-unreleased` and `--no-replace-unreleased` flags, now always replace unreleased section content
- Update configuration loading to use stricter and more consistent validation logic
- Modify internal CLI structure to use shared decorators, improving maintainability and consistency
- Improve changelog generation behavior to automatically remove unreleased section when commit is tagged and up-to-date
- Skip creating unreleased section when no unreleased commits are present
- Refactor utility imports and file discovery logic for better modularity and clarity

### Fixed

- Fix potential test interference by adding cleanup of generated `CHANGES.md` files after CLI update tests
- Prevent state contamination between tests by clearing git operation caches in test fixtures

## [0.2.1] - 2025-09-22

### Changed

- Remove deprecated `--preserve-existing` CLI option from all commands
- Refactor core changelog processing logic into modular handler functions for unreleased, auto, single tag, and tag range workflows
- Simplify `main_business_logic()` function from 288 to 106 lines to improve maintainability
- Reorganize codebase architecture to route changelog operations through specialized workflow handlers
- Update documentation to reflect removal of `--preserve-existing` flag and new modular structure

### Fixed

- Improve code quality and reduce complexity in changelog update functions
- Eliminate outdated backward compatibility code for deprecated CLI options
- Maintain full test coverage with all 216 tests passing after refactoring
- Fix broken internal links in project documentation
- Resolve inconsistent command option listings across usage guides

## [0.2.0] - 2025-09-22

### Added

- Add auto-detection of changelog files with preferred filenames (CHANGELOG.md, changelog.md, CHANGES.md, changes.md)
- Add exclusion patterns for changelog file variants to prevent duplication in git diff operations
- Introduce new comprehensive documentation files: USAGE.md for command-line usage and AGENTS.md for AI agent architecture

### Changed

- Replace black and isort with ruff format for code formatting and linting
- Reorganize README.md to reference new dedicated documentation files instead of inline technical details
- Simplify configuration interface by removing backward compatibility for deprecated CHANGELOG*UPDATER*\* environment variables
- Update development workflow with new make commands for testing and code quality assurance

### Removed

- Remove support for legacy CHANGELOG*UPDATER*\* environment variable prefixes
- Remove detailed command-line options and AI architecture sections from README.md

### Fixed

- Fix test patch decorators to correctly mock get_tags_since_last_changelog from the git_operations module

## [0.1.10] - 2025-09-22

### Changed

- Improve type safety in changelog processing by adding explicit type annotations and ensuring boolean consistency
- Remove redundant exception handling in git operations to prevent masking of underlying errors
- Reformat codebase and reorganize imports for better readability and maintainability
- Remove outdated implementation status documentation and placeholder changelog file

### Fixed

- Resolve test isolation issues causing order-dependent failures
- Fix AI mocking conflicts in test fixtures to ensure proper override behavior
- Correct git repository context handling in tests for more reliable operations
- Address file path and repository detection problems in the test suite

## [0.1.9] - 2025-09-22

### Fixed

- Resolve test isolation issues causing failures when tests were run in specific orders
- Fix AI mocking conflicts in test fixtures to ensure test-specific responses override global mocks
- Correct git repository context problems in multiple test cases to enable proper git operations
- Address and resolve all remaining test failures related to file path handling and repository detection
- Update test fixtures to properly include unreleased commits and improve test reliability
- Verify and document that all 216 tests now pass consistently in the test suite

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

- Add `kittylog init-changelog` command to automatically create and initialize missing changelog files with proper Keep a Changelog structure
- Introduce `kittylog update ` command for generating changelog entries for specific versions
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
- Refactor init_cli to use a constant path for .kittylog.env, enabling easier monkeypatching during tests
- Enhance commit display formatting in utils with smarter truncation logic

### Fixed

- Improve test stability by ensuring valid working directory context during git operations
- Fix indentation error in TestErrorHandlingIntegration test case
- Remove unused preview functionality from main business logic
- Ensure proper directory handling and cleanup in integration tests for better isolation

