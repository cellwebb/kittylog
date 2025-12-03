"""CLI for managing kittylog model configuration in $HOME/.kittylog.env."""

from pathlib import Path

import click
import questionary
from dotenv import dotenv_values, set_key

KITTYLOG_ENV_PATH = Path.home() / ".kittylog.env"


def _prompt_required_text(prompt: str) -> str | None:
    """Prompt until a non-empty string is provided or the user cancels."""
    while True:
        response = questionary.text(prompt).ask()
        if response is None:
            return None
        value = response.strip()
        if value:
            return value
        click.echo("A value is required. Please try again.")


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


def _configure_model(existing_env: dict[str, str]) -> bool:
    """Run the provider/model/API key configuration flow."""
    providers = [
        ("Anthropic", "claude-3-5-haiku-latest"),
        ("Cerebras", "zai-glm-4.6"),
        ("Chutes", "zai-org/GLM-4.6-FP8"),
        ("Claude Code", "claude-sonnet-4-5"),
        ("Custom (Anthropic)", ""),
        ("Custom (OpenAI)", ""),
        ("DeepSeek", "deepseek-chat"),
        ("Fireworks", "accounts/fireworks/models/gpt-oss-20b"),
        ("Gemini", "gemini-2.5-flash"),
        ("Groq", "meta-llama/llama-4-maverick-17b-128e-instruct"),
        ("LM Studio", "gemma3"),
        ("MiniMax", "MiniMax-M2"),
        ("Mistral", "mistral-small-latest"),
        ("Ollama", "gemma3"),
        ("OpenAI", "gpt-4.1-mini"),
        ("OpenRouter", "openrouter/auto"),
        ("Streamlake", ""),
        ("Synthetic", "hf:zai-org/GLM-4.6"),
        ("Together AI", "openai/gpt-oss-20B"),
        ("Z.AI", "glm-4.5-air"),
        ("Z.AI Coding", "glm-4.6"),
    ]
    provider_names = [p[0] for p in providers]
    provider = questionary.select(
        "Select your provider:",
        choices=provider_names,
        use_shortcuts=True,
        use_arrow_keys=True,
        use_jk_keys=False,
    ).ask()
    if not provider:
        click.echo("Provider selection cancelled. Exiting.")
        return False

    provider_key = provider.lower().replace(".", "").replace(" ", "-").replace("(", "").replace(")", "")

    is_streamlake = provider_key == "streamlake"
    is_zai_provider = provider_key in {"zai", "zai-coding"}
    is_custom_anthropic = provider_key == "custom-anthropic"
    is_custom_openai = provider_key == "custom-openai"
    is_ollama = provider_key == "ollama"
    is_lmstudio = provider_key == "lm-studio"
    is_claude_code = provider_key == "claude-code"

    if is_streamlake:
        endpoint_id = _prompt_required_text("Enter the Streamlake inference endpoint ID (required):")
        if endpoint_id is None:
            click.echo("Streamlake configuration cancelled. Exiting.")
            return False
        model_to_save = endpoint_id
    else:
        model_suggestion = dict(providers)[provider]
        model_prompt = (
            "Enter the model (required):"
            if model_suggestion == ""
            else f"Enter the model (default: {model_suggestion}):"
        )
        model = questionary.text(model_prompt, default=model_suggestion).ask()
        if model is None:
            click.echo("Model entry cancelled. Exiting.")
            return False
        model_to_save = model.strip() if model.strip() else model_suggestion

    set_key(str(KITTYLOG_ENV_PATH), "KITTYLOG_MODEL", f"{provider_key}:{model_to_save}")
    click.echo(f"Set KITTYLOG_MODEL={provider_key}:{model_to_save}")

    if is_custom_anthropic:
        base_url = _prompt_required_text("Enter the custom Anthropic-compatible base URL (required):")
        if base_url is None:
            click.echo("Custom Anthropic base URL entry cancelled. Exiting.")
            return False
        set_key(str(KITTYLOG_ENV_PATH), "CUSTOM_ANTHROPIC_BASE_URL", base_url)
        click.echo(f"Set CUSTOM_ANTHROPIC_BASE_URL={base_url}")

        api_version = questionary.text(
            "Enter the API version (press Enter for default 2023-06-01):",
            default="2023-06-01",
        ).ask()
        if api_version and api_version.strip() and api_version.strip() != "2023-06-01":
            set_key(str(KITTYLOG_ENV_PATH), "CUSTOM_ANTHROPIC_VERSION", api_version.strip())
            click.echo(f"Set CUSTOM_ANTHROPIC_VERSION={api_version.strip()}")

    if is_custom_openai:
        base_url = _prompt_required_text("Enter the custom OpenAI-compatible base URL (required):")
        if base_url is None:
            click.echo("Custom OpenAI base URL entry cancelled. Exiting.")
            return False
        set_key(str(KITTYLOG_ENV_PATH), "CUSTOM_OPENAI_BASE_URL", base_url)
        click.echo(f"Set CUSTOM_OPENAI_BASE_URL={base_url}")

    if is_ollama:
        default_url = "http://localhost:11434"
        provided_url = questionary.text(
            f"Enter the Ollama API URL (default: {default_url}):",
            default=default_url,
        ).ask()
        if provided_url is None:
            click.echo("Ollama URL entry cancelled. Exiting.")
            return False
        url_to_save = provided_url.strip() if provided_url.strip() else default_url
        set_key(str(KITTYLOG_ENV_PATH), "OLLAMA_API_URL", url_to_save)
        click.echo(f"Set OLLAMA_API_URL={url_to_save}")
        click.echo("Ollama typically runs locally; API keys are optional unless required by your setup.")

    if is_lmstudio:
        default_url = "http://localhost:1234"
        provided_url = questionary.text(
            f"Enter the LM Studio API URL (default: {default_url}):",
            default=default_url,
        ).ask()
        if provided_url is None:
            click.echo("LM Studio URL entry cancelled. Exiting.")
            return False
        url_to_save = provided_url.strip() if provided_url.strip() else default_url
        set_key(str(KITTYLOG_ENV_PATH), "LMSTUDIO_API_URL", url_to_save)
        click.echo(f"Set LMSTUDIO_API_URL={url_to_save}")
        click.echo("LM Studio typically runs locally; API keys are optional unless required by your setup.")

    # Handle Claude Code OAuth separately
    if is_claude_code:
        from kittylog.oauth.claude_code import authenticate_and_save, load_stored_token

        existing_token = load_stored_token()
        if existing_token:
            click.echo("\n✓ Claude Code access token already configured.")
            action = questionary.select(
                "What would you like to do?",
                choices=[
                    "Keep existing token",
                    "Re-authenticate (get new token)",
                ],
                use_shortcuts=True,
                use_arrow_keys=True,
                use_jk_keys=False,
            ).ask()

            if action is None or action.startswith("Keep existing"):
                if action is None:
                    click.echo("Claude Code configuration cancelled. Keeping existing token.")
                else:
                    click.echo("Keeping existing Claude Code token")
                return True
            else:
                click.echo("\n🔐 Starting Claude Code OAuth authentication...")
                if not authenticate_and_save(quiet=False):
                    click.echo("❌ Claude Code authentication failed. Keeping existing token.")
                    return False
                return True
        else:
            click.echo("\n🔐 Starting Claude Code OAuth authentication...")
            click.echo("   (Your browser will open automatically)\n")
            if not authenticate_and_save(quiet=False):
                click.echo("\n❌ Claude Code authentication failed. Exiting.")
                return False
            return True

    # Determine API key name based on provider
    if is_lmstudio:
        api_key_name = "LMSTUDIO_API_KEY"
    elif is_zai_provider:
        api_key_name = "ZAI_API_KEY"
    elif is_custom_anthropic:
        api_key_name = "CUSTOM_ANTHROPIC_API_KEY"
    elif is_custom_openai:
        api_key_name = "CUSTOM_OPENAI_API_KEY"
    else:
        api_key_name = f"{provider_key.upper().replace('-', '_')}_API_KEY"

    # Check if API key already exists
    existing_key = existing_env.get(api_key_name)

    if existing_key:
        # Key exists - offer options
        click.echo(f"\n{api_key_name} is already configured.")
        action = questionary.select(
            "What would you like to do?",
            choices=[
                "Keep existing key",
                "Enter new key",
            ],
            use_shortcuts=True,
            use_arrow_keys=True,
            use_jk_keys=False,
        ).ask()

        if action is None:
            click.echo("API key configuration cancelled. Keeping existing key.")
        elif action.startswith("Keep existing"):
            click.echo(f"Keeping existing {api_key_name}")
        elif action.startswith("Enter new"):
            api_key = questionary.password("Enter your new API key (input hidden):").ask()
            if api_key and api_key.strip():
                set_key(str(KITTYLOG_ENV_PATH), api_key_name, api_key)
                click.echo(f"Updated {api_key_name} (hidden)")
            else:
                click.echo(f"No key entered. Keeping existing {api_key_name}")
    else:
        # No existing key - prompt for new one
        api_key_prompt = "Enter your API key (input hidden, can be set later):"
        if is_ollama or is_lmstudio:
            click.echo(
                "This provider typically runs locally. API keys are optional unless your instance requires authentication."
            )
            api_key_prompt = "Enter your API key (optional, press Enter to skip):"

        api_key = questionary.password(api_key_prompt).ask()
        if api_key and api_key.strip():
            set_key(str(KITTYLOG_ENV_PATH), api_key_name, api_key)
            click.echo(f"Set {api_key_name} (hidden)")
        elif is_ollama or is_lmstudio:
            click.echo("Skipping API key. You can add one later if needed.")
        else:
            click.echo("No API key entered. You can add one later by editing ~/.kittylog.env")

    return True


@click.command()
def model() -> None:
    """Interactively update provider/model/API key without language prompts."""
    click.echo("Welcome to kittylog model configuration!\n")

    existing_env = _load_existing_env()
    if not _configure_model(existing_env):
        return

    click.echo(f"\nModel configuration complete. You can edit {KITTYLOG_ENV_PATH} to update values later.")
