# Changelog

## [3.0.7] - 2025-12-09

### What's New

- Include git diff context for more accurate changelog generation
- New Mistral model devstral-2512 now available

### Improvements

- Enhanced boundary detection with better parsing and classification
- More reliable tests with improved directory and configuration handling

### Bug Fixes

- Fixed test reliability issues across multiple test suites
- Resolved provider integration test failures with proper mocking

## [3.0.6] - 2025-12-07

### Improvements

- Enhanced test coverage for more reliable operation across all features
- Better tag handling with caching and improved error detection
- More comprehensive testing for authentication and configuration workflows
- Improved code formatting and build configuration for better maintenance

## [3.0.5] - 2025-12-06

### Improvements

- Better changelog generation with clearer rules to prevent duplicate announcements
- Improved instructions help AI distinguish between new features and existing functionality improvements

## [3.0.4] - 2025-12-06

### Improvements

- AI now remembers more context from previous changelog entries to avoid duplicates
- Better changelog formatting with consistent spacing between versions
- Cleaner documentation and formatting across all guides
- Smart session tracking prevents re-announcing the same features

### Bug Fixes

- Fixed duplicate entries appearing when processing multiple versions

## [3.0.3] - 2025-12-06

### What's New

- Generate changelogs tailored to different audiences - developers, users, or business stakeholders
- Smart prompts automatically adjust language based on who will read the changelog

### Improvements

- Changelog formatting now maintains consistent spacing between versions
- Better handling of audience-specific section names and headers
- Cleaner internal code organization for better reliability

### Bug Fixes

- Fixed crashes when saving files
- Resolved issues with audience parameter handling in changelog generation

## [3.0.2] - 2025-12-06

### Improvements

- Better changelog organization with dedicated modules for different tasks
- More reliable changelog generation with improved structure
- Cleaner internal code organization for better reliability

## [3.0.1] - 2025-12-06

### Improvements

- Better changelog generation with organized system for different audiences
- Enhanced prompt structure prevents re-announcing existing features
- Cleaner code organization with modular system for better reliability

## [3.0.0] - 2025-12-06

### Improvements

- Simplified commands by combining add and update into one unified command
- Cleaner code organization with redundant modules removed

## [2.11.0] - 2025-12-06

### Improvements

- Changelog generation now prevents re-announcing existing features from previous versions
- Default audience changed to developers for more technical changelogs
- Enhanced deduplication rules create cleaner, more concise changelog entries

## [2.10.3] - 2025-12-06

### Improvements

- AI now considers your last 5 changelog entries for better context

## [2.10.2] - 2025-12-06

### Improvements

- Changelog entries now maintain proper chronological order when inserted
- Incremental save option automatically updates changelog as you work
- Better handling of missing changelog entries with new boundary mode support

### Bug Fixes

- Fixed issue where grouping mode was ignored in missing entries
- Fixed crashes when saving files with proper error handling

## [2.10.1] - 2025-12-06

### Improvements

- Better handling of missing changelog entries with improved insertion logic
- Changelog entries now maintain proper chronological order when inserted
- Updated documentation screenshot with improved visual clarity

## [2.10.0] - 2025-12-06

### What's New

- Generate changelogs in different languages for your audience
- Colorful ASCII art banner now appears on startup

### Improvements

- Simplified workflow by removing confirmation prompts
- Changelog formatting now maintains consistent spacing between versions

### Bug Fixes

- Fixed crashes when saving files

## [2.9.2] - 2025-12-06

### Improvements

- Better commit range calculation for more accurate changelog entries

### Bug Fixes

- Fixed incorrect commit grouping when processing multiple versions

## [2.9.1] - 2025-12-06

### Improvements

- Enhanced test reliability with better mocking for all operation modes

## [2.9.0] - 2025-12-06

### Improvements

- Enhanced provider architecture for more reliable AI service connections
- Better support for local AI providers like LM Studio and Ollama
- Simplified configuration system with automatic API key detection
- Cleaner internal code organization for better stability

### Bug Fixes

- Fixed test issues for more reliable operation
- Corrected command references in integration tests

## [2.8.2] - 2025-12-05

### Improvements

- Cleaner changelog formatting by removing version headers from AI-generated content
- Simplified AI instructions for more consistent and reliable changelog generation

### Bug Fixes

- Fixed issue with placeholder version headers appearing in changelogs

## [2.8.1] - 2025-12-05

### Improvements

- Cleaner internal code organization for better reliability
- Removed outdated planning documentation

## [2.8.0] - 2025-12-05

### Improvements

- Better type safety and reliability across the app
- Streamlined CLI command processing for more consistent behavior

## [2.7.0] - 2025-12-05

### What's New

- New --detail option lets you control how detailed your changelog entries are

### Improvements

- AI now respects strict bullet limits to keep changelogs concise
- Better control over output verbosity with three detail presets: concise, normal, or detailed

## [2.6.0] - 2025-12-05

### Improvements

- Generate changelogs tailored to different audiences - developers, users, or business stakeholders
- Smart prompts automatically adjust language based on who will read the changelog

## [2.5.2] - 2025-12-05

### Improvements

- Fixed crashes when saving files with proper error handling
- Better handling of missing changelog entries with improved boundary mode
- Improved test reliability and isolation across all scenarios
- Removed unused dependencies for cleaner installation
- Enhanced AI error handling to protect against unexpected crashes
- Better configuration loading with improved performance
- Cleaner changelog formatting without redundant version references

### Bug Fixes

- Fixed test failures related to boundary handling and mock configurations
- Resolved KeyError issues in missing entries mode
- Fixed circular import issues in CLI modules

## [2.5.1] - 2025-12-05

### Improvements

- Better handling of missing changelog entries with new boundary mode support

### Bug Fixes

- Fixed issue where grouping mode was ignored in missing entries

## [2.5.0] - 2025-12-05

### What's New

- Incremental save option automatically updates changelog as you work

### Improvements

- Faster changelog generation with immediate saves after each entry
- Better progress tracking during multi-entry operations
- More reliable workflow with changelog file creation when needed

## [2.4.2] - 2025-12-05

### Improvements

- Better performance with on-demand AI provider initialization
- More reliable error handling across all AI services
- Streamlined provider architecture for improved stability

## [2.4.1] - 2025-12-04

### Improvements

- Cleaned up test formatting and organization for better reliability
- Updated internal imports for improved consistency and performance

## [2.4.0] - 2025-12-04

### What's New

- New Qwen AI provider with secure OAuth sign-in option

### Improvements

- Enhanced error handling for more helpful messages when things go wrong
- Better debugging with detailed logging information
- Changelog version formatting now matches your existing style automatically
- Added comprehensive testing for more reliable operation

### Bug Fixes

- Fixed version prefix handling to maintain consistent formatting

## [2.3.4] - 2025-12-04

### Improvements

- Version formatting is now consistent across all changelog entries
- Better handling of various version formats including prereleases
- Improved version recognition and boundary filtering in changelogs

## [2.3.3] - 2025-12-04

### Improvements

- Cleaner changelog formatting with consistent spacing
- Better handling of unreleased sections in changelogs

## [2.3.2] - 2025-12-04

### Improvements

- New unreleased mode for tracking changes between releases
- Better tag recognition when comparing versions
- Updated to latest AI models for improved changelog generation

## [2.3.1] - 2025-12-04

### Improvements

- Better AI-generated changelogs with improved historical context processing
- Updated to use latest AI models: gpt-5-mini, claude-haiku-4-5, and gpt-oss-20b

## [2.3.0] - 2025-12-04

### What's New

- New release command automates changelog preparation
- Style reference option helps AI generate more consistent changelogs

### Improvements

- Better support for over 18 AI providers with standardized error handling
- Cleaner configuration system with better environment variable management
- Simplified code organization for improved reliability and maintainability

### Bug Fixes

- Fixed tag recognition and changelog ordering issues
- Resolved configuration precedence problems with API key loading

## [2.2.0] - 2025-12-03

### What's New

- View configurations for both user and project levels with automatic security hiding
- Enhanced keyboard shortcuts for faster navigation in prompts

### Improvements

- Better support for international character sets and non-UTF-8 environments
- Streamlined test suite focusing on core functionality

## [2.1.0] - 2025-12-03

### Improvements

- New dedicated commands for authentication and model configuration
- More secure API key management without polluting your environment
- Better error messages when AI services respond unexpectedly
- Simplified code organization for improved reliability and maintainability

### Bug Fixes

- Fixed crashes when saving files with proper error handling
- Resolved issues with OAuth token storage consistency
- Prevented duplicate code that could cause cache inconsistencies

## [2.0.0] - 2025-12-02

### What's New

- Added support for 4 new AI providers: Azure OpenAI, Kimi Coding, Moonshot AI, and Replicate
- New Claude Code OAuth authentication for secure sign-in with automatic token refresh

### Improvements

- Major internal refactoring for better performance and reliability
- Support for Python 3.14 for future compatibility
- Better error handling with more specific and helpful messages
- Improved token counting fallback when AI models fail
- Enhanced test coverage and reliability across all features

### Bug Fixes

- Fixed changelog parser logic for proper handling of unreleased sections
- Resolved version comparison issues with v-prefix handling
- Fixed crashes when saving files with proper error chaining
- Corrected duplicate entries in changelog updates

## [1.6.0] - 2025-11-01

### What's New

- Customize changelog tone for different audiences - choose between technical details for developers, user-friendly descriptions, or business-focused summaries

### Improvements

- Interactive setup now guides you through selecting your target audience
- Audience settings can be configured through environment variables, .env files, or command line options

## [1.5.0] - 2025-11-01

### What's New

- Generate changelogs in over 30 different languages
- New interactive language selection with custom options

### Improvements

- Completely redesigned documentation with clearer structure and quick start guides
- Better visual organization with usage tables and power user recipes
- Enhanced configuration system for multilingual changelog generation

## [1.4.0] - 2025-10-31

### What's New

- Interactive configuration setup makes getting started easier
- Automatic version detection for unreleased changes

### Improvements

- Better changelog organization with automatic version headers
- Optional git diff analysis for more complete changelogs
- Smarter boundary detection for complex changelog formats

### Bug Fixes

- Fixed issues with configuration parameters not being passed correctly
- Resolved problems with nested brackets in date headings

## [1.3.0] - 2025-10-31

### What's New

- Added support for 11 new AI providers including Chutes, DeepSeek, Fireworks, Gemini, LM Studio, MiniMax, Mistral, StreamLake, Synthetic, and Together AI
- New custom Anthropic and OpenAI endpoints for connecting to your own AI services

### Improvements

- Enhanced setup with interactive configuration for new AI providers
- Added special handling for local AI providers like LM Studio and Ollama
- Updated documentation to reflect all new provider options and configuration

## [1.2.0] - 2025-10-04

### What's New

- New Z.AI Coding provider option for specialized AI models

### Improvements

- Simplified Z.AI provider configuration with dedicated coding endpoint
- Updated documentation to reflect direct provider integrations

### Bug Fixes

- Removed obsolete configuration settings for cleaner setup

## [1.1.0] - 2025-10-03

### What's New

- New AI provider Z.AI now available for changelog generation

### Improvements

- Better error handling for AI responses
- Code formatting improvements across the app
- Enhanced test coverage for more reliable operation

## [1.0.2] - 2025-10-01

### What's New

- Added support for OpenRouter as an AI provider
- Added support for Z.AI as an AI provider

### Improvements

- Updated dependencies for better performance and security
- Improved AI provider handling with normalized keys

## [1.0.1] - 2025-09-29

### Improvements

- Changelog generation now follows stricter rules to prevent duplicate entries and cleaner formatting
- Improved AI prompt structure for more consistent and accurate changelog creation
- Better handling of different AI model types with adjusted settings

## [1.0.0] - 2025-09-28

### Improvements

- Enhanced version management with automatic tagging and safety checks
- Updated to latest stable versions for better security and performance
- Streamlined code organization for improved maintainability and future updates
- Removed unnecessary formatting tools to reduce conflicts

## [0.6.0] - 2025-09-27

### What's New

- Added confirmation prompts to prevent accidental AI generation
- New --yes flag to skip prompts for automated workflows

### Improvements

- Changelog entries now maintain proper version order automatically
- Smarter version handling with support for complex version formats

### Bug Fixes

- Fixed version update tool that was causing errors

## [0.5.1] - 2025-09-25

### Improvements

- Better reliability with timezone handling and boundary detection
- Cleaner code organization and improved type checking
- More robust testing to prevent future issues

### Bug Fixes

- Fixed critical bug where all versions were reprocessed instead of just missing ones

## [0.4.0] - 2025-09-24

### What's New

- New AI provider support for OpenAI, Anthropic, Groq, Cerebras, and Ollama

### Improvements

- Improved AI integration with automatic retry logic
- Enhanced configuration with .kittylog.env file support
- Updated installation instructions and usage documentation

### Bug Fixes

- Fixed environment variable name in error messages

## [0.3.3] - 2025-09-22

### What's New

- Track AI token usage during changelog generation
- Smart bullet point limiting keeps changelog entries concise

### Improvements

- Simplified README with clearer installation and usage guides
- Better handling of unreleased changelog sections
- More consistent error messages throughout the app

## [0.3.2] - 2025-09-22

### What's New

- New option to skip 'Unreleased' sections in changelogs

### Improvements

- Better changelog section handling and formatting
- Added visual usage diagram to help understand features

## [0.3.1] - 2025-09-22

### Improvements

- Changelog updates now overwrite existing entries automatically
- Added quiet mode for cleaner automated workflows
- Updated badges and documentation for better visibility

### Bug Fixes

- Fixed environment variable name in error messages
- Corrected AI model references in tests

## [0.3.0] - 2025-09-22

### Improvements

- Project renamed from clog to kittylog for better identity
- Updated to use Cerebras AI model for improved changelog generation
- Added automated testing and publishing workflows for better reliability

### Bug Fixes

- Fixed incorrect environment variable name in error messages

## [0.2.3] - 2025-09-22

### Improvements

- Cleaner changelog formatting with better section headers
- Unified messaging system for more consistent user feedback
- Better duplicate detection across different versions

## [0.2.2] - 2025-09-22

### Improvements

- App now responds faster by remembering git operations
- Simplified handling of unreleased changes
- Better discovery of your changelog file
- More consistent command options across features

### Bug Fixes

- Fixed duplicate entries in changelog updates

## [0.2.1] - 2025-09-22

### Improvements

- Improved internal organization for better reliability and maintainability
- Removed outdated options to simplify your experience

## [0.2.0] - 2025-09-22

### What's New

- Automatically finds your changelog file (CHANGELOG.md, changelog.md, etc.)

### Improvements

- Simplified configuration settings for easier setup
- Better organized documentation with dedicated usage guides

## [0.1.10] - 2025-09-22

### Improvements

- Better error handling and more reliable operations
- Cleaner and more consistent code for improved stability
- Removed outdated files to reduce confusion

### Bug Fixes

- Fixed test reliability issues and git context problems

## [0.1.9] - 2025-09-22

### Improvements

- Better test reliability with improved file handling
- Cleaned up outdated documentation

## [0.1.8] - 2025-09-22

### What's New

- New unreleased command to track pending changes between versions
- New --all flag to update all changelog entries at once

### Improvements

- Changelog files are now automatically excluded from change analysis
- Better handling of changelog sections and headers
- Cleaner changelog formatting with consistent spacing

### Bug Fixes

- Fixed conflicting flag handling in unreleased command
- Resolved test isolation issues for more reliable behavior

## [0.1.7] - 2025-09-21

### Improvements

- Changelog generation is now smarter with automatic 'Unreleased' sections
- Better formatting prevents duplicate entries and cleans up messy content
- AI-generated changelogs now follow stricter rules for cleaner output

## [0.1.6] - 2025-09-21

### What's New

- Automatic 'Unreleased' section for tracking changes between versions

### Improvements

- Cleaner changelog formatting with automatic spacing and section organization
- Smarter changelog generation that prevents duplicate entries and cleans up extra formatting
- Better AI-generated content with stricter formatting requirements and bullet point limits

### Bug Fixes

- Fixed issues when processing git tags and merging content
- Resolved problems with empty sections and misplaced headers in generated changelogs

## [0.1.5] - 2025-09-21

### What's New

- New commands to initialize and update your changelog
- Generate changelog entries for specific versions

### Improvements

- Changelog formatting is now cleaner and more consistent
- Better handling of duplicate sections and empty content
- Improved AI-generated changelog quality with automatic cleanup

### Bug Fixes

- Fixed issues when processing git tags
- Resolved problems with None values during version updates

## [0.1.4] - 2025-09-21

### What's New

- Generate changelog entries for specific tags
- New unreleased command to track pending changes

### Improvements

- Automatically finds missing git tags from changelog
- Better formatting for long changelog entries

## [0.1.3] - 2025-09-21

### What's New

- New option to preserve existing changelog content
- Track unreleased changes between versions automatically

### Improvements

- Changelog generation now replaces unreleased content by default
- Better handling when working with multiple git tags
- Cleaner changelog formatting with automatic cleanup
- Smart bullet point limiting keeps changelog entries concise

### Bug Fixes

- Fixed duplicate entries in unreleased sections
- Resolved formatting issues when updating changelog sections

## [0.1.1] - 2025-09-20

### What's New

- Better handling when working with multiple git tags
- More flexible logging setup options

### Improvements

- Improved test reliability and stability
- Enhanced changelog generation with smarter content processing
- Better directory handling during operations

### Bug Fixes

- Fixed issues when working directory becomes invalid
- Fixed indentation errors in test cases

## [0.1.0] - 2025-09-20

### What's New

- AI-powered changelog generation automatically creates release notes from git history
- Interactive setup makes configuring your preferences quick and easy
- Support for multiple AI services gives you more choices

### Improvements

- Better error messages guide you when something goes wrong
- Dry-run mode lets you preview changes before applying them
- Automatic version management keeps everything consistent

