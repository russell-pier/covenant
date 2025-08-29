#!/usr/bin/env python3
"""
Camera System for 2D World Navigation

Handles camera position tracking, movement, and viewport calculations.
The camera represents the player's view into the infinite world.
"""

from typing import Tuple
from ..utils.config import CameraConfig


class Camera:
    """
    Camera system for navigating the infinite world.
    
    The camera tracks a cursor position in world coordinates that always
    appears at the center of the screen. Moving the camera makes the world
    appear to move underneath the cursor.
    """
    
    def __init__(self, config: CameraConfig):
        """
        Initialize the camera with configuration.
        
        Args:
            config: Camera configuration settings
        """
        self.config = config
        
        # Current camera position (world coordinates)
        self.cursor_x = config.initial_x
        self.cursor_y = config.initial_y
        
        # Movement state
        self.move_speed = config.move_speed
        self.fast_move_speed = config.fast_move_speed
    
    def get_cursor_position(self) -> Tuple[int, int]:
        """
        Get the current cursor position in world coordinates.
        
        Returns:
            Tuple of (world_x, world_y) for the cursor position
        """
        return self.cursor_x, self.cursor_y
    
    def set_cursor_position(self, world_x: int, world_y: int):
        """
        Set the cursor position directly.
        
        Args:
            world_x: New world X coordinate
            world_y: New world Y coordinate
        """
        self.cursor_x = world_x
        self.cursor_y = world_y
    
    def move_cursor(self, delta_x: int, delta_y: int):
        """
        Move the cursor by a relative amount.
        
        Args:
            delta_x: Change in X coordinate
            delta_y: Change in Y coordinate
        """
        self.cursor_x += delta_x
        self.cursor_y += delta_y
    
    def move_up(self, fast: bool = False):
        """Move cursor up."""
        speed = self.fast_move_speed if fast else self.move_speed
        self.move_cursor(0, -speed)
    
    def move_down(self, fast: bool = False):
        """Move cursor down."""
        speed = self.fast_move_speed if fast else self.move_speed
        self.move_cursor(0, speed)
    
    def move_left(self, fast: bool = False):
        """Move cursor left."""
        speed = self.fast_move_speed if fast else self.move_speed
        self.move_cursor(-speed, 0)
    
    def move_right(self, fast: bool = False):
        """Move cursor right."""
        speed = self.fast_move_speed if fast else self.move_speed
        self.move_cursor(speed, 0)
    
    def get_viewport_bounds(self, screen_width: int, screen_height: int) -> Tuple[int, int, int, int]:
        """
        Get the world coordinate bounds of the current viewport.
        
        Args:
            screen_width: Screen width in tiles
            screen_height: Screen height in tiles
            
        Returns:
            Tuple of (min_x, min_y, max_x, max_y) in world coordinates
        """
        half_width = screen_width // 2
        half_height = screen_height // 2
        
        min_x = self.cursor_x - half_width
        min_y = self.cursor_y - half_height
        max_x = self.cursor_x + half_width
        max_y = self.cursor_y + half_height
        
        return min_x, min_y, max_x, max_y
    
    def world_to_screen_coords(self, world_x: int, world_y: int, 
                              screen_width: int, screen_height: int) -> Tuple[int, int]:
        """
        Convert world coordinates to screen coordinates.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            screen_width: Screen width in tiles
            screen_height: Screen height in tiles
            
        Returns:
            Tuple of (screen_x, screen_y), or None if off-screen
        """
        # Calculate offset from cursor position
        offset_x = world_x - self.cursor_x
        offset_y = world_y - self.cursor_y
        
        # Convert to screen coordinates (cursor is at center)
        screen_x = (screen_width // 2) + offset_x
        screen_y = (screen_height // 2) + offset_y
        
        # Check if on screen
        if 0 <= screen_x < screen_width and 0 <= screen_y < screen_height:
            return screen_x, screen_y
        else:
            return None
    
    def screen_to_world_coords(self, screen_x: int, screen_y: int,
                              screen_width: int, screen_height: int) -> Tuple[int, int]:
        """
        Convert screen coordinates to world coordinates.
        
        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate
            screen_width: Screen width in tiles
            screen_height: Screen height in tiles
            
        Returns:
            Tuple of (world_x, world_y)
        """
        # Calculate offset from screen center
        offset_x = screen_x - (screen_width // 2)
        offset_y = screen_y - (screen_height // 2)
        
        # Convert to world coordinates
        world_x = self.cursor_x + offset_x
        world_y = self.cursor_y + offset_y
        
        return world_x, world_y
    
    def is_position_visible(self, world_x: int, world_y: int,
                           screen_width: int, screen_height: int) -> bool:
        """
        Check if a world position is visible on screen.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            screen_width: Screen width in tiles
            screen_height: Screen height in tiles
            
        Returns:
            True if position is visible
        """
        screen_coords = self.world_to_screen_coords(world_x, world_y, screen_width, screen_height)
        return screen_coords is not None
    
    def get_distance_from_cursor(self, world_x: int, world_y: int) -> float:
        """
        Get the distance from a world position to the cursor.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            
        Returns:
            Distance in world units
        """
        dx = world_x - self.cursor_x
        dy = world_y - self.cursor_y
        return (dx * dx + dy * dy) ** 0.5
    
    def __str__(self):
        return f"Camera(cursor=({self.cursor_x}, {self.cursor_y}))"
    
    def __repr__(self):
        return self.__str__()
