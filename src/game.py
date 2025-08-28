#!/usr/bin/env python3
"""
Game logic for 2D Minecraft-like World

Contains the core game state, rendering, and input handling logic.
Renders a tile-based world with pipeline generation.
"""

import tcod
from .generators import WorldGenerator
from .render import GameRenderer
from .config import get_config

# Game state
_config = get_config()
_world_generator = WorldGenerator(
    generator_type=_config.world.generator_type,
    seed=_config.world.seed,
    chunk_size=_config.world.chunk_size,
    pipeline_layers=_config.world.pipeline_layers,
    layer_configs=_config.world.layer_configs,
    visualize=False  # Set to True to see layer-by-layer generation
)
_renderer = GameRenderer()
_world_generated = False


def render_frame(console):
    """Render a single frame of the game."""
    global _world_generator, _world_generated, _renderer, _config

    # Get current console dimensions (these change with window resize)
    screen_width = console.width
    screen_height = console.height

    # Generate world if not already done or if screen size changed significantly
    if not _world_generated:
        # Generate world to fill the entire screen view
        _world_generator.generate_for_view(_config.world.center_x, _config.world.center_y, screen_width, screen_height)
        _world_generated = True
        print(f"Generated world for screen {screen_width}x{screen_height} centered at ({_config.world.center_x}, {_config.world.center_y})")

    # Calculate the world coordinates that correspond to the screen
    # Center the world view on the world center
    view_center_x = _config.world.center_x
    view_center_y = _config.world.center_y

    # Use the renderer to draw everything
    _renderer.render_frame(console, _world_generator, view_center_x, view_center_y)


def handle_input(event):
    """Handle input events. Returns True if the game should exit."""
    global _world_generated, _renderer

    if event.type == "QUIT":
        # Window close button was clicked
        return True
    elif event.type == "KEYDOWN":
        # Check for Ctrl+Q
        if event.sym == tcod.event.KeySym.Q and event.mod & tcod.event.Modifier.CTRL:
            print("Ctrl+Q pressed. Exiting gracefully...")
            return True
        # Also allow ESC as an alternative exit
        elif event.sym == tcod.event.KeySym.ESCAPE:
            print("ESC pressed. Exiting gracefully...")
            return True
        # R key to regenerate world
        elif event.sym == tcod.event.KeySym.R:
            print("Regenerating world...")
            _world_generated = False
            # Add a sparkle effect at the center when regenerating
            _renderer.add_effect('sparkle', _config.world.center_x, _config.world.center_y, 30, color=(255, 255, 0))
        # F1 key to toggle debug info
        elif event.sym == tcod.event.KeySym.F1:
            status_display = _renderer.get_status_display()
            status_display.toggle_debug()
            print(f"Debug display: {'ON' if status_display.show_debug else 'OFF'}")
        # F2 key to toggle coordinates
        elif event.sym == tcod.event.KeySym.F2:
            status_display = _renderer.get_status_display()
            status_display.toggle_coordinates()
            print(f"Coordinate display: {'ON' if status_display.show_coordinates else 'OFF'}")
    return False


def run_game():
    """Main game loop. This is the entry point for the game logic."""
    global _world_generated, _config
    print(f"Starting {_config.application.title}...")

    # Initialize the console with configured size
    console = tcod.console.Console(_config.window.initial_width, _config.window.initial_height, order="F")

    # Use default font for now - custom fonts can cause spacing issues
    # The seamless rendering system handles gaps using background colors
    with tcod.context.new_terminal(
        columns=console.width,
        rows=console.height,
        title=_config.application.title,
        vsync=_config.window.vsync,
    ) as context:
        main_loop(context, console)


def main_loop(context, console):
    """Main game loop extracted for reuse with different contexts."""
    global _world_generated

    while True:
            # Check if we need to resize the console based on context size
            context_width, context_height = context.recommended_console_size()
            if console.width != context_width or console.height != context_height:
                # Resize the console to match the window
                console = tcod.console.Console(context_width, context_height, order="F")
                # Force world regeneration on resize to ensure proper coverage
                _world_generated = False
                print(f"Console resized to {context_width}x{context_height}")
            
            # Render the frame with current console size
            render_frame(console)
            
            # Present the console to the screen
            context.present(console)
            
            # Handle events
            for event in tcod.event.wait():
                if handle_input(event):
                    return


if __name__ == "__main__":
    # Allow running the game directly for testing
    try:
        run_game()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Exiting gracefully...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("2D world game terminated.")
