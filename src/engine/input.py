#!/usr/bin/env python3
"""
Input Handler for 2D World Navigation

Handles keyboard input for camera movement, game controls, and debug features.
"""

import tcod
import time
from typing import Optional, Callable
from .camera import Camera


class InputHandler:
    """
    Handles all input events for the game.
    
    Manages camera movement, game controls, debug toggles, and other
    keyboard interactions. Provides a clean interface between input
    events and game systems.
    """
    
    def __init__(self):
        """Initialize the input handler."""
        # Callback functions for various actions
        self.on_regenerate_world: Optional[Callable] = None
        self.on_toggle_debug: Optional[Callable] = None
        self.on_toggle_coordinates: Optional[Callable] = None
        self.on_toggle_fps: Optional[Callable] = None
        self.on_toggle_chunk_debug: Optional[Callable] = None

        # Performance optimization - movement throttling
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
    
    def handle_keydown(self, event: tcod.event.KeyDown, camera: Camera) -> bool:
        """
        Handle a keydown event.
        
        Args:
            event: The keydown event
            camera: Camera to control with movement keys
            
        Returns:
            True if the camera moved (requiring world update)
        """
        current_time = time.time()
        
        # Check for movement throttling
        if current_time - self._last_movement_time < self._movement_throttle:
            return False
        
        camera_moved = False
        fast_mode = event.mod & tcod.event.KMOD_LSHIFT or event.mod & tcod.event.KMOD_RSHIFT
        
        # Movement keys
        if event.sym == tcod.event.KeySym.UP or event.sym == tcod.event.KeySym.W:
            camera.move_up(fast_mode)
            camera_moved = True
        elif event.sym == tcod.event.KeySym.DOWN or event.sym == tcod.event.KeySym.S:
            camera.move_down(fast_mode)
            camera_moved = True
        elif event.sym == tcod.event.KeySym.LEFT or event.sym == tcod.event.KeySym.A:
            camera.move_left(fast_mode)
            camera_moved = True
        elif event.sym == tcod.event.KeySym.RIGHT or event.sym == tcod.event.KeySym.D:
            camera.move_right(fast_mode)
            camera_moved = True
        
        # Action keys
        elif event.sym == tcod.event.KeySym.R:
            if self.on_regenerate_world:
                self.on_regenerate_world()
        elif event.sym == tcod.event.KeySym.F1:
            if self.on_toggle_debug:
                self.on_toggle_debug()
        elif event.sym == tcod.event.KeySym.F2:
            if self.on_toggle_coordinates:
                self.on_toggle_coordinates()
        elif event.sym == tcod.event.KeySym.F3:
            if self.on_toggle_fps:
                self.on_toggle_fps()
        elif event.sym == tcod.event.KeySym.F4:
            if self.on_toggle_chunk_debug:
                self.on_toggle_chunk_debug()
        
        # Update movement time if camera moved
        if camera_moved:
            self._last_movement_time = current_time
        
        return camera_moved
    
    def get_help_text(self) -> str:
        """
        Get help text for available controls.
        
        Returns:
            Multi-line string with control descriptions
        """
        return """
Controls:
  Arrow Keys / WASD - Move camera
  Shift + Movement - Fast movement
  R - Regenerate world
  F1 - Toggle debug info
  F2 - Toggle coordinates
  F3 - Toggle FPS display
  F4 - Toggle chunk debug
  ESC - Exit game
        """.strip()
