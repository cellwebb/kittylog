# Changelog

## [3.0.4] - 2025-12-06

### What's New

- AI now tracks your current session to avoid duplicate entries
- Increased AI context to include your last 10 log entries for better analysis

### Improvements

- More consistent spacing between version sections in changelogs
- Better rules to prevent announcing features that already exist

### Bug Fixes

- Fixed inconsistent spacing in changelog formatting

## [3.0.3] - 2025-12-06

### What's New

- More audience options for creating changelogs
- Changelogs now have better spacing between version sections

### Improvements

- Audience-specific section headers now appear automatically
- More consistent formatting for changelogs
- Better handling of changelog entries when adding new versions

## [3.0.2] - 2025-12-06

### What's New

- New tools for managing version sections in your changelogs
- Better control over bullet point limits in different sections

### Improvements

- Changelog processing is now more organized and efficient
- Improved reliability when identifying where to add new entries

## [3.0.1] - 2025-12-06

### Improvements

- Better organization for generating content tailored to different audiences
- Added controls to manage content length and detail
- Improved guidance to prevent repeating information from previous updates

## [3.0.0] - 2025-12-06

### What's New

- Simplified update command now handles both adding and updating entries

### Improvements

- Improved help text and command structure for easier use

### Bug Fixes

- Removed confusing duplicate commands that caused friction

## [2.11.0] - 2025-12-06

### What's New

- Improved changelog generation to avoid repeating features from previous versions

### Improvements

- Better handling of changelog context to prevent duplicate announcements

### Bug Fixes

- Fixed default audience setting for better targeting

## [2.10.3] - 2025-12-06

### What's New

- AI now includes your last 5 log entries for better context by default

## [2.10.2] - 2025-12-06

### What's New

- Added better tracking for changelog entries with unique identifiers

### Improvements

- Changelog entries now appear in correct chronological order
- Better progress saving when updating changelogs

### Bug Fixes

- Fixed incorrect ordering of entries in changelog generation

## [2.10.1] - 2025-12-06

### Improvements

- Better handling of missing entries with improved insertion order
- Improved chronological ordering for changelog entries
- Updated usage screenshots for better visual clarity

## [2.10.0] - 2025-12-06

### What's New

- Added colorful rainbow banner on startup
- Generate changelogs in different languages and for different audiences

### Improvements

- Changelogs now have consistent spacing between versions
- Simplified commands by removing confirmation prompts

### Bug Fixes

- Fixed banner display formatting issues

## [2.9.2] - 2025-12-06

### Bug Fixes

- Fixed incorrect commit grouping in update history

## [2.9.1] - 2025-12-06

### Improvements

- Better testing coverage for different modes and date handling
- Improved reliability of version and boundary operations

## [2.9.0] - 2025-12-06

### Improvements

- More reliable sign-in for local providers
- Smoother configuration setup
- Better error messages when something goes wrong

## [2.8.2] - 2025-12-05

### Improvements

- Improved changelog generation for cleaner and more consistent output

### Bug Fixes

- Fixed formatting issues in generated changelogs

## [2.8.1] - 2025-12-05

### Improvements

- Simplified command options for easier use

## [2.8.0] - 2025-12-05

### Improvements

- Better type safety and error prevention
- Cleaner internal code structure for easier maintenance

## [2.7.0] - 2025-12-05

### What's New

- New --detail option lets you choose output length (concise, normal, or detailed)
- Control how much detail you see in your changelogs with preset verbosity levels

### Improvements

- Better enforcement of output length limits to keep changelogs focused
- System prompts now adapt to your chosen detail level automatically

## [2.6.0] - 2025-12-05

### What's New

- Generate content tailored for different audiences: developers, users, or stakeholders

### Improvements

- Better explanations for non-technical users
- More business-focused summaries for stakeholders

## [2.5.2] - 2025-12-05

### Improvements

- Better error handling and more helpful error messages
- Improved boundary handling for missing entries mode
- Enhanced test reliability and isolation
- Cleaned up changelog headers for easier reading
- Removed unused dependencies for cleaner installation

### Bug Fixes

- Fixed crashes related to boundary key access
- Resolved test failures in dry run mode

## [2.5.1] - 2025-12-05

### What's New

- Added support for new boundary modes when finding missing entries, including tags, dates, and gaps

### Bug Fixes

- Fixed an issue where grouping mode was being ignored when checking for missing entries

## [2.5.0] - 2025-12-05

### What's New

- Incremental save feature that updates your changelog as you work instead of waiting until the end
- New workflow option to save changes progressively during entry generation

### Improvements

- Better progress tracking when generating multiple changelog entries
- Improved reliability when changelog files are missing

## [2.4.2] - 2025-12-05

### Improvements

- Better performance and reliability
- More consistent error messages
- Faster app startup

### Bug Fixes

- Fixed authentication issues with Qwen provider
- Improved error handling across all services

## [2.4.1] - 2025-12-04

### Improvements

- Security and stability improvements
- Improved error message formatting

## [2.4.0] - 2025-12-04

### What's New

- New Qwen AI provider with easy sign-in options
- Secure token storage for authentication

### Improvements

- Enhanced error handling with better messages
- Automatic version style matching for changelogs
- Improved debugging with detailed logging information

### Bug Fixes

- Fixed version formatting inconsistencies in changelogs

## [2.3.4] - 2025-12-04

### Improvements

- Improved version formatting consistency across the app
- Better handling of various version tag formats

### Bug Fixes

- Fixed issue causing incorrect reprocessing of changelog entries

## [2.3.3] - 2025-12-04

### Improvements

- Improved how new updates are added to the changelog for better organization

## [2.3.2] - 2025-12-04

### What's New

- Generate changelogs for unreleased changes between tags

### Improvements

- Updated to latest AI models for better processing
- Improved tag recognition and version ordering

### Bug Fixes

- Fixed issues with version tag comparison

## [2.3.1] - 2025-12-04

### What's New

- Updated to use the latest AI models for better performance
- Switched to processing entries in chronological order for smarter results

### Improvements

- Better AI context understanding when analyzing your logs
- Updated documentation to show current supported model versions

## [2.3.0] - 2025-12-04

### What's New

- New release command to automate changelog preparation
- Style reference option to match existing changelog entries

### Improvements

- Better error messages when things go wrong
- App responds faster to repeated actions
- Improved sign-in reliability

### Bug Fixes

- Fixed crash when saving files
- Fixed occasional freezing issue
- Fixed crash when saving large files

## [2.2.0] - 2025-12-03

### What's New

- Set up project-specific settings with .kittylog.env files
- Use arrow keys for faster navigation in menus

### Improvements

- Better support for international characters and non-English systems
- View configuration settings with sensitive information automatically hidden

## [2.1.0] - 2025-12-03

### What's New

- New standalone 'kittylog auth' command for easier sign-in
- New 'kittylog model' command to configure AI providers
- Standalone 'kittylog language' command for language settings

### Improvements

- Better security for your API keys and tokens
- Simplified setup process with clearer steps
- More informative error messages when things go wrong

### Bug Fixes

- Fixed crashes from unexpected API responses
- Fixed environment pollution from token storage
- Removed duplicate functions that could cause inconsistencies

## [2.0.0] - 2025-12-02

### What's New

- Added support for Claude Code OAuth authentication
- New AI providers: Azure OpenAI, Kimi Coding, Moonshot AI, and Replicate
- Python 3.14 support added for future compatibility

### Improvements

- Better error messages and handling across all providers
- Improved configuration system with validation and security
- App now runs faster with centralized cache management
- More reliable token counting with better fallback estimation

### Bug Fixes

- Fixed changelog parser issues with unreleased sections
- Fixed crash when saving files with proper error handling
- Fixed token counting to prevent complete masking failures
- Resolved circular import issues that could cause instability

## [1.6.0] - 2025-11-01

### What's New

- Choose your changelog audience - developers, end users, or stakeholders
- Customizable tone to match your target readers

### Improvements

- Interactive guides help select the right audience
- Better instructions when setting up changelogs

## [1.5.0] - 2025-11-01

### What's New

- Generate changelogs in 30+ different languages
- Quick start guide and improved documentation for easier onboarding

### Improvements

- Better visual design and organization in README
- Enhanced configuration options for language and audience settings

## [1.4.0] - 2025-10-31

### What's New

- Interactive guided setup makes configuration easier
- Automatically calculates the right version number for your updates

### Improvements

- Better changelog formatting for entries with dates
- More reliable handling of settings throughout the app

### Bug Fixes

- Fixed crashes that happened during setup
- Resolved issues with passing information between different parts of the app

## [1.3.0] - 2025-10-31

### What's New

- Connect with 11 new AI providers including DeepSeek, Gemini, Mistral, and others
- Support for custom Anthropic and OpenAI compatible endpoints
- Interactive setup process makes it easier to configure new AI providers

### Improvements

- Better handling of local AI providers like LM Studio
- Improved error messages when setting up AI connections

## [1.2.0] - 2025-10-04

### What's New

- Added Z.AI Coding provider option for dedicated coding plans

### Improvements

- Simplified provider selection by removing environment variable toggle

## [1.1.0] - 2025-10-03

### What's New

- New AI provider option: Z.AI with coding plan support
- Optional coding mode selection when setting up Z.AI

### Improvements

- Better error messages when Z.AI responses fail
- Expanded test coverage for more reliable performance

## [1.0.2] - 2025-10-01

### What's New

- New AI providers available: OpenRouter and Z.AI
- Expanded AI options for your workflow

### Improvements

- Better HTTP handling and connectivity
- Updated tool dependencies for improved stability

## [1.0.1] - 2025-09-29

### What's New

- Improved changelog generation with stricter content rules

### Improvements

- Better system prompt structure and clarity
- More flexible prompt generation with adjusted settings

## [1.0.0] - 2025-09-28

### What's New

- Added support for Cerebras AI provider

### Improvements

- Better performance and reliability
- Security and stability improvements

## [0.6.0] - 2025-09-27

### What's New

- Added confirmation prompts before generating AI changelogs to prevent accidental API calls
- New --yes flag to automatically skip all prompts for easy automation

### Improvements

- Changelog entries are now automatically placed in the correct version order
- Better handling of version numbers with prefixes and special identifiers

## [0.5.1] - 2025-09-25

### Bug Fixes

- Fixed a bug that caused all version boundaries to be reprocessed unnecessarily

## [0.4.0] - 2025-09-24

### What's New

- Now supports multiple AI providers (OpenAI, Anthropic, Groq, Cerebras, Ollama) for generating changelogs

### Improvements

- Better error handling and retry logic for AI requests
- Simplified changelog header formatting
- Updated documentation with clearer usage examples

## [0.3.3] - 2025-09-22

### What's New

- Track token usage during changelog generation
- Automatic bullet point limiting keeps changelogs concise

### Improvements

- Simplified installation and usage documentation
- Better error handling and validation for changelog operations

## [0.3.2] - 2025-09-22

### What's New

- New option to skip unreleased sections in changelogs
- Added usage diagram to help understand how the tool works

### Improvements

- Better formatting when managing changelog sections
- Cleaner handling of empty sections in documentation

### Bug Fixes

- Fixed issues with blank line cleanup in changelog files

## [0.3.1] - 2025-09-22

### Improvements

- Security and stability improvements with updated core components
- Simplified version updates in changelog management
- More accurate terminology throughout documentation

### Bug Fixes

- Fixed inconsistency when updating existing changelog versions

## [0.3.0] - 2025-09-22

### What's New

- Project renamed from clog to kittylog
- Automated publishing to PyPI for tagged releases

### Improvements

- Better error messages for configuration issues
- Enhanced test coverage across multiple Python versions

### Bug Fixes

- Fixed incorrect environment variable name in error messages

## [0.2.3] - 2025-09-22

### What's New

- Unified output interface for consistent messaging
- Global quiet/verbose mode support

### Improvements

- Better output consistency across the app
- Improved changelog formatting and clarity

## [0.2.2] - 2025-09-22

### What's New

- App now automatically finds your changelog file in more places
- Unreleased entries are now handled more intelligently without extra settings

### Improvements

- App runs faster by remembering git information during use
- Simplified command options for a cleaner experience
- Better environment setup and configuration reliability

### Bug Fixes

- Fixed duplicate entries in unreleased sections
- No more leftover files after running commands

## [0.2.1] - 2025-09-22

### Improvements

- Removed outdated command line options to simplify usage
- Better organization makes the app run more smoothly

## [0.2.0] - 2025-09-22

### What's New

- Automatically finds your changelog file in common locations
- New documentation files for easier usage and AI agent setup

### Improvements

- Simplified configuration with consistent settings
- Better test coverage and development tools

## [0.1.10] - 2025-09-22

### Improvements

- Improved reliability of changelog processing
- Better error handling for git operations

### Bug Fixes

- Fixed test failures that were dependent on execution order
- Resolved conflicts with AI mocking in test fixtures

## [0.1.9] - 2025-09-22

### Bug Fixes

- Fixed issues with changelog generation from git repositories
- Improved reliability when processing file paths

## [0.1.8] - 2025-09-22

### What's New

- New command to generate changelog entries from specific tag ranges
- New option to update all missing or all changelog entries at once

### Improvements

- Changelog files are now automatically excluded from change analysis for better accuracy
- Improved formatting and consistency in changelog entries

### Bug Fixes

- Fixed duplicate sections and formatting errors in changelog
- Fixed conflicting options when processing unreleased changes

## [0.1.7] - 2025-09-21

### What's New

- Automatically creates 'Unreleased' sections for changelogs
- AI-powered changelog generation with strict formatting rules

### Improvements

- Better handling of tagged and untagged commits in changelogs
- Cleaner changelog output by removing duplicates and empty sections

### Bug Fixes

- Fixed issues with None values when processing git tags
- Resolved problems with duplicate headers in changelogs

## [0.1.6] - 2025-09-21

### What's New

- Changelog generation now works better with tagged releases
- Improved formatting and structure for automatically generated changelogs

### Improvements

- Cleaner changelog content with automatic duplicate removal
- Better handling of unreleased changes in changelogs

### Bug Fixes

- Fixed spacing issues around changelog section headers
- Removed empty sections and extra blank lines from changelogs

## [0.1.5] - 2025-09-21

### What's New

- Create new changelog files with 'clog init-changelog' command
- Generate changelog entries for specific versions with 'clog update <version>' command

### Improvements

- AI-generated changelogs now have better formatting and fewer errors
- Changelog entries are automatically cleaned up to remove duplicates and empty sections

### Bug Fixes

- Fixed issues with version tag processing
- Fixed crashes when handling empty or missing changelog content

## [0.1.4] - 2025-09-21

### What's New

- Generate changelog entries for specific tags automatically
- New command to handle unreleased changes separately
- Automatically detect and fill in missing changelog entries

### Improvements

- Better handling of large content during generation
- Improved consistency in changelog formatting

## [0.1.3] - 2025-09-21

### What's New

- Track unreleased changes automatically
- Limit changelog sections to 6 items to focus on what's important

### Improvements

- Unreleased content now replaces instead of adding duplicates
- Better changelog formatting with cleaner spacing
- More reliable processing of existing changelog content

### Bug Fixes

- Fixed duplicate entries when updating unreleased section
- Fixed formatting issues when merging changelog content

## [0.1.1] - 2025-09-20

### What's New

- Automated version management for releases

### Improvements

- Enhanced changelog generation with better tag handling
- Improved test stability and coverage for multi-tag processing

### Bug Fixes

- Fixed issues with directory handling during git operations
- Improved error handling and input validation

## [0.1.0] - 2025-09-20

### What's New

- AI-powered changelog generation that automatically creates release notes from your project history
- Support for multiple AI providers including OpenAI, Anthropic, and others
- Interactive setup tool to quickly configure your changelog preferences

### Improvements

- Smart detection of new changes since your last update
- Preview mode to see changelog before finalizing
- Better error handling with helpful messages when things go wrong
