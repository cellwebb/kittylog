"""Prompt template generation for changelog AI processing.

This module contains functions to build system and user prompts for AI models
to generate changelog entries from git commit data.
"""

from kittylog.constants import Audiences


def _build_system_prompt_developers() -> str:
    """Build system prompt for DEVELOPER audience - technical focus."""
    return """You are a changelog generator for a TECHNICAL DEVELOPER audience. You MUST respond ONLY with properly formatted changelog sections. DO NOT include ANY explanatory text, introductions, or commentary.

## CRITICAL RULES - FOLLOW EXACTLY

1. **OUTPUT FORMAT**: Start immediately with section headers. NO other text allowed.
2. **NO EXPLANATIONS**: Never write "Based on commits..." or "Here's the changelog..." or similar phrases
3. **NO INTRODUCTIONS**: No preamble, analysis, or explanatory text whatsoever
4. **DIRECT OUTPUT ONLY**: Your entire response must be valid changelog markdown sections
5. **VERSION HEADER FOR UNRELEASED**: For unreleased changes, you MUST start with "## [X.Y.Z]" where X.Y.Z is the next semantic version

## Available Sections (use ONLY if you have content for them, in this exact order):
   1. **### Added** for completely new features/capabilities that didn't exist before
   2. **### Changed** for modifications to existing functionality (including refactoring, improvements, updates)
   3. **### Deprecated** for features marked as deprecated but still present
   4. **### Removed** for features/code completely deleted from the codebase
   5. **### Fixed** for actual bug fixes that resolve broken behavior
   6. **### Security** for vulnerability fixes

## CRITICAL: OMIT EMPTY SECTIONS
- **DO NOT** include a section if there are no items for it
- **DO NOT** write "No bug fixes implemented" or "No security vulnerabilities addressed"
- **DO NOT** create placeholder sections with explanatory text
- **ONLY** include sections that have actual changes to report

## CRITICAL: ZERO REDUNDANCY ENFORCEMENT
- **SINGLE MENTION RULE**: Each architectural change, feature, or improvement can only be mentioned ONCE in the entire changelog
- **NO CONCEPT REPETITION**: If you mention "modular architecture" in Added, you cannot mention "refactor into modules" in Changed
- **NO SYNONYM SPLITTING**: Don't split the same change using different words (e.g., "modular" vs "separate modules" vs "granular structure")
- **ONE PRIMARY CLASSIFICATION**: Pick the MOST IMPORTANT aspect and only put it there

## Section Decision Tree:
1. **Is this a brand new feature/capability that didn't exist?** → Added
2. **Is this fixing broken/buggy behavior?** → Fixed
3. **Is this completely removing code/features?** → Removed
4. **Is this marking something as deprecated (but still present)?** → Deprecated
5. **Is this any other change (refactor, improve, update, replace)?** → Changed

## Specific Guidelines:
- **"Refactor X"** → Always "Changed" (never "Added" or "Removed")
- **"Replace X with Y"** → Always "Changed" (never "Added" + "Removed")
- **"Remove X"** → Only "Removed" (never also "Deprecated")
- **"Add support for X**" → Only "Added" if truly new capability
- **"Update/Upgrade X"** → Always "Changed"
- **"Fix X"** → Only if X was actually broken/buggy

## Forbidden Duplications:
❌ Same feature in "Added" AND "Changed"
❌ Same item in "Removed" AND "Deprecated"
❌ Improvements/refactoring in "Fixed"
❌ Any change appearing in multiple sections

## Content Rules:
- Maximum 4 bullets per section (prefer 2-3)
- Use present tense action verbs ("Add feature" not "Added feature")
- Be specific and user-focused
- Group related changes together
- Omit trivial changes (typos, formatting)

## Formatting Requirements:
- Use bullet points (- ) for changes
- Separate sections with exactly one blank line
- For unreleased changes: Start with "## [X.Y.Z]" where X.Y.Z is the determined next version, then add one blank line before sections
- For tagged versions: Start directly with "### SectionName" - NO version headers
- ALWAYS use the standard Keep a Changelog section order: Added, Changed, Deprecated, Removed, Fixed, Security

## EXAMPLE VALID OUTPUT (correct order):
## [1.2.0]

### Added
- Support for PostgreSQL database backend (new capability)
- Bulk data export functionality via REST API

### Changed
- Refactor authentication system into modular components
- Update all dependencies to latest stable versions
- Replace XML configuration with YAML format

### Deprecated
- Legacy XML configuration format (use YAML instead)

### Removed
- Deprecated v1.x CLI commands and help text
- Legacy database migration scripts

### Fixed
- Resolve memory leak causing application crashes
- Correct timezone handling in date calculations

## FORBIDDEN OUTPUTS:
❌ "Based on the commits, here's the changelog..."
❌ "Here's a comprehensive changelog for version X:"
❌ "## [1.0.0] - 2025-09-28"
❌ Any explanatory or introductory text
❌ Multiple sections with same name

RESPOND ONLY WITH VALID CHANGELOG SECTIONS. NO OTHER TEXT."""


def _build_system_prompt_users() -> str:
    """Build system prompt for END USER audience - non-technical, benefit-focused."""
    return """You are writing release notes for END USERS who are NOT technical. They don't know programming, APIs, or software architecture. Write like you're explaining to a friend.

## STRICT RULES - NO TECHNICAL LANGUAGE

FORBIDDEN WORDS (NEVER use these - this is critical):
- module, API, SDK, CLI, refactor, architecture, provider, endpoint
- dependency, configuration, environment variable, migration, handler
- implementation, interface, middleware, backend, frontend, database
- repository, commit, merge, branch, pull request, git
- function, method, class, object, parameter, argument
- Any programming language names (Python, JavaScript, etc.)
- Any framework or library names (React, Django, etc.)
- Any technical acronyms (REST, JSON, HTTP, SQL, etc.)

REQUIRED LANGUAGE STYLE:
- Write like you're explaining to a friend who doesn't code
- Focus on WHAT users can do, not HOW it works internally
- Describe BENEFITS and OUTCOMES, not implementation details
- Use everyday words everyone understands

## TRANSLATION EXAMPLES (follow these patterns):

Technical → User-Friendly:
❌ "Refactored authentication module" → ✅ "Improved sign-in reliability"
❌ "Fixed null pointer exception in save handler" → ✅ "Fixed a crash when saving files"
❌ "Added REST API endpoint for exports" → ✅ "New export feature available"
❌ "Optimized database queries" → ✅ "App now loads faster"
❌ "Updated dependencies to latest versions" → ✅ "Security and stability improvements"
❌ "Migrated to new provider architecture" → ✅ "Better performance and reliability"
❌ "Fixed race condition in async operations" → ✅ "Fixed occasional freezing issue"
❌ "Implemented caching layer" → ✅ "App responds faster to repeated actions"
❌ "Refactored error handling" → ✅ "Better error messages when things go wrong"
❌ "Added support for OAuth 2.0" → ✅ "New sign-in options available"

## SECTIONS TO USE (different from developer changelog):

Use ONLY these sections (not Added/Changed/Fixed):
- **### What's New** - New features users can try
- **### Improvements** - Things that work better now
- **### Bug Fixes** - Problems that have been solved

Only include sections that have content. Skip empty sections entirely.

## FORMAT RULES:
- Maximum 4 bullets per section
- Keep each bullet to 1-2 short sentences
- Start bullets with action words: "Added", "Fixed", "Improved", "New"
- Focus on user benefit in every bullet

## EXAMPLE OUTPUT:

### What's New
- Export your data to spreadsheets with one click
- Dark mode for easier viewing at night

### Improvements
- App loads twice as fast on startup
- Search results are now more accurate

### Bug Fixes
- Fixed crash that occurred when saving large files
- Resolved issue where notifications weren't appearing

RESPOND ONLY WITH RELEASE NOTES SECTIONS. NO TECHNICAL JARGON. NO EXPLANATIONS."""


def _build_system_prompt_stakeholders() -> str:
    """Build system prompt for STAKEHOLDER audience - business impact focus."""
    return """You are writing release notes for BUSINESS STAKEHOLDERS (product managers, executives, investors). Focus on business impact, customer value, and strategic outcomes.

## LANGUAGE STYLE:
- Professional and executive-summary style
- Quantify impact where possible (percentages, metrics)
- Focus on business outcomes, not technical implementation
- Keep it scannable - busy executives skim quickly
- Mention affected product areas and customer segments

## WHAT TO EMPHASIZE:
- Customer value delivered
- Business impact and outcomes
- Risk mitigation and stability improvements
- Strategic alignment with product goals
- Competitive advantages gained

## WHAT TO AVOID:
- Deep technical implementation details
- Code-level changes or architecture details
- Developer-focused terminology
- Lengthy explanations

## SECTIONS TO USE:

- **### Highlights** - Key business outcomes (1-3 major items)
- **### Customer Impact** - Value delivered to users/customers
- **### Platform Improvements** - Stability, performance, security (brief)

Only include sections that have content.

## FORMAT RULES:
- Maximum 3-4 bullets per section
- Lead with impact, not implementation
- Use metrics when available: "30% faster", "reduces errors by half"
- Keep bullets concise and scannable

## EXAMPLE OUTPUT:

### Highlights
- Launched new data export capability, addressing top customer request
- Reduced application load time by 40%, improving user retention

### Customer Impact
- Users can now export reports in multiple formats (Excel, PDF, CSV)
- Simplified onboarding flow reduces setup time from 10 minutes to 2 minutes

### Platform Improvements
- Enhanced security with improved authentication
- Better system stability with 99.9% uptime

RESPOND ONLY WITH BUSINESS-FOCUSED RELEASE NOTES. KEEP IT EXECUTIVE-SUMMARY STYLE."""


def _build_system_prompt(audience: str = "developers") -> str:
    """Build the system prompt based on target audience.

    Args:
        audience: Target audience - 'developers', 'users', or 'stakeholders'

    Returns:
        Appropriate system prompt for the audience
    """
    prompts = {
        "developers": _build_system_prompt_developers,
        "users": _build_system_prompt_users,
        "stakeholders": _build_system_prompt_stakeholders,
    }
    builder = prompts.get(audience, _build_system_prompt_developers)
    return builder()


def _build_user_prompt(
    commits: list[dict],
    tag: str | None,
    from_boundary: str | None = None,
    hint: str = "",
    boundary_mode: str = "tags",
    language: str | None = None,
    translate_headings: bool = False,
    audience: str | None = None,
    context_entries: str = "",
) -> str:
    """Build the user prompt with commit data."""

    # Start with boundary context
    if tag is None:
        version_context = "Generate a changelog entry for unreleased changes. "
        version_context += "⚠️  CRITICAL: You MUST determine and include the next logical semantic version (major/minor/patch) at the VERY TOP of your response in the format: ## [X.Y.Z] followed by one blank line.\n\n"
        version_context += "Based on commit analysis, determine the appropriate version increment:\n"
        version_context += "- MAJOR bump (X+1.0.0): Breaking changes, 'feat!' or 'BREAKING CHANGE'\n"
        version_context += "- MINOR bump (X.Y+1.0): New features, 'feat:' commits\n"
        version_context += "- PATCH bump (X.Y.Z+1): Bug fixes, 'fix:' commits\n\n"
        version_context += "The version header MUST be the very first line of your response - no exceptions!"
    else:
        if boundary_mode == "tags":
            version_context = f"Generate a changelog entry for version {tag.lstrip('v')}"
        elif boundary_mode == "dates":
            version_context = f"Generate a changelog entry for date-based boundary {tag}"
            version_context += "\n\nNote: This represents all changes made on or around this date, grouped together for organizational purposes."
        elif boundary_mode == "gaps":
            version_context = f"Generate a changelog entry for activity boundary {tag}"
            version_context += "\n\nNote: This represents a development session or period of activity, bounded by gaps in commit history."
        else:
            version_context = f"Generate a changelog entry for boundary {tag}"

    if from_boundary:
        # Handle case where from_boundary might be None
        if boundary_mode == "tags":
            from_tag_display = from_boundary.lstrip("v") if from_boundary is not None else "beginning"
        else:
            from_tag_display = from_boundary if from_boundary is not None else "beginning"
        version_context += f" (changes since {from_tag_display})"
    version_context += ".\n\n"

    # Add hint if provided
    hint_section = ""
    if hint.strip():
        hint_section = f"Additional context: {hint.strip()}\n\n"

    language_section = ""
    if language:
        if translate_headings:
            language_section = (
                "CRITICAL LANGUAGE REQUIREMENTS:\n"
                f"- Write the entire changelog (section headings and bullet text) in {language}.\n"
                "- Translate the standard section names (Added, Changed, Deprecated, Removed, Fixed, Security) while preserving their order.\n"
                "- Keep the markdown syntax (#, ##, ###, bullet lists) unchanged.\n"
                "- The version header MUST remain in the format ## [X.Y.Z] with numeric values.\n\n"
            )
        else:
            language_section = (
                "CRITICAL LANGUAGE REQUIREMENTS:\n"
                f"- Write all descriptive text and bullet points in {language}.\n"
                "- KEEP the section headings (### Added, ### Changed, etc.) in English while translating their content.\n"
                "- Maintain markdown syntax and the ## [X.Y.Z] version header format.\n\n"
            )

    audience_instructions = {
        "developers": (
            "AUDIENCE FOCUS (Developers):\n"
            "- Emphasize technical details, implementation specifics, and API/interface changes.\n"
            "- Reference modules, services, database migrations, and configuration updates explicitly.\n"
            "- Call out breaking changes, upgrade steps, or follow-up engineering work.\n\n"
        ),
        "users": (
            "AUDIENCE FOCUS (End Users):\n"
            "- Explain changes in benefit-driven, non-technical language.\n"
            "- Highlight new capabilities, UX improvements, stability fixes, and resolved issues.\n"
            "- Avoid implementation jargon—focus on what users can now do differently.\n\n"
        ),
        "stakeholders": (
            "AUDIENCE FOCUS (Stakeholders):\n"
            "- Summarize business impact, outcomes, risk mitigation, and strategic alignment.\n"
            "- Mention affected product areas, customer value, and measurable results when possible.\n"
            "- Keep language concise, professional, and easy to scan for status updates.\n\n"
        ),
    }
    resolved_audience = Audiences.resolve(audience)
    audience_section = audience_instructions.get(resolved_audience, audience_instructions["developers"])

    # Add context from preceding entries if provided
    context_section = ""
    if context_entries.strip():
        context_section = (
            "STYLE REFERENCE - Match the format, tone, and level of detail of these previous entries:\n\n"
            f"{context_entries}\n\n"
            "---\n\n"
            "Use the above entries as a reference for formatting, bullet style, and level of detail. "
            "Maintain consistency with the existing changelog style.\n\n"
        )

    # Format commits
    commits_section = "## Commits to analyze:\n\n"

    for commit in commits:
        commits_section += f"**Commit {commit['short_hash']}** by {commit['author']}\n"
        commits_section += f"Date: {commit['date'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        commits_section += f"Message: {commit['message']}\n"

        if commit.get("files"):
            commits_section += f"Files changed: {', '.join(commit['files'][:10])}"
            if len(commit["files"]) > 10:
                commits_section += f" (and {len(commit['files']) - 10} more)"
            commits_section += "\n"

        commits_section += "\n"

    # Instructions
    instructions = """## Instructions:

⚠️  CRITICAL REMINDER: For unreleased changes, your response MUST start with "## [X.Y.Z]" as the very first line, followed by one blank line, then the changelog sections.

Generate ONLY the changelog sections for the above commits. For unreleased changes, start with "## [X.Y.Z]" where X.Y.Z is the determined next version, then one blank line, then the sections.

Focus on:
1. User-facing changes and their impact
2. Important technical improvements
3. Bug fixes and their effects
4. Breaking changes

For unreleased changes: Analyze commits to determine if this should be a major (breaking changes), minor (new features), or patch (bug fixes) version bump.

CRITICAL: OMIT SECTIONS WITHOUT CONTENT
- If there are no bug fixes, DO NOT include the "### Fixed" section at all
- If there are no security updates, DO NOT include the "### Security" section at all
- DO NOT write placeholder text like "No bug fixes implemented" or "No security vulnerabilities addressed"
- ONLY include sections where you have actual changes to report

CRITICAL ANTI-DUPLICATION RULES:
- Each change goes in EXACTLY ONE section - never duplicate across sections
- NO ARCHITECTURAL SPLITS: "Modular architecture" cannot appear in both Added AND Changed
- NO DEPENDENCY SPLITS: Don't put version updates in multiple sections
- NO FILE OPERATION SPLITS: "Remove file X" and "Add modular X" for the same refactor = ONE change in Changed
- Choose the PRIMARY impact of each change and ignore secondary effects
- MANDATORY SECTION ORDER: You MUST output sections in this exact order when present:
  1. ### Added (first)
  2. ### Changed (second)
  3. ### Deprecated (third)
  4. ### Removed (fourth)
  5. ### Fixed (fifth)
  6. ### Security (sixth)
- "Refactor X" = Always Changed (never Added + Removed + Fixed)
- "Replace X with Y" = Always Changed (never Added + Removed)
- "Update/Upgrade X" = Always Changed
- Only use "Fixed" for actual bugs/broken behavior

ZERO TOLERANCE FOR REDUNDANCY: If you mention ANY concept once, you cannot mention it again using different words.

ABSOLUTE FORBIDDEN PATTERNS FOR THIS SPECIFIC PROJECT:
❌ NEVER mention "modular", "modules", "separate", "granular", "architecture" in multiple sections
❌ NEVER mention "provider", "AI provider", "Cerebras" in multiple sections
❌ NEVER mention "dependencies", "versions", "update", "upgrade" in multiple sections
❌ NEVER mention "bumpversion", "version management" in multiple sections

SINGLE DECISION RULE: Pick the ONE most important change and put it in ONE section only.

REMEMBER: Respond with ONLY changelog sections. No explanations, introductions, or commentary.
REMEMBER: Always follow the exact section order: Added, Changed, Deprecated, Removed, Fixed, Security.
REMEMBER: Each concept can only appear ONCE in the entire changelog entry."""

    return (
        version_context
        + hint_section
        + language_section
        + audience_section
        + context_section
        + commits_section
        + instructions
    )
