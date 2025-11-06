#!/usr/bin/env python3
"""Business logic for kittylog.

Main entry point that coordinates workflow orchestration.

This module has been refactored to focus on coordination while delegating
specific workflow logic to specialized modules.
"""

import logging

from kittylog.changelog import read_changelog, update_changelog, write_changelog
from kittylog.config import load_config
from kittylog.workflow import main_business_logic

logger = logging.getLogger(__name__)

# Re-export the main business logic function for backward compatibility
__all__ = ["main_business_logic", "update_changelog", "read_changelog", "write_changelog"]


# For backward compatibility, expose the main function at module level
def main(*args, **kwargs):
    """Backward compatibility wrapper for main_business_logic."""
    return main_business_logic(*args, **kwargs)


# Also re-export with the original name for imports that expect it
main_business_logic = main_business_logic

# For backward compatibility, expose commonly-used objects
config = load_config()
