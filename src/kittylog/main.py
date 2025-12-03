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

# Re-export the main business logic function
__all__ = ["main_business_logic", "read_changelog", "update_changelog", "write_changelog"]
