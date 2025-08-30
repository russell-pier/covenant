#!/usr/bin/env python3
"""
Rendering system for the 2D Minecraft-like world

Handles all rendering operations including world tiles, UI overlays, and effects.
Separated from game logic for better organization and modularity.
"""

import tcod
from typing import Dict, Tuple, Optional, List
from ..world import Tile
from ..ui.status_display import StatusDisplay
from ..tiles import get_tile_registry
try:
    from ..profiler import profile_function, start_profiling, end_profiling
except ImportError:
    # Fallback for when profiler is not available
    def profile_function(name=None):
        def decorator(func):
            return func
        return decorator
    def start_profiling(name): pass
    def end_profiling(name): pass


class WorldRenderer:
    """Handles rendering of the world tiles and terrain."""

    def __init__(self):
        self.tile_registry = get_tile_registry()

    def _render_tile(self, console: tcod.console.Console, x: int, y: int, tile_config):
        """
        Render a tile using its configuration.

        Args:
            console: The tcod console to render to
            x: Screen X coordinate
            y: Screen Y coordinate
            tile_config: The tile configuration
        """
        console.print(x, y, tile_config.character,
                    fg=tile_config.font_color, bg=tile_config.background_color)
    
    @profile_function("renderer.render_world")
    def render_world(self, console: tcod.console.Console, world_source,
                    view_center_x: int, view_center_y: int):
        """
        Render the world tiles to the console (optimized version).

        Args:
            console: The tcod console to render to
            world_source: The world manager or generator containing tile data
            view_center_x: X coordinate of the view center
            view_center_y: Y coordinate of the view center
        """
        screen_width = console.width
        screen_height = console.height

        # Calculate world bounds for the current view
        half_width = screen_width // 2
        half_height = screen_height // 2

        # Calculate world coordinate bounds
        min_world_x = view_center_x - half_width
        max_world_x = view_center_x + half_width
        min_world_y = view_center_y - half_height
        max_world_y = view_center_y + half_height

        # Batch fetch all tiles for the visible area (major optimization!)
        start_profiling("renderer.batch_fetch_tiles")
        tile_cache = {}
        for world_y in range(min_world_y, max_world_y + 1):
            for world_x in range(min_world_x, max_world_x + 1):
                tile = world_source.get_tile(world_x, world_y)
                tile_cache[(world_x, world_y)] = tile
        end_profiling("renderer.batch_fetch_tiles")

        # Pre-fetch tile configurations to avoid repeated lookups
        start_profiling("renderer.prefetch_configs")
        tile_types = set(tile.tile_type for tile in tile_cache.values())
        config_cache = {}
        for tile_type in tile_types:
            config_cache[tile_type] = self.tile_registry.get_tile_config(tile_type)

        # Add cursor config
        cursor_config = self.tile_registry.get_tile_config('cursor')
        end_profiling("renderer.prefetch_configs")

        # Ultra-optimized rendering using numpy arrays (batch rendering)
        start_profiling("renderer.render_loop")

        # Prepare arrays for batch rendering
        import numpy as np

        # Create arrays for characters, foreground colors, and background colors
        # Note: tcod console expects (width, height) order
        chars = np.full((screen_width, screen_height), ord(' '), dtype=np.int32)
        fg_colors = np.zeros((screen_width, screen_height, 3), dtype=np.uint8)
        bg_colors = np.zeros((screen_width, screen_height, 3), dtype=np.uint8)

        # Fill arrays in one pass
        for screen_y in range(screen_height):
            for screen_x in range(screen_width):
                # Convert screen coordinates to world coordinates
                world_x = view_center_x + (screen_x - half_width)
                world_y = view_center_y + (screen_y - half_height)

                # Check if this is the cursor position (center of screen)
                if screen_x == half_width and screen_y == half_height:
                    # Use cursor config
                    config = cursor_config
                else:
                    # Get tile from cache
                    tile = tile_cache.get((world_x, world_y))
                    if tile:
                        config = config_cache.get(tile.tile_type)
                    else:
                        continue  # Skip if no tile

                if config:
                    chars[screen_x, screen_y] = ord(config.character)
                    fg_colors[screen_x, screen_y] = config.font_color
                    bg_colors[screen_x, screen_y] = config.background_color

        # Batch render all tiles at once (much faster than individual console.print calls)
        console.ch[:] = chars
        console.fg[:] = fg_colors
        console.bg[:] = bg_colors

        end_profiling("renderer.render_loop")
    
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

            # Render the tile
            self._render_tile(console, screen_x, screen_y, tile_config)
    
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
    
    def render_frame(self, console: tcod.console.Console, world_source,
                    view_center_x: int, view_center_y: int, **render_options):
        """
        Render a complete frame.

        Args:
            console: The tcod console to render to
            world_source: The world manager or generator containing tile data
            view_center_x: X coordinate of the view center
            view_center_y: Y coordinate of the view center
            **render_options: Additional rendering options including:
                - cursor_tile: Tile under cursor
                - cursor_position: (x, y) cursor position
                - chunk_info: Information about current chunk
                - world_stats: World manager statistics
        """
        # Update frame counter
        self.status_display.update_frame_count()

        # Clear the console
        console.clear(fg=(255, 255, 255), bg=self.clear_color)

        # Render world tiles
        self.world_renderer.render_world(console, world_source, view_center_x, view_center_y)

        # Update and render effects
        self.effect_renderer.update_effects()
        self.effect_renderer.render_effects(console, view_center_x, view_center_y)

        # Render highlights if specified
        if 'highlight_positions' in render_options:
            for pos in render_options['highlight_positions']:
                self.world_renderer.render_highlight_at_world_pos(
                    console, pos[0], pos[1], view_center_x, view_center_y
                )

        # Render chunk debug overlay if enabled (before UI overlays)
        if hasattr(world_source, 'world_to_chunk_coords') or hasattr(world_source, 'world_to_render_chunk_coords'):
            self.status_display.render_chunk_debug_overlay(console, world_source, view_center_x, view_center_y)

        # Render UI overlays with cursor information
        self.status_display.render_status_bar(
            console, view_center_x, view_center_y,
            cursor_tile=render_options.get('cursor_tile'),
            chunk_info=render_options.get('chunk_info'),
            world_stats=render_options.get('world_stats')
        )
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
