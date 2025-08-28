#!/usr/bin/env python3
"""
Rendering system for the 2D Minecraft-like world

Handles all rendering operations including world tiles, UI overlays, and effects.
Separated from game logic for better organization and modularity.
"""

import tcod
from typing import Dict, Tuple, Optional, List
from .generators.spiral import Tile
from .ui.status_display import StatusDisplay
from .tiles import get_tile_registry


class WorldRenderer:
    """Handles rendering of the world tiles and terrain."""

    def __init__(self):
        self.tile_registry = get_tile_registry()
        # Characters that should be rendered as seamless blocks
        # Note: Due to font rendering limitations, true seamless rendering may not be possible
        # We use background color filling as the best available solution
        self.seamless_block_chars = {"█", "▓", "▒", "░", "■", "▪", "▫"}
        # Whether to use seamless rendering for block characters
        self.use_seamless_rendering = True

    def _render_seamless_tile(self, console: tcod.console.Console, x: int, y: int,
                             tile_config, use_seamless: bool = True):
        """
        Render a tile with seamless block character support.

        Args:
            console: The tcod console to render to
            x: Screen X coordinate
            y: Screen Y coordinate
            tile_config: The tile configuration
            use_seamless: Whether to use seamless rendering for block characters
        """
        if use_seamless and tile_config.character in self.seamless_block_chars:
            # For seamless blocks, use space character with background color filling entire cell
            console.print(x, y, " ", fg=tile_config.background_color, bg=tile_config.background_color)
        else:
            # For regular characters, use normal foreground/background rendering
            console.print(x, y, tile_config.character,
                        fg=tile_config.font_color, bg=tile_config.background_color)
    
    def render_world(self, console: tcod.console.Console, world_generator, 
                    view_center_x: int, view_center_y: int):
        """
        Render the world tiles to the console.
        
        Args:
            console: The tcod console to render to
            world_generator: The world generator containing tile data
            view_center_x: X coordinate of the view center
            view_center_y: Y coordinate of the view center
        """
        screen_width = console.width
        screen_height = console.height
        
        # Calculate world bounds for the current view
        half_width = screen_width // 2
        half_height = screen_height // 2
        
        # Render tiles
        for screen_y in range(screen_height):
            for screen_x in range(screen_width):
                # Convert screen coordinates to world coordinates
                world_x = view_center_x + (screen_x - half_width)
                world_y = view_center_y + (screen_y - half_height)
                
                # Get the tile at this world position
                tile = world_generator.get_tile(world_x, world_y)

                # Get the tile configuration for rendering
                tile_config = self.tile_registry.get_tile_config(tile.tile_type)

                # Render the tile with seamless block support
                self._render_seamless_tile(console, screen_x, screen_y, tile_config, self.use_seamless_rendering)
    
    def render_tile_at_screen_pos(self, console: tcod.console.Console, tile: Tile,
                                 screen_x: int, screen_y: int):
        """
        Render a specific tile at a screen position.

        Args:
            console: The tcod console to render to
            tile: The tile to render
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate
        """
        if 0 <= screen_x < console.width and 0 <= screen_y < console.height:
            # Get the tile configuration for rendering
            tile_config = self.tile_registry.get_tile_config(tile.tile_type)

            # Render the tile with seamless block support
            self._render_seamless_tile(console, screen_x, screen_y, tile_config, self.use_seamless_rendering)
    
    def render_highlight_at_world_pos(self, console: tcod.console.Console, 
                                    world_x: int, world_y: int, 
                                    view_center_x: int, view_center_y: int,
                                    highlight_char: str = "X", 
                                    highlight_color: Tuple[int, int, int] = (255, 255, 0)):
        """
        Render a highlight marker at a world position.
        
        Args:
            console: The tcod console to render to
            world_x: World X coordinate to highlight
            world_y: World Y coordinate to highlight
            view_center_x: X coordinate of the view center
            view_center_y: Y coordinate of the view center
            highlight_char: Character to use for highlighting
            highlight_color: Color for the highlight
        """
        # Convert world coordinates to screen coordinates
        half_width = console.width // 2
        half_height = console.height // 2
        
        screen_x = (world_x - view_center_x) + half_width
        screen_y = (world_y - view_center_y) + half_height
        
        # Render if on screen
        if 0 <= screen_x < console.width and 0 <= screen_y < console.height:
            console.print(screen_x, screen_y, highlight_char, fg=highlight_color)

    def toggle_seamless_rendering(self):
        """Toggle seamless rendering for block characters."""
        self.use_seamless_rendering = not self.use_seamless_rendering
        return self.use_seamless_rendering


class EffectRenderer:
    """Handles rendering of visual effects and animations."""
    
    def __init__(self):
        self.effects = []
    
    def add_effect(self, effect_type: str, x: int, y: int, duration: int, **kwargs):
        """Add a visual effect to be rendered."""
        effect = {
            'type': effect_type,
            'x': x,
            'y': y,
            'duration': duration,
            'remaining': duration,
            **kwargs
        }
        self.effects.append(effect)
    
    def update_effects(self):
        """Update all active effects."""
        for effect in self.effects:
            effect['remaining'] -= 1

        # Remove effects that have expired
        self.effects = [effect for effect in self.effects
                       if effect['remaining'] > 0]
    
    def render_effects(self, console: tcod.console.Console, view_center_x: int, view_center_y: int):
        """Render all active effects."""
        half_width = console.width // 2
        half_height = console.height // 2
        
        for effect in self.effects:
            # Convert world coordinates to screen coordinates
            screen_x = (effect['x'] - view_center_x) + half_width
            screen_y = (effect['y'] - view_center_y) + half_height
            
            # Render if on screen
            if 0 <= screen_x < console.width and 0 <= screen_y < console.height:
                if effect['type'] == 'sparkle':
                    char = '*' if effect['remaining'] % 2 == 0 else '+'
                    color = effect.get('color', (255, 255, 255))
                    console.print(screen_x, screen_y, char, fg=color)


class GameRenderer:
    """Main renderer that coordinates all rendering subsystems."""
    
    def __init__(self):
        self.world_renderer = WorldRenderer()
        self.effect_renderer = EffectRenderer()
        self.status_display = StatusDisplay()
        self.clear_color = (0, 0, 0)  # Black background
    
    def render_frame(self, console: tcod.console.Console, world_generator, 
                    view_center_x: int, view_center_y: int, **render_options):
        """
        Render a complete frame.
        
        Args:
            console: The tcod console to render to
            world_generator: The world generator containing tile data
            view_center_x: X coordinate of the view center
            view_center_y: Y coordinate of the view center
            **render_options: Additional rendering options
        """
        # Update frame counter
        self.status_display.update_frame_count()
        
        # Clear the console
        console.clear(fg=(255, 255, 255), bg=self.clear_color)
        
        # Render world tiles
        self.world_renderer.render_world(console, world_generator, view_center_x, view_center_y)
        
        # Update and render effects
        self.effect_renderer.update_effects()
        self.effect_renderer.render_effects(console, view_center_x, view_center_y)
        
        # Render highlights if specified
        if 'highlight_positions' in render_options:
            for pos in render_options['highlight_positions']:
                self.world_renderer.render_highlight_at_world_pos(
                    console, pos[0], pos[1], view_center_x, view_center_y
                )
        
        # Render UI overlays
        self.status_display.render_status_bar(console, view_center_x, view_center_y)
        self.status_display.render_help_text(console)
        
        # Render custom messages if specified
        if 'messages' in render_options:
            for msg in render_options['messages']:
                self.status_display.render_message(
                    console, msg['text'], msg['x'], msg['y'], 
                    msg.get('type', 'info'), msg.get('bg_color')
                )
    
    def add_effect(self, effect_type: str, world_x: int, world_y: int, duration: int, **kwargs):
        """Add a visual effect at a world position."""
        self.effect_renderer.add_effect(effect_type, world_x, world_y, duration, **kwargs)
    
    def set_clear_color(self, color: Tuple[int, int, int]):
        """Set the background clear color."""
        self.clear_color = color
    
    def get_status_display(self) -> StatusDisplay:
        """Get the status display for external configuration."""
        return self.status_display

    def toggle_seamless_rendering(self) -> bool:
        """Toggle seamless rendering for block characters."""
        return self.world_renderer.toggle_seamless_rendering()
    
    def world_to_screen(self, world_x: int, world_y: int, view_center_x: int, view_center_y: int, 
                       console_width: int, console_height: int) -> Tuple[int, int]:
        """
        Convert world coordinates to screen coordinates.
        
        Returns:
            Tuple of (screen_x, screen_y)
        """
        half_width = console_width // 2
        half_height = console_height // 2
        
        screen_x = (world_x - view_center_x) + half_width
        screen_y = (world_y - view_center_y) + half_height
        
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x: int, screen_y: int, view_center_x: int, view_center_y: int,
                       console_width: int, console_height: int) -> Tuple[int, int]:
        """
        Convert screen coordinates to world coordinates.
        
        Returns:
            Tuple of (world_x, world_y)
        """
        half_width = console_width // 2
        half_height = console_height // 2
        
        world_x = view_center_x + (screen_x - half_width)
        world_y = view_center_y + (screen_y - half_height)
        
        return world_x, world_y


# Example usage and testing
if __name__ == "__main__":
    print("GameRenderer - use within the main game loop")
    print("Note: This module uses relative imports and should be imported, not run directly.")
    print("Run 'python main.py' to test the full application.")
