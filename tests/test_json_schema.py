"""Tests for JSON schema parsing and formatting."""

from kittylog.prompt.json_schema import (
    AUDIENCE_SCHEMAS,
    SECTION_ORDER,
    _remap_json_keys,
    format_changelog_from_json,
    json_to_markdown,
    parse_json_response,
)


class TestParseJsonResponse:
    """Tests for parse_json_response function."""

    def test_parse_json_in_code_block(self):
        """Test parsing JSON wrapped in code blocks."""
        content = """```json
{
  "added": ["New feature A", "New feature B"],
  "fixed": ["Bug fix C"]
}
```"""
        result = parse_json_response(content)
        assert result is not None
        assert result["added"] == ["New feature A", "New feature B"]
        assert result["fixed"] == ["Bug fix C"]

    def test_parse_raw_json(self):
        """Test parsing raw JSON without code blocks."""
        content = '{"whats_new": ["Feature X"], "improvements": ["Better Y"]}'
        result = parse_json_response(content)
        assert result is not None
        assert result["whats_new"] == ["Feature X"]
        assert result["improvements"] == ["Better Y"]

    def test_parse_json_with_surrounding_text(self):
        """Test parsing JSON with AI preamble text."""
        content = """Here's the changelog:
{"added": ["Something new"]}
Let me know if you need changes."""
        result = parse_json_response(content)
        assert result is not None
        assert result["added"] == ["Something new"]

    def test_parse_invalid_json_returns_none(self):
        """Test that invalid JSON returns None."""
        content = "This is not JSON at all"
        result = parse_json_response(content)
        assert result is None

    def test_parse_empty_arrays_filtered(self):
        """Test that empty values are filtered out."""
        content = '{"added": ["Item"], "changed": []}'
        result = parse_json_response(content)
        assert result is not None
        assert result["added"] == ["Item"]
        assert result.get("changed") == []


class TestJsonToMarkdown:
    """Tests for json_to_markdown function."""

    def test_developers_audience_headers(self):
        """Test that developers get correct headers."""
        data = {"added": ["New API"], "fixed": ["Bug in login"]}
        result = json_to_markdown(data, "developers")
        assert "### Added" in result
        assert "### Fixed" in result
        assert "- New API" in result
        assert "- Bug in login" in result

    def test_users_audience_headers(self):
        """Test that users get correct headers."""
        data = {"whats_new": ["New feature"], "bug_fixes": ["Fixed crash"]}
        result = json_to_markdown(data, "users")
        assert "### What's New" in result
        assert "### Bug Fixes" in result
        assert "- New feature" in result
        assert "- Fixed crash" in result

    def test_stakeholders_audience_headers(self):
        """Test that stakeholders get correct headers."""
        data = {"highlights": ["Major win"], "customer_impact": ["Better UX"]}
        result = json_to_markdown(data, "stakeholders")
        assert "### Highlights" in result
        assert "### Customer Impact" in result
        assert "- Major win" in result
        assert "- Better UX" in result

    def test_section_order_preserved(self):
        """Test that sections appear in correct order."""
        data = {"fixed": ["Bug"], "added": ["Feature"], "changed": ["Update"]}
        result = json_to_markdown(data, "developers")
        added_pos = result.find("### Added")
        changed_pos = result.find("### Changed")
        fixed_pos = result.find("### Fixed")
        assert added_pos < changed_pos < fixed_pos

    def test_empty_sections_omitted(self):
        """Test that empty sections are not included."""
        data = {"added": ["Feature"]}
        result = json_to_markdown(data, "developers")
        assert "### Added" in result
        assert "### Fixed" not in result
        assert "### Changed" not in result

    def test_items_get_bullet_prefix(self):
        """Test that items without bullets get them added."""
        data = {"added": ["No bullet", "- Has bullet"]}
        result = json_to_markdown(data, "developers")
        assert "- No bullet" in result
        assert "- Has bullet" in result
        assert "- - Has bullet" not in result  # Don't double-prefix


class TestFormatChangelogFromJson:
    """Tests for format_changelog_from_json function."""

    def test_full_workflow_users(self):
        """Test complete workflow for users audience."""
        content = """```json
{
  "whats_new": ["Dark mode support"],
  "improvements": ["Faster loading"],
  "bug_fixes": ["Fixed login issue"]
}
```"""
        result = format_changelog_from_json(content, "users")
        assert result is not None
        assert "### What's New" in result
        assert "### Improvements" in result
        assert "### Bug Fixes" in result
        assert "- Dark mode support" in result

    def test_returns_none_for_invalid_json(self):
        """Test that invalid JSON returns None for fallback."""
        content = "Not JSON content here"
        result = format_changelog_from_json(content, "developers")
        assert result is None


class TestAudienceSchemas:
    """Tests for audience schema definitions."""

    def test_all_audiences_have_schemas(self):
        """Test that all audiences have defined schemas."""
        assert "developers" in AUDIENCE_SCHEMAS
        assert "users" in AUDIENCE_SCHEMAS
        assert "stakeholders" in AUDIENCE_SCHEMAS

    def test_all_audiences_have_section_order(self):
        """Test that all audiences have defined section order."""
        assert "developers" in SECTION_ORDER
        assert "users" in SECTION_ORDER
        assert "stakeholders" in SECTION_ORDER

    def test_schema_keys_match_order(self):
        """Test that schema keys match section order."""
        for audience in ["developers", "users", "stakeholders"]:
            schema_keys = set(AUDIENCE_SCHEMAS[audience].keys())
            order_keys = set(SECTION_ORDER[audience])
            assert schema_keys == order_keys, f"Mismatch for {audience}"


class TestKeyRemapping:
    """Tests for remapping developer keys to audience keys."""

    def test_remap_developer_keys_to_users(self):
        """Test remapping developer JSON keys to user keys."""
        data = {"added": ["Feature A"], "changed": ["Update B"], "fixed": ["Bug C"]}
        result = _remap_json_keys(data, "users")

        assert "whats_new" in result
        assert "improvements" in result
        assert "bug_fixes" in result
        assert "added" not in result
        assert "changed" not in result
        assert "fixed" not in result

    def test_remap_developer_keys_to_stakeholders(self):
        """Test remapping developer JSON keys to stakeholder keys."""
        data = {"added": ["Feature"], "fixed": ["Bug"]}
        result = _remap_json_keys(data, "stakeholders")

        assert "highlights" in result
        assert "platform_improvements" in result

    def test_no_remap_for_developers(self):
        """Test that developer keys are not remapped for developers."""
        data = {"added": ["Feature"], "changed": ["Update"]}
        result = _remap_json_keys(data, "developers")

        assert result == data

    def test_preserves_correct_audience_keys(self):
        """Test that correct audience keys are preserved."""
        data = {"whats_new": ["Feature"], "improvements": ["Update"]}
        result = _remap_json_keys(data, "users")

        assert "whats_new" in result
        assert "improvements" in result

    def test_merges_remapped_keys(self):
        """Test that remapped keys are merged properly."""
        # Both 'fixed' and 'security' map to 'bug_fixes' for users
        data = {"fixed": ["Bug A"], "security": ["Security B"]}
        result = _remap_json_keys(data, "users")

        assert "bug_fixes" in result
        assert len(result["bug_fixes"]) == 2
        assert "Bug A" in result["bug_fixes"]
        assert "Security B" in result["bug_fixes"]


class TestJsonToMarkdownWithRemapping:
    """Test json_to_markdown with developer keys for non-developer audiences."""

    def test_developer_keys_converted_for_users(self):
        """Test that developer keys are converted to user headers."""
        data = {"added": ["New feature"], "fixed": ["Bug fix"]}
        result = json_to_markdown(data, "users")

        assert "### What's New" in result
        assert "### Bug Fixes" in result
        assert "- New feature" in result
        assert "- Bug fix" in result
        assert "### Added" not in result
        assert "### Fixed" not in result

    def test_developer_keys_converted_for_stakeholders(self):
        """Test that developer keys are converted to stakeholder headers."""
        data = {"added": ["Big win"], "changed": ["Improvement"]}
        result = json_to_markdown(data, "stakeholders")

        assert "### Highlights" in result
        assert "### Platform Improvements" in result
        assert "### Added" not in result
