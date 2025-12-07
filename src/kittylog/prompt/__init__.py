"""Prompt generation package for changelog AI processing.

This package provides functions to build system and user prompts for AI models
to generate changelog entries from git commit data.
"""

from kittylog.constants import Audiences
from kittylog.prompt.detail_limits import build_detail_limit_section, get_detail_limits
from kittylog.prompt.system import build_system_prompt
from kittylog.prompt.system_developers import build_system_prompt_developers
from kittylog.prompt.system_stakeholders import build_system_prompt_stakeholders
from kittylog.prompt.system_users import build_system_prompt_users
from kittylog.prompt.user import build_user_prompt
from kittylog.prompt_cleaning import categorize_commit_by_message, clean_changelog_content

# Backward compatibility aliases (prefixed with underscore as in original)
_build_system_prompt = build_system_prompt
_build_user_prompt = build_user_prompt
_get_detail_limits = get_detail_limits
_build_detail_limit_section = build_detail_limit_section


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
    "_build_detail_limit_section",
    "_build_system_prompt",
    "_build_user_prompt",
    "_get_detail_limits",
    "build_changelog_prompt",
    "build_detail_limit_section",
    "build_system_prompt",
    "build_system_prompt_developers",
    "build_system_prompt_stakeholders",
    "build_system_prompt_users",
    "build_user_prompt",
    "categorize_commit_by_message",
    "clean_changelog_content",
    "get_detail_limits",
]
