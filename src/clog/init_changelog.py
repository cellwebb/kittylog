"""CLI command for initializing changelog and analyzing missing tags."""

import logging
from pathlib import Path

import click

from clog.changelog import create_changelog_header, find_existing_tags, read_changelog, write_changelog
from clog.git_operations import get_all_tags

logger = logging.getLogger(__name__)


@click.command()
@click.option("--yes", "-y", is_flag=True, help="Automatically create changelog and fill missing tags without prompts")
@click.option("--file", "-f", default="CHANGELOG.md", help="Path to changelog file")
def init_changelog(yes, file):
    """Initialize changelog if missing and offer to fill missing tag entries."""
    # Auto-detect changelog file if using default
    if file == "CHANGELOG.md":
        from clog.utils import find_changelog_file
        file = find_changelog_file()
        logger.debug(f"Auto-detected changelog file: {file}")

    # Check if changelog exists
    changelog_path = Path(file)
    if not changelog_path.exists():
        if yes or click.confirm("No changelog found. Create one with standard header?"):
            header_content = create_changelog_header()
            write_changelog(file, header_content)
            click.echo(f"Created {file} with standard header")
        else:
            click.echo("Changelog initialization cancelled.")
            return

    # Read existing changelog
    existing_content = read_changelog(file)

    # Get all git tags
    all_tags = get_all_tags()
    if not all_tags:
        click.echo("No git tags found in repository.")
        return

    # Find existing tags in changelog
    existing_tags = find_existing_tags(existing_content)

    # Find missing tags
    missing_tags = []
    for tag in all_tags:
        # Normalize tag name (remove 'v' prefix for comparison)
        normalized_tag = tag.lstrip("v")
        if normalized_tag not in existing_tags:
            missing_tags.append(tag)

    if not missing_tags:
        click.echo("All tags already have changelog entries.")
        return

    # Report missing tags
    click.echo(f"Found {len(missing_tags)} tags missing from changelog:")
    for tag in missing_tags:
        click.echo(f"  - {tag}")

    # Offer to fill missing tags
    if yes or click.confirm("Would you like to create placeholder entries for these tags?"):
        # Create placeholder entries for missing tags
        updated_content = existing_content

        # For each missing tag, create a placeholder entry
        for tag in missing_tags:
            # Create a simple placeholder entry
            placeholder_entry = f"## [{tag.lstrip('v')}]\n\n### Added\n- Initial release\n\n"

            # Insert after the header or unreleased section
            lines = updated_content.split("\n")
            insert_point = 0

            # Find where to insert (after first version section or at beginning if none exist)
            for i, line in enumerate(lines):
                if line.startswith("## [") and "unreleased" not in line.lower():
                    insert_point = i
                    break
                elif line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
                    insert_point = i + 1

            # Insert the placeholder entry
            lines.insert(insert_point, placeholder_entry.rstrip())
            updated_content = "\n".join(lines)

        # Write updated changelog
        write_changelog(file, updated_content)
        click.echo(f"Added placeholder entries for {len(missing_tags)} tags to {file}")


if __name__ == "__main__":
    init_changelog()
