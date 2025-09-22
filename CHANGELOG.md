# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Add support for automatically tracking and including 'Unreleased' changes in the changelog when the current commit is not tagged
- Introduce `--replace-unreleased` CLI option to replace existing unreleased content instead of appending to it
- Document AI agent integration and configuration, including supported providers (Anthropic, OpenAI, Groq, Ollama, Cerebras)
- Add contribution guidelines with instructions for AI provider integration and code quality standards
- Implement automated semantic versioning using bumpversion configuration
### Changed
- Improve changelog formatting by removing empty sections and excessive newlines
- Refactor core logic to seamlessly handle both tagged releases and unreleased changes
- Replace manual commit categorization with LLM-driven analysis for more accurate and flexible changelog generation
- Enhance console output to clearly indicate when unreleased changes are being processed
- Update integration tests to ensure proper git working directory context and cleanup
- Rename main Click group function from `main` to `cli` for improved clarity
### Fixed
- Resolve issue where unreleased sections were duplicated instead of properly merged
- Fix type handling issues that occurred when None values were passed to functions expecting non-nullable types
- Correct logic for extracting and merging AI-generated changelog entries to prevent duplicate headers
- Improve test stability related to git working directory context and global configuration interference
- Ensure trailing newlines are properly cleaned up to maintain consistent formatting
- Handle git tag detection and changelog generation more robustly when tags are not present
### Removed
- Remove unused preview functionality
- Remove redundant test setup steps


## [0.1.1] - 2222-09-20

### Added

- Something

## [0.1.0] - 2025-01-01

### Added

- Something else
