#!/usr/bin/env python3
"""
Camera System for 2D World Navigation

Handles camera position tracking, movement, and viewport calculations.
The camera represents the player's view into the infinite world.
"""

from typing import Tuple
from ..config import CameraConfig


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
            world_x: World X coordinate
            world_y: World Y coordinate
        """
        self.cursor_x = world_x
        self.cursor_y = world_y
    
    def move_cursor(self, dx: int, dy: int, fast_mode: bool = False):
        """
        Move the cursor by the specified offset.
        
        Args:
            dx: Change in X position
            dy: Change in Y position
            fast_mode: Whether to use fast movement speed
        """
        speed = self.fast_move_speed if fast_mode else self.move_speed
        self.cursor_x += dx * speed
        self.cursor_y += dy * speed
    
    def move_up(self, fast_mode: bool = False):
        """Move cursor up (negative Y direction)."""
        self.move_cursor(0, -1, fast_mode)
    
    def move_down(self, fast_mode: bool = False):
        """Move cursor down (positive Y direction)."""
        self.move_cursor(0, 1, fast_mode)
    
    def move_left(self, fast_mode: bool = False):
        """Move cursor left (negative X direction)."""
        self.move_cursor(-1, 0, fast_mode)
    
    def move_right(self, fast_mode: bool = False):
        """Move cursor right (positive X direction)."""
        self.move_cursor(1, 0, fast_mode)
    
    def get_view_bounds(self, screen_width: int, screen_height: int) -> Tuple[int, int, int, int]:
        """
        Calculate the world bounds visible on screen.
        
        Args:
            screen_width: Width of the screen in tiles
            screen_height: Height of the screen in tiles
            
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
    
    def world_to_screen(self, world_x: int, world_y: int, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """
        Convert world coordinates to screen coordinates.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            screen_width: Width of the screen in tiles
            screen_height: Height of the screen in tiles
            
        Returns:
            Tuple of (screen_x, screen_y)
        """
        half_width = screen_width // 2
        half_height = screen_height // 2
        
        screen_x = (world_x - self.cursor_x) + half_width
        screen_y = (world_y - self.cursor_y) + half_height
        
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x: int, screen_y: int, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """
        Convert screen coordinates to world coordinates.
        
        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate
            screen_width: Width of the screen in tiles
            screen_height: Height of the screen in tiles
            
        Returns:
            Tuple of (world_x, world_y)
        """
        half_width = screen_width // 2
        half_height = screen_height // 2
        
        world_x = self.cursor_x + (screen_x - half_width)
        world_y = self.cursor_y + (screen_y - half_height)
        
        return world_x, world_y
    
    def is_position_visible(self, world_x: int, world_y: int, screen_width: int, screen_height: int) -> bool:
        """
        Check if a world position is visible on screen.
        
        Args:
            world_x: World X coordinate to check
            world_y: World Y coordinate to check
            screen_width: Width of the screen in tiles
            screen_height: Height of the screen in tiles
            
        Returns:
            True if the position is visible on screen
        """
        screen_x, screen_y = self.world_to_screen(world_x, world_y, screen_width, screen_height)
        return 0 <= screen_x < screen_width and 0 <= screen_y < screen_height
    
    def get_cursor_info(self) -> dict:
        """
        Get information about the current camera state.
        
        Returns:
            Dictionary with camera information for debugging/display
        """
        return {
            "cursor_x": self.cursor_x,
            "cursor_y": self.cursor_y,
            "move_speed": self.move_speed,
            "fast_move_speed": self.fast_move_speed
        }


# Example usage and testing
if __name__ == "__main__":
    from ..config import CameraConfig
    
    # Test the camera system
    config = CameraConfig(initial_x=100, initial_y=200, move_speed=1, fast_move_speed=5)
    camera = Camera(config)
    
    print("Camera System Test")
    print(f"Initial position: {camera.get_cursor_position()}")
    
    # Test movement
    camera.move_right()
    print(f"After moving right: {camera.get_cursor_position()}")
    
    camera.move_up(fast_mode=True)
    print(f"After fast move up: {camera.get_cursor_position()}")
    
    # Test coordinate conversion
    screen_width, screen_height = 80, 50
    bounds = camera.get_view_bounds(screen_width, screen_height)
    print(f"View bounds for {screen_width}x{screen_height} screen: {bounds}")
    
    # Test screen/world conversion
    center_screen = (screen_width // 2, screen_height // 2)
    world_pos = camera.screen_to_world(*center_screen, screen_width, screen_height)
    print(f"Screen center {center_screen} -> World {world_pos}")
    
    back_to_screen = camera.world_to_screen(*world_pos, screen_width, screen_height)
    print(f"World {world_pos} -> Screen {back_to_screen}")
    
    print(f"Camera info: {camera.get_cursor_info()}")
