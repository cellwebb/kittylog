"""User prompt generation for changelog AI processing.

This module builds the user prompt with commit data and context.
"""

from kittylog.constants import Audiences


def _build_instructions(audience: str) -> str:
    """Build audience-specific instructions for the user prompt."""
    if audience == "users":
        return """## Instructions:

Generate ONLY the release notes sections for the above commits.

Focus on:
1. New features users can try
2. Improvements to existing functionality
3. Bug fixes that affected users

CRITICAL: OMIT SECTIONS WITHOUT CONTENT
- Only include sections where you have actual changes to report
- Skip empty sections entirely

USE ONLY THESE SECTIONS (in this order):
1. ### What's New
2. ### Improvements
3. ### Bug Fixes

DO NOT use "Added", "Changed", "Fixed", or any other section names.

ANTI-DUPLICATION RULES:
- Each change goes in EXACTLY ONE section
- If something is both new and improved, pick the most important aspect
- Never mention the same feature in multiple sections

REMEMBER: Respond with ONLY release notes sections. No explanations or commentary.
REMEMBER: Use ONLY "What's New", "Improvements", "Bug Fixes" as section headers."""

    elif audience == "stakeholders":
        return """## Instructions:

Generate ONLY the release notes sections for the above commits.

Focus on:
1. Key business outcomes and customer value
2. Impact on users and customers
3. Platform stability and improvements

CRITICAL: OMIT SECTIONS WITHOUT CONTENT
- Only include sections where you have actual changes to report
- Skip empty sections entirely

USE ONLY THESE SECTIONS (in this order):
1. ### Highlights
2. ### Customer Impact
3. ### Platform Improvements

DO NOT use "Added", "Changed", "Fixed", or any other section names.

ANTI-DUPLICATION RULES:
- Each change goes in EXACTLY ONE section
- Lead with business impact, not technical details
- Never mention the same outcome in multiple sections

REMEMBER: Respond with ONLY release notes sections. No explanations or commentary.
REMEMBER: Use ONLY "Highlights", "Customer Impact", "Platform Improvements" as section headers."""

    else:  # developers (default)
        return """## Instructions:

Generate ONLY the changelog sections for the above commits.

Focus on:
1. User-facing changes and their impact
2. Important technical improvements
3. Bug fixes and their effects
4. Breaking changes

CRITICAL: OMIT SECTIONS WITHOUT CONTENT
- If there are no bug fixes, DO NOT include the "### Fixed" section at all
- If there are no security updates, DO NOT include the "### Security" section at all
- DO NOT write placeholder text like "No bug fixes implemented"
- ONLY include sections where you have actual changes to report

CRITICAL ANTI-DUPLICATION RULES:
- Each change goes in EXACTLY ONE section - never duplicate across sections
- Choose the PRIMARY impact of each change and ignore secondary effects
- CROSS-VERSION DEDUPLICATION: If a feature already exists in context entries, put updates in Changed, not Added

MANDATORY SECTION ORDER (use only these, in this order):
1. ### Added (first)
2. ### Changed (second)
3. ### Deprecated (third)
4. ### Removed (fourth)
5. ### Fixed (fifth)
6. ### Security (sixth)

CLASSIFICATION RULES:
- "Refactor X" = Always Changed (never Added + Removed + Fixed)
- "Replace X with Y" = Always Changed (never Added + Removed)
- "Update/Upgrade X" = Always Changed
- Only use "Fixed" for actual bugs/broken behavior

REMEMBER: Respond with ONLY changelog sections. No explanations, introductions, or commentary.
REMEMBER: Each concept can only appear ONCE in the entire changelog entry."""


def build_user_prompt(
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
        version_context = "Generate a changelog entry for unreleased changes.\n"
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
                "- Keep the markdown syntax (###, bullet lists) unchanged.\n\n"
            )
        else:
            language_section = (
                "CRITICAL LANGUAGE REQUIREMENTS:\n"
                f"- Write all descriptive text and bullet points in {language}.\n"
                "- KEEP the section headings (### Added, ### Changed, etc.) in English while translating their content.\n"
                "- Maintain markdown syntax.\n\n"
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
            "CRITICAL CONTEXT - WHAT'S ALREADY IN THE CHANGELOG:\n"
            "These are the most recent changelog entries from previous versions. "
            "They represent features and changes that have ALREADY BEEN ANNOUNCED:\n\n"
            f"{context_entries}\n\n"
            "---\n\n"
            "⚠️ MANDATORY DEDUPLICATION RULE:\n"
            "- If ANY feature, improvement, or fix in the above entries is related to the commits you're analyzing, "
            "do NOT announce it as brand new\n"
            "- If a feature from the context appears in current commits, treat it as an update/improvement\n"
            "- NEVER re-announce something already documented above as if it's new\n"
            "- Use the above entries as a reference for formatting, tone, and level of detail\n"
            "- Maintain consistency with the existing changelog style\n\n"
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

    # Instructions - audience-specific
    instructions = _build_instructions(resolved_audience)

    return (
        version_context
        + hint_section
        + language_section
        + audience_section
        + context_section
        + commits_section
        + instructions
    )
