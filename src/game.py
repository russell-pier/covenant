#!/usr/bin/env python3
"""
Game logic for 2D Minecraft-like World

Contains the core game state, rendering, and input handling logic.
Renders a tile-based world with pipeline generation.
"""

import time
import tcod
from .generators import WorldGenerator
from .render import GameRenderer
from .config import get_config
from .camera import Camera
from .input_handler import InputHandler
from .async_world import AsyncWorldManager
try:
    from .profiler import profile_function, start_profiling, end_profiling, print_profiling_stats
except ImportError:
    # Fallback for when profiler is not available
    def profile_function(name=None):
        def decorator(func):
            return func
        return decorator
    def start_profiling(name): pass
    def end_profiling(name): pass
    def print_profiling_stats(n): pass

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

# Initialize camera and async world manager
_camera = Camera(_config.camera)
_world_manager = AsyncWorldManager(_config.world)
_input_handler = InputHandler(_camera)

# Set up input handler callbacks
def _regenerate_world():
    """Callback for world regeneration."""
    _world_manager.regenerate_world()
    _renderer.add_effect('sparkle', *_camera.get_cursor_position(), 30, color=(255, 255, 0))

def _toggle_debug():
    """Callback for debug toggle."""
    status_display = _renderer.get_status_display()
    status_display.toggle_debug()
    print(f"Debug display: {'ON' if status_display.show_debug else 'OFF'}")

def _toggle_coordinates():
    """Callback for coordinates toggle."""
    status_display = _renderer.get_status_display()
    status_display.toggle_coordinates()
    print(f"Coordinate display: {'ON' if status_display.show_coordinates else 'OFF'}")

def _toggle_fps():
    """Callback for FPS toggle."""
    status_display = _renderer.get_status_display()
    status_display.toggle_fps()
    print(f"FPS display: {'ON' if status_display.show_fps else 'OFF'}")

def _toggle_chunk_debug():
    """Callback for chunk debug toggle."""
    status_display = _renderer.get_status_display()
    status_display.toggle_chunk_debug()
    print(f"Chunk debug: {'ON' if status_display.show_chunk_debug else 'OFF'}")

_input_handler.set_regenerate_callback(_regenerate_world)
_input_handler.set_debug_callbacks(
    toggle_debug=_toggle_debug,
    toggle_coordinates=_toggle_coordinates,
    toggle_fps=_toggle_fps,
    toggle_chunk_debug=_toggle_chunk_debug
)


@profile_function("game.render_frame")
def render_frame(console):
    """Render a single frame of the game."""
    global _world_manager, _camera, _renderer

    # Get current console dimensions (these change with window resize)
    screen_width = console.width
    screen_height = console.height

    # Update world chunks based on camera position and screen viewport
    start_profiling("world.update_chunks")
    _world_manager.update_chunks(_camera, screen_width, screen_height)
    end_profiling("world.update_chunks")

    # Get camera position for rendering
    start_profiling("camera.get_position")
    view_center_x, view_center_y = _camera.get_cursor_position()
    end_profiling("camera.get_position")

    # Get tile under cursor for status display
    start_profiling("world.get_tile")
    cursor_tile = _world_manager.get_tile(view_center_x, view_center_y)
    end_profiling("world.get_tile")

    start_profiling("world.get_chunk_info")
    chunk_info = _world_manager.get_chunk_info(view_center_x, view_center_y)
    end_profiling("world.get_chunk_info")

    start_profiling("world.get_statistics")
    world_stats = _world_manager.get_statistics()
    end_profiling("world.get_statistics")

    # Prepare render options with cursor information
    render_options = {
        'cursor_tile': cursor_tile,
        'cursor_position': (view_center_x, view_center_y),
        'chunk_info': chunk_info,
        'world_stats': world_stats,
        'highlight_positions': [(view_center_x, view_center_y)]  # Highlight cursor position
    }

    # Use the renderer to draw everything
    start_profiling("renderer.render_frame")
    _renderer.render_frame(console, _world_manager, view_center_x, view_center_y, **render_options)
    end_profiling("renderer.render_frame")


def handle_input(event):
    """Handle input events. Returns True if the game should exit."""
    global _input_handler

    # Use the input handler to process all events
    return _input_handler.handle_event(event)


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

    try:
        frame_count = 0
        last_profile_print = time.time()
        target_fps = 60
        frame_time = 1.0 / target_fps
        last_frame_time = time.time()

        while True:
            start_profiling("game.main_loop")
            frame_count += 1

            # Check if we need to resize the console based on context size
            start_profiling("console.resize_check")
            context_width, context_height = context.recommended_console_size()
            if console.width != context_width or console.height != context_height:
                # Resize the console to match the window
                console = tcod.console.Console(context_width, context_height, order="F")
                print(f"Console resized to {context_width}x{context_height}")
            end_profiling("console.resize_check")

            # Render the frame with current console size
            render_frame(console)

            # Present the console to the screen
            start_profiling("tcod.present")
            context.present(console)
            end_profiling("tcod.present")

            # Handle events (non-blocking for smooth 60 FPS)
            start_profiling("event.handling")
            for event in tcod.event.get():  # Non-blocking event handling
                if handle_input(event):
                    return
            end_profiling("event.handling")

            end_profiling("game.main_loop")

            # Frame rate limiting
            current_time = time.time()
            elapsed = current_time - last_frame_time
            if elapsed < frame_time:
                sleep_time = frame_time - elapsed
                time.sleep(sleep_time)
            last_frame_time = time.time()

            # Print profiling stats every 10 seconds (reduced frequency)
            if current_time - last_profile_print > 10.0:
                print(f"\n📊 PROFILING STATS (Frame {frame_count}):")
                print_profiling_stats(10)
                last_profile_print = current_time
    finally:
        # Cleanup async world manager
        print("Shutting down game systems...")
        _world_manager.shutdown()


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
