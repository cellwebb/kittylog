"""Tests for changelog file discovery functionality."""


from clog.utils import find_changelog_file


class TestFindChangelogFile:
    """Test find_changelog_file function."""

    def test_find_changelog_file_root_priority(self, temp_dir):
        """Test that root directory files take precedence over docs/ directory files."""
        # Create docs directory
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        # Create changelog files in both locations
        root_changelog = temp_dir / "CHANGELOG.md"
        docs_changelog = docs_dir / "CHANGELOG.md"

        root_changelog.write_text("# Root Changelog")
        docs_changelog.write_text("# Docs Changelog")

        # Should find root changelog first
        result = find_changelog_file(str(temp_dir))
        assert result == "CHANGELOG.md"

    def test_find_changelog_file_docs_fallback(self, temp_dir):
        """Test that docs/ directory is searched when no root changelog exists."""
        # Create docs directory
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        # Create changelog file only in docs/
        docs_changelog = docs_dir / "CHANGES.md"
        docs_changelog.write_text("# Docs Changes")

        # Should find docs changelog
        result = find_changelog_file(str(temp_dir))
        assert result == "docs/CHANGES.md"

    def test_find_changelog_file_root_exists(self, temp_dir):
        """Test that existing root files are found with correct priority."""
        # Create different changelog files in root one at a time
        changelog_files = ["CHANGELOG.md", "changelog.md", "CHANGES.md", "changes.md"]

        # Remove any existing root files first
        for existing_file in changelog_files:
            existing_path = temp_dir / existing_file
            if existing_path.exists():
                existing_path.unlink()

        for filename in changelog_files:
            changelog_path = temp_dir / filename
            changelog_path.write_text(f"# {filename}")

            result = find_changelog_file(str(temp_dir))
            assert result == filename

            # Clean up for next test
            changelog_path.unlink()

    def test_find_changelog_file_docs_exists(self, temp_dir):
        """Test that existing docs/ files are found with correct priority."""
        # Create docs directory
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        # Test each filename pattern in docs/ (but ensure no root files exist)
        changelog_files = ["CHANGELOG.md", "changelog.md", "CHANGES.md", "changes.md"]

        for filename in changelog_files:
            # Remove any existing root files
            for root_file in ["CHANGELOG.md", "changelog.md", "CHANGES.md", "changes.md"]:
                root_path = temp_dir / root_file
                if root_path.exists():
                    root_path.unlink()

            # Remove any existing docs files except the one we're testing
            for existing_docs_file in ["CHANGELOG.md", "changelog.md", "CHANGES.md", "changes.md"]:
                docs_filepath = docs_dir / existing_docs_file
                if docs_filepath.exists() and existing_docs_file != filename:
                    docs_filepath.unlink()

            docs_changelog_path = docs_dir / filename
            docs_changelog_path.write_text(f"# {filename}")

            result = find_changelog_file(str(temp_dir))
            assert result == f"docs/{filename}"

    def test_find_changelog_file_no_docs_directory(self, temp_dir):
        """Test behavior when docs/ directory doesn't exist."""
        # Remove docs directory if it exists
        docs_dir = temp_dir / "docs"
        if docs_dir.exists():
            docs_dir.rmdir()

        result = find_changelog_file(str(temp_dir))
        assert result == "CHANGELOG.md"  # Should fallback to default

    def test_find_changelog_file_empty_docs_directory(self, temp_dir):
        """Test behavior when docs/ directory exists but is empty."""
        # Create empty docs directory
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        result = find_changelog_file(str(temp_dir))
        assert result == "CHANGELOG.md"  # Should fallback to default

    def test_find_changelog_file_priority_order(self, temp_dir):
        """Test that the priority order is maintained for docs/ directory."""
        # Create docs directory
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        # Create files in priority order and test each
        priority_files = ["CHANGELOG.md", "changelog.md", "CHANGES.md", "changes.md"]

        for filename in priority_files:
            # Create the current file
            docs_changelog_path = docs_dir / filename
            docs_changelog_path.write_text(f"# {filename}")

            result = find_changelog_file(str(temp_dir))
            assert result == f"docs/{filename}"

            # Clean up for next test
            docs_changelog_path.unlink()

    def test_find_changelog_file_fallback_default(self, temp_dir):
        """Test that function falls back to CHANGELOG.md when no files found."""
        # Ensure no changelog files exist
        for filename in ["CHANGELOG.md", "changelog.md", "CHANGES.md", "changes.md"]:
            filepath = temp_dir / filename
            if filepath.exists():
                filepath.unlink()

            docs_filepath = temp_dir / "docs" / filename
            if docs_filepath.exists():
                docs_filepath.unlink()

        # Ensure docs directory doesn't exist
        docs_dir = temp_dir / "docs"
        if docs_dir.exists():
            docs_dir.rmdir()

        result = find_changelog_file(str(temp_dir))
        assert result == "CHANGELOG.md"
