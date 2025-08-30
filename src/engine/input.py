#!/usr/bin/env python3
"""
Input Handler for 2D World Navigation

Handles keyboard input for camera movement, game controls, and debug features.
Uses TOML configuration for customizable key bindings.
"""

import tcod
import os
from typing import Optional, Callable, Dict, Set
from .camera import Camera

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for older Python versions


class InputHandler:
    """
    Handles all input events for the game using TOML-based key configuration.

    Manages camera movement, game controls, debug toggles, and other
    keyboard interactions. Key bindings are loaded from input.toml.
    """

    def __init__(self, camera: Camera, config_file: str = "input.toml"):
        """
        Initialize the input handler.

        Args:
            camera: Camera instance to control with movement keys
            config_file: Path to the input configuration TOML file
        """
        self.camera = camera
        self.config_file = config_file

        # Load input configuration
        self.config = self._load_input_config()

        # Build key mapping from config
        self.key_actions = self._build_key_mapping()

        # Callback functions for various actions
        self.on_regenerate_world: Optional[Callable] = None
        self.on_toggle_debug: Optional[Callable] = None
        self.on_toggle_coordinates: Optional[Callable] = None
        self.on_toggle_fps: Optional[Callable] = None
        self.on_toggle_chunk_debug: Optional[Callable] = None

        # Performance optimization - movement throttling
        import time
        self._last_movement_time = 0
        self._movement_throttle = self.config.get('settings', {}).get('movement_throttle', 0.016)

    def _load_input_config(self) -> Dict:
        """Load input configuration from TOML file."""
        if not os.path.exists(self.config_file):
            print(f"Warning: Input config file '{self.config_file}' not found. Using defaults.")
            return self._get_default_config()

        try:
            with open(self.config_file, 'rb') as f:
                config = tomllib.load(f)
            print(f"Loaded input configuration from {self.config_file}")
            return config
        except Exception as e:
            print(f"Error loading input config: {e}. Using defaults.")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default input configuration if TOML file is missing."""
        return {
            'movement': {
                'up': {'primary': 'UP', 'alternate': 'W'},
                'down': {'primary': 'DOWN', 'alternate': 'S'},
                'left': {'primary': 'LEFT', 'alternate': 'A'},
                'right': {'primary': 'RIGHT', 'alternate': 'D'}
            },
            'game_actions': {
                'regenerate_world': {'primary': 'R'},
                'exit': {'primary': 'ESCAPE', 'alternate': 'Q'}
            },
            'debug_actions': {
                'toggle_debug': {'primary': 'F1'},
                'toggle_coordinates': {'primary': 'F2'},
                'toggle_chunk_debug': {'primary': 'F3'},
                'toggle_fps': {'primary': 'F4'}
            },
            'modifiers': {
                'fast_movement': 'SHIFT',
                'exit_modifier': 'CTRL'
            },
            'settings': {
                'movement_throttle': 0.016
            }
        }

    def _build_key_mapping(self) -> Dict[str, str]:
        """Build a mapping from key names to action names."""
        key_actions = {}

        # Movement keys
        for action, keys in self.config.get('movement', {}).items():
            primary = keys.get('primary')
            alternate = keys.get('alternate')
            if primary:
                key_actions[primary] = f"move_{action}"
            if alternate:
                key_actions[alternate] = f"move_{action}"

        # Game action keys
        for action, keys in self.config.get('game_actions', {}).items():
            primary = keys.get('primary')
            alternate = keys.get('alternate')
            if primary:
                key_actions[primary] = action
            if alternate:
                key_actions[alternate] = action

        # Debug action keys
        for action, keys in self.config.get('debug_actions', {}).items():
            primary = keys.get('primary')
            alternate = keys.get('alternate')
            if primary:
                key_actions[primary] = action
            if alternate:
                key_actions[alternate] = action

        return key_actions

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
        Handle keyboard key press events using TOML configuration.

        Args:
            event: tcod keydown event

        Returns:
            True if the game should exit, False otherwise
        """
        # Check for modifier keys
        shift_held = bool(event.mod & tcod.event.Modifier.SHIFT)
        ctrl_held = bool(event.mod & tcod.event.Modifier.CTRL)

        # Convert tcod key symbol to string
        key_name = self._get_key_name(event.sym)
        if not key_name:
            return False

        # Get action for this key
        action = self.key_actions.get(key_name)
        if not action:
            return False

        # Handle exit commands (check for required modifiers)
        if action == "exit":
            exit_modifier = self.config.get('modifiers', {}).get('exit_modifier', 'CTRL')
            if key_name == "Q" and exit_modifier == "CTRL" and not ctrl_held:
                return False  # Q without Ctrl doesn't exit
            if key_name == "ESCAPE" or (key_name == "Q" and ctrl_held):
                print("Exit command received. Exiting gracefully...")
                return True

        # Handle movement actions
        if action.startswith("move_"):
            direction = action[5:]  # Remove "move_" prefix
            if self._can_move():
                fast_modifier = self.config.get('modifiers', {}).get('fast_movement', 'SHIFT')
                fast_mode = shift_held if fast_modifier == 'SHIFT' else False

                if direction == "up":
                    self.camera.move_up(fast_mode=fast_mode)
                elif direction == "down":
                    self.camera.move_down(fast_mode=fast_mode)
                elif direction == "left":
                    self.camera.move_left(fast_mode=fast_mode)
                elif direction == "right":
                    self.camera.move_right(fast_mode=fast_mode)
            return False

        # Handle game actions
        elif action == "regenerate_world":
            if self.on_regenerate_world:
                self.on_regenerate_world()
            return False

        # Handle debug actions
        elif action == "toggle_debug":
            if self.on_toggle_debug:
                self.on_toggle_debug()
            return False
        elif action == "toggle_coordinates":
            if self.on_toggle_coordinates:
                self.on_toggle_coordinates()
            return False
        elif action == "toggle_chunk_debug":
            if self.on_toggle_chunk_debug:
                self.on_toggle_chunk_debug()
            return False
        elif action == "toggle_fps":
            if self.on_toggle_fps:
                self.on_toggle_fps()
            return False

        # Unknown action - no action
        return False

    def _get_key_name(self, key_sym) -> Optional[str]:
        """Convert tcod key symbol to string name."""
        # Map tcod key symbols to string names
        key_map = {
            tcod.event.KeySym.UP: "UP",
            tcod.event.KeySym.DOWN: "DOWN",
            tcod.event.KeySym.LEFT: "LEFT",
            tcod.event.KeySym.RIGHT: "RIGHT",
            tcod.event.KeySym.W: "W",
            tcod.event.KeySym.A: "A",
            tcod.event.KeySym.S: "S",
            tcod.event.KeySym.D: "D",
            tcod.event.KeySym.R: "R",
            tcod.event.KeySym.Q: "Q",
            tcod.event.KeySym.ESCAPE: "ESCAPE",
            tcod.event.KeySym.F1: "F1",
            tcod.event.KeySym.F2: "F2",
            tcod.event.KeySym.F3: "F3",
            tcod.event.KeySym.F4: "F4",
        }
        return key_map.get(key_sym)

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
        Get help text for movement controls based on configuration.

        Returns:
            String describing movement controls
        """
        # Build help text from configuration
        help_parts = []

        # Movement keys
        movement_keys = []
        for direction, keys in self.config.get('movement', {}).items():
            primary = keys.get('primary', '')
            alternate = keys.get('alternate', '')
            if primary and alternate:
                movement_keys.append(f"{primary}/{alternate}")
            elif primary:
                movement_keys.append(primary)

        if movement_keys:
            help_parts.append(f"Movement: {', '.join(movement_keys)}")

        # Fast movement modifier
        fast_mod = self.config.get('modifiers', {}).get('fast_movement', 'SHIFT')
        help_parts.append(f"Hold {fast_mod} for fast movement")

        # Game actions
        for action, keys in self.config.get('game_actions', {}).items():
            primary = keys.get('primary', '')
            if primary and action == 'regenerate_world':
                help_parts.append(f"{primary}: Regenerate")
            elif primary and action == 'exit':
                exit_mod = self.config.get('modifiers', {}).get('exit_modifier', '')
                if exit_mod and keys.get('alternate'):
                    help_parts.append(f"{exit_mod}+{keys['alternate']} or {primary}: Exit")
                else:
                    help_parts.append(f"{primary}: Exit")

        # Debug actions
        debug_keys = []
        for action, keys in self.config.get('debug_actions', {}).items():
            primary = keys.get('primary', '')
            if primary:
                action_name = action.replace('toggle_', '').title()
                debug_keys.append(f"{primary}: {action_name}")

        if debug_keys:
            help_parts.append(" | ".join(debug_keys))

        return " | ".join(help_parts)
    
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
    from ..config import CameraConfig
    
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
