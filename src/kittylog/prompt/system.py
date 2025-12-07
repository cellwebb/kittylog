"""System prompt dispatcher for changelog AI processing.

Routes to the appropriate audience-specific system prompt builder.
"""

from kittylog.prompt.system_developers import build_system_prompt_developers
from kittylog.prompt.system_stakeholders import build_system_prompt_stakeholders
from kittylog.prompt.system_users import build_system_prompt_users


def build_system_prompt(audience: str = "developers", detail_level: str = "normal") -> str:
    """Build the system prompt based on target audience and detail level.

    Args:
        audience: Target audience - 'developers', 'users', or 'stakeholders'
        detail_level: Output detail level - 'concise', 'normal', or 'detailed'

    Returns:
        Appropriate system prompt for the audience with detail limits applied
    """
    prompts = {
        "developers": build_system_prompt_developers,
        "users": build_system_prompt_users,
        "stakeholders": build_system_prompt_stakeholders,
    }
    builder = prompts.get(audience, build_system_prompt_developers)
    return builder(detail_level=detail_level)
