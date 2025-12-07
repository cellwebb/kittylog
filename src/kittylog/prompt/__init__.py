"""Prompt generation package for changelog AI processing.

This package provides functions to build system and user prompts for AI models
to generate changelog entries from git commit data.

Submodules:
- **detail_limits**: Detail level configuration (concise/normal/detailed)
- **system**: System prompt dispatcher
- **system_developers**: Developer audience system prompt
- **system_users**: End user audience system prompt
- **system_stakeholders**: Stakeholder audience system prompt
- **user**: User prompt builder with commit data
"""

from kittylog.constants import Audiences
from kittylog.prompt.system import build_system_prompt
from kittylog.prompt.user import build_user_prompt
from kittylog.prompt_cleaning import clean_changelog_content


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
    resolved_audience = Audiences.resolve(audience) if audience else "developers"
    system_prompt = build_system_prompt(audience=resolved_audience, detail_level=detail_level)
    user_prompt = build_user_prompt(
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


__all__ = [
    "build_changelog_prompt",
    "clean_changelog_content",
]
