# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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