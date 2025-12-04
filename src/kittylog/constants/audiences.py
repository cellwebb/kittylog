"""Audience presets for changelog tone and focus."""

from collections.abc import Iterator


class Audiences:
    """Audience presets for changelog tone and focus."""

    OPTIONS: list[tuple[str, str, str]] = [
        (
            "Developers (engineering-focused)",
            "developers",
            "Highlight implementation details, APIs, and technical nuances.",
        ),
        ("End Users (product-focused)", "users", "Explain benefits, UX improvements, and bug fixes in plain language."),
        ("Product & Stakeholders", "stakeholders", "Emphasize business impact, outcomes, and strategic context."),
    ]

    _ALIAS_MAP: dict[str, str] = {
        "developer": "developers",
        "dev": "developers",
        "devs": "developers",
        "engineering": "developers",
        "eng": "developers",
        "user": "users",
        "customers": "users",
        "customer": "users",
        "product": "stakeholders",
        "stakeholder": "stakeholders",
        "stakeholders": "stakeholders",
        "pm": "stakeholders",
        "management": "stakeholders",
    }

    @classmethod
    def slugs(cls) -> list[str]:
        """Return supported audience identifiers."""
        return [option[1] for option in cls.OPTIONS]

    @classmethod
    def resolve(cls, value: str | None) -> str:
        """Resolve a raw audience value to a supported slug."""
        # Import here to avoid circular imports
        from .env_defaults import EnvDefaults

        if not value:
            return EnvDefaults.AUDIENCE
        slug = value.strip().lower()
        if slug in cls._ALIAS_MAP:
            return cls._ALIAS_MAP[slug]
        if slug in cls.slugs():
            return slug
        return EnvDefaults.AUDIENCE

    @classmethod
    def display(cls, slug: str) -> str:
        """Return display label for slug."""
        for label, value, _ in cls.OPTIONS:
            if value == slug:
                return label
        return slug.title()

    @classmethod
    def __iter__(cls) -> Iterator[str]:
        """Make the class iterable over its audience options."""
        return iter(cls.slugs())
