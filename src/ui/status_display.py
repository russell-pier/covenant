#!/usr/bin/env python3
"""
Status display UI component for the 2D Minecraft-like game

Handles rendering of status information, debug info, and other UI elements.
"""

import tcod
from typing import Tuple, Optional
from ..config import get_config


class StatusDisplay:
    """Handles rendering of status information and UI overlays."""
    
    def __init__(self):
        self.frame_count = 0
        self.config = get_config()

        # Initialize display settings from config
        self.show_debug = self.config.debug.show_debug_on_startup
        self.show_coordinates = self.config.debug.show_coordinates_on_startup
        self.show_fps = self.config.debug.show_fps_on_startup

        # Colors from configuration
        self.info_color = self.config.ui.info_color
        self.debug_color = self.config.ui.debug_color
        self.warning_color = self.config.ui.warning_color
    
    def update_frame_count(self):
        """Increment the frame counter."""
        self.frame_count += 1
    
    def render_floating_container(self, console, content_lines: list, position: str = "top",
                                 max_lines: int = None, bg_color: tuple = None):
        """
        Render a full-width floating container with box drawing borders.

        Args:
            console: The tcod console to render to
            content_lines: List of strings to display inside the container
            position: "top" or "bottom" for container placement
            max_lines: Maximum number of content lines to display
            bg_color: Background color for the container
        """
        if not content_lines:
            return

        screen_width = console.width
        screen_height = console.height

        # Full width with 2-character margins
        container_width = screen_width - 4  # 2 character margin on each side
        inner_width = container_width - 4  # Account for left/right borders and padding

        # Limit content lines if max_lines specified
        if max_lines:
            content_lines = content_lines[:max_lines]

        # Container height: borders + content (no title)
        container_height = len(content_lines) + 2  # Top and bottom borders only

        # Calculate position (2-character margin from left edge)
        start_x = 2  # 2 characters from left edge

        if position == "top":
            start_y = 1  # 1 space from top edge
        else:  # bottom
            start_y = screen_height - container_height - 1  # 1 space from bottom edge

        # Use provided background color or config default
        container_bg = bg_color if bg_color else self.config.ui.panel_background

        # Draw container background
        for y in range(container_height):
            for x in range(container_width):
                console.print(start_x + x, start_y + y, " ", fg=self.info_color, bg=container_bg)

        # Draw borders using box drawing characters
        border_color = self.config.ui.border_color

        # Top border
        console.print(start_x, start_y, "┌", fg=border_color, bg=container_bg)
        for x in range(1, container_width - 1):
            console.print(start_x + x, start_y, "─", fg=border_color, bg=container_bg)
        console.print(start_x + container_width - 1, start_y, "┐", fg=border_color, bg=container_bg)

        # Bottom border
        bottom_y = start_y + container_height - 1
        console.print(start_x, bottom_y, "└", fg=border_color, bg=container_bg)
        for x in range(1, container_width - 1):
            console.print(start_x + x, bottom_y, "─", fg=border_color, bg=container_bg)
        console.print(start_x + container_width - 1, bottom_y, "┘", fg=border_color, bg=container_bg)

        # Side borders
        for y in range(1, container_height - 1):
            console.print(start_x, start_y + y, "│", fg=border_color, bg=container_bg)
            console.print(start_x + container_width - 1, start_y + y, "│", fg=border_color, bg=container_bg)

        # Render content lines (no title)
        content_start_y = start_y + 1
        for i, line in enumerate(content_lines):
            if content_start_y + i >= start_y + container_height - 1:
                break  # Don't overflow container

            # Truncate line if too long
            display_line = line[:inner_width] if len(line) > inner_width else line
            content_x = start_x + 2  # 2 chars padding from left border
            console.print(content_x, content_start_y + i, display_line, fg=self.info_color, bg=container_bg)

    def render_status_bar(self, console: tcod.console.Console, world_center_x: int, world_center_y: int):
        """Render the floating status bar with debug information (max 2 lines)."""
        if not self.show_debug:
            return

        screen_width = console.width
        screen_height = console.height

        # Prepare compact status content (max 2 lines)
        status_lines = []

        # Line 1: Coordinates and screen size
        line1_parts = []
        if self.show_coordinates:
            line1_parts.append(f"Center: ({world_center_x}, {world_center_y})")
        line1_parts.append(f"Screen: {screen_width}x{screen_height}")
        status_lines.append(" | ".join(line1_parts))

        # Line 2: Frame count and FPS
        line2_parts = [f"Frame: {self.frame_count}"]
        if self.show_fps:
            line2_parts.append(f"FPS: {self.fps:.1f}")
        status_lines.append(" | ".join(line2_parts))

        # Render as floating container (max lines from config)
        self.render_floating_container(console, status_lines, "top", max_lines=self.config.ui.top_panel_max_lines)
    
    def render_help_text(self, console: tcod.console.Console):
        """
        Render help text at the bottom of the screen.
        
        Args:
            console: The tcod console to render to
        """
        screen_width = console.width
        screen_height = console.height
        
        if screen_height < 3:  # Not enough space for help
            return
        
        # Compact help text (max 3 lines)
        help_lines = [
            "Ctrl+Q/ESC: Quit | R: Regenerate world",
            "F1: Debug | F2: Coordinates | F3: Seamless blocks",
            "Hot reload: Save any .py file to restart"
        ]

        # Render as floating container at bottom (max lines from config)
        self.render_floating_container(console, help_lines, "bottom", max_lines=self.config.ui.bottom_panel_max_lines)
    
    def render_message(self, console: tcod.console.Console, message: str, x: int, y: int, 
                      message_type: str = "info", bg_color: Optional[Tuple[int, int, int]] = None):
        """
        Render a message at a specific location.
        
        Args:
            console: The tcod console to render to
            message: The message text to display
            x: X coordinate to render at
            y: Y coordinate to render at
            message_type: Type of message ("info", "debug", "warning", "error")
            bg_color: Optional background color override
        """
        if y < 0 or y >= console.height or x < 0:
            return
        
        # Choose color based on message type
        if message_type == "debug":
            fg_color = self.debug_color
        elif message_type == "warning":
            fg_color = self.warning_color
        elif message_type == "error":
            fg_color = self.error_color
        else:
            fg_color = self.info_color
        
        # Use default black background if none specified
        if bg_color is None:
            bg_color = (0, 0, 0)
        
        # Truncate message if it's too long for the screen
        max_length = console.width - x
        if len(message) > max_length:
            message = message[:max_length-3] + "..."
        
        console.print(x, y, message, fg=fg_color, bg=bg_color)
    
    def render_centered_message(self, console: tcod.console.Console, message: str, y: int, 
                               message_type: str = "info", bg_color: Optional[Tuple[int, int, int]] = None):
        """
        Render a centered message at a specific Y coordinate.
        
        Args:
            console: The tcod console to render to
            message: The message text to display
            y: Y coordinate to render at
            message_type: Type of message ("info", "debug", "warning", "error")
            bg_color: Optional background color override
        """
        if len(message) >= console.width:
            # If message is too long, render left-aligned
            self.render_message(console, message, 0, y, message_type, bg_color)
        else:
            # Center the message
            x = (console.width - len(message)) // 2
            self.render_message(console, message, x, y, message_type, bg_color)
    
    def toggle_debug(self):
        """Toggle debug information display."""
        self.show_debug = not self.show_debug
    
    def toggle_coordinates(self):
        """Toggle coordinate display."""
        self.show_coordinates = not self.show_coordinates
    
    def toggle_fps(self):
        """Toggle FPS display."""
        self.show_fps = not self.show_fps


# Example usage and testing
if __name__ == "__main__":
    # This would normally be used within the game loop
    print("StatusDisplay component - use within the main game loop")
    
    # Create a test instance
    status = StatusDisplay()
    print(f"Debug mode: {status.show_debug}")
    print(f"Show coordinates: {status.show_coordinates}")
    
    # Test toggle functions
    status.toggle_debug()
    print(f"After toggle - Debug mode: {status.show_debug}")
