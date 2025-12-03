"""CLI for initializing kittylog configuration interactively."""

from pathlib import Path

import click
from dotenv import dotenv_values

from kittylog.language_cli import configure_language_init_workflow
from kittylog.model_cli import _configure_model

KITTYLOG_ENV_PATH = Path.home() / ".kittylog.env"


def _load_existing_env() -> dict[str, str]:
    """Ensure the env file exists and return its current values."""
    existing_env: dict[str, str] = {}
    if KITTYLOG_ENV_PATH.exists():
        click.echo(f"$HOME/.kittylog.env already exists at {KITTYLOG_ENV_PATH}. Values will be updated.")
        existing_env = {k: v for k, v in dotenv_values(str(KITTYLOG_ENV_PATH)).items() if v is not None}
    else:
        KITTYLOG_ENV_PATH.touch()
        click.echo(f"Created $HOME/.kittylog.env at {KITTYLOG_ENV_PATH}.")
    return existing_env


@click.command()
def init() -> None:
    """Interactively set up $HOME/.kittylog.env for kittylog."""
    kittylog_env_path = KITTYLOG_ENV_PATH

    if hasattr(init, "_mock_env_path"):
        kittylog_env_path = init._mock_env_path

    click.echo("Welcome to kittylog initialization!\n")

    existing_env = _load_existing_env()

    if not _configure_model(existing_env):
        click.echo("Model configuration cancelled. Exiting.")
        return

    # Configure language and audience using the consolidated workflow
    # (configure_language_init_workflow internally handles audience configuration too)
    success = configure_language_init_workflow(kittylog_env_path)

    if not success:
        click.echo("Language configuration cancelled or failed.")

    click.echo("\nkittylog environment setup complete 🎉")
    click.echo("Configuration saved to:")
    click.echo(f"  {kittylog_env_path}")
    click.echo("\nYou can now run 'kittylog' in any Git repository to generate changelog entries.")
    click.echo("Run 'kittylog --help' to see available options.")
