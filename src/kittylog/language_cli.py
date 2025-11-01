"""CLI for selecting changelog language interactively."""

from pathlib import Path

import click
import questionary
from dotenv import set_key, unset_key

from kittylog.constants import Languages

KITTYLOG_ENV_PATH = Path.home() / ".kittylog.env"


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
        except Exception:
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
        click.echo("\n  Section headings will be translated (e.g., '### Añadido')")
    else:
        click.echo("  KITTYLOG_TRANSLATE_HEADINGS=false")
        click.echo(f"\n  Section headings will remain in English while entries use {language_value}")
    click.echo(f"\n  Configuration saved to {KITTYLOG_ENV_PATH}")
