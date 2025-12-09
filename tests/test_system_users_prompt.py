"""Test suite for system_users prompt module."""

from kittylog.prompt.system_users import build_system_prompt_users


class TestBuildSystemPromptUsers:
    """Test the build_system_prompt_users function."""

    def test_builds_system_prompt_with_default_detail_level(self):
        """Test building system prompt with default detail level."""
        prompt = build_system_prompt_users()

        # Check that basic components are present
        assert "You are writing release notes for END USERS" in prompt
        assert "NOT technical" in prompt
        assert "whats_new" in prompt
        assert "improvements" in prompt
        assert "bug_fixes" in prompt
        assert "JSON ONLY" in prompt
        assert "ZERO REDUNDANCY ENFORCEMENT" in prompt

    def test_builds_system_prompt_with_different_detail_levels(self):
        """Test building system prompt with different detail levels."""
        # Test with minimal detail
        prompt_minimal = build_system_prompt_users("minimal")
        assert "You are writing release notes for END USERS" in prompt_minimal
        assert "whats_new" in prompt_minimal
        assert "improvements" in prompt_minimal
        assert "bug_fixes" in prompt_minimal

        # Test with verbose detail
        prompt_verbose = build_system_prompt_users("verbose")
        assert "You are writing release notes for END USERS" in prompt_verbose
        assert "whats_new" in prompt_verbose
        assert "improvements" in prompt_verbose
        assert "bug_fixes" in prompt_verbose

    def test_includes_forbidden_words_section(self):
        """Test that forbidden words section is included."""
        prompt = build_system_prompt_users()

        assert "FORBIDDEN WORDS" in prompt
        assert "NEVER use these" in prompt
        # Check that some technical terms are listed as forbidden
        assert "module" in prompt
        assert "API" in prompt
        assert "refactor" in prompt

    def test_includes_translation_examples(self):
        """Test that translation examples are included."""
        prompt = build_system_prompt_users()

        assert "TRANSLATION EXAMPLES" in prompt
        assert "Technical → User-Friendly" in prompt
        assert "Refactored authentication module" in prompt
        assert "Improved sign-in reliability" in prompt

    def test_includes_output_format_section(self):
        """Test that output format section is included."""
        prompt = build_system_prompt_users()

        assert "OUTPUT FORMAT - JSON ONLY" in prompt
        assert "whats_new" in prompt
        assert "improvements" in prompt
        assert "bug_fixes" in prompt

    def test_includes_example_output(self):
        """Test that example output is included."""
        prompt = build_system_prompt_users()

        assert "EXAMPLE OUTPUT:" in prompt
        assert "whats_new" in prompt
        assert "Export your data" in prompt
        assert "Dark mode" in prompt

    def test_includes_rules_section(self):
        """Test that rules section is included."""
        prompt = build_system_prompt_users()

        assert "## RULES:" in prompt
        assert "RESPECT THE BULLET LIMITS" in prompt
        assert "Keep each item to 1-2 short sentences" in prompt
        assert "Do NOT include bullet points" in prompt

    def test_returns_string(self):
        """Test that function returns a string."""
        prompt = build_system_prompt_users()
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be a substantial prompt

    def test_prompt_contains_user_focus_language(self):
        """Test that prompt emphasizes user focus."""
        prompt = build_system_prompt_users()

        # Check for user-focused language
        assert "Write like you're explaining to a friend" in prompt
        assert "Focus on WHAT users can do" in prompt
        assert "Describe BENEFITS and OUTCOMES" in prompt
        assert "everyday words everyone understands" in prompt

    def test_prompt_emphasizes_non_technical_audience(self):
        """Test that prompt emphasizes non-technical audience."""
        prompt = build_system_prompt_users()

        assert "END USERS who are NOT technical" in prompt
        assert "don't know programming, APIs, or software architecture" in prompt
        assert "NO TECHNICAL JARGON" in prompt
