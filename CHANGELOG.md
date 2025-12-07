# Changelog

## [3.0.4] - 2025-12-06

### What's New

- Smart deduplication prevents repeating features from previous changelog entries

### Improvements

- Better changelog spacing with consistent single blank lines between versions
- Enhanced AI context with 10 previous changelog entries for more accurate generation

### Bug Fixes

- Fixed changelog formatting issues around version headers
- Resolved duplicate content when generating changelogs for multiple versions

## [3.0.3] - 2025-12-06

### What's New

- Generate changelogs tailored for different audiences - developers, users, or stakeholders

### Improvements

- Better changelog formatting with consistent spacing between versions
- Cleaner and more organized code structure
- Enhanced audience support with 'end_users' aliases

### Bug Fixes

- Fixed formatting issues when inserting changelog entries

## [3.0.2] - 2025-12-06

### What's New

- More reliable changelog generation with improved version boundary detection
- Better control over changelog length with automatic bullet point limits

### Improvements

- Cleaner code organization for more reliable updates
- Enhanced AI context using recent changelog entries for consistency

### Bug Fixes

- Fixed issues with changelog entry insertion and ordering

## [3.0.1] - 2025-12-06

### What's New

- Tailored changelog prompts for different audiences - developers, users, or stakeholders

### Improvements

- Better detail level control with automatic bullet limits
- Smarter changelog generation that prevents repeating features from previous versions

## [3.0.0] - 2025-12-06

### What's New

- Simplified command structure with unified update command

### Improvements

- Update command is now the default action for quicker changelog creation
- Cleaner code structure for more reliable operation

## [2.11.0] - 2025-12-06

### Improvements

- Changelogs now automatically avoid repeating features from previous versions
- Default changelog audience changed to developers for more technical updates

## [2.10.3] - 2025-12-06

### Improvements

- AI context now automatically includes the last 5 changelog entries for better consistency
- Version bumped to 2.10.3

## [2.10.2] - 2025-12-06

### Improvements

- Better changelog entry ordering keeps versions organized chronologically

### Bug Fixes

- Fixed changelog entries appearing in wrong order when grouping by dates or time gaps

## [2.10.1] - 2025-12-06

### Improvements

- Better handling of missing changelog entries with improved insertion logic
- Enhanced chronological ordering for changelog entries
- Cleaner changelog formatting with consistent date formatting

## [2.10.0] - 2025-12-06

### What's New

- Generate changelogs in different languages and styles for specific audiences
- New colorful rainbow banner on startup

### Improvements

- Cleaner changelog formatting with consistent spacing between versions
- Simplified workflow with automatic saving and no more confirmation prompts

### Bug Fixes

- Fixed issues with version section spacing in changelogs

## [2.9.2] - 2025-12-06

### Bug Fixes

- Fixed incorrect commit grouping when generating changelogs
- Fixed issue where all entries included commits from the beginning of the project

## [2.9.1] - 2025-12-06

### Improvements

- More reliable changelog generation with better test coverage
- Improved handling of tag operations and date boundaries

### Bug Fixes

- Fixed issues with missing changelog entries in certain modes

## [2.9.0] - 2025-12-06

### Improvements

- Better support for local AI providers like LM Studio and Ollama
- Simplified configuration system with automatic API key detection
- More reliable provider connections with improved error handling

### Bug Fixes

- Fixed issues with provider initialization and authentication
- Resolved boundary detection problems in changelog generation

## [2.8.2] - 2025-12-05

### Improvements

- Cleaner changelog formatting with automatic version header removal
- Simplified AI instructions for more consistent changelog generation
- Better changelog cleaning that removes placeholder version entries

## [2.8.1] - 2025-12-05

### Improvements

- Simplified CLI command structure with cleaner parameter handling
- Improved code organization for better maintainability

## [2.8.0] - 2025-12-05

### Improvements

- Improved reliability and performance with centralized CLI handling
- Better type safety throughout the application

## [2.7.0] - 2025-12-05

### What's New

- New --detail option with three levels: concise, normal, or detailed

### Improvements

- Better control over changelog length with automatic bullet limits based on detail level

## [2.6.0] - 2025-12-05

### What's New

- Generate changelogs tailored for different audiences - developers, users, or stakeholders

### Improvements

- Better changelog generation with audience-specific prompts and language

## [2.5.2] - 2025-12-05

### Improvements

- Better error handling for AI requests with specific exception types
- Improved test reliability with better mock configurations
- Cleaner changelog formatting with simplified header text
- Enhanced type safety for better development support

### Bug Fixes

- Fixed issues with missing entries mode and boundary handling
- Resolved test failures across different scenarios
- Fixed problems with environment file loading in tests

## [2.5.1] - 2025-12-05

### Bug Fixes

- Fixed missing changelog entries when using grouping modes
- Resolved boundary detection issues for better changelog generation

## [2.5.0] - 2025-12-05

### What's New

- Incremental save feature updates your changelog as you work instead of all at once

### Improvements

- Better progress tracking during changelog updates
- More reliable changelog creation that won't fail if files are missing

## [2.4.2] - 2025-12-05

### Improvements

- More reliable AI provider connections with better error handling
- Simplified provider configuration with standardized setup
- Improved stability when switching between AI providers
- Better error messages when authentication fails

### Bug Fixes

- Fixed Qwen authentication to use modern OAuth flow
- Resolved issues with provider initialization on startup

## [2.4.1] - 2025-12-04

### Improvements

- Cleaner test formatting and better import organization
- More consistent logging with updated import statements

## [2.4.0] - 2025-12-04

### What's New

- New Qwen AI provider with OAuth and API key support
- OAuth device flow for secure Qwen authentication
- New Qwen authentication commands in CLI

### Improvements

- Structured logging with better debugging information
- Enhanced version formatting to match your changelog style
- Improved test reliability with simplified mocking tools

### Bug Fixes

- Fixed version prefix stripping and import order issues
- Corrected test configuration by removing trailing comments

## [2.3.4] - 2025-12-04

### Improvements

- Version numbers now display consistently without 'v' prefix
- Better handling of version formats including prereleases and semantic versions
- More reliable changelog processing with improved version recognition

### Bug Fixes

- Fixed boundary filtering that was causing incorrect reprocessing
- Resolved tag recognition issues for better version comparison
- Fixed changelog ordering to process tags correctly

## [2.3.3] - 2025-12-04

### Improvements

- Better handling of unreleased sections in changelogs
- Cleaner changelog formatting with consistent spacing

### Bug Fixes

- Fixed unreleased section insertion logic

## [2.3.2] - 2025-12-04

### What's New

- Generate changelogs for unreleased changes between tags
- Better release workflow with incremental commit processing

### Improvements

- Updated to latest AI models for better performance
- Improved changelog generation with historical context
- Enhanced version recognition with semantic ordering

### Bug Fixes

- Fixed tag recognition issues by normalizing version prefixes
- Fixed changelog ordering to process tags correctly

## [2.3.1] - 2025-12-04

### Improvements

- Updated to use the latest AI models for better performance
- Improved changelog generation with better historical context
- Documentation updated with current model examples

## [2.3.0] - 2025-12-04

### What's New

- New context entries feature for consistent changelog style
- New release command to automate changelog preparation

### Improvements

- Better configuration management with simplified API key handling
- Improved changelog ordering and version recognition
- More reliable provider system with standardized error handling

### Bug Fixes

- Fixed tag recognition issues when comparing versions
- Fixed changelog ordering to process tags correctly
- Resolved configuration precedence problems

## [2.2.0] - 2025-12-03

### What's New

- View both project and user-level configuration settings with the new config show command
- Automatic hiding of sensitive information like API keys when displaying configuration

### Improvements

- Faster navigation with keyboard shortcuts in provider selection prompts
- Better support for international environments with enhanced text encoding

### Bug Fixes

- Fixed issues with text display in non-English environments

## [2.1.0] - 2025-12-03

### What's New

- New 'kittylog auth' command for Claude Code authentication
- New 'kittylog model' command for easy AI provider setup

### Improvements

- Cleaner configuration system with better error messages
- More reliable API responses with better error handling
- Improved security for your API keys

### Bug Fixes

- Fixed OAuth token storage to prevent environment issues
- Resolved duplicate git repository access problems

## [2.0.0] - 2025-12-02

### What's New

- Support for 5 new AI providers: Azure OpenAI, Kimi Coding, Moonshot AI, Replicate, and Claude Code
- Claude Code OAuth authentication for seamless subscription access
- New 'config reauth' command to refresh authentication tokens
- Comprehensive provider test suite with complete coverage for all AI services

### Improvements

- Modernized configuration system with better validation and type safety
- More reliable AI integration with improved error handling and retry logic
- Better token counting fallback when primary estimation fails
- Enhanced test isolation and reliability across all test suites
- Cleaner error messages with proper exception chaining throughout the app

### Bug Fixes

- Fixed changelog parser logic for proper handling of unreleased sections
- Fixed regex pattern for accurate bullet point counting
- Fixed version comparison to handle 'v' prefix correctly
- Fixed cache interference issues between test runs
- Fixed missing runtime dependency that caused startup failures

## [1.6.0] - 2025-11-01

### What's New

- Customize changelog tone for different audiences - developers, end users, or stakeholders

### Improvements

- Interactive setup now helps you choose the right changelog style
- Better AI prompts generate content tailored to your audience

## [1.5.0] - 2025-11-01

### What's New

- Generate changelogs in 30+ different languages
- Interactive language selection for your changelogs

### Improvements

- Completely redesigned README with clearer structure and visual design
- Expanded key features with detailed descriptions and use cases
- Enhanced configuration section with multilingual examples

## [1.4.0] - 2025-10-31

### What's New

- Automatic version detection calculates the right version number for unreleased changes
- Interactive setup with guided configuration and optional git diff analysis

### Improvements

- Better changelog formatting preserves AI-generated version headers
- Enhanced boundary detection handles complex date heading formats
- Configuration now respects environment variables over config files

### Bug Fixes

- Fixed parameter passing issues that were causing test failures
- Resolved nested bracket handling in changelog date headings

## [1.3.0] - 2025-10-31

### What's New

- Support for 11 new AI providers: Chutes, Custom Anthropic/OpenAI, DeepSeek, Fireworks, Gemini, LM Studio, MiniMax, Mistral, StreamLake, Synthetic, and Together AI
- Interactive setup now guides you through configuration for all new providers
- Custom endpoint support for Anthropic and OpenAI compatible services

### Improvements

- Enhanced local provider support with automatic URL detection for LM Studio and Ollama
- Simplified configuration system handles all provider environment variables automatically

## [1.2.0] - 2025-10-04

### What's New

- New Z.AI Coding provider with dedicated API endpoint

### Improvements

- Cleaner configuration with removed obsolete settings
- Updated documentation for easier provider setup

## [1.1.0] - 2025-10-03

### What's New

- Support for Z.AI provider with coding plan API endpoint

### Improvements

- Enhanced error handling for Z.AI API responses
- Updated dependencies for better security and performance

## [1.0.2] - 2025-10-01

### What's New

- Support for OpenRouter AI provider added
- Support for Z.AI provider added

### Improvements

- Updated dependencies for better security and performance
- Improved provider key handling in configuration

## [1.0.1] - 2025-09-29

### Improvements

- Better changelog generation with stricter content rules
- Enhanced prompt structure for clearer and more organized updates

## [1.0.0] - 2025-09-28

### What's New

- Support for Cerebras AI provider added

### Improvements

- More reliable version updates with automated tagging
- Updated to latest stable dependency versions for better security and performance

## [0.6.0] - 2025-09-27

### What's New

- Added confirmation prompts to prevent accidental AI calls
- New --yes flag to skip prompts for automated workflows
- Smart version ordering keeps changelog entries organized correctly

### Improvements

- Better handling of version numbers with prefixes like 'v1.0.0'
- More reliable version bumping with updated tooling

### Bug Fixes

- Fixed version ordering issues in changelog generation

## [0.5.1] - 2025-09-25

### What's New

- Flexible changelog grouping modes - organize changes by tags, dates, or time gaps

### Improvements

- Better boundary detection for different commit patterns
- Enhanced configuration options for changelog generation
- More reliable AI integration with improved error handling

### Bug Fixes

- Fixed critical bug causing all boundaries to be reprocessed unnecessarily
- Resolved test failures and improved overall reliability
- Fixed issues with boundary object handling in changelog processing

## [0.4.0] - 2025-09-24

### What's New

- Support for more AI providers including Groq and Cerebras
- New --no-unreleased flag to skip pending changes in changelogs

### Improvements

- More reliable AI integration with direct API calls
- Better error handling and retry logic for AI requests
- Cleaner project structure and documentation

## [0.3.3] - 2025-09-22

### What's New

- See AI token usage during changelog generation
- Bullet point limits keep changelogs clean and readable

### Improvements

- Smarter unreleased section handling that replaces old content automatically
- Clearer README with simplified installation and usage instructions

## [0.3.2] - 2025-09-22

### What's New

- New flag to skip unreleased sections in changelogs
- Visual usage diagram added to help you get started

### Improvements

- Better changelog formatting with cleaner section management
- More reliable handling of unreleased sections across commands

## [0.3.1] - 2025-09-22

### Improvements

- Version updates now overwrite existing entries for cleaner changelogs
- Added quiet mode for automated workflows
- Updated project name from clog to kittylog for better identity

### Bug Fixes

- Fixed incorrect environment variable name in error messages

## [0.3.0] - 2025-09-22

### What's New

- Automated publishing to PyPI for new releases

### Improvements

- Better error messages with correct setting names
- Improved test coverage and code quality

### Bug Fixes

- Fixed incorrect environment variable references in error messages

## [0.2.3] - 2025-09-22

### What's New

- Unified output system for clearer and more consistent messages

### Improvements

- Better changelog formatting with consistent section headers
- Cleaner code structure for more reliable updates

### Bug Fixes

- Fixed duplicate detection across different versions

## [0.2.2] - 2025-09-22

### Improvements

- App now responds faster with git operation caching
- Smarter changelog handling automatically manages unreleased sections
- Simplified configuration with standardized settings
- Improved file discovery finds your changelog in more locations

### Bug Fixes

- Fixed duplicate entries in unreleased sections
- Better test reliability with cleaner environment handling

## [0.2.1] - 2025-09-22

### Improvements

- Simplified command structure with cleaner organization
- More reliable changelog processing with improved workflow handling

## [0.2.0] - 2025-09-22

### What's New

- Automatically finds your changelog file no matter what you name it
- New documentation files for easier reference and better organization

### Improvements

- Simplified configuration with consistent setting names
- Cleaner documentation structure with separate usage and agent guides

## [0.1.10] - 2025-09-22

### Improvements

- More reliable changelog generation with better test consistency
- Cleaner and more organized code structure
- Removed outdated documentation files for a cleaner repository

### Bug Fixes

- Fixed test failures that depended on execution order
- Resolved git context handling issues in test environment

## [0.1.9] - 2025-09-22

### Improvements

- Cleaned up outdated documentation files
- Improved test reliability with better git repository handling

## [0.1.8] - 2025-09-22

### What's New

- New unreleased command to manage pending changes from specific tag ranges
- New --all flag to update missing or all changelog entries at once

### Improvements

- Better changelog formatting with consistent structure across all versions
- More accurate AI analysis by excluding changelog files from change detection

### Bug Fixes

- Fixed formatting issues around section headers and spacing
- Resolved test conflicts and improved reliability of changelog generation

## [0.1.7] - 2025-09-21

### Improvements

- Smarter Unreleased section handling - only appears for untagged changes
- Cleaner changelog formatting with better section management
- More reliable changelog generation with improved tag detection

## [0.1.6] - 2025-09-21

### What's New

- Automatic 'Unreleased' section for pending changes
- AI-powered changelog cleaning for better formatting

### Improvements

- Stricter AI formatting with bullet point limits
- Better handling of duplicate changelog entries

### Bug Fixes

- Fixed formatting issues around section headers
- Removed empty sections and extra blank lines

## [0.1.5] - 2025-09-21

### What's New

- New commands to create and update changelogs
- Automatically formats AI-generated changelog content

### Improvements

- Better handling of duplicate changelog entries
- Cleaner formatting with proper spacing and structure

### Bug Fixes

- Fixed issues with processing git tags and versions

## [0.1.4] - 2025-09-21

### What's New

- Generate changelog entries for specific versions automatically
- New unreleased command for managing pending changes

### Improvements

- Better handling of missing tags in changelog
- Improved formatting consistency

### Bug Fixes

- Fixed issues with processing large prompts

## [0.1.3] - 2025-09-21

### What's New

- Automatic changelog updates for all git tags by default
- New option to preserve existing changelog content when updating

### Improvements

- Unreleased section now always replaces content instead of adding duplicates
- Simplified changelog processing with better section management

### Bug Fixes

- Fixed duplicate entries in unreleased sections
- Fixed formatting issues when inserting unreleased changes

## [0.1.1] - 2025-09-20

### Improvements

- Better handling of changelog updates for multiple versions
- Improved stability when processing git tags
- Enhanced logging options with more flexible configuration

### Bug Fixes

- Fixed occasional issues with directory detection during git operations
- Improved error handling in multi-tag scenarios

## [0.1.0] - 2025-09-20

### What's New

- AI-powered changelog generation creates updates automatically
- Support for multiple AI providers (OpenAI, Anthropic, Ollama, and more)
- Interactive setup makes configuration quick and easy

### Improvements

- Better version management with automatic version bumping
- Rich formatting makes output easier to read
- Dry-run preview lets you check changes before applying them

### Bug Fixes

- Fixed issues with automatic git tag detection
- Improved error messages with helpful retry options

