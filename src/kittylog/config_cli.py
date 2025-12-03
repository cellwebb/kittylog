"""CLI for managing kittylog configuration in $HOME/.kittylog.env."""

import os
from pathlib import Path

import click
from dotenv import load_dotenv, set_key

KITTYLOG_ENV_PATH = Path.home() / ".kittylog.env"


@click.group()
def config():
    """Manage kittylog configuration."""
    pass


@config.command()
def show() -> None:
    """Show all current config values from both user and project sources."""
    from dotenv import dotenv_values
    
    # User-level config
    user_config_path = KITTYLOG_ENV_PATH
    user_exists = user_config_path.exists()
    
    # Project-level config
    project_config_path = Path(".kittylog.env")
    project_exists = project_config_path.exists()
    
    if not user_exists and not project_exists:
        click.echo("No kittylog configuration found.")
        click.echo("Expected locations:")
        click.echo(f"  User config: {user_config_path}")
        click.echo(f"  Project config: {project_config_path}")
        return
    
    # Show user config
    if user_exists:
        click.echo(f"User config ({user_config_path}):")
        user_config = dotenv_values(str(user_config_path))
        for key, value in sorted(user_config.items()):
            if value is not None:
                # Hide sensitive values like API keys and tokens
                if any(sensitive in key.lower() for sensitive in ["key", "token", "secret"]):
                    display_value = "***hidden***"
                else:
                    display_value = value
                click.echo(f"  {key}={display_value}")
        click.echo()
    
    # Show project config
    if project_exists:
        click.echo(f"Project config ({project_config_path}):")
        project_config = dotenv_values(str(project_config_path))
        for key, value in sorted(project_config.items()):
            if value is not None:
                # Hide sensitive values like API keys and tokens
                if any(sensitive in key.lower() for sensitive in ["key", "token", "secret"]):
                    display_value = "***hidden***"
                else:
                    display_value = value
                click.echo(f"  {key}={display_value}")
        click.echo("\nNote: Project-level values override user-level values.")


@config.command()
@click.argument("key")
@click.argument("value")
def set(key: str, value: str) -> None:
    """Set a config KEY to VALUE in $HOME/.kittylog.env."""
    KITTYLOG_ENV_PATH.touch(exist_ok=True)
    set_key(str(KITTYLOG_ENV_PATH), key, value)
    click.echo(f"Set {key} in $HOME/.kittylog.env")


@config.command()
@click.argument("key")
def get(key: str) -> None:
    """Get a config value by KEY."""
    load_dotenv(KITTYLOG_ENV_PATH, override=True)
    value = os.getenv(key)
    if value is None:
        click.echo(f"{key} not set.")
    else:
        click.echo(value)


@config.command()
@click.argument("key")
def unset(key: str) -> None:
    """Remove a config KEY from $HOME/.kittylog.env."""
    if not KITTYLOG_ENV_PATH.exists():
        click.echo("No $HOME/.kittylog.env found.")
        return
    lines = KITTYLOG_ENV_PATH.read_text().splitlines()
    new_lines = [line for line in lines if not line.strip().startswith(f"{key}=")]
    KITTYLOG_ENV_PATH.write_text("\n".join(new_lines) + "\n")
    click.echo(f"Unset {key} in $HOME/.kittylog.env")
