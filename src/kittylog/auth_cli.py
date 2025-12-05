"""CLI for OAuth authentication with various providers.

Provides commands to authenticate and manage OAuth tokens for supported providers.
"""

import logging
from pathlib import Path

import click

from kittylog.oauth import (
    QwenOAuthProvider,
    TokenStore,
    authenticate_and_save,
    get_token_storage_path,
    load_stored_token,
)

logger = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def auth(ctx: click.Context) -> None:
    """Manage OAuth authentication for AI providers.

    Supports authentication for:
    - claude-code: Claude Code subscription OAuth
    - qwen: Qwen AI OAuth (device flow)

    Examples:
        kittylog auth                        # Show authentication status
        kittylog auth claude-code login      # Login to Claude Code
        kittylog auth claude-code logout     # Logout from Claude Code
        kittylog auth claude-code status     # Check Claude Code auth status
        kittylog auth qwen login             # Login to Qwen
        kittylog auth qwen logout            # Logout from Qwen
        kittylog auth qwen status            # Check Qwen auth status
    """
    if ctx.invoked_subcommand is None:
        _show_auth_status()


def _show_auth_status() -> None:
    """Show authentication status for all providers."""
    click.echo("OAuth Authentication Status")
    click.echo("-" * 40)

    # Check Claude Code
    claude_token = load_stored_token()
    if claude_token:
        click.echo("Claude Code: ✓ Authenticated")
    else:
        click.echo("Claude Code: ✗ Not authenticated")
        click.echo("             Run 'kittylog auth claude-code login' to login")

    # Check Qwen
    token_store = TokenStore()
    qwen_token = token_store.get_token("qwen")
    if qwen_token:
        click.echo("Qwen:        ✓ Authenticated")
    else:
        click.echo("Qwen:        ✗ Not authenticated")
        click.echo("             Run 'kittylog auth qwen login' to login")


# Claude Code commands
@auth.group("claude-code")
def claude_code() -> None:
    """Manage Claude Code OAuth authentication.

    Use browser-based authentication to log in to Claude Code.
    """
    pass


@claude_code.command("login")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
def claude_code_login(quiet: bool = False) -> None:
    """Login to Claude Code using OAuth."""
    if not quiet:
        click.echo("🔐 Starting Claude Code OAuth authentication...")
        click.echo("   (Your browser will open automatically)\n")

    if authenticate_and_save(quiet=quiet):
        if not quiet:
            click.echo("\n✓ Successfully authenticated with Claude Code!")
            click.echo(f"   Token saved to {get_token_storage_path()}")
    else:
        click.echo("\n❌ Authentication failed.")
        click.echo("   Please try again.")
        raise click.Abort()


@claude_code.command("logout")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
def claude_code_logout(quiet: bool = False) -> None:
    """Logout from Claude Code and remove stored tokens."""
    env_path = get_token_storage_path()

    if not env_path.exists():
        if not quiet:
            click.echo("[info] No Claude Code token found to remove.")
        return

    try:
        from dotenv import unset_key

        unset_key(str(env_path), "CLAUDE_CODE_ACCESS_TOKEN")

        if not quiet:
            click.echo("✓ Successfully logged out from Claude Code")
            click.echo(f"   Token removed from {env_path}")
    except ImportError:
        # Fallback: manually remove the key by rewriting the file
        if not quiet:
            click.echo("⚠️  python-dotenv's unset_key not available, using fallback method")

        _remove_token_from_env_file(env_path, "CLAUDE_CODE_ACCESS_TOKEN", quiet)
    except Exception as e:
        click.echo(f"❌ Error removing token: {e}")
        raise click.Abort() from None


def _remove_token_from_env_file(env_path: Path, key: str, quiet: bool = False) -> None:
    """Remove a key from .env file by rewriting it."""
    try:
        lines = env_path.read_text().splitlines()
        filtered_lines = [line for line in lines if not line.startswith(f"{key}=")]

        env_path.write_text("\n".join(filtered_lines) + "\n" if filtered_lines else "")

        if not quiet:
            click.echo("✓ Successfully logged out from Claude Code")
            click.echo(f"   Token removed from {env_path}")
    except Exception as e:
        click.echo(f"❌ Error removing token: {e}")
        raise click.Abort() from None


@claude_code.command("status")
def claude_code_status() -> None:
    """Check Claude Code authentication status."""
    click.echo("Claude Code Authentication Status")
    click.echo("-" * 40)

    token = load_stored_token()
    if token:
        click.echo("Status: ✓ Authenticated")
        click.echo(f"Token stored in: {get_token_storage_path()}")
        click.echo(f"Token preview: {token[:20]}...{token[-10:] if len(token) > 30 else ''}")
    else:
        click.echo("Status: ✗ Not authenticated")
        click.echo("\nTo authenticate, run: kittylog auth claude-code login")


# Qwen commands
@auth.group()
def qwen() -> None:
    """Manage Qwen OAuth authentication.

    Use device flow authentication to log in to Qwen AI.
    """
    pass


@qwen.command("login")
@click.option("--no-browser", is_flag=True, help="Don't automatically open browser")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
def qwen_login(no_browser: bool = False, quiet: bool = False) -> None:
    """Login to Qwen using OAuth device flow."""
    try:
        oauth_provider = QwenOAuthProvider(TokenStore())

        # Check if already authenticated
        if oauth_provider.is_authenticated() and not quiet:
            click.echo("[info] Already authenticated with Qwen")
            response = click.prompt(
                "Do you want to re-authenticate?",
                type=click.Choice(["y", "n"], case_sensitive=False),
                default="n",
            )
            if response.lower() != "y":
                click.echo("Authentication cancelled.")
                return

        oauth_provider.initiate_auth(open_browser=not no_browser)

        if not quiet:
            click.echo("\n✓ Successfully authenticated with Qwen!")

    except KeyboardInterrupt:
        click.echo("\n\n❌ Authentication cancelled by user.")
        raise click.Abort() from None
    except Exception as e:
        click.echo(f"\n❌ Authentication failed: {e}")
        logger.exception("Qwen authentication error")
        raise click.Abort() from None


@qwen.command("logout")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
def qwen_logout(quiet: bool = False) -> None:
    """Logout from Qwen and remove stored tokens."""
    try:
        oauth_provider = QwenOAuthProvider(TokenStore())
        oauth_provider.logout()

        if not quiet:
            click.echo("✓ Successfully logged out from Qwen")

    except Exception as e:
        click.echo(f"❌ Error during logout: {e}")
        logger.exception("Qwen logout error")
        raise click.Abort() from None


@qwen.command("status")
def qwen_status() -> None:
    """Check Qwen authentication status."""
    click.echo("Qwen Authentication Status")
    click.echo("-" * 40)

    token_store = TokenStore()
    token = token_store.get_token("qwen")

    if token:
        click.echo("Status: ✓ Authenticated")
        click.echo(f"Token stored in: {token_store.base_dir / 'qwen.json'}")

        # Show token metadata (without exposing the actual token)
        if "expiry" in token:
            import time
            from datetime import datetime

            expiry_time = datetime.fromtimestamp(token["expiry"])
            time_left = token["expiry"] - time.time()

            if time_left > 0:
                hours_left = int(time_left // 3600)
                minutes_left = int((time_left % 3600) // 60)
                click.echo(f"Expires: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
                click.echo(f"Time remaining: {hours_left}h {minutes_left}m")
            else:
                click.echo(f"Expired: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
                click.echo("⚠️  Token is expired. Run 'kittylog auth qwen login' to re-authenticate.")

        if token.get("scope"):
            click.echo(f"Scopes: {token['scope']}")
    else:
        click.echo("Status: ✗ Not authenticated")
        click.echo("\nTo authenticate, run: kittylog auth qwen login")
