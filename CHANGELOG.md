# Changelog


## [3.0.2] - 2025-12-06

### Improvements

- Better organization of changelog features for improved performance
- More accurate version boundary detection and content handling


## [3.0.1] - 2025-12-06

### What's New

- Generate targeted updates for different audiences (developers, users, or stakeholders)

### Improvements

- Better organization to prevent mentioning the same feature twice
- More accurate control over update length with detailed limits per section


## [3.0.0] - 2025-12-06

### What's New

- Simplified command structure with a single update command

### Improvements

- Better help text and guidance when updating entries
- More reliable command processing


## [2.11.0] - 2025-12-06

### Improvements

- Better change summaries that don't repeat what you've already seen
- Improved how features are organized in updates


## [2.10.3] - 2025-12-06

### What's New

- AI features now include 5 previous log entries for better context


## [2.10.2] - 2025-12-06

### What's New

- Added identifiers to boundary commits for better tracking in changelogs

### Improvements

- Changelogs now save progressively during updates to prevent lost progress
- Better spacing and formatting in changelog entries

### Bug Fixes

- Fixed incorrect ordering of entries in changelogs - newest now appear first correctly


## [2.10.1] - 2025-12-06

### Improvements

- Better handling of missing entries in your logs
- Improved chronological ordering of changelog entries
- Clearer date formatting and spacing in generated logs


## [2.10.0] - 2025-12-06

### What's New

- Colorful rainbow banner now appears when starting the app
- Generate changelogs in different languages for different audiences

### Improvements

- Removed confirmation prompts to make commands run faster
- Changelog formatting now keeps consistent spacing between versions


## [2.9.2] - 2025-12-06

### Bug Fixes

- Fixed incorrect grouping of changes in generated logs


## [2.9.1] - 2025-12-06

### Improvements

- More reliable processing when handling version tags and dates
- Better handling of empty change lists and special date ranges


## [2.9.0] - 2025-12-06

### Improvements

- Better support for optional API keys with LMStudio and Ollama providers
- More reliable error handling across all AI providers
- Streamlined provider detection for easier setup


## [2.8.2] - 2025-12-05

### Improvements

- Cleaner changelog formatting without version headers


## [2.8.1] - 2025-12-05

### Improvements

- Simplified command line options for easier use


## [2.8.0] - 2025-12-05

### Improvements

- More reliable command processing
- Better type safety and error prevention


## [2.7.0] - 2025-12-05

### What's New

- New --detail option to control how much information you see in the output
- Choose between concise, normal, or detailed output formats to fit your needs

### Improvements

- System now enforces strict limits on output length to keep notes focused and readable


## [2.6.0] - 2025-12-05

### What's New

- Generate changelogs tailored for different audiences: developers, users, or stakeholders

### Improvements

- Better content targeting based on who will read your changelog


## [2.5.2] - 2025-12-05

### Improvements

- App starts up faster and responds more quickly
- Better error messages when things go wrong
- Improved reliability for missing entries handling

### Bug Fixes

- Fixed crashes related to boundary processing
- Resolved test interference issues
- Fixed exception handling to properly respond to system interruptions


## [2.5.1] - 2025-12-05

### What's New

- New boundary mode helps find missing entries by dates or gaps

### Bug Fixes

- Fixed grouping mode being ignored when checking for missing entries


## [2.5.0] - 2025-12-05

### What's New

- New incremental save option that updates your changelog as you work instead of waiting until the end

### Improvements

- Better progress tracking when processing multiple entries
- More reliable handling of changelog files


## [2.4.2] - 2025-12-05

### Improvements

- Improved reliability and performance across all services
- Better error messages when things go wrong

### Bug Fixes

- Fixed authentication issues with Qwen service


## [2.4.1] - 2025-12-04

### Improvements

- Improved system stability and reliability


## [2.4.0] - 2025-12-04

### What's New

- Added support for Qwen AI provider with easy sign-in
- New secure token storage keeps your authentication safe
- Enhanced authentication commands with status for all providers

### Improvements

- Better error messages when things go wrong
- Automatic version style matching keeps changelogs consistent
- Improved debugging with more detailed information

### Bug Fixes

- Fixed version prefix handling in changelogs
- Corrected import ordering for better reliability


## [2.3.4] - 2025-12-04

### What's New

- Consistent version numbering in changelogs

### Improvements

- Better handling of various version formats including pre-release versions

### Bug Fixes

- Fixed incorrect reprocessing of changelog entries
- Resolved issues with version tag recognition


## [2.3.3] - 2025-12-04

### Improvements

- Cleaner changelog formatting and organization
- Better handling of unreleased updates in the changelog


## [2.3.2] - 2025-12-04

### What's New

- Added unreleased mode for generating changelogs between releases

### Improvements

- Updated AI models to latest versions for better results
- Improved changelog processing to handle dates and versions more accurately

### Bug Fixes

- Fixed tag recognition issues when comparing versions


## [2.3.1] - 2025-12-04

### What's New

- Updated to latest AI models for better performance

### Improvements

- AI now processes entries in chronological order for better context


## [2.3.0] - 2025-12-04

### What's New

- New release command for automated changelog preparation
- Style reference feature to maintain consistent changelog format

### Improvements

- Better performance and reliability through code improvements
- Enhanced configuration management with clearer precedence rules
- More accurate error messages and improved stability

### Bug Fixes

- Fixed tag recognition and changelog ordering issues
- Resolved configuration loading and API key handling problems


## [2.2.0] - 2025-12-03

### What's New

- Set project-specific settings that override your main config
- Keyboard shortcuts now make navigating menus faster

### Improvements

- App now works better on computers with different languages
- Configuration display now hides sensitive information for privacy


## [2.1.0] - 2025-12-03

### What's New

- New standalone 'kittylog auth' command for easier sign-in
- New 'kittylog model' command to configure AI providers independently
- Support for 20+ AI providers including custom endpoints

### Improvements

- Setup process is now simpler and more guided
- Better error messages when API calls fail
- Improved security for API key storage

### Bug Fixes

- Fixed crashes from invalid API responses
- Removed duplicate code that could cause inconsistencies
- Fixed token storage to not modify system environment


## [2.0.0] - 2025-12-02

### What's New

- New AI providers available: Azure OpenAI, Kimi Coding, Moonshot AI, and Replicate
- Claude Code OAuth authentication for secure sign-in
- Support for Python 3.14
- New missing entries mode for processing skipped changelog entries
- Re-authentication command for refreshing expired tokens

### Improvements

- Better error messages with more context when things go wrong
- More accurate token counting fallback for AI requests
- Faster and more reliable performance with centralized caching
- Cleaner configuration system with better validation
- Improved changelog parsing and insertion point detection

### Bug Fixes

- Fixed crash when saving files in some scenarios
- Fixed version comparison issues with v-prefix tags
- Resolved circular import problems
- Fixed bullet point counting in AI-generated content
- Corrected changelog insertion logic for edge cases


## [1.6.0] - 2025-11-01

### What's New

- Create changelogs tailored for different audiences (developers, users, or stakeholders)
- New interactive prompts help you choose the right tone for your audience

### Improvements

- Better changelog customization options in settings
- Enhanced AI generates more relevant content based on your audience


## [1.5.0] - 2025-11-01

### What's New

- Generate changelogs in 30+ languages with custom language options
- Interactive language selection with easy-to-use commands

### Improvements

- Better organized documentation with clear examples and guides
- Enhanced help section with direct links to detailed documentation


## [1.4.0] - 2025-10-31

### What's New

- Interactive configuration mode with guided setup
- Automatic version detection for unreleased changes
- Optional git diff inclusion for better context

### Improvements

- Better grouping mode explanations with smart defaults
- Environment variable support for secure API keys
- Enhanced changelog boundary detection

### Bug Fixes

- Fixed configuration parameter propagation issues
- Resolved nested bracket handling in date headings
- Fixed trailing whitespace in output


## [1.3.0] - 2025-10-31

### What's New

- Connect with 11 new AI providers including DeepSeek, Gemini, Mistral, and Together AI
- Use custom endpoints with OpenAI and Anthropic-compatible services
- Local AI support for LM Studio and Ollama

### Improvements

- Interactive setup makes adding new AI providers easier
- Updated configuration system supports more AI service options


## [1.2.0] - 2025-10-04

### What's New

- New Z.AI coding provider option available
- Dedicated support for Z.AI coding plans

### Improvements

- Simplified provider setup with shared Z.AI key
- Better documentation for adding new providers

### Bug Fixes

- Removed outdated configuration settings
- Fixed provider selection in setup


## [1.1.0] - 2025-10-03

### What's New

- New Z.AI provider support with coding plan option

### Improvements

- Better error handling for AI responses
- Improved code style and formatting

### Bug Fixes

- Fixed validation for empty or missing content


## [1.0.2] - 2025-10-01

### What's New

- Now supports OpenRouter and Z.AI as new AI options

### Improvements

- Better HTTP handling and overall stability
- Updated configuration with improved temperature settings


## [1.0.1] - 2025-09-29

### What's New

- Improved changelog generation with stricter content rules

### Improvements

- Better organization and clarity of change descriptions
- More flexible and accurate prompt generation


## [1.0.0] - 2025-09-28

### What's New

- Added support for Cerebras AI provider

### Improvements

- Better performance and reliability with updated AI integrations
- Security and stability improvements with updated dependencies


## [0.6.0] - 2025-09-27

### What's New

- Added confirmation prompts before generating changelogs to prevent accidental API calls
- New --yes flag to automatically skip prompts for automation
- Improved changelog version ordering to keep versions in the right sequence

### Improvements

- Better handling of complex version numbers in changelogs


## [0.5.1] - 2025-09-25

### Bug Fixes

- Fixed issue causing all boundaries to be reprocessed instead of just missing ones


## [0.4.0] - 2025-09-24

### What's New

- Choose from multiple AI providers (OpenAI, Anthropic, Groq, Cerebras, Ollama) for changelog generation
- New --no-unreleased option to skip unreleased changes in your changelog

### Improvements

- Better error handling and retry logic for AI requests
- Streamlined configuration with environment variable support


## [0.3.3] - 2025-09-22

### What's New

- Token usage tracking now shows AI operation costs
- Smart changelog management with automatic bullet limiting

### Improvements

- Better organization of changelog sections
- Cleaner README with simplified installation and usage guides


## [0.3.2] - 2025-09-22

### What's New

- Added option to skip unreleased sections when managing changelogs

### Improvements

- Better handling of unreleased sections with conditional formatting
- Added visual usage diagram to help understand workflows


## [0.3.1] - 2025-09-22

### Improvements

- Changelog updates now overwrite existing entries automatically for better workflow consistency

### Bug Fixes

- Fixed incorrect environment variable name in error messages


## [0.3.0] - 2025-09-22

### What's New

- Project renamed to kittylog with new configuration files and settings

### Improvements

- Better error messages now show the correct setting names
- Automated publishing to package manager for new releases

### Bug Fixes

- Fixed incorrect environment variable name in error messages


## [0.2.3] - 2025-09-22

### Improvements

- Messages and error reports now appear more consistently throughout the app
- Better organization of change history with cleaner formatting


## [0.2.2] - 2025-09-22

### Improvements

- App runs faster by remembering git operations
- Simplified changelog updates by automatically handling unreleased sections
- Better file discovery to find your changelog in more locations


## [0.2.1] - 2025-09-22

### Improvements

- Simplified the interface with removed unnecessary options
- Better organization makes changelog updates more reliable


## [0.2.0] - 2025-09-22

### What's New

- Automatically finds your changelog file no matter what it's named
- New documentation with detailed usage guides and examples

### Improvements

- Simplified settings with consistent naming
- Better organization of help documentation


## [0.1.10] - 2025-09-22

### Improvements

- Better reliability and accuracy when generating changelogs
- Improved test coverage and stability
- Cleaner codebase for better performance


## [0.1.9] - 2025-09-22

### Improvements

- Better test reliability and more accurate changelog generation

### Bug Fixes

- Fixed issues with file path handling and git repository context


## [0.1.8] - 2025-09-22

### What's New

- New 'unreleased' command to generate changelog from specific tag ranges
- New --all flag to update all changelog entries at once

### Improvements

- Better changelog formatting consistency across all versions
- Smarter analysis by ignoring changelog files when processing changes

### Bug Fixes

- Fixed conflicts between --replace-unreleased and --no-replace-unreleased flags
- Fixed duplicate sections and formatting issues in changelog


## [0.1.7] - 2025-09-21

### What's New

- Smart changelog generation that adapts to tagged and untagged releases
- Automatic 'Unreleased' section for changes between official releases

### Improvements

- Cleaner changelog formatting with automatic duplicate removal
- Better handling of changelog sections and content organization

### Bug Fixes

- Fixed issues with processing tagged commits
- Resolved content merging problems for smoother changelog updates


## [0.1.6] - 2025-09-21

### What's New

- Automatic changelog generation for unreleased changes
- Improved AI-generated changelog formatting with automatic cleanup

### Improvements

- Better handling of duplicate content and formatting errors
- Cleaner spacing and structure in generated changelogs

### Bug Fixes

- Fixed issues with empty sections appearing in changelogs
- Fixed problems with content merging when processing tags


## [0.1.5] - 2025-09-21

### What's New

- New commands to create and update changelogs
- Automatically formats and cleans up AI-generated changelog content

### Improvements

- Better handling of duplicate sections and empty content
- More reliable processing of version tags and unreleased changes

### Bug Fixes

- Fixed crashes when processing git tags
- Resolved formatting issues with misplaced headers


## [0.1.4] - 2025-09-21

### What's New

- Generate changelog entries for specific release tags
- New command for handling unreleased changes

### Improvements

- Better formatting and consistency in changelog entries
- Improved handling of large content without issues


## [0.1.3] - 2025-09-21

### What's New

- Automatically tracks unreleased changes since last version
- New option to preserve existing changelog content when updating
- Better control over how unreleased entries are handled

### Improvements

- Changelog entries now limited to 6 items per section for cleaner output
- Smarter merging prevents duplicate entries in unreleased section
- Improved formatting removes extra blank lines and empty sections

### Bug Fixes

- Fixed duplicate entries appearing in unreleased section
- Fixed formatting issues when inserting new content
- Resolved crashes when processing commits without tags


## [0.1.1] - 2025-09-20

### What's New

- Better support for managing multiple update tags
- More flexible changelog generation with existing content

### Improvements

- Enhanced test reliability for git operations
- Improved commit message display formatting
- Better input validation for logging levels

### Bug Fixes

- Fixed issues with directory handling during operations
- Resolved test failures related to invalid working directories


## [0.1.0] - 2025-09-20

### What's New

- AI-powered changelog generation from your git history
- Support for multiple AI providers (Anthropic, OpenAI, and more)
- Interactive setup to configure your preferences

### Improvements

- Automatic detection of new changes since last update
- Preview mode to see changelog before applying changes
- Better error messages and automatic retry for failed operations

