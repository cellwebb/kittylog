"""Changelog package for kittylog.

This package provides a clean, organized separation of concerns for changelog operations:
- io: File I/O operations (read, write, create header)
- parser: Parsing and analysis functions (boundaries, insertion points, extraction)
- updater: Update logic and entry insertion

For backward compatibility, all functions are re-exported from their original locations.
"""

# Import functions from submodules and re-export for backward compatibility
from kittylog.changelog.io import (
    backup_changelog,
    create_changelog_header,
    ensure_changelog_exists,
    get_changelog_stats,
    prepare_release,
    read_changelog,
    validate_changelog_format,
    write_changelog,
)
from kittylog.changelog.parser import (
    extract_preceding_entries,
    extract_version_boundaries,
    find_end_of_unreleased_section,
    find_existing_boundaries,
    find_insertion_point,
    find_insertion_point_by_version,
    find_unreleased_section,
    find_version_section,
    get_latest_version_in_changelog,
    is_version_in_changelog,
    limit_bullets_in_sections,
)
from kittylog.changelog.updater import (
    handle_unreleased_section_update,
    handle_version_update,
    remove_unreleased_sections,
    update_changelog,
)

# Public API exports for backward compatibility
__all__ = [
    "backup_changelog",
    "create_changelog_header",
    "ensure_changelog_exists",
    "extract_preceding_entries",
    "extract_version_boundaries",
    "find_end_of_unreleased_section",
    "find_existing_boundaries",
    "find_insertion_point",
    "find_insertion_point_by_version",
    "find_unreleased_section",
    "find_version_section",
    "get_changelog_stats",
    "get_latest_version_in_changelog",
    "handle_unreleased_section_update",
    "handle_version_update",
    "is_version_in_changelog",
    "limit_bullets_in_sections",
    "prepare_release",
    "read_changelog",
    "remove_unreleased_sections",
    "update_changelog",
    "validate_changelog_format",
    "write_changelog",
]
