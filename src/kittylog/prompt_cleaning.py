"""Content cleaning and categorization utilities for changelog processing.

This module provides functions to clean AI-generated changelog content and
categorize commits based on their messages.
"""

import re


def clean_changelog_content(content: str, preserve_version_header: bool = False) -> str:
    """Clean and format AI-generated changelog content.

    Args:
        content: Raw AI-generated content
        preserve_version_header: Whether to preserve version headers (for unreleased changes)

    Returns:
        Cleaned and formatted changelog content
    """
    if not content:
        return ""

    # Remove version headers unless we want to preserve them (for unreleased changes)
    if not preserve_version_header:
        # Remove numeric version headers like ## [1.2.3] or ## v1.2.3
        content = re.sub(r"^##\s*\[?v?\d+\.\d+\.\d+[^\n]*\n?", "", content, flags=re.MULTILINE)
        # Remove placeholder version headers like ## [X.Y.Z] that AI might output
        content = re.sub(r"^##\s*\[X\.Y\.Z\][^\n]*\n?", "", content, flags=re.MULTILINE)
        # Remove any other version-like headers (e.g., ## [Unreleased])
        content = re.sub(r"^##\s*\[Unreleased\][^\n]*\n?", "", content, flags=re.MULTILINE | re.IGNORECASE)

    # Remove any "### Changelog" sections that might have been included
    content = re.sub(r"^###\s+Changelog\s*\n?", "", content, flags=re.MULTILINE)

    # Remove any date stamps
    content = re.sub(r"- \d{4}-\d{2}-\d{2}[^\n]*\n?", "", content, flags=re.MULTILINE)

    # Remove explanatory introductions and conclusions
    explanatory_patterns = [
        r"^Based on the commits.*?:\s*\n?",
        r"^Here's? .*? changelog.*?:\s*\n?",
        r"^.*comprehensive changelog.*?:\s*\n?",
        r"^.*changelog entry.*?:\s*\n?",
        r"^.*following.*change.*?:\s*\n?",
        r"^.*version.*include.*?:\s*\n?",
        r"^.*summary of changes.*?:\s*\n?",
        r"^.*changes made.*?:\s*\n?",
    ]

    for pattern in explanatory_patterns:
        content = re.sub(pattern, "", content, flags=re.MULTILINE | re.IGNORECASE)

    # Remove any remaining lines that are purely explanatory
    lines = content.split("\n")
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        # Skip lines that look like explanatory text
        if (
            stripped
            and not stripped.startswith("###")
            and not stripped.startswith("-")
            and not stripped.startswith("*")
            and any(
                phrase in stripped.lower()
                for phrase in [
                    "based on",
                    "here is",
                    "here's",
                    "changelog for",
                    "version",
                    "following changes",
                    "summary",
                    "commits",
                    "entry for",
                ]
            )
            and len(stripped) > 30
        ):  # Only remove longer explanatory lines
            continue
        cleaned_lines.append(line)

    content = "\n".join(cleaned_lines)

    # Clean up any XML tags that might have leaked
    xml_tags = [
        "<thinking>",
        "</thinking>",
        "<analysis>",
        "<summary>",
        "</summary>",
        "<changelog>",
        "</changelog>",
        "<entry>",
        "</entry>",
        "<version>",
        "</version>",
    ]

    for tag in xml_tags:
        content = content.replace(tag, "")

    # Normalize whitespace
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = content.strip()

    # Ensure sections have proper spacing
    content = re.sub(r"\n(### [^\n]+)\n([^\n])", r"\n\1\n\n\2", content)

    # Normalize section headers to use ### format consistently
    content = re.sub(r"^##\s+([A-Z][a-z]+)", r"### \1", content, flags=re.MULTILINE)

    # Normalize bullet points to use consistent format (- instead of *)
    content = re.sub(r"^\*\s+", "- ", content, flags=re.MULTILINE)

    # Clean up the content using our new postprocessing module
    from kittylog.postprocess import postprocess_changelog_content

    content = postprocess_changelog_content(content)

    return content


def categorize_commit_by_message(message: str) -> str:
    """Categorize a commit based on its message.

    Args:
        message: The commit message

    Returns:
        Category string (Added, Changed, Fixed, etc.)
    """
    message_lower = message.lower()
    first_line = message.split("\n")[0].lower()

    # Conventional commit patterns
    if any(word in first_line for word in ["feat:", "feature:"]):
        return "Added"
    elif any(word in first_line for word in ["fix:", "bugfix:", "hotfix:"]):
        return "Fixed"
    elif any(word in first_line for word in ["break:", "breaking:"]):
        return "Changed"
    elif any(word in first_line for word in ["remove:", "delete:"]):
        return "Removed"
    elif any(word in first_line for word in ["deprecate:"]):
        return "Deprecated"
    elif any(word in first_line for word in ["security:", "sec:"]):
        return "Security"

    # Keyword-based detection
    if any(word in message_lower for word in ["add", "new", "implement", "introduce"]):
        return "Added"
    elif any(word in message_lower for word in ["fix", "bug", "issue", "problem", "error"]):
        return "Fixed"
    elif any(word in message_lower for word in ["remove", "delete", "drop"]):
        return "Removed"
    elif any(word in message_lower for word in ["update", "change", "modify", "improve", "enhance"]):
        return "Changed"
    elif any(word in message_lower for word in ["deprecate"]):
        return "Deprecated"
    elif any(word in message_lower for word in ["security", "vulnerability", "cve"]):
        return "Security"

    # Default to Changed for other modifications
    return "Changed"
