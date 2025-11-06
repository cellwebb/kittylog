"""Changelog file I/O operations for kittylog.

This module handles reading, writing, and basic file operations
for changelog files.
"""

import logging
from pathlib import Path

# create_changelog_header is defined below to avoid circular import

logger = logging.getLogger(__name__)


def create_changelog_header(include_unreleased: bool = True) -> str:
    """Create a standard changelog header.

    Args:
        include_unreleased: Whether to include an unreleased section

    Returns:
        String containing the changelog header
    """
    header = "# Changelog\n\n"
    header += "All notable changes to this project will be documented in this file.\n\n"
    header += "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), "
    header += "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"

    if include_unreleased:
        header += "## [Unreleased]\n\n"
        header += "### Added\n\n"
        header += "### Changed\n\n"
        header += "### Fixed\n\n"

    return header


def read_changelog(file_path: str) -> str:
    """Read the contents of a changelog file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.info(f"Changelog file {file_path} not found, will create new one")
        return ""
    except Exception as e:
        logger.error(f"Error reading changelog file: {e}")
        raise


def write_changelog(file_path: str, content: str) -> None:
    """Write content to a changelog file.

    Args:
        file_path: Path to the changelog file
        content: Content to write to the file
    """
    try:
        # Create directory if it doesn't exist
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Successfully wrote changelog to {file_path}")
    except Exception as e:
        logger.error(f"Error writing changelog file: {e}")
        raise


def ensure_changelog_exists(file_path: str, no_unreleased: bool = False) -> str:
    """Ensure a changelog file exists, creating it with a header if needed.

    Args:
        file_path: Path to the changelog file
        no_unreleased: Whether to include an unreleased section in new files

    Returns:
        The content of the changelog file (original or newly created)
    """
    existing_content = read_changelog(file_path)

    # If changelog doesn't exist, create header
    if not existing_content.strip():
        changelog_content = create_changelog_header(include_unreleased=not no_unreleased)
        logger.info("Created new changelog header")
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

    except Exception as e:
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

    except Exception as e:
        logger.error(f"Failed to get changelog stats: {e}")
        return {"error": str(e)}
