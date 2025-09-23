"""CLI for initializing kittylog configuration interactively."""

from pathlib import Path

import click
import questionary
from dotenv import set_key

KITTYLOG_ENV_PATH = Path.home() / ".kittylog.env"


@click.command()
def init() -> None:
    """Interactively set up $HOME/.kittylog.env for kittylog."""
    # Determine path - use global variable to allow monkeypatching
    kittylog_env_path = KITTYLOG_ENV_PATH

    # Allow monkeypatching for tests
    if hasattr(init, "_mock_env_path"):
        kittylog_env_path = init._mock_env_path

    click.echo("Welcome to kittylog initialization!\n")
    if kittylog_env_path.exists():
        click.echo(f"$HOME/.kittylog.env already exists at {kittylog_env_path}.")
    else:
        kittylog_env_path.touch()
        click.echo(f"Created $HOME/.kittylog.env at {kittylog_env_path}.")

    providers = [
        ("Anthropic", "claude-3-5-haiku-latest"),
        ("Cerebras", "qwen-3-coder-480b"),
        ("Groq", "meta-llama/llama-4-maverick-17b-128e-instruct"),
        ("Ollama", "gemma3"),
        ("OpenAI", "gpt-4.1-mini"),
    ]
    provider_names = [p[0] for p in providers]
    provider = questionary.select("Select your provider:", choices=provider_names).ask()
    if not provider:
        click.echo("Provider selection cancelled. Exiting.")
        return
    provider_key = provider.lower()
    model_suggestion = dict(providers)[provider]
    model = questionary.text(f"Enter the model (default: {model_suggestion}):", default=model_suggestion).ask()
    model_to_save = model.strip() if model.strip() else model_suggestion
    set_key(str(kittylog_env_path), "KITTYLOG_MODEL", f"{provider_key}:{model_to_save}")
    click.echo(f"Set KITTYLOG_MODEL={provider_key}:{model_to_save}")

    api_key = questionary.password("Enter your API key (input hidden, can be set later):").ask()
    if api_key:
        set_key(str(kittylog_env_path), f"{provider_key.upper()}_API_KEY", api_key)
        click.echo(f"Set {provider_key.upper()}_API_KEY (hidden)")

    click.echo(f"\nkittylog environment setup complete. You can edit {kittylog_env_path} to update values later.")
