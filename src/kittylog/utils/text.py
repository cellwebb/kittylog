"""Text processing utilities for kittylog."""

import re
from pathlib import Path


def count_tokens(text: str, model: str) -> int:
    """Count tokens in text using simple estimation.

    Args:
        text: Text to count tokens in
        model: Model name for tokenization rules

    Returns:
        Estimated token count
    """
    # Simple character-based estimation as fallback
    # This is approximate - real tokenization would use model-specific tokenizers
    chars_per_token: float = 4  # Rough estimate for most models

    # Adjust for different models
    if "claude" in model.lower():
        chars_per_token = 3.5
    elif "gpt" in model.lower():
        chars_per_token = 4

    return max(1, len(text) // int(chars_per_token))


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        suffix: Suffix to add when truncated

    Returns:
        Truncated text or original if under limit
    """
    if len(text) <= max_length:
        return text

    # Find a good break point (space, newline, punctuation)
    truncate_at = max_length - len(suffix)
    break_chars = [" ", "\n", ".", "!", "?"]

    for i in range(truncate_at, max(0, truncate_at - 20), -1):
        if text[i] in break_chars:
            return text[: i + 1] + suffix

    # No good break point, just cut it
    return text[:truncate_at] + suffix


def clean_changelog_content(content: str) -> str:
    """Clean changelog content by removing unwanted artifacts.

    Args:
        content: Raw changelog content

    Returns:
        Cleaned changelog content
    """
    # Handle empty or whitespace-only content
    if not content or not content.strip():
        return ""

    # Remove markdown code blocks around the entire content
    content = re.sub(r"^```(?:markdown)?\s*\n(.*?)\n```\s*$", r"\1", content, flags=re.MULTILINE | re.DOTALL)

    # Remove AI-generated preamble (at the beginning)
    content = re.sub(r"^Here(\'s| is) the changelog[^#]*", "", content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r"^I(\'ll| will) help you.*?\n\n", "", content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r"^I(\'ve| have) generated.*?\n\n", "", content, flags=re.IGNORECASE | re.DOTALL)

    # Remove trailing AI chatter
    content = re.sub(r"\n\nLet me know if you need anything.*$", "", content, flags=re.IGNORECASE)
    content = re.sub(r"\n\nIs there anything else.*$", "", content, flags=re.IGNORECASE)
    content = re.sub(r"\n\nThe changelog entry above.*$", "", content, flags=re.IGNORECASE)

    # Remove leading/trailing whitespace
    content = content.strip()

    # Handle empty-ish content that has no real changelog sections
    if content and not re.search(r"###\s+\w+|^-\s+", content, re.MULTILINE):
        return ""

    return content


def is_semantic_version(version: str) -> bool:
    """Check if a version string follows semantic versioning.

    Args:
        version: Version string to check

    Returns:
        True if version appears to be semantic version
    """
    # Match patterns like v1.0.0, 2.1.3, 1.0.0-beta.1, 1.2.3-alpha.1+build.1, etc.
    pattern = r"^v?(\d+)\.(\d+)\.(\d+)(?:-([\w.]+))?(?:\+([\w.]+))?$"
    return bool(re.match(pattern, version))


def normalize_tag(tag: str) -> str:
    """Normalize a git tag to a version string.

    Args:
        tag: Git tag string

    Returns:
        Normalized version string
    """
    # Remove 'v' or 'V' prefix if present (case-insensitive)
    if tag.lower().startswith("v"):
        return tag[1:]
    return tag


def find_changelog_file(directory: str = ".") -> str:
    """Find changelog file in directory using common patterns.

    Searches root directory first, then docs/ directory as a fallback.
    Returns relative path from the search directory.

    Args:
        directory: Directory to search in

    Returns:
        Relative path to changelog file (e.g., "CHANGELOG.md" or "docs/CHANGELOG.md")
        Returns "CHANGELOG.md" as default if no file is found
    """
    base_path = Path(directory)
    patterns = get_changelog_file_patterns()

    # Get actual filenames in root directory for case-insensitive filesystem support
    try:
        root_files = {f.name for f in base_path.iterdir() if f.is_file()}
    except OSError:
        root_files = set()

    # Search root directory first - check exact case match
    for pattern in patterns:
        if pattern in root_files:
            return pattern

    # Search docs/ directory as fallback
    docs_dir = base_path / "docs"
    if docs_dir.exists() and docs_dir.is_dir():
        try:
            docs_files = {f.name for f in docs_dir.iterdir() if f.is_file()}
        except OSError:
            docs_files = set()

        for pattern in patterns:
            if pattern in docs_files:
                return f"docs/{pattern}"

    # Return default if no file found
    return "CHANGELOG.md"


def get_changelog_file_patterns() -> list[str]:
    """Get common changelog file patterns to search for.

    Returns:
        List of changelog file patterns in order of preference
    """
    return [
        "CHANGELOG.md",
        "changelog.md",
        "CHANGELOG.markdown",
        "CHANGES.md",
        "changes.md",
        "HISTORY.md",
        "CHANGELOG",
        "CHANGES",
        "HISTORY",
    ]


def determine_next_version(latest_version: str | None, commits: list[dict]) -> str:
    """Determine the next version based on commits.

    Args:
        latest_version: Latest version string or None
        commits: List of commit dictionaries

    Returns:
        Next version string
    """
    if not latest_version:
        return "0.1.0"

    # Parse semantic version
    if not is_semantic_version(latest_version):
        return f"{latest_version}.1"

    # Extract version numbers
    version = latest_version.lstrip("v")
    parts = version.split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2].split("-")[0]) if len(parts) > 2 else 0

    # Look for breaking changes
    breaking_changes = any(
        "BREAKING CHANGE" in commit.get("message", "")
        or "BREAKING-CHANGE" in commit.get("message", "")
        or commit.get("message", "").startswith("feat!")
        or "!" in commit.get("message", "").split(" ")[0]
        for commit in commits
    )

    # Look for new features
    features = any(commit.get("message", "").startswith("feat") for commit in commits)

    # Determine version bump
    if breaking_changes:
        return f"v{major + 1}.0.0"
    elif features:
        return f"v{major}.{minor + 1}.0"
    else:
        return f"v{major}.{minor}.{patch + 1}"


def detect_changelog_version_style(content: str) -> bool:
    """Detect if the changelog uses 'v' prefix for versions.

    Args:
        content: Existing changelog content

    Returns:
        True if changelog uses 'v' prefix (e.g., ## [v1.0.0]), False otherwise
    """
    # Look for version headers like ## [v1.0.0] or ## [1.0.0]
    # Match the first versioned section (not Unreleased)
    pattern = r"##\s*\[\s*(v)?(\d+\.\d+\.\d+)"
    match = re.search(pattern, content, re.IGNORECASE)
    if match:
        return match.group(1) is not None and match.group(1).lower() == "v"
    return False  # Default to no prefix


def format_version_for_changelog(tag: str, existing_content: str = "") -> str:
    """Format a version tag to match the existing changelog style.

    Args:
        tag: Git tag string (e.g., "v1.0.0" or "1.0.0")
        existing_content: Existing changelog content to detect style from

    Returns:
        Version string formatted to match existing style
    """
    # Get the base version without prefix
    base_version = normalize_tag(tag)

    # If we have existing content, match its style
    if existing_content.strip():
        uses_v_prefix = detect_changelog_version_style(existing_content)
        if uses_v_prefix:
            return f"v{base_version}"

    # Default: no prefix
    return base_version
