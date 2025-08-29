#!/usr/bin/env python3
"""
World Renderer

Handles rendering of the world tiles and terrain.
"""

import tcod
from typing import Dict, Tuple, Optional, List
from ..generation import Tile
from ..utils.tiles import get_tile_registry

try:
    from ..utils.profiler import profile_function
except ImportError:
    def profile_function(name=None):
        def decorator(func):
            return func
        return decorator


class WorldRenderer:
    """
    Handles rendering of world tiles and terrain.
    """
    
    def __init__(self):
        """Initialize the world renderer."""
        self.tile_registry = get_tile_registry()
    
    @profile_function("renderer.render_world")
    def render_world(self, console: tcod.console.Console, world_manager, camera,
                    screen_width: int, screen_height: int):
        """
        Render the world tiles visible on screen.
        
        Args:
            console: TCOD console to render to
            world_manager: World manager providing tiles
            camera: Camera for viewport calculations
            screen_width: Screen width in characters
            screen_height: Screen height in characters
        """
        cursor_x, cursor_y = camera.get_cursor_position()
        
        # Calculate visible area
        start_x = cursor_x - screen_width // 2
        start_y = cursor_y - screen_height // 2
        end_x = start_x + screen_width
        end_y = start_y + screen_height
        
        # Render tiles in visible area
        for screen_y in range(screen_height):
            for screen_x in range(screen_width):
                world_x = start_x + screen_x
                world_y = start_y + screen_y
                
                # Get tile from world manager
                tile = world_manager.get_tile(world_x, world_y)
                
                # Get tile configuration
                tile_config = self.tile_registry.get(tile.tile_type, {
                    'character': '?',
                    'background_color': (255, 0, 255),
                    'font_color': (255, 255, 255)
                })
                
                # Render tile
                console.print(
                    screen_x, screen_y,
                    tile_config['character'],
                    fg=tile_config['font_color'],
                    bg=tile_config['background_color']
                )
    
    def get_tile_at_screen_position(self, screen_x: int, screen_y: int, 
                                   camera, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """
        Convert screen coordinates to world coordinates.
        
        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate
            camera: Camera object
            screen_width: Screen width in characters
            screen_height: Screen height in characters
            
        Returns:
            Tuple of (world_x, world_y)
        """
        cursor_x, cursor_y = camera.get_cursor_position()
        
        start_x = cursor_x - screen_width // 2
        start_y = cursor_y - screen_height // 2
        
        world_x = start_x + screen_x
        world_y = start_y + screen_y
        
        return world_x, world_y
