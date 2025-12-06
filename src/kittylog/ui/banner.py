"""Kittylog banner ASCII art."""

BANNER = r"""
██╗  ██╗██╗████████╗████████╗██╗   ██╗██╗      ██████╗  ██████╗ 
██║ ██╔╝██║╚══██╔══╝╚══██╔══╝╚██╗ ██╔╝██║     ██╔═══██╗██╔════╝ 
█████╔╝ ██║   ██║      ██║    ╚████╔╝ ██║     ██║   ██║██║  ███╗
██╔═██╗ ██║   ██║      ██║     ╚██╔╝  ██║     ██║   ██║██║   ██║
██║  ██╗██║   ██║      ██║      ██║   ███████╗╚██████╔╝╚██████╔╝
╚═╝  ╚═╝╚═╝   ╚═╝      ╚═╝      ╚═╝   ╚══════╝ ╚═════╝  ╚═════╝                                        
"""

def print_banner(output_manager=None) -> None:
    """Print the kittylog banner."""
    if output_manager:
        output_manager.print(BANNER, style="bold magenta")
    else:
        print(BANNER)
