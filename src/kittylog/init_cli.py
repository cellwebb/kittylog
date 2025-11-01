"""CLI for initializing kittylog configuration interactively."""

from pathlib import Path

import click
import questionary
from dotenv import set_key

from kittylog.constants import Audiences, Languages

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


@click.command()
def init() -> None:
    """Interactively set up $HOME/.kittylog.env for kittylog."""
    kittylog_env_path = KITTYLOG_ENV_PATH

    if hasattr(init, "_mock_env_path"):
        kittylog_env_path = init._mock_env_path

    click.echo("Welcome to kittylog initialization!\n")
    if kittylog_env_path.exists():
        click.echo(f"$HOME/.kittylog.env already exists at {kittylog_env_path}. Values will be updated.")
    else:
        kittylog_env_path.touch()
        click.echo(f"Created $HOME/.kittylog.env at {kittylog_env_path}.")

    providers = [
        ("Anthropic", "claude-3-5-haiku-latest"),
        ("Cerebras", "qwen-3-coder-480b"),
        ("Chutes", "zai-org/GLM-4.6-FP8"),
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
    provider = questionary.select("Select your provider:", choices=provider_names).ask()
    if not provider:
        click.echo("Provider selection cancelled. Exiting.")
        return

    provider_key = provider.lower().replace(".", "").replace(" ", "-").replace("(", "").replace(")", "")

    is_streamlake = provider_key == "streamlake"
    is_zai_provider = provider_key in {"zai", "zai-coding"}
    is_custom_anthropic = provider_key == "custom-anthropic"
    is_custom_openai = provider_key == "custom-openai"
    is_ollama = provider_key == "ollama"
    is_lmstudio = provider_key == "lm-studio"

    if is_streamlake:
        endpoint_id = _prompt_required_text("Enter the Streamlake inference endpoint ID (required):")
        if endpoint_id is None:
            click.echo("Streamlake configuration cancelled. Exiting.")
            return
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
            return
        model_to_save = model.strip() if model.strip() else model_suggestion

    set_key(str(kittylog_env_path), "KITTYLOG_MODEL", f"{provider_key}:{model_to_save}")
    click.echo(f"Set KITTYLOG_MODEL={provider_key}:{model_to_save}")

    if is_custom_anthropic:
        base_url = _prompt_required_text("Enter the custom Anthropic-compatible base URL (required):")
        if base_url is None:
            click.echo("Custom Anthropic base URL entry cancelled. Exiting.")
            return
        set_key(str(kittylog_env_path), "CUSTOM_ANTHROPIC_BASE_URL", base_url)
        click.echo(f"Set CUSTOM_ANTHROPIC_BASE_URL={base_url}")

        api_version = questionary.text(
            "Enter the API version (press Enter for default 2023-06-01):",
            default="2023-06-01",
        ).ask()
        if api_version and api_version.strip() and api_version.strip() != "2023-06-01":
            set_key(str(kittylog_env_path), "CUSTOM_ANTHROPIC_VERSION", api_version.strip())
            click.echo(f"Set CUSTOM_ANTHROPIC_VERSION={api_version.strip()}")

    if is_custom_openai:
        base_url = _prompt_required_text("Enter the custom OpenAI-compatible base URL (required):")
        if base_url is None:
            click.echo("Custom OpenAI base URL entry cancelled. Exiting.")
            return
        set_key(str(kittylog_env_path), "CUSTOM_OPENAI_BASE_URL", base_url)
        click.echo(f"Set CUSTOM_OPENAI_BASE_URL={base_url}")

    if is_ollama:
        default_url = "http://localhost:11434"
        provided_url = questionary.text(
            f"Enter the Ollama API URL (default: {default_url}):",
            default=default_url,
        ).ask()
        if provided_url is None:
            click.echo("Ollama URL entry cancelled. Exiting.")
            return
        url_to_save = provided_url.strip() if provided_url.strip() else default_url
        set_key(str(kittylog_env_path), "OLLAMA_API_URL", url_to_save)
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
            return
        url_to_save = provided_url.strip() if provided_url.strip() else default_url
        set_key(str(kittylog_env_path), "LMSTUDIO_API_URL", url_to_save)
        click.echo(f"Set LMSTUDIO_API_URL={url_to_save}")
        click.echo("LM Studio typically runs locally; API keys are optional unless required by your setup.")

    api_key_prompt = "Enter your API key (input hidden, can be set later):"
    if is_ollama or is_lmstudio:
        api_key_prompt = "Enter your API key (optional, press Enter to skip):"

    api_key = questionary.password(api_key_prompt).ask()
    if api_key:
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
        set_key(str(kittylog_env_path), api_key_name, api_key)
        click.echo(f"Set {api_key_name} (hidden)")
    elif is_ollama or is_lmstudio:
        click.echo("Skipping API key. You can add one later if needed.")

    # Language selection mirrors gac's i18n flow
    click.echo("\n")
    display_names = [lang[0] for lang in Languages.LANGUAGES]
    language_selection = questionary.select(
        "Select a language for changelog entries:", choices=display_names, use_shortcuts=True, use_arrow_keys=True
    ).ask()

    if not language_selection:
        click.echo("Language selection cancelled. Using English (default).")
    elif language_selection == "English":
        click.echo("Set language to English (default)")
    else:
        if language_selection == "Custom":
            custom_language = questionary.text("Enter the language name (e.g., 'Spanish', 'Français', '日本語'):").ask()
            if not custom_language or not custom_language.strip():
                click.echo("No language entered. Using English (default).")
                language_value = None
            else:
                language_value = custom_language.strip()
        else:
            language_value = next(lang[1] for lang in Languages.LANGUAGES if lang[0] == language_selection)

        if language_value:
            heading_choice = questionary.select(
                "How should changelog section headings be handled?",
                choices=[
                    "Keep section headings in English (Added, Changed, etc.)",
                    f"Translate section headings into {language_value}",
                ],
            ).ask()

            if not heading_choice:
                click.echo("Section heading selection cancelled. Using English headings.")
                translate_headings = False
            else:
                translate_headings = heading_choice.startswith("Translate section headings")

            set_key(str(kittylog_env_path), "KITTYLOG_LANGUAGE", language_value)
            set_key(str(kittylog_env_path), "KITTYLOG_TRANSLATE_HEADINGS", "true" if translate_headings else "false")
            click.echo(f"Set KITTYLOG_LANGUAGE={language_value}")
            click.echo(f"Set KITTYLOG_TRANSLATE_HEADINGS={'true' if translate_headings else 'false'}")

    click.echo("")

    audience_choices = [
        questionary.Choice(
            title=f"{label} — {description}",
            value=slug,
        )
        for label, slug, description in Audiences.OPTIONS
    ]

    audience_selection = questionary.select(
        "Who's the primary audience for your changelog updates?", choices=audience_choices
    ).ask()

    if not audience_selection:
        click.echo("Audience selection cancelled. Using developers (default).")
    else:
        set_key(str(kittylog_env_path), "KITTYLOG_AUDIENCE", audience_selection)
        click.echo(f"Set KITTYLOG_AUDIENCE={audience_selection}")

    click.echo(f"\nkittylog environment setup complete. You can edit {kittylog_env_path} to update values later.")
