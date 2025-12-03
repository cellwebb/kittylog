"""CLI for managing kittylog authentication."""

import click

from kittylog.oauth.claude_code import authenticate_and_save, load_stored_token


@click.command()
def auth() -> None:
    """Authenticate with Claude Code OAuth (refresh expired token or set up new auth)."""
    existing_token = load_stored_token()
    if not existing_token:
        click.echo("❌ No existing Claude Code token found.")
        click.echo("   Run 'kittylog init' to set up Claude Code authentication.")
        return

    click.echo("🔐 Re-authenticating with Claude Code...")
    click.echo("   (Your browser will open automatically)\n")

    if authenticate_and_save(quiet=False):
        click.echo("\n✓ Successfully re-authenticated with Claude Code!")
        click.echo("   Your new token has been saved.")
    else:
        click.echo("\n❌ Re-authentication failed.")
        click.echo("   Please try again or run 'kittylog init' to reconfigure.")
