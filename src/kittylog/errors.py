"""Error handling module for kittylog."""

import logging
import sys
from collections.abc import Callable
from typing import TypeVar

from kittylog.output import get_output_manager

logger = logging.getLogger(__name__)
T = TypeVar("T")


class KittylogError(Exception):
    """Base exception class for all kittylog errors."""

    exit_code = 1  # Default exit code

    def __init__(
        self,
        message: str,
        details: str | None = None,
        suggestion: str | None = None,
        exit_code: int | None = None,
        **kwargs,
    ):
        """
        Initialize a new KittylogError.

        Args:
            message: The error message
            details: Optional details about the error
            suggestion: Optional suggestion for the user
            exit_code: Optional exit code to override the class default
            **kwargs: Additional attributes to store
        """
        super().__init__(message)
        self.message = message
        self.details = details
        self.suggestion = suggestion
        if exit_code is not None:
            self.exit_code = exit_code
        # Store any additional keyword arguments as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)


class ConfigError(KittylogError):
    """Error related to configuration issues."""

    exit_code = 2

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_value: str | None = None,
        exit_code: int | None = None,
    ):
        """Initialize a ConfigError with additional configuration-specific details.

        Args:
            message: The error message
            config_key: The configuration key that caused the error
            config_value: The configuration value that caused the error
            exit_code: Optional exit code to override the default
        """
        super().__init__(message, exit_code=exit_code)
        self.config_key = config_key
        self.config_value = config_value


class GitError(KittylogError):
    """Error related to Git operations."""

    exit_code = 3

    def __init__(
        self,
        message: str,
        command: str | None = None,
        exit_code: int | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
    ):
        """Initialize a GitError with additional Git-specific details.

        Args:
            message: The error message
            command: The Git command that failed
            exit_code: The exit code from the Git command
            stdout: The stdout from the Git command
            stderr: The stderr from the Git command
        """
        super().__init__(message, exit_code=exit_code)
        self.command = command
        self.stdout = stdout
        self.stderr = stderr


class AIError(KittylogError):
    """Error related to AI provider or models."""

    exit_code = 4

    def __init__(self, message: str, error_type: str = "unknown", exit_code: int | None = None, **kwargs):
        """Initialize an AIError with a specific error type.

        Args:
            message: The error message
            error_type: The type of AI error (from AI_ERROR_CODES keys)
            exit_code: Optional exit code to override the default
            **kwargs: Additional attributes to store
        """
        super().__init__(message, exit_code=exit_code, **kwargs)
        self.error_type = error_type
        self.error_code = AI_ERROR_CODES.get(error_type, AI_ERROR_CODES["unknown"])
        # Store any additional keyword arguments as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def authentication_error(cls, message: str) -> "AIError":
        """Create an authentication error."""
        return cls(message, error_type="authentication")

    @classmethod
    def connection_error(cls, message: str) -> "AIError":
        """Create a connection error."""
        return cls(message, error_type="connection")

    @classmethod
    def rate_limit_error(cls, message: str) -> "AIError":
        """Create a rate limit error."""
        return cls(message, error_type="rate_limit")

    @classmethod
    def timeout_error(cls, message: str) -> "AIError":
        """Create a timeout error."""
        return cls(message, error_type="timeout")

    @classmethod
    def model_error(cls, message: str) -> "AIError":
        """Create a model error."""
        return cls(message, error_type="model")

    @classmethod
    def generation_error(cls, message: str) -> "AIError":
        """Create a generation error."""
        return cls(message, error_type="generation")


class ChangelogError(KittylogError):
    """Error related to changelog operations."""

    exit_code = 5

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        line_number: int | None = None,
        line_content: str | None = None,
        expected_format: str | None = None,
        exit_code: int | None = None,
    ):
        """Initialize a ChangelogError with additional changelog-specific details.

        Args:
            message: The error message
            file_path: Path to the changelog file
            line_number: Line number where the error occurred
            line_content: Content of the line that caused the error
            expected_format: Expected format for the line
            exit_code: Optional exit code to override the default
        """
        super().__init__(message, exit_code=exit_code)
        self.file_path = file_path
        self.line_number = line_number
        self.line_content = line_content
        self.expected_format = expected_format


# Error codes for AI errors
AI_ERROR_CODES = {
    "authentication": 401,  # Authentication failures
    "connection": 503,  # Connection issues
    "rate_limit": 429,  # Rate limits
    "timeout": 408,  # Timeouts
    "model": 400,  # Model-related errors
    "generation": 500,  # Generation failures
    "unknown": 500,  # Unknown errors
}


def handle_error(error: Exception, exit_program: bool = False, quiet: bool = False) -> None:
    """Handle an error with proper logging and user feedback.

    Args:
        error: The error to handle
        exit_program: If True, exit the program after handling the error
        quiet: If True, suppress non-error output
    """

    error_message = format_error_for_user(error)
    output = get_output_manager()
    output.error(error_message)
    logger.error(f"Error: {str(error)}")

    if isinstance(error, GitError):
        logger.error("Git operation failed. Please check your repository status.")
    elif isinstance(error, AIError):
        logger.error("AI operation failed. Please check your configuration and API keys.")
    elif isinstance(error, ChangelogError):
        logger.error("Changelog operation failed. Please check your changelog file and permissions.")
    else:
        logger.error("An unexpected error occurred.")

    if exit_program:
        logger.error("Exiting program due to error.")
        sys.exit(error.exit_code if hasattr(error, "exit_code") else 1)


def format_error_for_user(error: Exception) -> str:
    """
    Format an error message for display to the user.

    Args:
        error: The exception to format

    Returns:
        A user-friendly error message with remediation steps if applicable
    """
    base_message = str(error)

    # More specific remediation for AI errors based on error type
    if isinstance(error, AIError):
        if hasattr(error, "error_type"):
            if error.error_type == "authentication":
                return f"{base_message}\n\nPlease check your API key and ensure it is valid."
            elif error.error_type == "connection":
                return f"{base_message}\n\nPlease check your internet connection and try again."
            elif error.error_type == "rate_limit":
                return f"{base_message}\n\nYou've hit the rate limit for this AI provider. Please wait and try again later."
            elif error.error_type == "timeout":
                return f"{base_message}\n\nThe request timed out. Please try again or use a different model."
            elif error.error_type == "model":
                return f"{base_message}\n\nPlease check that the specified model exists and is available to you."
            elif error.error_type == "generation":
                return (
                    f"{base_message}\n\nThe AI failed to generate content. Please try again with different parameters."
                )
        return f"{base_message}\n\nPlease check your API key, model name, and internet connection."

    # Mapping of error types to remediation steps
    remediation_steps = {
        ConfigError: "Please check your configuration settings.",
        GitError: "Please ensure Git is installed and you're in a valid Git repository.",
        ChangelogError: "Please check your changelog file permissions and format.",
    }

    # Generic remediation for unexpected errors
    if not any(isinstance(error, t) for t in remediation_steps.keys()):
        return f"{base_message}\n\nIf this issue persists, please report it as a bug."

    # Get remediation steps for the specific error type
    for error_class, steps in remediation_steps.items():
        if isinstance(error, error_class):
            return f"{base_message}\n\n{steps}"

    # Fallback (though we should never reach this)
    return base_message


def with_error_handling(
    error_type: type[KittylogError], error_message: str, quiet: bool = False, exit_on_error: bool = True
) -> Callable[[Callable[..., T]], Callable[..., T | None]]:
    """
    A decorator that wraps a function with standardized error handling.

    Args:
        error_type: The specific error type to raise if an exception occurs
        error_message: The error message to use
        quiet: If True, suppress non-error output
        exit_on_error: If True, exit the program on error

    Returns:
        A decorator function that handles errors for the wrapped function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T | None]:
        def wrapper(*args, **kwargs) -> T | None:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Create a specific error with our message and the original error
                specific_error = error_type(f"{error_message}: {e}")
                # Handle the error using our standardized handler
                handle_error(specific_error, quiet=quiet, exit_program=exit_on_error)
                return None

        return wrapper

    return decorator
