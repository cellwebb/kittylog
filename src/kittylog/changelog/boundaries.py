"""Boundary detection and version checking for changelog content.

This module handles finding existing boundaries (versions, dates, gaps)
and checking version existence in changelog files.
"""

import logging
import re

logger = logging.getLogger(__name__)


def find_existing_boundaries(content: str) -> set[str]:
    """Find all existing boundaries in the changelog content.

    Args:
        content: The changelog content as a string

    Returns:
        Set of existing boundary identifiers (excluding 'unreleased')
    """
    existing_boundaries = set()
    lines = content.split("\n")

    for line in lines:
        # Match patterns like ## [0.1.0], ## [v0.1.0], ## [Unreleased], ## [2024-01-15], ## [Gap-2024-01-15], etc.
        # Handle nested brackets like ## [[2024-01-03] - January 03, 2024]
        match = re.match(r"##\s*\[+\s*([^\]]+)\s*\]+", line, re.IGNORECASE)
        if match:
            boundary = match.group(1).strip()
            # Skip unreleased section
            if boundary.lower() != "unreleased":
                # For version boundaries, strip 'v' prefix for consistency
                if re.match(r"v?\d+\.\d+", boundary):
                    boundary = boundary.lstrip("v")
                existing_boundaries.add(boundary)

    logger.debug(f"Found existing boundaries: {existing_boundaries}")
    return existing_boundaries


def extract_version_boundaries(content: str) -> list[dict]:
    """Extract version boundaries from changelog content.

    Args:
        content: The changelog content

    Returns:
        List of version boundary dictionaries
    """
    lines = content.split("\n")
    boundaries = []

    for i, line in enumerate(lines):
        match = re.match(r"##\s*\[\s*([^\]]+)\s*\]", line, re.IGNORECASE)
        if match:
            version = match.group(1).strip()
            if version.lower() != "unreleased" and re.match(r"v?\d+\.\d+", version):
                boundaries.append(
                    {
                        "identifier": version,
                        "line": i,
                        "raw_line": line,
                    }
                )

    return boundaries


def get_latest_version_in_changelog(content: str) -> str | None:
    """Get the latest version from changelog content.

    Args:
        content: The changelog content

    Returns:
        The latest version string or None if not found
    """
    boundaries = extract_version_boundaries(content)
    if not boundaries:
        return None

    # Return the first version (which should be the latest in Keep a Changelog format)
    return boundaries[0]["identifier"]


def is_version_in_changelog(content: str, version: str) -> bool:
    """Check if a version exists in the changelog.

    Args:
        content: The changelog content
        version: The version to check

    Returns:
        True if version exists, False otherwise
    """
    boundaries = extract_version_boundaries(content)
    version_patterns = [
        version,
        version.lstrip("v"),
        f"v{version}" if not version.startswith("v") else version,
    ]

    for boundary in boundaries:
        boundary_version = boundary["identifier"]
        if boundary_version in version_patterns:
            return True

    return False
