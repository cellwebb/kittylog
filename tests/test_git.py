"""Corrected version of test_git.py with proper fixture isolation."""

import os
from pathlib import Path

import pytest

from kittylog.tag_operations import (
    clear_git_cache,
    get_all_tags,
    get_latest_tag,
)


class TestGetAllTags:
    """Test get_all_tags function."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_git_cache()

    def test_get_all_tags_success(self, git_repo_with_tags):
        """Test getting all tags from a repository."""
        # Change to the test repository directory
        original_cwd = str(Path.cwd())
        try:
            os.chdir(git_repo_with_tags.working_dir)

            tags = get_all_tags()
            assert "v0.1.0" in tags
            assert "v0.2.0" in tags
            assert "v0.2.1" in tags
            assert len(tags) == 3
        finally:
            os.chdir(original_cwd)

    def test_get_all_tags_empty_repo(self, clean_git_repo):
        """Test getting tags from repository with no tags."""
        # Change to the test repository directory
        original_cwd = str(Path.cwd())
        try:
            os.chdir(clean_git_repo.working_dir)

            tags = get_all_tags()
            assert tags == []
        finally:
            os.chdir(original_cwd)

    def test_get_all_tags_sorting(self, clean_git_repo):
        """Test that tags are sorted correctly."""
        repo = clean_git_repo

        # Change to the test repository directory
        original_cwd = str(Path.cwd())
        try:
            os.chdir(repo.working_dir)

            # Create tags in non-sequential order
            test_file = Path(repo.working_dir) / "test.py"
            for version in ["v0.10.0", "v0.2.0", "v0.1.0"]:
                with test_file.open("w") as f:
                    f.write(f"# Version {version}\n")
                repo.index.add([test_file])
                commit = repo.index.commit(f"Version {version}")
                repo.create_tag(version, commit)

            tags = get_all_tags()
            assert tags == ["v0.1.0", "v0.2.0", "v0.10.0"]
        finally:
            os.chdir(original_cwd)


class TestGetLatestTag:
    """Test get_latest_tag function."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_git_cache()

    def test_get_latest_tag_success(self, git_repo_with_tags):
        """Test getting the latest tag."""
        # Change to the test repository directory
        original_cwd = str(Path.cwd())
        try:
            os.chdir(git_repo_with_tags.working_dir)

            latest = get_latest_tag()
            assert latest == "v0.2.1"
        finally:
            os.chdir(original_cwd)

    def test_get_latest_tag_no_tags(self, clean_git_repo):
        """Test getting latest tag when no tags exist."""
        # Change to the test repository directory
        original_cwd = str(Path.cwd())
        try:
            os.chdir(clean_git_repo.working_dir)

            latest = get_latest_tag()
            assert latest is None
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
