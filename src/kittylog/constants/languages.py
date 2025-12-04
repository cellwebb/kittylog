"""Language code mappings and utilities for changelog generation."""

from collections.abc import Iterator


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

    @classmethod
    def __iter__(cls) -> Iterator[tuple[str, str]]:
        """Make the class iterable over its language options."""
        return iter(cls.LANGUAGES)
