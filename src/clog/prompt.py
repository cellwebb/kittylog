"""Prompt generation for changelog AI processing.

This module creates prompts for AI models to generate changelog entries from git commit data.
"""

import logging
import re

logger = logging.getLogger(__name__)


def build_changelog_prompt(
    commits: list[dict],
    tag: str,
    from_tag: str | None = None,
    hint: str = "",
) -> tuple[str, str]:
    """Build prompts for AI changelog generation.

    Args:
        commits: List of commit dictionaries
        tag: The target tag/version
        from_tag: The previous tag (for context)
        hint: Additional context hint

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(commits, tag, from_tag, hint)

    return system_prompt, user_prompt


def _build_system_prompt() -> str:
    """Build the system prompt with instructions for changelog generation."""
    return """You are an expert technical writer specializing in creating clear, comprehensive changelog entries from git commit history. Your task is to analyze commits and generate well-structured changelog entries following the "Keep a Changelog" format.

## Instructions

1. **Analyze the commits** to understand the changes made in this version
2. **Categorize changes** into appropriate sections:
   - **Added** for new features
   - **Changed** for changes in existing functionality\n
   - **Deprecated** for soon-to-be removed features
   - **Removed** for now removed features
   - **Fixed** for any bug fixes
   - **Security** for vulnerability fixes

3. **Write clear, user-focused descriptions** that explain:
   - What changed from a user's perspective
   - Why the change matters
   - Any important technical details

4. **Follow these conventions**:
   - Use present tense ("Add feature" not "Added feature")
   - Start entries with action verbs
   - Be specific and descriptive
   - Group related changes together
   - Prioritize user-facing changes over internal refactoring
   - Include breaking changes prominently

5. **Format requirements**:
   - Use markdown formatting
   - Use bullet points (- ) for individual changes
   - Do not include the version header (## [x.x.x])
   - Do not include dates
   - Start directly with the category sections

## Example Output Format

### Added

- New user authentication system with OAuth2 support
- Dashboard widgets for real-time monitoring
- Export functionality for reports in PDF and CSV formats

### Changed

- Improved performance of search functionality by 50%
- Updated user interface with modern design system
- Enhanced error messages to be more descriptive

### Fixed

- Fixed issue where users couldn't save preferences
- Resolved memory leak in background processing
- Corrected timezone handling in date displays

## Guidelines

- Focus on changes that matter to users and developers
- Combine similar commits into coherent feature descriptions
- Omit trivial commits (typo fixes, formatting changes) unless they're significant
- Highlight breaking changes and migrations clearly
- Use technical terms appropriately for the audience
- Be concise but informative"""


def _build_user_prompt(
    commits: list[dict],
    tag: str,
    from_tag: str | None = None,
    hint: str = "",
) -> str:
    """Build the user prompt with commit data."""

    # Start with version context
    if tag is None:
        version_context = "Generate a changelog entry for unreleased changes"
    else:
        version_context = f"Generate a changelog entry for version {tag.lstrip('v')}"
    if from_tag:
        # Handle case where from_tag might be None
        from_tag_display = from_tag.lstrip('v') if from_tag is not None else 'beginning'
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

Analyze the above commits and generate a well-structured changelog entry. Focus on:
1. User-facing changes and their impact
2. Important technical improvements
3. Bug fixes and their effects
4. Any breaking changes or migration notes

Group related commits together and write clear, descriptive entries that help users understand what's new and what's changed."""

    return version_context + hint_section + commits_section + instructions


def clean_changelog_content(content: str) -> str:
    """Clean and format AI-generated changelog content.

    Args:
        content: Raw AI-generated content

    Returns:
        Cleaned and formatted changelog content
    """
    if not content:
        return ""

    # Remove any version headers that might have been included
    content = re.sub(r"^##\s*\[?v?\d+\.\d+\.\d+[^\n]*\n?", "", content, flags=re.MULTILINE)

    # Remove any date stamps
    content = re.sub(r"- \d{4}-\d{2}-\d{2}[^\n]*\n?", "", content, flags=re.MULTILINE)

    # Clean up any XML tags that might have leaked
    xml_tags = [
        "<thinking>",
        "</thinking>",
        "<analysis>",
        "</analysis>",
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
