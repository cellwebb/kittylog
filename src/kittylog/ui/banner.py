"""Kittylog banner ASCII art."""

import colorsys
from rich.text import Text

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
    if not output_manager:
        print(BANNER)
        return

    # Create rainbow text
    lines = BANNER.strip("\n").splitlines()
    text = Text()
    
    for y, line in enumerate(lines):
        length = len(line)
        for x, char in enumerate(line):
            # Calculate hue based on position to create a rainbow effect
            # We offset the hue by the y position slightly to create a diagonal gradient
            hue = (x / (length or 1) + y / 10) % 1.0
            r, g, b = colorsys.hls_to_rgb(hue, 0.6, 1.0)
            
            # Format hex color
            color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            
            text.append(char, style=f"bold {color}")
        text.append("\n")

    output_manager.print(text)
