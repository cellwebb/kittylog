"""System utilities for kittylog."""

import subprocess
from typing import Any, NoReturn


def run_subprocess_with_encoding(
    cmd: list[str],
    encoding: str | None = None,
    capture_output: bool = True,
    text: bool = True,
    check: bool = False,
) -> subprocess.CompletedProcess[Any]:
    """Run subprocess with automatic encoding fallback.

    Args:
        cmd: Command to run as list of strings
        encoding: Optional encoding to use
        capture_output: Whether to capture stdout/stderr
        text: Whether to decode output as text
        check: Whether to raise exception on non-zero exit

    Returns:
        CompletedProcess with results
    """
    from kittylog.utils_logging import get_safe_encodings

    encodings_to_try = [*get_safe_encodings(), encoding] if encoding else []

    last_error = None
    for enc in encodings_to_try:
        try:
            return subprocess.run(
                cmd,
                capture_output=capture_output,
                text=text,
                encoding=enc,
                check=check,
            )
        except (UnicodeDecodeError, UnicodeError) as e:
            last_error = e
            continue

    # If all encodings failed, raise the last error
    if last_error:
        raise last_error

    # Default fallback with no encoding
    return subprocess.run(
        cmd,
        capture_output=capture_output,
        text=text,
        encoding=encoding,
        check=check,
    )


def run_subprocess(
    cmd: list[str],
    encoding: str | None = None,
    capture_output: bool = True,
    text: bool = True,
    check: bool = False,
) -> str:
    """Run subprocess and return stdout as string.

    Args:
        cmd: Command to run as list of strings
        encoding: Optional encoding to use
        capture_output: Whether to capture stdout/stderr
        text: Whether to decode output as text
        check: Whether to raise exception on non-zero exit

    Returns:
        Command output as string

    Raises:
        subprocess.CalledProcessError: If command fails and check=True
        UnicodeDecodeError: If output cannot be decoded with any encoding
    """
    result = run_subprocess_with_encoding(
        cmd=cmd,
        encoding=encoding,
        capture_output=capture_output,
        text=text,
        check=check,
    )
    return result.stdout


def exit_with_error(message: str, exit_code: int = 1) -> NoReturn:
    """Exit the program with an error message.

    Args:
        message: Error message to display
        exit_code: Exit code to use
    """
    from kittylog.utils_logging import print_message

    print_message(message, "error")
    exit(exit_code)
