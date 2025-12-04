"""General utility constants."""

import os


class Utility:
    """General utility constants."""

    DEFAULT_ENCODING: str = "cl100k_base"  # LLM encoding
    MAX_WORKERS: int = os.cpu_count() or 4  # Maximum number of parallel workers
    DEFAULT_MAX_MESSAGE_LENGTH: int = 80  # Default max length for commit messages
    DEFAULT_MAX_FILES: int = 5  # Default max number of files to display
