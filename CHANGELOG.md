# Changelog

## [0.1.3] - 2025-09-21
## CHANGELOG
### v0.1.3 
#### Added
- Support for unreleased changes section in CHANGELOG
- AI agent integration documentation
#### Changed
- Improved formatting for changelog entries
- Enhanced documentation for AI agent configuration
### v0.1.2 
#### Added
- New AI providers for changelog generation
- Support for `.clog.env` configuration files
#### Changed
- Updated documentation for AI agent integration
- Improved error handling for changelog generation
### v0.1.1 
#### Added
- Initial support for changelog generation
- Documentation for AI agent configuration
#### Changed
- Improved formatting for changelog entries
- Enhanced documentation for AI agent integration

## [0.1.1] - 2025-09-20
### Changelog
### Added
- Allow `None` as log level in `setup_logging` to enable more flexible configuration
- Implement `bumpversion` for automated version management and releases
- Introduce `uv` for dependency management and reproducible builds
### Changed
- Refactor `cli` module to improve structure and readability
- Enhance `update_changelog` to support flexible file handling and improve performance
- Improve error handling and logging throughout the codebase
### Fixed
- Resolve issues with directory handling and file paths in various modules
- Fix edge cases in `update_changelog` and improve robustness
### Removed
- Deprecated code and unused functions to improve maintainability
### Notes
- This changelog entry follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.
- The changes are grouped by category to improve readability.
- The entries are concise and focused on the changes made.

## [0.1.0] - 2025-09-20
### Added
- Initial release with core functionality for changelog generation
- Support for multiple AI providers including Anthropic, OpenAI, and Cerebras
- Integration with git for automatic changelog updates
- Configuration options for customizing changelog output
- Extensive test suite for verifying functionality
### Changed
- Improved documentation for easier onboarding and usage
- Refactored codebase for better maintainability and scalability
### Removed
- None
### Fixed
- None
### Security
- Implemented secure handling of API keys and sensitive data
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Improved formatting consistency in changelog generation
- Enhanced handling of large prompts in AI-driven changelog creation
### Changed
- Updated AI model interaction to include detailed diff content for better context
- Modified error handling to prevent timeouts and improve overall stability
### Fixed
- Resolved issue with excessive blank lines in generated changelogs
- Ensured proper spacing between sections in changelog output