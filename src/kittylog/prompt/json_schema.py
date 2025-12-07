"""JSON schemas and formatting for audience-specific changelog output.

This module defines the JSON structure for each audience type and provides
functions to convert JSON responses to properly formatted markdown.
"""

import json
import re

# JSON keys and their corresponding markdown headers for each audience
AUDIENCE_SCHEMAS: dict[str, dict[str, str]] = {
    "developers": {
        "added": "Added",
        "changed": "Changed",
        "deprecated": "Deprecated",
        "removed": "Removed",
        "fixed": "Fixed",
        "security": "Security",
    },
    "users": {
        "whats_new": "What's New",
        "improvements": "Improvements",
        "bug_fixes": "Bug Fixes",
    },
    "stakeholders": {
        "highlights": "Highlights",
        "customer_impact": "Customer Impact",
        "platform_improvements": "Platform Improvements",
    },
}

# Order of sections for each audience
SECTION_ORDER: dict[str, list[str]] = {
    "developers": ["added", "changed", "deprecated", "removed", "fixed", "security"],
    "users": ["whats_new", "improvements", "bug_fixes"],
    "stakeholders": ["highlights", "customer_impact", "platform_improvements"],
}


def get_json_schema_for_audience(audience: str) -> str:
    """Get the JSON schema description for a specific audience.

    Args:
        audience: The target audience ('developers', 'users', 'stakeholders')

    Returns:
        String describing the expected JSON format
    """
    schema = AUDIENCE_SCHEMAS.get(audience, AUDIENCE_SCHEMAS["developers"])
    keys = list(schema.keys())

    example = {key: ["Example item 1", "Example item 2"] for key in keys[:2]}

    return f"""{{
  {', '.join(f'"{k}": ["item1", "item2", ...]' for k in keys)}
}}

Example:
```json
{json.dumps(example, indent=2)}
```"""


def get_json_keys_for_audience(audience: str) -> list[str]:
    """Get the JSON keys for a specific audience.

    Args:
        audience: The target audience

    Returns:
        List of JSON keys in order
    """
    return SECTION_ORDER.get(audience, SECTION_ORDER["developers"])


def parse_json_response(content: str) -> dict[str, list[str]] | None:
    """Parse JSON from AI response, handling common formatting issues.

    Args:
        content: Raw AI response that may contain JSON

    Returns:
        Parsed JSON dict or None if parsing fails
    """
    # Try to extract JSON from the response
    # First, try to find JSON in code blocks
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        # Try to find raw JSON (object starting with {)
        json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            return None

    try:
        parsed = json.loads(json_str)
        if isinstance(parsed, dict):
            # Ensure all values are lists of strings
            result: dict[str, list[str]] = {}
            for key, value in parsed.items():
                if isinstance(value, list):
                    result[key] = [str(item) for item in value if item]
                elif value:
                    result[key] = [str(value)]
            return result
    except json.JSONDecodeError:
        pass

    return None


# Mapping from developer keys to audience keys
KEY_REMAPPING: dict[str, dict[str, str]] = {
    "users": {
        "added": "whats_new",
        "changed": "improvements",
        "fixed": "bug_fixes",
        "deprecated": "bug_fixes",
        "removed": "improvements",
        "security": "bug_fixes",
    },
    "stakeholders": {
        "added": "highlights",
        "changed": "platform_improvements",
        "fixed": "platform_improvements",
        "deprecated": "platform_improvements",
        "removed": "platform_improvements",
        "security": "platform_improvements",
    },
}


def _remap_json_keys(data: dict[str, list[str]], audience: str) -> dict[str, list[str]]:
    """Remap developer JSON keys to audience-specific keys.

    If the AI returns developer keys (added, changed, fixed) when we asked for
    user keys (whats_new, improvements, bug_fixes), this remaps them.
    """
    if audience not in KEY_REMAPPING:
        return data

    remapping = KEY_REMAPPING[audience]
    result: dict[str, list[str]] = {}

    for key, items in data.items():
        if key in remapping:
            # Remap developer key to audience key
            new_key = remapping[key]
            if new_key in result:
                result[new_key].extend(items)
            else:
                result[new_key] = list(items)
        else:
            # Keep the key as-is (might already be an audience key)
            if key in result:
                result[key].extend(items)
            else:
                result[key] = list(items)

    return result


def json_to_markdown(data: dict[str, list[str]], audience: str) -> str:
    """Convert parsed JSON to markdown with correct section headers.

    Args:
        data: Parsed JSON data with section keys
        audience: The target audience for header mapping

    Returns:
        Formatted markdown string
    """
    # First, remap any developer keys to audience keys
    data = _remap_json_keys(data, audience)

    schema = AUDIENCE_SCHEMAS.get(audience, AUDIENCE_SCHEMAS["developers"])
    order = SECTION_ORDER.get(audience, SECTION_ORDER["developers"])

    sections = []

    for key in order:
        items = data.get(key)
        if items:
            header = schema.get(key, key.replace("_", " ").title())

            section_lines = [f"### {header}", ""]
            for item in items:
                # Ensure items start with "- " for bullet points
                item = item.strip()
                if not item.startswith("- "):
                    item = f"- {item}"
                section_lines.append(item)
            section_lines.append("")

            sections.append("\n".join(section_lines))

    return "\n".join(sections).strip()


def format_changelog_from_json(content: str, audience: str) -> str | None:
    """Parse JSON response and format as markdown with correct headers.

    Args:
        content: Raw AI response
        audience: Target audience for header mapping

    Returns:
        Formatted markdown or None if JSON parsing failed or resulted in empty output
    """
    parsed = parse_json_response(content)
    if parsed is None:
        return None

    result = json_to_markdown(parsed, audience)

    # Return None if the result is empty (no matching sections found)
    if not result or not result.strip():
        return None

    return result
