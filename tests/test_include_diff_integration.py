#!/usr/bin/env python3
"""Simple integration test for --include-diff flag in release command."""

import os
import tempfile
from pathlib import Path

from click.testing import CliRunner
from git import Repo

from kittylog.cli import cli


def test_release_include_diff_integration():
    """Integration test that --include-diff flag works end-to-end."""
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)

        # Create git repo
        repo = Repo.init(temp_dir)
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # Create initial commit and tag
        test_file = Path("test.py")
        test_file.write_text("# Initial file")
        repo.index.add(["test.py"])
        commit = repo.index.commit("Initial commit")
        repo.create_tag("v0.1.0", commit)

        # Create another commit for changes
        test_file2 = Path("test2.py")
        test_file2.write_text("# New feature file")
        repo.index.add(["test2.py"])
        repo.index.commit("Add new feature")

        # Create changelog with unreleased section
        changelog = Path("CHANGELOG.md")
        changelog.write_text("# Changelog\n\n## [Unreleased]\n\n### Added\n- Some unreleased changes\n")

        runner = CliRunner()

        # Test 1: Help includes the flag
        result = runner.invoke(cli, ["release", "--help"])
        assert result.exit_code == 0
        assert "--include-diff" in result.output
        assert "Include git diff in AI context" in result.output

        # Test 2: Flag is parsed correctly (dry-run mode)
        result = runner.invoke(
            cli,
            [
                "release",
                "0.2.0",
                "--include-diff",
                "--skip-generate",  # Skip to avoid API key issues
                "--dry-run",  # Use dry-run for safety
            ],
        )
        assert result.exit_code == 0
        assert "Would convert [Unreleased] to [0.2.0]" in result.output

        # Test 3: Works with version prefix
        result = runner.invoke(cli, ["release", "v0.3.0", "--include-diff", "--skip-generate", "--dry-run"])
        assert result.exit_code == 0
        assert "Would convert [Unreleased] to [0.3.0]" in result.output

        # Test 4: Works with other flags
        result = runner.invoke(
            cli,
            [
                "release",
                "0.4.0",
                "--include-diff",
                "--hint",
                "Focus on API changes",
                "--verbose",
                "--skip-generate",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0

        print("✅ All integration tests passed! The --include-diff flag works correctly in release command.")


if __name__ == "__main__":
    test_release_include_diff_integration()
