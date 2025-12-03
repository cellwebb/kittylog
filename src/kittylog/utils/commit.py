"""Commit formatting utilities for kittylog."""


def format_commit_for_display(commit: dict, max_message_length: int | None = None, max_files: int | None = None) -> str:
    """Format a commit dictionary for display.

    Args:
        commit: Commit dictionary with hash, message, author, date, and files
        max_message_length: Optional maximum length for commit message
        max_files: Optional maximum number of files to display

    Returns:
        Formatted commit string
    """
    short_hash = commit.get("short_hash", commit.get("hash", "")[:8])
    message = commit.get("message", "")
    author = commit.get("author", "")
    date = commit.get("date", "")
    files = commit.get("files", [])

    # Format message
    if max_message_length and len(message) > max_message_length:
        message = message[:max_message_length] + "..."

    # Split into first line and rest
    message_lines = message.split("\n", 1)
    first_line = message_lines[0].strip()
    rest_of_message = message_lines[1].strip() if len(message_lines) > 1 else ""

    # Format files
    files_display = ""
    if files and max_files:
        file_list = files[:max_files]
        if len(files) > max_files:
            file_list.append(f"... and {len(files) - max_files} more")
        files_display = f" [{', '.join(file_list)}]"
    elif files:
        files_display = f" [{', '.join(files)}]"

    # Build result
    result = f"{short_hash}: {first_line}{files_display}"

    # Add author if available
    if author:
        result += f" ({author})"

    # Add date if available
    if date:
        result += f" {date}"

    # Add rest of message if available
    if rest_of_message:
        result += f"\n    {rest_of_message}"

    return result
