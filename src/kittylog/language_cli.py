"""CLI for selecting changelog language interactively."""

import os
from pathlib import Path

import click
import questionary
from dotenv import load_dotenv, set_key, unset_key

from kittylog.constants import Audiences, Languages

KITTYLOG_ENV_PATH = Path.home() / ".kittylog.env"


def configure_language_init_workflow(env_path: Path | str) -> bool:
    """Configure language as part of init workflow.

    This is used by init_cli.py to handle language configuration
    when the init command is run.

    Args:
        env_path: Path to the environment file

    Returns:
        True if language configuration succeeded, False if cancelled
    """
    try:
        # Use the provided path instead of our default KITTYLOG_ENV_PATH
        temp_env_path = Path(env_path) if isinstance(env_path, str) else env_path

        # If no env file, create it and proceed directly to language selection
        if not temp_env_path.exists():
            language_value = _run_language_selection_flow(temp_env_path)
            if language_value is not None:
                _configure_audience(temp_env_path)
            return language_value is not None

        # Clear any existing environ state to avoid cross-test contamination
        env_keys_to_clear = [k for k in os.environ if k.startswith("KITTYLOG_")]
        for key in env_keys_to_clear:
            del os.environ[key]

        # File exists - check for existing language
        load_dotenv(temp_env_path)
        existing_language = os.getenv("KITTYLOG_LANGUAGE")

        if existing_language:
            # Language already exists - ask what to do
            preserve_action = questionary.select(
                f"Found existing language: {existing_language}. How would you like to proceed?",
                choices=[
                    f"Keep existing language ({existing_language})",
                    "Select new language",
                ],
                use_shortcuts=True,
                use_arrow_keys=True,
                use_jk_keys=False,
            ).ask()

            if not preserve_action:
                click.echo("Language configuration cancelled. Proceeding with init...")
                return True  # Continue with init, just skip language part

            if preserve_action.startswith("Keep existing language"):
                click.echo(f"Keeping existing language: {existing_language}")
                _configure_audience(temp_env_path)
                return True

            # User wants to select new language
            language_value = _run_language_selection_flow(temp_env_path)
            if language_value is not None:
                _configure_audience(temp_env_path)
                return True
            else:
                click.echo("Language selection cancelled. Proceeding with init...")
                return True  # Continue with init, just skip language part
        else:
            # No existing language
            language_value = _run_language_selection_flow(temp_env_path)
            if language_value is not None:
                _configure_audience(temp_env_path)
                return language_value is not None
            else:
                click.echo("Language selection cancelled. Proceeding with init...")
                return True  # Continue with init, just skip language part

    except (OSError, ValueError, KeyboardInterrupt) as e:
        click.echo(f"Language configuration error: {e}")
        return False


def _run_language_selection_flow(env_path: Path) -> str | None:
    """Run the language selection flow and return the selected language.

    Args:
        env_path: Path to the environment file

    Returns:
        Selected language value, or None if cancelled
    """
    display_names = [lang[0] for lang in Languages.LANGUAGES]
    language_selection = questionary.select(
        "Select a language for changelog entries:", choices=display_names, use_shortcuts=True, use_arrow_keys=True
    ).ask()

    if not language_selection:
        click.echo("Language selection cancelled. Using English (default).")
        return None
    elif language_selection == "English":
        click.echo("Set language to English (default)")
        try:
            unset_key(str(env_path), "KITTYLOG_LANGUAGE")
            unset_key(str(env_path), "KITTYLOG_TRANSLATE_HEADINGS")
        except (KeyError, OSError):
            # It's okay if unsetting fails - file might not exist or key not set
            pass
        return None
    else:
        if language_selection == "Custom":
            custom_language = questionary.text("Enter the language name (e.g., 'Spanish', 'Français', '日本語'):").ask()
            if not custom_language or not custom_language.strip():
                click.echo("No language entered. Using English (default).")
                return None
            else:
                language_value = custom_language.strip()
        else:
            language_value = next(lang[1] for lang in Languages.LANGUAGES if lang[0] == language_selection)

        heading_choice = questionary.select(
            "How should changelog section headings be handled?",
            choices=[
                "Keep section headings in English",
                f"Translate section headings into {language_value}",
            ],
        ).ask()

        if not heading_choice:
            click.echo("Section heading selection cancelled. Using English headings.")
            translate_headings = False
        else:
            translate_headings = heading_choice.startswith("Translate section headings")

        set_key(str(env_path), "KITTYLOG_LANGUAGE", language_value)
        set_key(str(env_path), "KITTYLOG_TRANSLATE_HEADINGS", "true" if translate_headings else "false")
        click.echo(f"Set KITTYLOG_LANGUAGE={language_value}")
        click.echo(f"Set KITTYLOG_TRANSLATE_HEADINGS={'true' if translate_headings else 'false'}")
        return language_value


def _configure_audience(env_path: Path) -> None:
    """Configure the audience for changelog entries."""
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
        set_key(str(env_path), "KITTYLOG_AUDIENCE", audience_selection)
        click.echo(f"Set KITTYLOG_AUDIENCE={audience_selection}")


@click.command()
def language() -> None:
    """Set the language for changelog entries interactively."""
    click.echo("Select a language for kittylog changelog entries:\n")

    display_names = [lang[0] for lang in Languages.LANGUAGES]
    selection = questionary.select(
        "Choose your language:", choices=display_names, use_shortcuts=True, use_arrow_keys=True
    ).ask()

    if not selection:
        click.echo("Language selection cancelled.")
        return

    if not KITTYLOG_ENV_PATH.exists():
        KITTYLOG_ENV_PATH.touch()
        click.echo(f"Created {KITTYLOG_ENV_PATH}")

    if selection == "English":
        try:
            unset_key(str(KITTYLOG_ENV_PATH), "KITTYLOG_LANGUAGE")
            unset_key(str(KITTYLOG_ENV_PATH), "KITTYLOG_TRANSLATE_HEADINGS")
            click.echo("✓ Set language to English (default)")
            click.echo(f"  Removed KITTYLOG_LANGUAGE from {KITTYLOG_ENV_PATH}")
        except (KeyError, OSError):
            # It's okay if env file operations fail - continue with default
            click.echo("✓ Set language to English (default)")
        return

    if selection == "Custom":
        custom_language = questionary.text("Enter the language name (e.g., 'Spanish', 'Français', '日本語'):").ask()
        if not custom_language or not custom_language.strip():
            click.echo("No language entered. Cancelled.")
            return
        language_value = custom_language.strip()
    else:
        language_value = next(lang[1] for lang in Languages.LANGUAGES if lang[0] == selection)

    click.echo()  # spacing
    heading_choice = questionary.select(
        "How should changelog section headings be handled?",
        choices=[
            "Keep section headings in English (Added, Changed, etc.)",
            f"Translate section headings into {language_value}",
        ],
    ).ask()

    if not heading_choice:
        click.echo("Section heading selection cancelled.")
        return

    translate_headings = heading_choice.startswith("Translate section headings")

    set_key(str(KITTYLOG_ENV_PATH), "KITTYLOG_LANGUAGE", language_value)
    set_key(str(KITTYLOG_ENV_PATH), "KITTYLOG_TRANSLATE_HEADINGS", "true" if translate_headings else "false")

    click.echo(f"\n✓ Set language to {selection}")
    click.echo(f"  KITTYLOG_LANGUAGE={language_value}")
    if translate_headings:
        click.echo("  KITTYLOG_TRANSLATE_HEADINGS=true")
        click.echo(f"\n  Section headings will be translated into {language_value}")
    else:
        click.echo("  KITTYLOG_TRANSLATE_HEADINGS=false")
        click.echo(f"\n  Section headings will remain in English while entries use {language_value}")
    click.echo(f"\n  Configuration saved to {KITTYLOG_ENV_PATH}")
