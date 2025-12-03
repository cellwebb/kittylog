"""Mode handlers for kittylog.

This module provides a unified interface to all mode handler functions.
"""

# Import all mode handler functions from specialized modules
from .mode_handlers import (
    determine_missing_entries,
    handle_boundary_range_mode,
    handle_missing_entries_mode,
    handle_single_boundary_mode,
    handle_unreleased_mode,
    handle_update_all_mode,
)

# Re-export everything for backward compatibility
__all__ = [
    "determine_missing_entries",
    "handle_boundary_range_mode",
    "handle_missing_entries_mode",
    "handle_single_boundary_mode",
    "handle_unreleased_mode",
    "handle_update_all_mode",
]
