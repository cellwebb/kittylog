#!/usr/bin/env python3
import re
import sys
from datetime import datetime
from pathlib import Path


def update_changelog(file_path, new_version):
    today = datetime.now().strftime("%Y-%m-%d")

    with Path(file_path).open() as file:
        content = file.read()

    # Check if there's an Unreleased section to replace
    if "## [Unreleased]" in content:
        # Replace "## [Unreleased]" with the new version header
        content = re.sub(r"## \[Unreleased\]\s*\n", f"## [{new_version}] - {today}\n\n", content, count=1)
    else:
        # If no Unreleased section, add new version at the beginning
        content = re.sub(r"# Changelog\s*\n", f"# Changelog\n\n## [{new_version}] - {today}\n\n", content, count=1)

    # Extract link format from existing link and add new one if links exist
    link_match = re.search(r"\[\d+\.\d+\.\d+\]:\s+(.*?)v\d+\.\d+\.\d+", content)
    if link_match:
        base_url = link_match.group(1)
        new_link = f"[{new_version}]: {base_url}v{new_version}\n"

        # Find the position of the first link reference
        first_link = re.search(r"^\[\d+\.\d+\.\d+\]:", content, re.MULTILINE)
        if first_link:
            pos = first_link.start()
            content = content[:pos] + new_link + content[pos:]

    with Path(file_path).open("w") as file:
        file.write(content)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <changelog_file> <new_version>")
        sys.exit(1)

    update_changelog(sys.argv[1], sys.argv[2])
    print(f"Updated changelog for version {sys.argv[2]}")
