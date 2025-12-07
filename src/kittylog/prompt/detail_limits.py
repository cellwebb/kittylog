"""Detail limit configuration for changelog prompts.

This module provides functions to configure bullet point limits
based on the desired detail level (concise, normal, detailed).
"""


def get_detail_limits(detail_level: str) -> dict[str, int | str]:
    """Get bullet limits based on detail level.

    Args:
        detail_level: One of 'concise', 'normal', or 'detailed'

    Returns:
        Dictionary with 'per_section', 'total', and 'instruction' keys
    """
    limits: dict[str, dict[str, int | str]] = {
        "concise": {
            "per_section": 2,
            "total": 6,
            "instruction": "Be extremely brief. Only mention the most critical changes.",
        },
        "normal": {
            "per_section": 3,
            "total": 10,
            "instruction": "Balance completeness with brevity. Combine related changes.",
        },
        "detailed": {
            "per_section": 5,
            "total": 15,
            "instruction": "Be comprehensive but still prioritize important changes.",
        },
    }
    return limits.get(detail_level, limits["normal"])


def build_detail_limit_section(detail_level: str) -> str:
    """Build the detail limit section for prompts.

    Args:
        detail_level: One of 'concise', 'normal', or 'detailed'

    Returns:
        Formatted string with strict bullet limits
    """
    limits = get_detail_limits(detail_level)
    return f"""
## ⚠️ CRITICAL OUTPUT LIMITS - STRICTLY ENFORCED

YOU MUST NOT EXCEED THESE LIMITS - THIS IS MANDATORY:
- Maximum bullets PER SECTION: {limits["per_section"]}
- Maximum bullets in ENTIRE RESPONSE: {limits["total"]}
- {limits["instruction"]}

If you have more changes than allowed:
1. COMBINE related items into single bullets
2. PRIORITIZE the most important/impactful changes
3. DROP trivial changes (typos, minor refactors, formatting)

VIOLATION OF THESE LIMITS WILL CAUSE YOUR RESPONSE TO BE REJECTED.
COUNT YOUR BULLETS BEFORE RESPONDING.

"""
