"""User prompt generation for changelog AI processing.

This module builds the user prompt with commit data and context.
"""

from kittylog.constants import Audiences
from kittylog.prompt.json_schema import AUDIENCE_SCHEMAS, SECTION_ORDER


def _get_section_names_for_audience(audience: str) -> str:
    """Get the section names used for a specific audience.

    Args:
        audience: The target audience ('developers', 'users', 'stakeholders')

    Returns:
        Comma-separated string of section names
    """
    schema = AUDIENCE_SCHEMAS.get(audience, AUDIENCE_SCHEMAS["developers"])
    return ", ".join(schema.values())


def _get_json_keys_for_audience(audience: str) -> list[str]:
    """Get the JSON keys for a specific audience."""
    return SECTION_ORDER.get(audience, SECTION_ORDER["developers"])


def _build_instructions(audience: str) -> str:
    """Build audience-specific instructions for the user prompt."""
    keys = _get_json_keys_for_audience(audience)

    # Build the JSON structure example
    json_keys_str = ", ".join(f'"{k}"' for k in keys)

    if audience == "users":
        focus_items = """1. New features users can try (ONLY if not in previous changelog entries)
2. Improvements to existing functionality
3. Bug fixes that affected users"""
        classification_rules = """- ONLY brand new capabilities go in "whats_new" (check context first!)
- Enhancements/refinements to EXISTING features go in "improvements"
- Resolved issues go in "bug_fixes"
- If a feature was mentioned in previous versions, it's NOT new - use "improvements\""""

    elif audience == "stakeholders":
        focus_items = """1. Key business outcomes and customer value
2. Impact on users and customers
3. Platform stability and improvements"""
        classification_rules = """- Major achievements and wins go in "highlights"
- Changes affecting customers go in "customer_impact"
- Infrastructure and reliability go in "platform_improvements\""""

    else:  # developers
        focus_items = """1. User-facing changes and their impact
2. Important technical improvements
3. Bug fixes and their effects
4. Breaking changes"""
        classification_rules = """- ONLY brand new features/capabilities go in "added" (check context first!)
- Modifications/refinements to EXISTING features go in "changed"
- Soon-to-be-removed features go in "deprecated"
- Removed features go in "removed"
- Bug fixes go in "fixed"
- Security patches go in "security"
- "Refactor X" = Always "changed" (never split across sections)
- "Replace X with Y" = Always "changed"
- If a feature was mentioned in previous versions, it's NOT new - use "changed\""""

    return f"""## Instructions:

Analyze the commits above and respond with a JSON object.

Focus on:
{focus_items}

RESPOND WITH ONLY THIS JSON STRUCTURE:
```json
{{
  {", ".join(f'"{k}": ["item 1", "item 2"]' for k in keys)}
}}
```

RULES:
- Use ONLY these keys: {json_keys_str}
- Each value is an array of strings (the changelog items)
- OMIT keys with no items (empty arrays)
- Each item should be a concise description of the change
- Do NOT include bullet points or markdown in the items

CLASSIFICATION:
{classification_rules}

ANTI-DUPLICATION:
- Each change goes in EXACTLY ONE section
- Never mention the same feature in multiple sections
- If a feature fits multiple categories, pick the most important one

RESPOND WITH ONLY THE JSON OBJECT. No explanations, no markdown formatting outside the JSON."""


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
    session_context: str = "",
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

    # Build language section with audience-appropriate section names
    language_section = ""
    if language:
        section_names = _get_section_names_for_audience(resolved_audience)
        if translate_headings:
            language_section = (
                "CRITICAL LANGUAGE REQUIREMENTS:\n"
                f"- Write the entire changelog (section headings and bullet text) in {language}.\n"
                f"- Translate the section names ({section_names}) while preserving their order.\n"
                "- Keep the markdown syntax (###, bullet lists) unchanged.\n\n"
            )
        else:
            language_section = (
                "CRITICAL LANGUAGE REQUIREMENTS:\n"
                f"- Write all descriptive text and bullet points in {language}.\n"
                f"- KEEP the section headings ({section_names}) in English while translating their content.\n"
                "- Maintain markdown syntax.\n\n"
            )

    # Add context from preceding entries if provided
    context_section = ""
    if context_entries.strip():
        context_section = (
            "🚨 CRITICAL: FEATURES ALREADY ANNOUNCED IN PREVIOUS VERSIONS 🚨\n"
            "The following changelog entries are from PREVIOUS versions. "
            "These features ALREADY EXIST and have ALREADY BEEN ANNOUNCED:\n\n"
            f"{context_entries}\n\n"
            "---\n\n"
            "⛔ STRICT DEDUPLICATION RULES (MUST FOLLOW):\n\n"
            "1. SCAN THE ABOVE ENTRIES FIRST before writing anything\n"
            "2. If a feature appears above (audience options, JSON output, spacing, etc.), "
            "it is NOT NEW - do NOT put it in 'whats_new' or 'added'\n"
            "3. Work on existing features = 'improvements' or 'changed', NEVER 'whats_new' or 'added'\n"
            "4. Bug fixes to existing features = 'bug_fixes' or 'fixed', NEVER 'whats_new' or 'added'\n"
            "5. Only genuinely NEW capabilities that don't exist above go in 'whats_new' or 'added'\n"
            "6. When in doubt, put it in 'improvements' NOT 'whats_new'\n\n"
            "EXAMPLE: If 'audience options' appears above and commits mention audience features, "
            "that goes in 'improvements' as 'Enhanced audience options' NOT in 'whats_new' as 'New audience options'\n\n"
        )

    # Add session context (items already generated in this kittylog run)
    session_section = ""
    if session_context.strip():
        session_section = (
            "⚠️ ITEMS ALREADY WRITTEN IN THIS SESSION ⚠️\n"
            "These items were just generated for OTHER versions in this same kittylog run.\n"
            "DO NOT repeat these items - they are already in the changelog:\n\n"
            f"{session_context}\n\n"
            "If you see similar content in the commits, either SKIP IT or describe a different aspect.\n\n"
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
        + session_section
        + commits_section
        + instructions
    )
