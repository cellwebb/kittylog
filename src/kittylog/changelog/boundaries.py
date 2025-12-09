"""Boundary detection and version checking for changelog content.

This module handles finding existing boundaries (versions, dates, gaps)
and checking version existence in changelog files.

Boundary Types:
- Version: semantic version like 1.0.0, v1.0.0, v1.0.0-beta.1
- Date: YYYY-MM-DD pattern
- Gap: anything starting with "Gap-"
- Custom: other bracketed H2 headers (excluding invalid version-like patterns)
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import NamedTuple

from kittylog.utils.text import is_semantic_version

logger = logging.getLogger(__name__)

# Regex patterns for boundary detection
# Pattern for proper double brackets: ## [[content]]
_DOUBLE_BRACKET_PATTERN = re.compile(r"^##\s*\[\[(.+?)\]\]\s*[-]?\s*(.*)$", re.IGNORECASE)
# Pattern for nested bracket edge case: ## [[date] - description] (single closing bracket)
_NESTED_BRACKET_PATTERN = re.compile(r"^##\s*\[\[(.+?)\]\s*-\s*(.+?)\]\s*$", re.IGNORECASE)
# Pattern for single brackets: ## [content]
_SINGLE_BRACKET_PATTERN = re.compile(r"^##\s*\[([^\]]+)\]\s*[-]?\s*(.*)$", re.IGNORECASE)
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INVALID_VERSION_PATTERNS = [
    re.compile(r"^\d+\.\d+$"),  # Two-part version like "1.0"
    re.compile(r"^\d+(?:\.\d+){3,}$"),  # Four+ part version like "1.0.0.0"
    re.compile(r"^v\d+\.\d+$"),  # v-prefixed two-part like "v1.0"
    re.compile(r"^v\d+(?:\.\d+){3,}$"),  # v-prefixed four+ part like "v1.0.0.0"
]

# Keywords that indicate a failed version attempt when combined with dashes
_VERSION_KEYWORDS = frozenset(["version", "ver", "v", "release"])


class BoundaryType(Enum):
    """Types of changelog boundaries."""

    VERSION = auto()
    DATE = auto()
    GAP = auto()
    CUSTOM = auto()
    UNRELEASED = auto()
    INVALID = auto()


class ParsedBoundary(NamedTuple):
    """A parsed boundary from changelog content.

    Attributes:
        content: The main boundary content (inside brackets)
        trailing_text: Any text after the closing bracket and dash
        is_double_bracket: Whether the boundary used [[...]] format
        boundary_type: Classified type of the boundary
    """

    content: str
    trailing_text: str
    is_double_bracket: bool
    boundary_type: BoundaryType


def _looks_like_failed_version(content: str) -> bool:
    """Check if content looks like a failed version attempt.

    This catches boundaries that contain version-related keywords combined
    with dashes, which typically indicate malformed version strings.

    Args:
        content: The boundary content

    Returns:
        True if this looks like a failed version attempt
    """
    if "-" not in content:
        return False
    content_lower = content.lower()
    return any(keyword in content_lower for keyword in _VERSION_KEYWORDS)


def _classify_boundary(content: str, is_double_bracket: bool) -> BoundaryType:
    """Classify the type of a boundary based on its content.

    Args:
        content: The boundary content (text inside brackets)
        is_double_bracket: Whether this was a [[...]] boundary

    Returns:
        The classified BoundaryType
    """
    if content.lower() == "unreleased":
        return BoundaryType.UNRELEASED

    if is_semantic_version(content):
        return BoundaryType.VERSION

    if _DATE_PATTERN.match(content):
        return BoundaryType.DATE

    if content.startswith("Gap-"):
        return BoundaryType.GAP

    # Check for invalid version-like patterns
    for pattern in _INVALID_VERSION_PATTERNS:
        if pattern.match(content):
            return BoundaryType.INVALID

    # Check for failed version attempts (e.g., "not-a-version")
    if _looks_like_failed_version(content):
        return BoundaryType.INVALID

    return BoundaryType.CUSTOM


def _parse_line(line: str) -> ParsedBoundary | None:
    """Parse a single line to extract boundary information.

    Args:
        line: A line from the changelog

    Returns:
        ParsedBoundary if line is a boundary header, None otherwise
    """
    # Try double bracket pattern first [[content]]
    match = _DOUBLE_BRACKET_PATTERN.match(line)
    if match:
        content = match.group(1).strip()
        trailing = match.group(2).strip() if match.group(2) else ""
        return ParsedBoundary(
            content=content,
            trailing_text=trailing,
            is_double_bracket=True,
            boundary_type=_classify_boundary(content, is_double_bracket=True),
        )

    # Try nested bracket edge case: ## [[date] - description] (malformed double bracket)
    # This handles cases like "## [[2024-01-15] - January 15, 2024]"
    match = _NESTED_BRACKET_PATTERN.match(line)
    if match:
        inner_content = match.group(1).strip()  # e.g., "2024-01-15"
        description = match.group(2).strip()  # e.g., "January 15, 2024"

        # Check if inner content is a date - if so, return just the date
        if _DATE_PATTERN.match(inner_content):
            return ParsedBoundary(
                content=inner_content,
                trailing_text=description,
                is_double_bracket=True,
                boundary_type=BoundaryType.DATE,
            )

        # Otherwise, reconstruct as "[content] - description" for custom boundaries
        content = f"[{inner_content}] - {description}"
        return ParsedBoundary(
            content=content,
            trailing_text="",
            is_double_bracket=True,
            boundary_type=BoundaryType.CUSTOM,
        )

    # Try single bracket pattern [content]
    match = _SINGLE_BRACKET_PATTERN.match(line)
    if match:
        content = match.group(1).strip()
        trailing = match.group(2).strip() if match.group(2) else ""
        return ParsedBoundary(
            content=content,
            trailing_text=trailing,
            is_double_bracket=False,
            boundary_type=_classify_boundary(content, is_double_bracket=False),
        )

    return None


def _normalize_boundary(boundary: ParsedBoundary) -> str | None:
    """Normalize a parsed boundary to its canonical string representation.

    Args:
        boundary: A parsed boundary

    Returns:
        Normalized string representation, or None if boundary should be excluded
    """
    # Skip unreleased and invalid boundaries
    if boundary.boundary_type in (BoundaryType.UNRELEASED, BoundaryType.INVALID):
        return None

    content = boundary.content
    trailing = boundary.trailing_text

    # Version boundaries: strip 'v' prefix for consistency
    if boundary.boundary_type == BoundaryType.VERSION:
        if boundary.is_double_bracket:
            # Double-bracketed versions preserve with single brackets
            if trailing:
                return f"[{content}] - {trailing}"
            return f"[{content}]"
        # Single-bracket versions: just return the version without 'v'
        return content.lstrip("v")

    # Date boundaries: return just the date
    if boundary.boundary_type == BoundaryType.DATE:
        return content

    # Gap boundaries: return full content
    if boundary.boundary_type == BoundaryType.GAP:
        return content

    # Custom boundaries (double-bracketed): content already contains the inner brackets
    # e.g., content="[2024-01-15] - January 15, 2024" -> return as-is
    if boundary.is_double_bracket:
        return content

    # Custom boundaries (single-bracketed): include trailing if present
    if trailing:
        return f"{content} - {trailing}"
    return content


def find_existing_boundaries(content: str) -> set[str]:
    """Find all existing boundaries in the changelog content.

    Args:
        content: The changelog content as a string

    Returns:
        Set of existing boundary identifiers (excluding 'unreleased')
    """
    existing_boundaries: set[str] = set()

    for line in content.split("\n"):
        parsed = _parse_line(line)
        if parsed is None:
            continue

        normalized = _normalize_boundary(parsed)
        if normalized is not None:
            existing_boundaries.add(normalized)

    logger.debug(f"Found existing boundaries: {existing_boundaries}")
    return existing_boundaries


@dataclass
class VersionBoundary:
    """A version boundary with its location in the changelog.

    Attributes:
        identifier: The version string (may include 'v' prefix)
        line: Line number in the file (1-based)
        raw_line: The original line text
    """

    identifier: str
    line: int
    raw_line: str


def extract_version_boundaries(content: str) -> list[dict]:
    """Extract version boundaries from changelog content.

    Args:
        content: The changelog content

    Returns:
        List of version boundary dictionaries with keys:
        - identifier: version string
        - line: line number (1-based)
        - raw_line: original line text
    """
    lines = content.split("\n")
    boundaries: list[dict] = []

    for i, line in enumerate(lines):
        parsed = _parse_line(line)
        if parsed is None:
            continue

        # Skip non-version boundaries
        if parsed.boundary_type != BoundaryType.VERSION:
            continue

        # Calculate line number (first boundary gets i+1, others get i+2)
        # This quirky behavior is preserved for backward compatibility
        line_num = i + 1 if len(boundaries) == 0 else i + 2

        boundaries.append(
            {
                "identifier": parsed.content,
                "line": line_num,
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

    # Return the first version (latest in Keep a Changelog format)
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

    # Normalize the search version for comparison
    version_patterns = [
        version,
        version.lstrip("v"),
        f"v{version}" if not version.startswith("v") else version,
    ]

    return any(boundary["identifier"] in version_patterns for boundary in boundaries)
