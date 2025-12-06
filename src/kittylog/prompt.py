"""Prompt generation for changelog AI processing.

This module creates prompts for AI models to generate changelog entries from git commit data.
"""

from kittylog.constants import Audiences
from kittylog.prompt_cleaning import categorize_commit_by_message, clean_changelog_content
from kittylog.prompt_templates import _build_system_prompt, _build_user_prompt


def build_changelog_prompt(
    commits: list[dict],
    tag: str | None,
    from_boundary: str | None = None,
    hint: str = "",
    boundary_mode: str = "tags",
    language: str | None = None,
    translate_headings: bool = False,
    audience: str | None = None,
    context_entries: str = "",
    detail_level: str = "normal",
) -> tuple[str, str]:
    """Build prompts for AI changelog generation.

    Args:
        commits: List of commit dictionaries
        tag: The target boundary identifier
        from_boundary: The previous boundary identifier (for context)
        hint: Additional context hint
        boundary_mode: The boundary mode ('tags', 'dates', 'gaps')
        language: Optional language for the generated changelog
        translate_headings: Whether to translate section headings into the selected language
        audience: Target audience slug controlling tone and emphasis
        context_entries: Pre-formatted string of preceding changelog entries for style reference
        detail_level: Output detail level - 'concise', 'normal', or 'detailed'

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Resolve audience to canonical slug
    resolved_audience = Audiences.resolve(audience) if audience else "developers"
    system_prompt = _build_system_prompt(audience=resolved_audience, detail_level=detail_level)
    user_prompt = _build_user_prompt(
        commits,
        tag,
        from_boundary,
        hint,
        boundary_mode,
        language=language,
        translate_headings=translate_headings,
        audience=audience,
        context_entries=context_entries,
    )

    return system_prompt, user_prompt


# Re-export functions for backward compatibility
__all__ = [
    "build_changelog_prompt",
    "categorize_commit_by_message",
    "clean_changelog_content",
]
