#!/usr/bin/env python3
"""
Input Handler for 2D World Navigation

Handles keyboard input for camera movement, game controls, and debug features.
Extracted from game.py to provide better organization and extensibility.
"""

import tcod
from typing import Optional, Callable
from .camera import Camera


class InputHandler:
    """
    Handles all input events for the game.
    
    Manages camera movement, game controls, debug toggles, and other
    keyboard interactions. Provides a clean interface between input
    events and game systems.
    """
    
    def __init__(self, camera: Camera):
        """
        Initialize the input handler.

        Args:
            camera: Camera instance to control with movement keys
        """
        self.camera = camera

        # Callback functions for various actions
        self.on_regenerate_world: Optional[Callable] = None
        self.on_toggle_debug: Optional[Callable] = None
        self.on_toggle_coordinates: Optional[Callable] = None
        self.on_toggle_fps: Optional[Callable] = None
        self.on_toggle_chunk_debug: Optional[Callable] = None

        # Performance optimization - movement throttling
        import time
        self._last_movement_time = 0
        self._movement_throttle = 0.016  # ~60 FPS (16ms between movements)
    
    def set_regenerate_callback(self, callback: Callable):
        """Set callback for world regeneration (R key)."""
        self.on_regenerate_world = callback
    
    def set_debug_callbacks(self, 
                           toggle_debug: Callable = None,
                           toggle_coordinates: Callable = None,
                           toggle_fps: Callable = None,
                           toggle_chunk_debug: Callable = None):
        """Set callbacks for debug toggles."""
        if toggle_debug:
            self.on_toggle_debug = toggle_debug
        if toggle_coordinates:
            self.on_toggle_coordinates = toggle_coordinates
        if toggle_fps:
            self.on_toggle_fps = toggle_fps
        if toggle_chunk_debug:
            self.on_toggle_chunk_debug = toggle_chunk_debug
    
    def handle_event(self, event) -> bool:
        """
        Handle a single input event.
        
        Args:
            event: tcod event to process
            
        Returns:
            True if the game should exit, False otherwise
        """
        if event.type == "QUIT":
            # Window close button was clicked
            return True
        
        elif event.type == "KEYDOWN":
            return self._handle_keydown(event)
        
        return False
    
    def _handle_keydown(self, event) -> bool:
        """
        Handle keyboard key press events.
        
        Args:
            event: tcod keydown event
            
        Returns:
            True if the game should exit, False otherwise
        """
        # Check for modifier keys
        shift_held = bool(event.mod & tcod.event.Modifier.SHIFT)
        ctrl_held = bool(event.mod & tcod.event.Modifier.CTRL)
        
        # Exit commands
        if (event.sym == tcod.event.KeySym.Q and ctrl_held) or event.sym == tcod.event.KeySym.ESCAPE:
            print("Exit command received. Exiting gracefully...")
            return True
        
        # Camera movement - WASD keys (with throttling)
        elif event.sym == tcod.event.KeySym.W:
            if self._can_move():
                self.camera.move_up(fast_mode=shift_held)
            return False
        elif event.sym == tcod.event.KeySym.A:
            if self._can_move():
                self.camera.move_left(fast_mode=shift_held)
            return False
        elif event.sym == tcod.event.KeySym.S:
            if self._can_move():
                self.camera.move_down(fast_mode=shift_held)
            return False
        elif event.sym == tcod.event.KeySym.D:
            if self._can_move():
                self.camera.move_right(fast_mode=shift_held)
            return False

        # Camera movement - Arrow keys (with throttling)
        elif event.sym == tcod.event.KeySym.UP:
            if self._can_move():
                self.camera.move_up(fast_mode=shift_held)
            return False
        elif event.sym == tcod.event.KeySym.DOWN:
            if self._can_move():
                self.camera.move_down(fast_mode=shift_held)
            return False
        elif event.sym == tcod.event.KeySym.LEFT:
            if self._can_move():
                self.camera.move_left(fast_mode=shift_held)
            return False
        elif event.sym == tcod.event.KeySym.RIGHT:
            if self._can_move():
                self.camera.move_right(fast_mode=shift_held)
            return False
        
        # World regeneration
        elif event.sym == tcod.event.KeySym.R:
            if self.on_regenerate_world:
                self.on_regenerate_world()
            return False
        
        # Debug toggles
        elif event.sym == tcod.event.KeySym.F1:
            if self.on_toggle_debug:
                self.on_toggle_debug()
            return False
        elif event.sym == tcod.event.KeySym.F2:
            if self.on_toggle_coordinates:
                self.on_toggle_coordinates()
            return False
        elif event.sym == tcod.event.KeySym.F3:
            if self.on_toggle_chunk_debug:
                self.on_toggle_chunk_debug()
            return False
        elif event.sym == tcod.event.KeySym.F4:
            if self.on_toggle_fps:
                self.on_toggle_fps()
            return False
        
        # Unknown key - no action
        return False

    def _can_move(self) -> bool:
        """
        Check if movement is allowed based on throttling.

        Returns:
            True if movement is allowed, False if throttled
        """
        import time
        current_time = time.time()
        if current_time - self._last_movement_time >= self._movement_throttle:
            self._last_movement_time = current_time
            return True
        return False
    
    def get_movement_help_text(self) -> str:
        """
        Get help text for movement controls.
        
        Returns:
            String describing movement controls
        """
        return (
            "Movement: WASD or Arrow Keys | "
            "Hold Shift for fast movement | "
            "R: Regenerate | "
            "F1: Debug | F2: Coords | F3: Chunks | F4: FPS | "
            "Ctrl+Q or ESC: Exit"
        )
    
    def get_camera_position(self) -> tuple:
        """
        Get the current camera position.
        
        Returns:
            Tuple of (x, y) camera position
        """
        return self.camera.get_cursor_position()
    
    def set_camera_position(self, x: int, y: int):
        """
        Set the camera position directly.
        
        Args:
            x: World X coordinate
            y: World Y coordinate
        """
        self.camera.set_cursor_position(x, y)


# Example usage and testing
if __name__ == "__main__":
    from .camera import Camera
    from .config import CameraConfig
    
    # Test the input handler
    config = CameraConfig(initial_x=0, initial_y=0, move_speed=1, fast_move_speed=5)
    camera = Camera(config)
    input_handler = InputHandler(camera)
    
    print("Input Handler Test")
    print(f"Initial camera position: {input_handler.get_camera_position()}")
    
    # Set up some test callbacks
    def test_regenerate():
        print("World regeneration requested!")
    
    def test_debug_toggle():
        print("Debug display toggled!")
    
    input_handler.set_regenerate_callback(test_regenerate)
    input_handler.set_debug_callbacks(toggle_debug=test_debug_toggle)
    
    print(f"Movement help: {input_handler.get_movement_help_text()}")
    
    # Simulate some key events (this would normally come from tcod)
    print("\nSimulating movement...")
    
    # Create mock events for testing
    class MockEvent:
        def __init__(self, event_type, sym, mod=0):
            self.type = event_type
            self.sym = sym
            self.mod = mod
    
    # Test movement
    w_event = MockEvent("KEYDOWN", tcod.event.KeySym.W)
    input_handler.handle_event(w_event)
    print(f"After W key: {input_handler.get_camera_position()}")
    
    d_event = MockEvent("KEYDOWN", tcod.event.KeySym.D)
    input_handler.handle_event(d_event)
    print(f"After D key: {input_handler.get_camera_position()}")
    
    # Test fast movement
    shift_s_event = MockEvent("KEYDOWN", tcod.event.KeySym.S, tcod.event.Modifier.SHIFT)
    input_handler.handle_event(shift_s_event)
    print(f"After Shift+S: {input_handler.get_camera_position()}")
    
    print("Input handler test completed!")
