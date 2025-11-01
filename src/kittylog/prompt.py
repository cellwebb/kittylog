"""Prompt generation for changelog AI processing.

This module creates prompts for AI models to generate changelog entries from git commit data.
"""

import logging
import re

logger = logging.getLogger(__name__)


def build_changelog_prompt(
    commits: list[dict],
    tag: str | None,
    from_tag: str | None = None,
    hint: str = "",
    boundary_mode: str = "tags",
) -> tuple[str, str]:
    """Build prompts for AI changelog generation.

    Args:
        commits: List of commit dictionaries
        tag: The target boundary identifier
        from_tag: The previous boundary identifier (for context)
        hint: Additional context hint
        boundary_mode: The boundary mode ('tags', 'dates', 'gaps')

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(commits, tag, from_tag, hint, boundary_mode)

    return system_prompt, user_prompt


def _build_system_prompt() -> str:
    """Build the system prompt with strict instructions for changelog generation."""
    return """You are a changelog generator. You MUST respond ONLY with properly formatted changelog sections. DO NOT include ANY explanatory text, introductions, or commentary.

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
- **"Add support for X"** → Only "Added" if truly new capability
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


def _build_user_prompt(
    commits: list[dict],
    tag: str | None,
    from_tag: str | None = None,
    hint: str = "",
    boundary_mode: str = "tags",
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

    if from_tag:
        # Handle case where from_tag might be None
        if boundary_mode == "tags":
            from_tag_display = from_tag.lstrip("v") if from_tag is not None else "beginning"
        else:
            from_tag_display = from_tag if from_tag is not None else "beginning"
        version_context += f" (changes since {from_tag_display})"
    version_context += ".\n\n"

    # Add hint if provided
    hint_section = ""
    if hint.strip():
        hint_section = f"Additional context: {hint.strip()}\n\n"

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

    return version_context + hint_section + commits_section + instructions


def clean_changelog_content(content: str, preserve_version_header: bool = False) -> str:
    """Clean and format AI-generated changelog content.

    Args:
        content: Raw AI-generated content
        preserve_version_header: Whether to preserve version headers (for unreleased changes)

    Returns:
        Cleaned and formatted changelog content
    """
    if not content:
        return ""

    # Remove version headers unless we want to preserve them (for unreleased changes)
    if not preserve_version_header:
        content = re.sub(r"^##\s*\[?v?\d+\.\d+\.\d+[^\n]*\n?", "", content, flags=re.MULTILINE)

    # Remove any "### Changelog" sections that might have been included
    content = re.sub(r"^###\s+Changelog\s*\n?", "", content, flags=re.MULTILINE)

    # Remove any date stamps
    content = re.sub(r"- \d{4}-\d{2}-\d{2}[^\n]*\n?", "", content, flags=re.MULTILINE)

    # Remove explanatory introductions and conclusions
    explanatory_patterns = [
        r"^Based on the commits.*?:\s*\n?",
        r"^Here's? .*? changelog.*?:\s*\n?",
        r"^.*comprehensive changelog.*?:\s*\n?",
        r"^.*changelog entry.*?:\s*\n?",
        r"^.*following.*change.*?:\s*\n?",
        r"^.*version.*include.*?:\s*\n?",
        r"^.*summary of changes.*?:\s*\n?",
        r"^.*changes made.*?:\s*\n?",
    ]

    for pattern in explanatory_patterns:
        content = re.sub(pattern, "", content, flags=re.MULTILINE | re.IGNORECASE)

    # Remove any remaining lines that are purely explanatory
    lines = content.split("\n")
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        # Skip lines that look like explanatory text
        if (
            stripped
            and not stripped.startswith("###")
            and not stripped.startswith("-")
            and not stripped.startswith("*")
            and any(
                phrase in stripped.lower()
                for phrase in [
                    "based on",
                    "here is",
                    "here's",
                    "changelog for",
                    "version",
                    "following changes",
                    "summary",
                    "commits",
                    "entry for",
                ]
            )
            and len(stripped) > 30
        ):  # Only remove longer explanatory lines
            continue
        cleaned_lines.append(line)

    content = "\n".join(cleaned_lines)

    # Clean up any XML tags that might have leaked
    xml_tags = [
        "<thinking>",
        "</thinking>",
        "<analysis>",
        "<summary>",
        "</summary>",
        "<changelog>",
        "</changelog>",
        "<entry>",
        "</entry>",
        "<version>",
        "</version>",
    ]

    for tag in xml_tags:
        content = content.replace(tag, "")

    # Normalize whitespace
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = content.strip()

    # Ensure sections have proper spacing
    content = re.sub(r"\n(### [^\n]+)\n([^\n])", r"\n\1\n\n\2", content)

    # Normalize section headers to use ### format consistently
    content = re.sub(r"^##\s+([A-Z][a-z]+)", r"### \1", content, flags=re.MULTILINE)

    # Normalize bullet points to use consistent format (- instead of *)
    content = re.sub(r"^\*\s+", "- ", content, flags=re.MULTILINE)

    # Clean up the content using our new postprocessing module
    from kittylog.postprocess import postprocess_changelog_content

    content = postprocess_changelog_content(content)

    return content


def categorize_commit_by_message(message: str) -> str:
    """Categorize a commit based on its message.

    Args:
        message: The commit message

    Returns:
        Category string (Added, Changed, Fixed, etc.)
    """
    message_lower = message.lower()
    first_line = message.split("\n")[0].lower()

    # Conventional commit patterns
    if any(word in first_line for word in ["feat:", "feature:"]):
        return "Added"
    elif any(word in first_line for word in ["fix:", "bugfix:", "hotfix:"]):
        return "Fixed"
    elif any(word in first_line for word in ["break:", "breaking:"]):
        return "Changed"
    elif any(word in first_line for word in ["remove:", "delete:"]):
        return "Removed"
    elif any(word in first_line for word in ["deprecate:"]):
        return "Deprecated"
    elif any(word in first_line for word in ["security:", "sec:"]):
        return "Security"

    # Keyword-based detection
    if any(word in message_lower for word in ["add", "new", "implement", "introduce"]):
        return "Added"
    elif any(word in message_lower for word in ["fix", "bug", "issue", "problem", "error"]):
        return "Fixed"
    elif any(word in message_lower for word in ["remove", "delete", "drop"]):
        return "Removed"
    elif any(word in message_lower for word in ["update", "change", "modify", "improve", "enhance"]):
        return "Changed"
    elif any(word in message_lower for word in ["deprecate"]):
        return "Deprecated"
    elif any(word in message_lower for word in ["security", "vulnerability", "cve"]):
        return "Security"

    # Default to Changed for other modifications
    return "Changed"
