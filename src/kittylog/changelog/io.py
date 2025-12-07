"""Changelog file I/O operations for kittylog.

This module handles reading, writing, and basic file operations
for changelog files.
"""

import logging
from pathlib import Path

from kittylog.errors import ChangelogError

logger = logging.getLogger(__name__)


def create_changelog_header() -> str:
    """Create a minimal changelog header.

    Returns:
        String containing the changelog header
    """
    return "# Changelog\n\n"


def read_changelog(file_path: str) -> str:
    """Read the contents of a changelog file."""
    try:
        return Path(file_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.info(f"Changelog file {file_path} not found, will create new one")
        return ""
    except (OSError, UnicodeDecodeError) as e:
        logger.error(f"Error reading changelog file: {e}")
        raise


def _ensure_spacing_between_entries(content: str) -> str:
    """Ensure proper spacing in changelog content.

    - Exactly 1 blank line after # Changelog header
    - Exactly 1 blank line between version entries

    Args:
        content: Changelog content

    Returns:
        Content with proper spacing
    """
    import re

    # Normalize spacing after # Changelog header (exactly 1 blank line before first ## [)
    content = re.sub(
        r"(^# Changelog)\n+(?=## \[)",  # Header followed by newlines before ## [
        r"\1\n\n",  # Replace with exactly 1 blank line
        content,
        flags=re.MULTILINE,
    )

    # Find version headers preceded by bullet points and ensure 1 blank line before them
    # Pattern matches: bullet point line (starts with -) followed by newlines, then ## [version]
    # We want: bullet line + \n\n + ## [version] (2 newlines = 1 blank line)
    content = re.sub(
        r"(^- [^\n]*)\n+(?=## \[)",  # Bullet point line followed by newlines before ## [
        r"\1\n\n",  # Replace with 1 blank line
        content,
        flags=re.MULTILINE,
    )

    return content


def write_changelog(file_path: str, content: str) -> None:
    """Write content to a changelog file.

    Args:
        file_path: Path to the changelog file
        content: Content to write to the file
    """
    try:
        # Create directory if it doesn't exist
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # Ensure proper spacing between version entries
        content = _ensure_spacing_between_entries(content)

        Path(file_path).write_text(content, encoding="utf-8")

        logger.info(f"Successfully wrote changelog to {file_path}")
    except (PermissionError, FileNotFoundError, OSError) as e:
        logger.error(f"Error writing changelog file: {e}")
        raise ChangelogError(
            f"Failed to write changelog file: {e}",
            file_path=file_path,
        ) from e


def ensure_changelog_exists(file_path: str) -> str:
    """Ensure a changelog file exists, creating it with a header if needed.

    Args:
        file_path: Path to the changelog file

    Returns:
        The content of the changelog file (original or newly created)
    """
    existing_content = read_changelog(file_path)

    # If changelog doesn't exist, create it with just the header
    if not existing_content.strip():
        changelog_content = create_changelog_header()
        write_changelog(file_path, changelog_content)
        logger.info("Created new changelog file with header")
        return changelog_content
    else:
        return existing_content


def backup_changelog(file_path: str) -> str:
    """Create a backup of the changelog file.

    Args:
        file_path: Path to the changelog file

    Returns:
        Path to the backup file
    """
    try:
        original_path = Path(file_path)
        if not original_path.exists():
            logger.warning(f"Changelog file {file_path} does not exist, no backup created")
            return ""

        # Create backup with timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = original_path.with_suffix(f".backup_{timestamp}.md")

        import shutil

        shutil.copy2(original_path, backup_path)

        logger.info(f"Created changelog backup at {backup_path}")
        return str(backup_path)

    except (OSError, shutil.Error) as e:
        logger.error(f"Failed to create changelog backup: {e}")
        raise


def validate_changelog_format(content: str) -> list[str]:
    """Validate the format of changelog content.

    Args:
        content: Changelog content to validate

    Returns:
        List of validation warnings/errors
    """
    warnings: list[str] = []

    if not content.strip():
        return warnings  # Empty content is valid (will be created)

    lines = content.split("\n")

    # Check for header
    if not any("# Changelog" in line for line in lines[:5]):
        warnings.append("Missing changelog header (should contain '# Changelog')")

    # Check for version sections
    version_sections = [line for line in lines if line.startswith("## [")]
    if not version_sections and not any("unreleased" in line.lower() for line in lines):
        warnings.append("No version sections or unreleased section found")

    # Check for Keep a Changelog format
    if content and "### Added" not in content and "### Fixed" not in content:
        warnings.append("No standard sections found (Consider using Added, Changed, Fixed, etc.)")

    return warnings


def get_changelog_stats(file_path: str) -> dict:
    """Get statistics about a changelog file.

    Args:
        file_path: Path to the changelog file

    Returns:
        Dictionary with file statistics
    """
    try:
        content = read_changelog(file_path)
        lines = content.split("\n")

        version_sections = [
            line for line in lines if line.startswith("## [") and not line.lower().startswith("## [unreleased")
        ]
        unreleased_section = any("unreleased" in line.lower() for line in lines)

        # Count standard sections
        section_counts = {}
        standard_sections = ["added", "changed", "deprecated", "removed", "fixed", "security"]
        for section in standard_sections:
            pattern = f"### {section.title()}"
            section_counts[section] = sum(1 for line in lines if pattern in line)

        return {
            "file_path": file_path,
            "exists": Path(file_path).exists(),
            "line_count": len(lines),
            "size_bytes": len(content.encode("utf-8")),
            "version_count": len(version_sections),
            "has_unreleased": unreleased_section,
            "section_counts": section_counts,
        }

    except (OSError, UnicodeDecodeError, ValueError) as e:
        logger.error(f"Failed to get changelog stats: {e}")
        return {"error": str(e)}


def prepare_release(file_path: str, version: str) -> str:
    """Prepare changelog for release by converting Unreleased section to versioned.

    This function:
    1. Replaces "## [Unreleased]" with "## [version] - YYYY-MM-DD"
    2. Adds a version link reference if link references exist in the file

    Args:
        file_path: Path to the changelog file
        version: Version string (e.g., "2.3.0" - without 'v' prefix)

    Returns:
        The updated changelog content
    """
    import re
    from datetime import datetime

    content = read_changelog(file_path)
    if not content:
        raise ChangelogError(
            f"Changelog file {file_path} is empty or does not exist",
            file_path=file_path,
        )

    today = datetime.now().strftime("%Y-%m-%d")

    # Normalize version (remove 'v' prefix if present)
    version = version.lstrip("v")

    # Check if there's an Unreleased section to replace
    if "## [Unreleased]" in content:
        # Replace "## [Unreleased]" with the new version header
        content = re.sub(
            r"## \[Unreleased\]\s*\n",
            f"## [{version}] - {today}\n\n",
            content,
            count=1,
        )
        logger.info(f"Converted [Unreleased] section to [{version}] - {today}")
    else:
        logger.warning("No [Unreleased] section found in changelog")

    # Extract link format from existing link and add new one if links exist
    link_match = re.search(r"\[[\d.]+\]:\s+(.*?)v[\d.]+", content)
    if link_match:
        base_url = link_match.group(1)
        new_link = f"[{version}]: {base_url}v{version}\n"

        # Find the position of the first link reference
        first_link = re.search(r"^\[[\d.]+\]:", content, re.MULTILINE)
        if first_link:
            pos = first_link.start()
            content = content[:pos] + new_link + content[pos:]
            logger.info(f"Added version link reference for {version}")

    write_changelog(file_path, content)
    return content
