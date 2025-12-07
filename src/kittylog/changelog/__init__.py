"""Changelog package for kittylog.

This package provides changelog operations organized by concern:

- **boundaries**: Boundary detection and version checking
  - find_existing_boundaries, extract_version_boundaries
  - get_latest_version_in_changelog, is_version_in_changelog

- **insertion**: Insertion point detection
  - find_insertion_point, find_insertion_point_by_version
  - find_unreleased_section, find_end_of_unreleased_section, find_version_section

- **content**: Content manipulation
  - limit_bullets_in_sections, extract_preceding_entries

- **io**: File I/O operations
  - read_changelog, write_changelog, ensure_changelog_exists
  - create_changelog_header, backup_changelog, validate_changelog_format

- **updater**: Update logic and entry insertion
  - update_changelog, handle_version_update, handle_unreleased_section_update
"""
