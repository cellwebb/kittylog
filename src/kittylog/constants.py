"""Constants for the Changelog Updater project."""

import os
from enum import Enum


class FileStatus(Enum):
    """File status for Git operations."""

    MODIFIED = "M"
    ADDED = "A"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNTRACKED = "?"


class GroupingMode(str, Enum):
    """Grouping modes for changelog entries."""
    
    TAGS = "tags"
    DATES = "dates"
    GAPS = "gaps"


class DateGrouping(str, Enum):
    """Date grouping strategies."""
    
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class EnvDefaults:
    """Default values for environment variables."""

    MAX_RETRIES: int = 3
    TEMPERATURE: float = 1.0
    MAX_OUTPUT_TOKENS: int = 1024
    WARNING_LIMIT_TOKENS: int = 16384
    GROUPING_MODE: str = GroupingMode.TAGS.value
    GAP_THRESHOLD_HOURS: float = 4.0
    DATE_GROUPING: str = DateGrouping.DAILY.value
    TRANSLATE_HEADINGS: bool = False
    AUDIENCE: str = "stakeholders"


class Logging:
    """Logging configuration constants."""

    DEFAULT_LEVEL: str = "WARNING"
    LEVELS: list[str] = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Utility:
    """General utility constants."""

    DEFAULT_ENCODING: str = "cl100k_base"  # LLM encoding
    MAX_WORKERS: int = os.cpu_count() or 4  # Maximum number of parallel workers
    DEFAULT_MAX_MESSAGE_LENGTH: int = 80  # Default max length for commit messages
    DEFAULT_MAX_FILES: int = 5  # Default max number of files to display


class ChangelogSections:
    """Standard changelog sections."""

    ADDED = "Added"
    CHANGED = "Changed"
    DEPRECATED = "Deprecated"
    REMOVED = "Removed"
    FIXED = "Fixed"
    SECURITY = "Security"

    ALL_SECTIONS = [ADDED, CHANGED, DEPRECATED, REMOVED, FIXED, SECURITY]


class CommitKeywords:
    """Keywords for categorizing commits."""

    FEATURE_KEYWORDS = ["feat:", "feature:", "add", "new", "implement", "introduce"]
    FIX_KEYWORDS = ["fix:", "bugfix:", "hotfix:", "fix", "bug", "issue", "problem", "error"]
    BREAKING_KEYWORDS = ["break:", "breaking:", "BREAKING CHANGE"]
    REMOVE_KEYWORDS = ["remove:", "delete:", "drop", "remove", "delete"]
    DEPRECATE_KEYWORDS = ["deprecate:", "deprecate"]
    SECURITY_KEYWORDS = ["security:", "sec:", "security", "vulnerability", "cve"]
    CHANGE_KEYWORDS = ["update", "change", "modify", "improve", "enhance", "refactor"]


class Languages:
    """Language code mappings and utilities for changelog generation."""

    CODE_MAP: dict[str, str] = {
        "en": "English",
        "zh": "Simplified Chinese",
        "zh-cn": "Simplified Chinese",
        "zh-hans": "Simplified Chinese",
        "zh-tw": "Traditional Chinese",
        "zh-hant": "Traditional Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "es": "Spanish",
        "pt": "Portuguese",
        "fr": "French",
        "de": "German",
        "ru": "Russian",
        "hi": "Hindi",
        "it": "Italian",
        "pl": "Polish",
        "tr": "Turkish",
        "nl": "Dutch",
        "vi": "Vietnamese",
        "th": "Thai",
        "id": "Indonesian",
        "sv": "Swedish",
        "ar": "Arabic",
        "he": "Hebrew",
        "el": "Greek",
        "da": "Danish",
        "no": "Norwegian",
        "nb": "Norwegian",
        "nn": "Norwegian",
        "fi": "Finnish",
    }

    LANGUAGES: list[tuple[str, str]] = [
        ("English", "English"),
        ("简体中文", "Simplified Chinese"),
        ("繁體中文", "Traditional Chinese"),
        ("日本語", "Japanese"),
        ("한국어", "Korean"),
        ("Español", "Spanish"),
        ("Português", "Portuguese"),
        ("Français", "French"),
        ("Deutsch", "German"),
        ("Русский", "Russian"),
        ("हिन्दी", "Hindi"),
        ("Italiano", "Italian"),
        ("Polski", "Polish"),
        ("Türkçe", "Turkish"),
        ("Nederlands", "Dutch"),
        ("Tiếng Việt", "Vietnamese"),
        ("ไทย", "Thai"),
        ("Bahasa Indonesia", "Indonesian"),
        ("Svenska", "Swedish"),
        ("العربية", "Arabic"),
        ("עברית", "Hebrew"),
        ("Ελληνικά", "Greek"),
        ("Dansk", "Danish"),
        ("Norsk", "Norwegian"),
        ("Suomi", "Finnish"),
        ("Custom", "Custom"),
    ]

    @staticmethod
    def resolve_code(language: str) -> str:
        """Resolve a language code to its full name."""
        code_lower = language.lower().strip()
        if code_lower in Languages.CODE_MAP:
            return Languages.CODE_MAP[code_lower]
        return language


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
