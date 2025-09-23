"""Unified output interface for consistent user messaging.

This module provides a centralized OutputManager class that standardizes all user-facing
output while maintaining Rich styling and global quiet/verbose control.
"""

from typing import Any

from rich.console import Console
from rich.panel import Panel


class OutputManager:
    """Unified interface for all user-facing output.

    Centralizes output handling to provide consistent styling, formatting,
    and control over quiet/verbose modes across the entire application.
    """

    def __init__(self, quiet: bool = False, verbose: bool = False, console: Console | None = None):
        """Initialize OutputManager with global control flags.

        Args:
            quiet: If True, suppress all non-error output
            verbose: If True, show additional informational output
            console: Optional Rich console instance (creates new if None)
        """
        self.quiet = quiet
        self.verbose = verbose
        self.console = console or Console()

    def info(self, message: str) -> None:
        """Output informational message.

        Args:
            message: The information message to display
        """
        if not self.quiet:
            self.console.print(f"[cyan]{message}[/cyan]")

    def success(self, message: str) -> None:
        """Output success message.

        Args:
            message: The success message to display
        """
        if not self.quiet:
            self.console.print(f"[green]✅ {message}[/green]")

    def warning(self, message: str) -> None:
        """Output warning message.

        Args:
            message: The warning message to display
        """
        # Warnings are shown even in quiet mode (but not errors)
        self.console.print(f"[yellow]⚠️  {message}[/yellow]")

    def error(self, message: str) -> None:
        """Output error message.

        Args:
            message: The error message to display
        """
        # Errors are always shown, regardless of quiet mode
        self.console.print(f"[red]❌ {message}[/red]")

    def processing(self, message: str) -> None:
        """Output processing status message.

        Args:
            message: The processing status message
        """
        if not self.quiet:
            self.console.print(f"[bold blue]{message}[/bold blue]")

    def debug(self, message: str) -> None:
        """Output debug message (only in verbose mode).

        Args:
            message: The debug message to display
        """
        if self.verbose and not self.quiet:
            self.console.print(f"[dim]🔍 {message}[/dim]")

    def panel(self, content: str, title: str, style: str = "cyan") -> None:
        """Output content in a styled panel.

        Args:
            content: The content to display in the panel
            title: The panel title
            style: The panel border style
        """
        if not self.quiet:
            self.console.print(Panel(content, title=title, border_style=style))

    def print(self, message: Any, **kwargs) -> None:
        """Direct access to Rich console print (for complex formatting).

        Args:
            message: Message to print
            **kwargs: Additional Rich console.print arguments
        """
        if not self.quiet:
            self.console.print(message, **kwargs)

    def echo(self, message: str) -> None:
        """Plain text output (Click.echo replacement).

        Args:
            message: Plain text message to display
        """
        if not self.quiet:
            self.console.print(message)


# Global output manager instance
output = OutputManager()


def set_output_mode(quiet: bool = False, verbose: bool = False) -> None:
    """Configure global output manager mode.

    Args:
        quiet: If True, suppress all non-error output
        verbose: If True, show additional informational output
    """
    global output
    output.quiet = quiet
    output.verbose = verbose


def get_output_manager() -> OutputManager:
    """Get the global output manager instance.

    Returns:
        The global OutputManager instance
    """
    return output
