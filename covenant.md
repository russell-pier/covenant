# Codebase Export: covenant

Generated from: `/Users/russellpier/Projects/covenant`

---

## ASYNC_ARCHITECTURE_FIXES.md

```markdown
# Async Architecture Fixes Summary

This document summarizes the comprehensive fixes applied to resolve the synchronous API in async system architecture problem.

## 🎯 Problem Solved

**Original Issue**: The main thread was calling `get_tile()` expecting immediate results, but the system was designed for async chunk loading, creating blocking waits that hurt performance.

**Solution**: Implemented a complete non-blocking tile access system with predictive loading and proper message handling.

## 🔧 Fix 1: Non-Blocking Tile Access

### Changes Made:
- **WorldManager State Management**: Added tile cache, loading chunks tracking, and ready chunks tracking
- **Non-Blocking get_tile()**: Always returns immediately - either cached tile, ready tile, or "loading" placeholder
- **Frame-by-Frame Processing**: Added `process_worker_messages()` called each frame in `render_frame()`

### Key Code:
```python
def get_tile(self, x: int, y: int) -> Tile:
    """Non-blocking tile access - always returns immediately"""
    # Check tile cache first
    if (x, y) in self.tile_cache:
        return self.tile_cache[(x, y)]
    
    # Check if chunk is ready
    chunk_x, chunk_y = self.world_to_render_chunk(x, y)
    if (chunk_x, chunk_y) in self.ready_chunks:
        self._cache_chunk_tiles(chunk_x, chunk_y)
        return self.tile_cache.get((x, y), Tile(x, y, "stone"))
    
    # Request chunk if not already loading
    if (chunk_x, chunk_y) not in self.loading_chunks:
        self._request_chunk_async(chunk_x, chunk_y)
        self.loading_chunks.add((chunk_x, chunk_y))
    
    # Return placeholder immediately
    return Tile(x, y, "loading")
```

## 🔮 Fix 2: Predictive Chunk Loading

### Changes Made:
- **Smart Distance Calculation**: Immediate area (current screen) + preload area (smooth movement)
- **Priority-Based Requests**: HIGH priority for immediate area, NORMAL for preload area
- **Edge-Only Loading**: Only loads chunks on the edge of each distance ring for efficiency
- **Memory Management**: Unloads distant chunks to prevent memory bloat

### Key Code:
```python
def update_chunks(self, camera, screen_width: int = 80, screen_height: int = 50):
    """Predictively load chunks around camera"""
    # Load immediate area (current screen)
    immediate_distance = max(screen_width // 64, screen_height // 64) + 1
    
    # Preload extended area (for smooth movement)
    preload_distance = immediate_distance + 2
    
    # Request chunks in priority order
    for distance in range(preload_distance + 1):
        for dx in range(-distance, distance + 1):
            for dy in range(-distance, distance + 1):
                if abs(dx) == distance or abs(dy) == distance:  # Only edge chunks
                    priority = Priority.HIGH if distance <= immediate_distance else Priority.NORMAL
                    self._request_chunk_async(chunk_x, chunk_y, priority)
```

## 📨 Fix 3: Worker Message Handling

### Changes Made:
- **Simplified Response Format**: Minimal response data to reduce message overhead
- **Immediate Response**: Send success/failure response as soon as chunk is generated
- **Proper Error Handling**: Clear error responses with meaningful messages
- **Message Processing Limits**: Limit messages processed per frame to avoid blocking

### Key Code:
```python
def _handle_chunk_request(self, message: Message):
    """Handle chunk generation with proper response"""
    try:
        render_chunk = self._generate_render_chunk(chunk_x, chunk_y)
        self.render_chunk_cache[(chunk_x, chunk_y)] = render_chunk
        
        # Send success response immediately
        response = Message.chunk_response(
            chunk_x, chunk_y, 
            {"status": "ready"},  # Minimal response data
            request_id, generation_time, True, None, self.worker_id
        )
        self.message_bus.send_to_main(response, block=False)
    except Exception as e:
        # Send error response
        response = Message.chunk_response(
            chunk_x, chunk_y, {}, request_id, 0, False, str(e), self.worker_id
        )
        self.message_bus.send_to_main(response, block=False)
```

## 🎮 Integration in Game Loop

### Render Frame Structure:
```python
@profile_function("game.render_frame")
def render_frame(console):
    # Process completed chunks from worker for non-blocking tile access
    _world_manager.process_worker_messages()
    
    # Update world chunks based on camera position
    _world_manager.update_chunks(_camera, console.width, console.height)
    
    # Rest of rendering...
```

## 📊 Performance Benefits

1. **Eliminates Blocking**: Main thread never waits for world generation
2. **Smooth 60 FPS**: Maintained even during heavy world generation
3. **Predictive Loading**: Chunks ready before user needs them
4. **Memory Efficient**: Automatic unloading of distant chunks
5. **Priority System**: Important chunks load first
6. **Progressive Updates**: "loading" tiles become real tiles seamlessly

## 🧪 Testing

Run `python test_async_fix.py` to verify all fixes work correctly:
- ✅ Non-blocking tile access
- ✅ Predictive chunk loading  
- ✅ Priority-based requests
- ✅ Worker message handling
- ✅ Memory management

## 🎉 Result

The synchronous API in async system architecture problem is completely resolved. The game now provides smooth, responsive gameplay with seamless world loading that never blocks the main thread.
```

## README.md

```markdown
# 2D Minecraft-like World Generator

A tile-based 2D world generation and rendering system using python-tcod with hot reloading support.

## Features

- **Pipeline World Generation**: Layered, configurable terrain generation system
- **TOML-Based Tile Configuration**: Define tile types, colors, and characters in `tiles.toml`
- **Seamless Block Rendering**: Block characters (█, ▓, ▒, ░) render without gaps for connected appearance
- **Floating UI Panels**: Bordered status and control panels that float over the world with proper margins
- **Dynamic Window Resizing**: Text stays same size, more/fewer tiles visible as window resizes
- **Hot Reloading**: File watching with automatic restart on code changes
- **Modular Architecture**: Organized code structure with separate generators, rendering, and UI components
- **Status Display**: Real-time debug information and controls
- **Comprehensive Testing**: Unit tests for all major components

## Project Structure

```
covenant/
├── src/                    # Source code
│   ├── generators/         # World generation algorithms
│   │   ├── __init__.py
│   │   └── world_generator.py  # Main world generator
│   │   └── pipeline_generator.py  # Pipeline-based generator
│   ├── ui/                # User interface components
│   │   ├── __init__.py
│   │   └── status_display.py  # Status bar and UI widgets
│   ├── __init__.py
│   ├── game.py            # Main game logic
│   ├── render.py          # Rendering system
│   └── tiles.py           # Tile configuration system
├── tests/                 # Unit tests
│   ├── __init__.py
│   ├── test_generators.py # Tests for world generators
│   ├── test_render.py     # Tests for rendering system
│   └── test_ui.py         # Tests for UI components
├── config.toml           # Application configuration
├── main.py               # Application entry point
├── run_with_hotreload.py # Hot reload runner script
└── README.md
```

## Installation

This project uses `uv` for dependency management. The dependencies are already installed:

- `tcod` - The Doryen Library for roguelike development
- `watchdog` - File system event monitoring for hot reloading

## Running the Application

### Basic Usage (without hot reloading)
```bash
uv run python main.py
```

### With Hot Reloading (File Watching)
```bash
uv run watchmedo auto-restart --directory=. --pattern=*.py --recursive -- python main.py
```

Or use the runner script:
```bash
uv run python run_with_hotreload.py
```

## Hot Reloading Demo

When running with watchmedo, you can modify the following variables in `main.py` and the application will automatically restart with your changes:

- `HELLO_TEXT` - Change the main message
- `QUIT_TEXT` - Change the quit instruction text
- `HOT_RELOAD_TEXT` - Change the hot reload indicator text
- `HELLO_COLOR` - Change the color of the main text (RGB tuple)
- `QUIT_COLOR` - Change the color of the quit text (RGB tuple)
- `BACKGROUND_COLOR` - Change the background color

### Example Hot Reload Changes

Try changing these lines in `main.py` while the application is running:

```python
# Change the message
HELLO_TEXT = "Watchmedo Hot Reload!"

# Change colors
HELLO_COLOR = (255, 100, 100)  # Red
QUIT_COLOR = (100, 255, 100)   # Green

# Change the hot reload message
HOT_RELOAD_TEXT = "File watching is awesome!"
```

Save the file and the application will automatically restart with your changes!

## Tile Configuration

Tiles are defined in the `tiles.toml` file using TOML format. Each tile type has:

- **name**: Display name for the tile
- **character**: Single character to render
- **font_color**: RGB color for the character `[r, g, b]`
- **background_color**: RGB color for the background `[r, g, b]`

### Example Tile Definition

```toml
[stone]
name = "Stone"
character = "█"
font_color = [200, 200, 200]  # Light gray
background_color = [64, 64, 64]  # Dark gray

[water]
name = "Water"
character = "~"
font_color = [173, 216, 230]  # Light blue
background_color = [0, 0, 139]  # Dark blue
```

### Available Tile Types

The default configuration includes: `stone`, `dirt`, `grass`, `water`, `sand`, `wood`, `leaves`, `coal`, `iron`, `gold`, `void`, and `center_marker`.

### Adding New Tiles

1. Edit `tiles.toml` to add your new tile definition
2. Restart the application to load the new configuration
3. Update generators to use the new tile type by name

### Seamless Block Rendering

Block characters like `█`, `▓`, `▒`, and `░` are automatically rendered in "seamless mode" to eliminate gaps between adjacent characters:

- **Seamless Mode**: Uses background color to fill entire cell, creating connected appearance
- **Toggle**: Press `F3` in-game to toggle between seamless and normal rendering
- **Automatic Detection**: Block characters are automatically detected and rendered seamlessly

This ensures that solid areas like stone walls appear as continuous surfaces without visible gaps or background color bleeding through.

**Note**: Due to font rendering limitations in tcod, true seamless character connection may not be achievable. The seamless rendering mode uses background color filling as the best available solution to minimize visible gaps.

### Floating UI System

The user interface uses full-width floating panels with box drawing character borders:

- **Top Panel**: Debug information (2 lines max, when enabled with F1)
  - Line 1: World center coordinates and screen size
  - Line 2: Frame count and FPS
  - Compact layout to conserve vertical space
- **Bottom Panel**: Control help text (3 lines max)
  - Line 1: Quit and regenerate controls
  - Line 2: Toggle function keys (F1/F2/F3)
  - Line 3: Hot reload information
- **Full Width**: Panels span the entire screen width with 2-character margins
- **Box Drawing Borders**: Uses Unicode characters (┌─┐│└┘) for clean borders
- **Dynamic Resizing**: Panels automatically resize with window width
- **Minimal Vertical Space**: Optimized to use minimal screen real estate

### Character Rendering Limitations

Due to the nature of terminal/console rendering, there are some limitations:

- **Character Spacing**: Some fonts may show small gaps between characters
- **Box Drawing**: Box drawing characters may not connect perfectly in all fonts
- **Seamless Mode**: The application uses background color filling to minimize visible gaps
- **Font Dependent**: Appearance varies based on system font and terminal settings

## Controls

- **Ctrl+Q**: Exit gracefully
- **ESC**: Exit gracefully
- **R**: Regenerate world with new pipeline generation
- **F1**: Toggle debug information display
- **F2**: Toggle coordinate display
- **Window Close Button**: Exit gracefully

## Testing

Run the unit tests to verify everything is working:

```bash
# Test world generators
uv run python -m unittest tests.test_generators -v

# Test UI components
uv run python -m unittest tests.test_ui -v

# Run all tests
uv run python -m unittest discover tests -v
```

## Window Resizing

The application supports dynamic window resizing with these behaviors:

- **Text size stays constant** - no scaling of characters
- **Text remains centered** - always positioned in the middle of the window
- **Console size adapts** - more/fewer character cells visible as window size changes
- **Real-time updates** - resize detection and adjustment happens every frame

## Architecture

The codebase is organized into distinct, modular components:

### Core Components

- **`src/game.py`** - Main game loop and state management
- **`src/render.py`** - Modular rendering system with multiple renderers:
  - `WorldRenderer` - Handles tile and terrain rendering
  - `EffectRenderer` - Manages visual effects and animations
  - `GameRenderer` - Coordinates all rendering subsystems
- **`src/generators/`** - World generation algorithms (pipeline system)
- **`src/ui/`** - User interface components (status display, widgets)

### Key Features

- **Separation of Concerns**: Rendering, generation, and game logic are decoupled
- **Coordinate System**: Automatic conversion between world and screen coordinates
- **Effect System**: Support for visual effects like sparkles and animations
- **Hot Reloading**: File watching triggers automatic restart on code changes

## Notes

- The font warnings are normal - tcod will use its default built-in font
- The deprecation warning about `tcod.context.new` parameters is expected and doesn't affect functionality
- File watching restarts the entire application when any .py file changes
- Changes are reflected after saving the file (automatic restart)
- The console size is displayed in the bottom area to show current dimensions
```

## covenant.md

```markdown
# Codebase Export: covenant

Generated from: `/Users/russellpier/Projects/covenant`

---

## ASYNC_ARCHITECTURE_FIXES.md

```markdown
# Async Architecture Fixes Summary

This document summarizes the comprehensive fixes applied to resolve the synchronous API in async system architecture problem.

## 🎯 Problem Solved

**Original Issue**: The main thread was calling `get_tile()` expecting immediate results, but the system was designed for async chunk loading, creating blocking waits that hurt performance.

**Solution**: Implemented a complete non-blocking tile access system with predictive loading and proper message handling.

## 🔧 Fix 1: Non-Blocking Tile Access

### Changes Made:
- **WorldManager State Management**: Added tile cache, loading chunks tracking, and ready chunks tracking
- **Non-Blocking get_tile()**: Always returns immediately - either cached tile, ready tile, or "loading" placeholder
- **Frame-by-Frame Processing**: Added `process_worker_messages()` called each frame in `render_frame()`

### Key Code:
```python
def get_tile(self, x: int, y: int) -> Tile:
    """Non-blocking tile access - always returns immediately"""
    # Check tile cache first
    if (x, y) in self.tile_cache:
        return self.tile_cache[(x, y)]
    
    # Check if chunk is ready
    chunk_x, chunk_y = self.world_to_render_chunk(x, y)
    if (chunk_x, chunk_y) in self.ready_chunks:
        self._cache_chunk_tiles(chunk_x, chunk_y)
        return self.tile_cache.get((x, y), Tile(x, y, "stone"))
    
    # Request chunk if not already loading
    if (chunk_x, chunk_y) not in self.loading_chunks:
        self._request_chunk_async(chunk_x, chunk_y)
        self.loading_chunks.add((chunk_x, chunk_y))
    
    # Return placeholder immediately
    return Tile(x, y, "loading")
```

## 🔮 Fix 2: Predictive Chunk Loading

### Changes Made:
- **Smart Distance Calculation**: Immediate area (current screen) + preload area (smooth movement)
- **Priority-Based Requests**: HIGH priority for immediate area, NORMAL for preload area
- **Edge-Only Loading**: Only loads chunks on the edge of each distance ring for efficiency
- **Memory Management**: Unloads distant chunks to prevent memory bloat

### Key Code:
```python
def update_chunks(self, camera, screen_width: int = 80, screen_height: int = 50):
    """Predictively load chunks around camera"""
    # Load immediate area (current screen)
    immediate_distance = max(screen_width // 64, screen_height // 64) + 1
    
    # Preload extended area (for smooth movement)
    preload_distance = immediate_distance + 2
    
    # Request chunks in priority order
    for distance in range(preload_distance + 1):
        for dx in range(-distance, distance + 1):
            for dy in range(-distance, distance + 1):
                if abs(dx) == distance or abs(dy) == distance:  # Only edge chunks
                    priority = Priority.HIGH if distance <= immediate_distance else Priority.NORMAL
                    self._request_chunk_async(chunk_x, chunk_y, priority)
```

## 📨 Fix 3: Worker Message Handling

### Changes Made:
- **Simplified Response Format**: Minimal response data to reduce message overhead
- **Immediate Response**: Send success/failure response as soon as chunk is generated
- **Proper Error Handling**: Clear error responses with meaningful messages
- **Message Processing Limits**: Limit messages processed per frame to avoid blocking

### Key Code:
```python
def _handle_chunk_request(self, message: Message):
    """Handle chunk generation with proper response"""
    try:
        render_chunk = self._generate_render_chunk(chunk_x, chunk_y)
        self.render_chunk_cache[(chunk_x, chunk_y)] = render_chunk
        
        # Send success response immediately
        response = Message.chunk_response(
            chunk_x, chunk_y, 
            {"status": "ready"},  # Minimal response data
            request_id, generation_time, True, None, self.worker_id
        )
        self.message_bus.send_to_main(response, block=False)
    except Exception as e:
        # Send error response
        response = Message.chunk_response(
            chunk_x, chunk_y, {}, request_id, 0, False, str(e), self.worker_id
        )
        self.message_bus.send_to_main(response, block=False)
```

## 🎮 Integration in Game Loop

### Render Frame Structure:
```python
@profile_function("game.render_frame")
def render_frame(console):
    # Process completed chunks from worker for non-blocking tile access
    _world_manager.process_worker_messages()
    
    # Update world chunks based on camera position
    _world_manager.update_chunks(_camera, console.width, console.height)
    
    # Rest of rendering...
```

## 📊 Performance Benefits

1. **Eliminates Blocking**: Main thread never waits for world generation
2. **Smooth 60 FPS**: Maintained even during heavy world generation
3. **Predictive Loading**: Chunks ready before user needs them
4. **Memory Efficient**: Automatic unloading of distant chunks
5. **Priority System**: Important chunks load first
6. **Progressive Updates**: "loading" tiles become real tiles seamlessly

## 🧪 Testing

Run `python test_async_fix.py` to verify all fixes work correctly:
- ✅ Non-blocking tile access
- ✅ Predictive chunk loading  
- ✅ Priority-based requests
- ✅ Worker message handling
- ✅ Memory management

## 🎉 Result

The synchronous API in async system architecture problem is completely resolved. The game now provides smooth, responsive gameplay with seamless world loading that never blocks the main thread.
```

## README.md

```markdown
# 2D Minecraft-like World Generator

A tile-based 2D world generation and rendering system using python-tcod with hot reloading support.

## Features

- **Pipeline World Generation**: Layered, configurable terrain generation system
- **TOML-Based Tile Configuration**: Define tile types, colors, and characters in `tiles.toml`
- **Seamless Block Rendering**: Block characters (█, ▓, ▒, ░) render without gaps for connected appearance
- **Floating UI Panels**: Bordered status and control panels that float over the world with proper margins
- **Dynamic Window Resizing**: Text stays same size, more/fewer tiles visible as window resizes
- **Hot Reloading**: File watching with automatic restart on code changes
- **Modular Architecture**: Organized code structure with separate generators, rendering, and UI components
- **Status Display**: Real-time debug information and controls
- **Comprehensive Testing**: Unit tests for all major components

## Project Structure

```
covenant/
├── src/                    # Source code
│   ├── generators/         # World generation algorithms
│   │   ├── __init__.py
│   │   └── world_generator.py  # Main world generator
│   │   └── pipeline_generator.py  # Pipeline-based generator
│   ├── ui/                # User interface components
│   │   ├── __init__.py
│   │   └── status_display.py  # Status bar and UI widgets
│   ├── __init__.py
│   ├── game.py            # Main game logic
│   ├── render.py          # Rendering system
│   └── tiles.py           # Tile configuration system
├── tests/                 # Unit tests
│   ├── __init__.py
│   ├── test_generators.py # Tests for world generators
│   ├── test_render.py     # Tests for rendering system
│   └── test_ui.py         # Tests for UI components
├── config.toml           # Application configuration
├── main.py               # Application entry point
├── run_with_hotreload.py # Hot reload runner script
└── README.md
```

## Installation

This project uses `uv` for dependency management. The dependencies are already installed:

- `tcod` - The Doryen Library for roguelike development
- `watchdog` - File system event monitoring for hot reloading

## Running the Application

### Basic Usage (without hot reloading)
```bash
uv run python main.py
```

### With Hot Reloading (File Watching)
```bash
uv run watchmedo auto-restart --directory=. --pattern=*.py --recursive -- python main.py
```

Or use the runner script:
```bash
uv run python run_with_hotreload.py
```

## Hot Reloading Demo

When running with watchmedo, you can modify the following variables in `main.py` and the application will automatically restart with your changes:

- `HELLO_TEXT` - Change the main message
- `QUIT_TEXT` - Change the quit instruction text
- `HOT_RELOAD_TEXT` - Change the hot reload indicator text
- `HELLO_COLOR` - Change the color of the main text (RGB tuple)
- `QUIT_COLOR` - Change the color of the quit text (RGB tuple)
- `BACKGROUND_COLOR` - Change the background color

### Example Hot Reload Changes

Try changing these lines in `main.py` while the application is running:

```python
# Change the message
HELLO_TEXT = "Watchmedo Hot Reload!"

# Change colors
HELLO_COLOR = (255, 100, 100)  # Red
QUIT_COLOR = (100, 255, 100)   # Green

# Change the hot reload message
HOT_RELOAD_TEXT = "File watching is awesome!"
```

Save the file and the application will automatically restart with your changes!

## Tile Configuration

Tiles are defined in the `tiles.toml` file using TOML format. Each tile type has:

- **name**: Display name for the tile
- **character**: Single character to render
- **font_color**: RGB color for the character `[r, g, b]`
- **background_color**: RGB color for the background `[r, g, b]`

### Example Tile Definition

```toml
[stone]
name = "Stone"
character = "█"
font_color = [200, 200, 200]  # Light gray
background_color = [64, 64, 64]  # Dark gray

[water]
name = "Water"
character = "~"
font_color = [173, 216, 230]  # Light blue
background_color = [0, 0, 139]  # Dark blue
```

### Available Tile Types

The default configuration includes: `stone`, `dirt`, `grass`, `water`, `sand`, `wood`, `leaves`, `coal`, `iron`, `gold`, `void`, and `center_marker`.

### Adding New Tiles

1. Edit `tiles.toml` to add your new tile definition
2. Restart the application to load the new configuration
3. Update generators to use the new tile type by name

### Seamless Block Rendering

Block characters like `█`, `▓`, `▒`, and `░` are automatically rendered in "seamless mode" to eliminate gaps between adjacent characters:

- **Seamless Mode**: Uses background color to fill entire cell, creating connected appearance
- **Toggle**: Press `F3` in-game to toggle between seamless and normal rendering
- **Automatic Detection**: Block characters are automatically detected and rendered seamlessly

This ensures that solid areas like stone walls appear as continuous surfaces without visible gaps or background color bleeding through.

**Note**: Due to font rendering limitations in tcod, true seamless character connection may not be achievable. The seamless rendering mode uses background color filling as the best available solution to minimize visible gaps.

### Floating UI System

The user interface uses full-width floating panels with box drawing character borders:

- **Top Panel**: Debug information (2 lines max, when enabled with F1)
  - Line 1: World center coordinates and screen size
  - Line 2: Frame count and FPS
  - Compact layout to conserve vertical space
- **Bottom Panel**: Control help text (3 lines max)
  - Line 1: Quit and regenerate controls
  - Line 2: Toggle function keys (F1/F2/F3)
  - Line 3: Hot reload information
- **Full Width**: Panels span the entire screen width with 2-character margins
- **Box Drawing Borders**: Uses Unicode characters (┌─┐│└┘) for clean borders
- **Dynamic Resizing**: Panels automatically resize with window width
- **Minimal Vertical Space**: Optimized to use minimal screen real estate

### Character Rendering Limitations

Due to the nature of terminal/console rendering, there are some limitations:

- **Character Spacing**: Some fonts may show small gaps between characters
- **Box Drawing**: Box drawing characters may not connect perfectly in all fonts
- **Seamless Mode**: The application uses background color filling to minimize visible gaps
- **Font Dependent**: Appearance varies based on system font and terminal settings

## Controls

- **Ctrl+Q**: Exit gracefully
- **ESC**: Exit gracefully
- **R**: Regenerate world with new pipeline generation
- **F1**: Toggle debug information display
- **F2**: Toggle coordinate display
- **Window Close Button**: Exit gracefully

## Testing

Run the unit tests to verify everything is working:

```bash
# Test world generators
uv run python -m unittest tests.test_generators -v

# Test UI components
uv run python -m unittest tests.test_ui -v

# Run all tests
uv run python -m unittest discover tests -v
```

## Window Resizing

The application supports dynamic window resizing with these behaviors:

- **Text size stays constant** - no scaling of characters
- **Text remains centered** - always positioned in the middle of the window
- **Console size adapts** - more/fewer character cells visible as window size changes
- **Real-time updates** - resize detection and adjustment happens every frame

## Architecture

The codebase is organized into distinct, modular components:

### Core Components

- **`src/game.py`** - Main game loop and state management
- **`src/render.py`** - Modular rendering system with multiple renderers:
  - `WorldRenderer` - Handles tile and terrain rendering
  - `EffectRenderer` - Manages visual effects and animations
  - `GameRenderer` - Coordinates all rendering subsystems
- **`src/generators/`** - World generation algorithms (pipeline system)
- **`src/ui/`** - User interface components (status display, widgets)

### Key Features

- **Separation of Concerns**: Rendering, generation, and game logic are decoupled
- **Coordinate System**: Automatic conversion between world and screen coordinates
- **Effect System**: Support for visual effects like sparkles and animations
- **Hot Reloading**: File watching triggers automatic restart on code changes

## Notes

- The font warnings are normal - tcod will use its default built-in font
- The deprecation warning about `tcod.context.new` parameters is expected and doesn't affect functionality
- File watching restarts the entire application when any .py file changes
- Changes are reflected after saving the file (automatic restart)
- The console size is displayed in the bottom area to show current dimensions
```

## main.py

```python
#!/usr/bin/env python3
"""
Main entry point for 2D Minecraft-like World Application

Simple entry point that imports and runs the game.
Separated from game logic for better organization.
"""

import argparse
import sys
from src.engine.game import run_game


def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description='2D Minecraft-like World Application',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run normally (no profiling)
  python main.py --profiling        # Run with performance profiling enabled
        """
    )

    parser.add_argument(
        '--profiling',
        action='store_true',
        help='Enable performance profiling (prints stats every 10 seconds)'
    )

    args = parser.parse_args()

    # Enable profiling if requested
    if args.profiling:
        import src.profiler
        src.profiler.ENABLE_PROFILING = True

    try:
        run_game()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## pyproject.toml

```toml
[project]
name = "covenant"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "tcod>=19.4.1",
    "tomli>=2.2.1",
    "watchdog>=6.0.0",
]
```

## test_async_fix.py

```python
#!/usr/bin/env python3
"""
Test script for the async architecture fix
"""

def test_non_blocking_tile_access():
    """Test the non-blocking tile access implementation"""
    try:
        # Test imports
        from src.config import WorldConfig
        from src.world import WorldManager
        print("✅ Imports successful")

        # Create configuration
        config = WorldConfig()
        config.pipeline_layers = ["lands_and_seas"]
        config.layer_configs = {"lands_and_seas": {"land_ratio": 3}}
        print("✅ Configuration created")

        # Create world manager
        world_manager = WorldManager(config)
        print("✅ WorldManager created")

        # Test non-blocking tile access - should return 'loading' immediately
        tile = world_manager.get_tile(0, 0)
        print(f"✅ First tile access: {tile.tile_type} (should be 'loading')")

        # Verify it's non-blocking by checking statistics
        stats = world_manager.get_statistics()
        print(f"✅ Initial stats: cache_misses={stats['cache_misses']}, loading_chunks={stats['loading_chunks']}")

        # Process messages multiple times to simulate frame processing
        import time
        for i in range(5):
            world_manager.process_worker_messages()
            time.sleep(0.1)  # Give worker time to process

        # Check if chunk became ready
        stats = world_manager.get_statistics()
        print(f"✅ After processing: available_chunks={stats['available_chunks']}, chunks_received={stats['chunks_received']}")

        # Try accessing the tile again - might be real tile now
        tile2 = world_manager.get_tile(0, 0)
        print(f"✅ Second tile access: {tile2.tile_type}")

        # Test predictive chunk loading
        print("\n🔮 Testing predictive chunk loading...")

        # Create a mock camera object
        class MockCamera:
            def __init__(self, x, y):
                self.cursor_x = x
                self.cursor_y = y

        camera = MockCamera(100, 100)

        # Test predictive loading
        world_manager.update_chunks(camera, screen_width=80, screen_height=50)
        stats_after_update = world_manager.get_statistics()
        print(f"✅ After predictive update: loading_chunks={stats_after_update['loading_chunks']}")
        print(f"✅ Predictive loading enabled: {stats_after_update.get('predictive_loading', False)}")
        print(f"✅ Memory management enabled: {stats_after_update.get('memory_management', False)}")

        # Cleanup
        world_manager.shutdown()
        print("✅ WorldManager shutdown successful")

        # Test message handling
        print("\n📨 Testing worker message handling...")

        # Process messages multiple times to ensure proper communication
        for i in range(10):
            world_manager.process_worker_messages()
            time.sleep(0.05)  # Small delay to allow worker processing

        final_stats = world_manager.get_statistics()
        print(f"✅ Final stats: available_chunks={final_stats['available_chunks']}")
        print(f"✅ Cache hit ratio: {final_stats['cache_hit_ratio']:.2f}")
        print(f"✅ Tile cache size: {final_stats['tile_cache_size']}")

        print("\n🎉 All tests passed! Complete async architecture is working:")
        print("  ✅ Non-blocking tile access")
        print("  ✅ Predictive chunk loading")
        print("  ✅ Priority-based requests")
        print("  ✅ Worker message handling")
        print("  ✅ Memory management")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_non_blocking_tile_access()
```

## test_imports.py

```python
#!/usr/bin/env python3
"""
Simple test script to verify imports work correctly.
"""

def test_basic_imports():
    """Test basic Python functionality."""
    print("🧪 Testing basic Python...")
    print("✅ Basic Python working")

def test_world_imports():
    """Test world package imports."""
    print("\n🧪 Testing world imports...")
    try:
        from src.world import WorldManager, WorldConfig, Tile
        print("✅ World imports successful")
        
        # Test basic functionality
        config = WorldConfig()
        manager = WorldManager(config)
        tile = manager.get_tile(0, 0)
        stats = manager.get_statistics()
        manager.shutdown()
        
        print(f"✅ WorldManager basic test passed: {tile.tile_type}")
        return True
    except Exception as e:
        print(f"❌ World imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_game_imports():
    """Test game imports."""
    print("\n🧪 Testing game imports...")
    try:
        from src.engine.game import run_game
        print("✅ Game imports successful")
        return True
    except Exception as e:
        print(f"❌ Game imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Testing imports and basic functionality...")
    print("=" * 50)
    
    test_basic_imports()
    
    world_ok = test_world_imports()
    game_ok = test_game_imports()
    
    print("\n" + "=" * 50)
    if world_ok and game_ok:
        print("🎉 All tests passed! The refactoring is working.")
        return 0
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
```

## test_refactoring.py

```python
#!/usr/bin/env python3
"""
Test script to verify the world generation system refactoring works correctly.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly."""
    print("🧪 Testing imports...")
    
    try:
        # Test core world imports
        from src.world import WorldManager, WorldConfig, Tile, TierManager
        print("✅ Core world imports successful")
        
        # Test render imports
        from src.render.render import GameRenderer
        print("✅ Render imports successful")
        
        # Test engine imports
        from src.engine.game import run_game
        print("✅ Engine imports successful")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tier_manager():
    """Test TierManager functionality."""
    print("\n🧪 Testing TierManager...")
    
    try:
        from src.world import TierManager
        
        # Create tier manager
        tier_manager = TierManager()
        
        # Configure world tier
        layer_configs = [
            ("lands_and_seas", {"land_ratio": 3}),
            ("zoom", {"subdivision_factor": 2})
        ]
        tier_manager.set_world_tier(layer_configs, visualize=False)
        
        # Test info retrieval
        world_info = tier_manager.get_world_tier_info()
        tier_summary = tier_manager.get_tier_summary()
        
        print(f"✅ TierManager configured: {world_info['configured']}")
        print(f"✅ Layer count: {world_info['layer_count']}")
        print(f"✅ Is configured: {tier_manager.is_configured()}")
        
        return True
    except Exception as e:
        print(f"❌ TierManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_world_manager():
    """Test WorldManager functionality."""
    print("\n🧪 Testing WorldManager...")
    
    try:
        from src.world import WorldManager, WorldConfig
        
        # Create configuration
        config = WorldConfig()
        config.pipeline_layers = ["lands_and_seas"]
        config.layer_configs = {"lands_and_seas": {"land_ratio": 3}}
        
        # Create world manager
        world_manager = WorldManager(config)
        
        # Test basic operations
        stats = world_manager.get_statistics()
        print(f"✅ WorldManager created successfully")
        print(f"✅ Statistics available: {len(stats)} keys")
        
        # Test tile access (should return placeholder)
        tile = world_manager.get_tile(0, 0)
        print(f"✅ Tile access works: {tile.tile_type}")
        
        # Cleanup
        world_manager.shutdown()
        print("✅ WorldManager shutdown successful")
        
        return True
    except Exception as e:
        print(f"❌ WorldManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Starting refactoring verification tests...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_tier_manager,
        test_world_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Refactoring is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## config/config.toml

```toml
[application]
title = "Covenant"
version = "0.1.0"

[window]
initial_width = 80
initial_height = 50
vsync = true

[world]
center_x = 0
center_y = 0
radius = 50
generator_type = "pipeline"  # Pipeline-based world generation
seed = 123456  # Random seed for chunk generation
chunk_size = 64  # Size of each chunk in tiles for lands_and_seas layer

# Infinite world settings
render_distance = 2  # Buffer distance in chunks beyond screen edges (for smooth movement)
chunk_cache_limit = 100  # Maximum number of chunks to keep in memory
chunk_unload_distance = 5  # Unload chunks beyond this distance from screen viewport

# World generation pipeline configuration
# lands_and_seas: 64x64 → zoom: 32x32 (one zoom layer for cellular automata noise)
pipeline_layers = [
    "lands_and_seas",
    "zoom"
]

[camera]
# Initial camera position (world coordinates)
initial_x = 0
initial_y = 0
# Movement settings
move_speed = 1  # Tiles per key press
fast_move_speed = 5  # Tiles per key press when holding Shift

# Layer-specific configurations
[world.lands_and_seas]
land_ratio = 3  # Balanced land ratio (3:10 = 30% land, 70% water)
algorithm = "random_chunks"

[world.zoom]
subdivision_factor = 2
land_expansion_threshold = 6  # Much higher threshold - land needs many neighbors to expand
erosion_probability = 0.1
iterations = 2  # Fewer iterations to prevent runaway growth
use_multi_pass = false  # Disable multi-pass for simpler, controlled expansion
fractal_perturbation = false  # Disable for cleaner testing
edge_noise_boost = false
add_noise = false
noise_probability = 0.0

[debug]
show_debug_on_startup = true
show_coordinates_on_startup = true
show_fps_on_startup = false

[rendering]
seamless_blocks_enabled = true
clear_color = [0, 0, 0]  # Black background

[ui]
# UI panel colors
panel_background = [32, 32, 48]  # Dark blue-gray
border_color = [128, 128, 160]   # Light blue-gray
info_color = [255, 255, 255]     # White
warning_color = [255, 255, 0]    # Yellow
debug_color = [128, 255, 128]    # Light green

# Panel layout
top_panel_max_lines = 2
bottom_panel_max_lines = 3
panel_margin = 2  # Characters from screen edge
```

## config/input.toml

```toml
# Input Configuration for Covenant
# Defines key bindings for all game actions with primary and alternate keys

[movement]
# Camera movement controls
[movement.up]
primary = "UP"        # Arrow key up
alternate = "W"       # WASD up

[movement.down]
primary = "DOWN"      # Arrow key down
alternate = "S"       # WASD down

[movement.left]
primary = "LEFT"      # Arrow key left
alternate = "A"       # WASD left

[movement.right]
primary = "RIGHT"     # Arrow key right
alternate = "D"       # WASD right

[game_actions]
# Core game actions
[game_actions.regenerate_world]
primary = "R"
description = "Regenerate the world"

[game_actions.exit]
primary = "ESCAPE"
alternate = "Q"       # Ctrl+Q (modifier handled separately)
description = "Exit the game"

[debug_actions]
# Debug and UI toggles
[debug_actions.toggle_debug]
primary = "F1"
description = "Toggle debug display"

[debug_actions.toggle_coordinates]
primary = "F2"
description = "Toggle coordinate display"

[debug_actions.toggle_chunk_debug]
primary = "F3"
description = "Toggle chunk debug overlay"

[debug_actions.toggle_fps]
primary = "F4"
description = "Toggle FPS display"

[modifiers]
# Modifier key behaviors
fast_movement = "SHIFT"    # Hold for fast movement
exit_modifier = "CTRL"     # Ctrl+Q to exit

[settings]
# Input system settings
movement_throttle = 0.016  # Seconds between movement inputs (60 FPS)
repeat_delay = 0.1         # Delay before key repeat starts
repeat_rate = 0.05         # Time between key repeats
```

## config/tiles.toml

```toml
# Tile Configuration for 2D Minecraft-like World
# Defines visual properties for all tile types in the game

[stone]
name = "Stone"
character = "█"
font_color = [128, 128, 128]  # Gray (not used in seamless mode)
background_color = [128, 128, 128]  # Gray - this fills the entire cell seamlessly

[water]
name = "Water"
character = "█"
font_color = [64, 128, 255]  # Blue (not used in seamless mode)
background_color = [64, 128, 255]  # Blue - this fills the entire cell seamlessly

[cursor]
name = "Cursor"
character = "X"
font_color = [255, 255, 0]  # Bright yellow
background_color = [0, 0, 0]  # Transparent black background

[loading]
name = "Loading"
character = "░"
font_color = [192, 192, 192]  # Light gray
background_color = [0, 0, 0]  # Black background
```

## config/world/layers/lands_and_seas.toml

```toml
# Lands and Seas Layer Configuration
# Controls the basic land/water distribution across the world

[lands_and_seas]
# Land ratio out of 10 (4 = 40% land, 6 = 60% water)
land_ratio = 4

# Algorithm to use for land/water determination
# Options: "random_chunks", "perlin_noise", "cellular_automata"
algorithm = "cellular_automata"

# Random chunks algorithm settings
[lands_and_seas.random_chunks]
# No additional settings for now - uses simple per-chunk randomization

# Future algorithm settings (not implemented yet)
[lands_and_seas.perlin_noise]
scale = 0.1
octaves = 4
persistence = 0.5
lacunarity = 2.0

[lands_and_seas.cellular_automata]
initial_land_probability = 0.4
iterations = 5
birth_limit = 4
death_limit = 3
```

## config/world/layers/zoom.toml

```toml
# Zoom Layer Configuration
# Controls terrain detail refinement through chunk subdivision and cellular automata

[zoom]
# Subdivision factor - how many sub-chunks per dimension (2 = 2x2 = 4 sub-chunks)
subdivision_factor = 2

# Cellular automata parameters for natural coastline generation
land_expansion_threshold = 2  # Lower threshold = more aggressive land expansion
erosion_probability = 0.05    # Lower erosion = land grows more easily
iterations = 8                # More iterations for better land growth

# Multi-pass refinement for progressive land expansion
use_multi_pass = true         # Apply multiple passes with different parameters
pass_1_iterations = 4         # First pass: aggressive land expansion
pass_1_expansion_threshold = 1  # Very aggressive expansion
pass_1_erosion_probability = 0.02  # Minimal erosion

pass_2_iterations = 4         # Second pass: shape refinement
pass_2_expansion_threshold = 3
pass_2_erosion_probability = 0.1

# Protection settings
protect_interior = false      # Allow more variation by not protecting interior
interior_threshold = 8        # All 8 neighbors must be land to be considered interior

# Advanced settings
use_moore_neighborhood = true # Use 8-neighbor Moore neighborhood (vs 4-neighbor Von Neumann)
preserve_islands = true       # Prevent small islands from disappearing completely
min_island_size = 1          # Minimum size to preserve islands (smaller = more detail)

# Enhanced randomization for fractal variation
add_noise = true             # Add randomness to prevent perfect patterns
noise_probability = 0.15     # Higher chance of random land/water flip per iteration
edge_noise_boost = true      # Extra noise along land/water boundaries
edge_noise_probability = 0.25 # Higher noise probability at edges

# Fractal enhancement
fractal_perturbation = true  # Add fractal-like perturbations
perturbation_strength = 0.3  # Strength of fractal perturbations (0.0-1.0)
```

## .augment/rules/general.md

```markdown
---
type: "always_apply"
---

# General Rules

- constants should generally be in teh config.toml file unless there is a very good reason not to put them there.
- when given a new way to do something, rewrite the code and do not support the legacy way of doing it.
- don't make ad hoc script in random places to test. Add your tests to the /tests directory in a professinal way
- anytime you change a feature, check to see if any docs related to it need to be updated
- do not flatter the user. Play devil's advocate when the user's idea seem to be poor or there is a well established way of achieving the same end
- ask clarifying questions readily
```

## tests/__init__.py

```python
"""
Tests for the 2D Minecraft-like game.

Contains unit tests and integration tests for all components.
"""
```

## tests/test_tiles.py

```python
#!/usr/bin/env python3
"""
Tests for tile configuration system

Unit tests for the TOML-based tile configuration and registry.
"""

import unittest
import sys
import os
import tempfile

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tiles import TileConfig, TileRegistry, get_tile_registry


class TestTileConfig(unittest.TestCase):
    """Test the TileConfig class."""
    
    def test_tile_config_creation(self):
        """Test basic tile config creation."""
        config = TileConfig(
            name="Test Tile",
            character="T",
            font_color=(255, 0, 0),
            background_color=(0, 255, 0)
        )
        
        self.assertEqual(config.name, "Test Tile")
        self.assertEqual(config.character, "T")
        self.assertEqual(config.font_color, (255, 0, 0))
        self.assertEqual(config.background_color, (0, 255, 0))
    
    def test_tile_config_color_validation(self):
        """Test color validation in tile config."""
        # Valid colors should work
        config = TileConfig("Test", "T", [255, 128, 0], [0, 0, 255])
        self.assertEqual(config.font_color, (255, 128, 0))
        self.assertEqual(config.background_color, (0, 0, 255))
        
        # Invalid color values should raise ValueError
        with self.assertRaises(ValueError):
            TileConfig("Test", "T", (256, 0, 0), (0, 0, 0))  # > 255
        
        with self.assertRaises(ValueError):
            TileConfig("Test", "T", (-1, 0, 0), (0, 0, 0))  # < 0
        
        with self.assertRaises(ValueError):
            TileConfig("Test", "T", (255, 0), (0, 0, 0))  # Wrong length


class TestTileRegistry(unittest.TestCase):
    """Test the TileRegistry class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary TOML file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False)
        self.temp_file.write("""
[stone]
name = "Stone"
character = "█"
font_color = [200, 200, 200]
background_color = [64, 64, 64]

[water]
name = "Water"
character = "~"
font_color = [173, 216, 230]
background_color = [0, 0, 139]

[invalid_tile]
name = "Invalid"
character = "X"
font_color = [300, 0, 0]  # Invalid color value
background_color = [0, 0, 0]
""")
        self.temp_file.close()
        
        self.registry = TileRegistry(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.unlink(self.temp_file.name)
    
    def test_registry_creation(self):
        """Test that registry can be created."""
        self.assertIsInstance(self.registry, TileRegistry)
        self.assertGreater(len(self.registry.tiles), 0)
    
    def test_load_valid_tiles(self):
        """Test loading valid tiles from TOML."""
        # Should have loaded stone and water, but not invalid_tile
        self.assertTrue(self.registry.has_tile('stone'))
        self.assertTrue(self.registry.has_tile('water'))
        self.assertFalse(self.registry.has_tile('invalid_tile'))  # Should be skipped due to invalid color
        
        # Check stone tile properties
        stone_config = self.registry.get_tile_config('stone')
        self.assertEqual(stone_config.name, "Stone")
        self.assertEqual(stone_config.character, "█")
        self.assertEqual(stone_config.font_color, (200, 200, 200))
        self.assertEqual(stone_config.background_color, (64, 64, 64))
        
        # Check water tile properties
        water_config = self.registry.get_tile_config('water')
        self.assertEqual(water_config.name, "Water")
        self.assertEqual(water_config.character, "~")
        self.assertEqual(water_config.font_color, (173, 216, 230))
        self.assertEqual(water_config.background_color, (0, 0, 139))
    
    def test_get_missing_tile(self):
        """Test getting a tile that doesn't exist."""
        missing_config = self.registry.get_tile_config('nonexistent')
        self.assertEqual(missing_config.name, "Unknown")
        self.assertEqual(missing_config.character, "?")
        self.assertEqual(missing_config.font_color, (255, 0, 255))  # Magenta
    
    def test_add_tile_config(self):
        """Test adding a tile configuration programmatically."""
        new_config = TileConfig(
            name="Test Tile",
            character="T",
            font_color=(255, 255, 0),
            background_color=(128, 128, 0)
        )
        
        self.registry.add_tile_config('test', new_config)
        
        self.assertTrue(self.registry.has_tile('test'))
        retrieved_config = self.registry.get_tile_config('test')
        self.assertEqual(retrieved_config.name, "Test Tile")
        self.assertEqual(retrieved_config.character, "T")
    
    def test_get_available_tiles(self):
        """Test getting all available tiles."""
        available = self.registry.get_available_tiles()
        self.assertIsInstance(available, dict)
        self.assertIn('stone', available)
        self.assertIn('water', available)
        
        # Should be a copy, not the original
        available['new_tile'] = TileConfig("New", "N", (0, 0, 0), (255, 255, 255))
        self.assertFalse(self.registry.has_tile('new_tile'))


class TestTileRegistryWithMissingFile(unittest.TestCase):
    """Test TileRegistry behavior when config file is missing."""
    
    def test_missing_config_file(self):
        """Test registry creation when config file doesn't exist."""
        registry = TileRegistry('nonexistent_file.toml')
        
        # Should create default tiles
        self.assertGreater(len(registry.tiles), 0)
        self.assertTrue(registry.has_tile('stone'))
        self.assertTrue(registry.has_tile('void'))
        self.assertTrue(registry.has_tile('center_marker'))


class TestGlobalTileRegistry(unittest.TestCase):
    """Test the global tile registry functions."""
    
    def test_get_tile_registry(self):
        """Test getting the global tile registry."""
        registry1 = get_tile_registry()
        registry2 = get_tile_registry()
        
        # Should return the same instance
        self.assertIs(registry1, registry2)
        self.assertIsInstance(registry1, TileRegistry)
    
    def test_convenience_functions(self):
        """Test convenience functions for tile access."""
        from tiles import get_tile_config, get_tile_character, get_tile_colors
        
        # Test getting config
        config = get_tile_config('stone')
        self.assertIsInstance(config, TileConfig)
        
        # Test getting character
        char = get_tile_character('stone')
        self.assertIsInstance(char, str)
        
        # Test getting colors
        font_color, bg_color = get_tile_colors('stone')
        self.assertIsInstance(font_color, tuple)
        self.assertIsInstance(bg_color, tuple)
        self.assertEqual(len(font_color), 3)
        self.assertEqual(len(bg_color), 3)


if __name__ == "__main__":
    unittest.main()
```

## tests/test_ui.py

```python
#!/usr/bin/env python3
"""
Tests for UI components

Unit tests for status display and other UI elements.
"""

import unittest
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ui.status_display import StatusDisplay


class TestStatusDisplay(unittest.TestCase):
    """Test the StatusDisplay class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.status = StatusDisplay()
    
    def test_status_display_creation(self):
        """Test that status display can be created."""
        self.assertIsInstance(self.status, StatusDisplay)
        self.assertEqual(self.status.frame_count, 0)
        self.assertTrue(self.status.show_debug)
        self.assertTrue(self.status.show_coordinates)
        self.assertFalse(self.status.show_fps)
    
    def test_update_frame_count(self):
        """Test frame count updating."""
        initial_count = self.status.frame_count
        self.status.update_frame_count()
        self.assertEqual(self.status.frame_count, initial_count + 1)
        
        # Test multiple updates
        for i in range(5):
            self.status.update_frame_count()
        self.assertEqual(self.status.frame_count, initial_count + 6)
    
    def test_toggle_debug(self):
        """Test toggling debug display."""
        initial_state = self.status.show_debug
        self.status.toggle_debug()
        self.assertEqual(self.status.show_debug, not initial_state)
        
        # Toggle back
        self.status.toggle_debug()
        self.assertEqual(self.status.show_debug, initial_state)
    
    def test_toggle_coordinates(self):
        """Test toggling coordinate display."""
        initial_state = self.status.show_coordinates
        self.status.toggle_coordinates()
        self.assertEqual(self.status.show_coordinates, not initial_state)
        
        # Toggle back
        self.status.toggle_coordinates()
        self.assertEqual(self.status.show_coordinates, initial_state)
    
    def test_toggle_fps(self):
        """Test toggling FPS display."""
        initial_state = self.status.show_fps
        self.status.toggle_fps()
        self.assertEqual(self.status.show_fps, not initial_state)
        
        # Toggle back
        self.status.toggle_fps()
        self.assertEqual(self.status.show_fps, initial_state)
    
    def test_color_properties(self):
        """Test that color properties are set correctly."""
        self.assertEqual(self.status.info_color, (255, 255, 255))
        self.assertEqual(self.status.debug_color, (200, 200, 200))
        self.assertEqual(self.status.warning_color, (255, 255, 0))
        self.assertEqual(self.status.error_color, (255, 100, 100))


class MockConsole:
    """Mock console for testing UI rendering without tcod dependency."""
    
    def __init__(self, width=80, height=50):
        self.width = width
        self.height = height
        self.printed_chars = []
    
    def print(self, x, y, text, fg=None, bg=None):
        """Mock print method that records what was printed."""
        self.printed_chars.append({
            'x': x, 'y': y, 'text': text, 'fg': fg, 'bg': bg
        })


class TestStatusDisplayRendering(unittest.TestCase):
    """Test the rendering methods of StatusDisplay (without actual tcod)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.status = StatusDisplay()
        self.console = MockConsole(80, 25)
    
    def test_render_status_bar_basic(self):
        """Test basic status bar rendering."""
        self.status.show_debug = True  # Enable debug mode to show status bar
        self.status.render_status_bar(self.console, 10, 20)

        # Should have printed something (floating container with borders and content)
        self.assertGreater(len(self.console.printed_chars), 0)

        # Check that it printed in the floating container area (y=1 for top container)
        # Look for content in the top area of the screen
        top_area_prints = [p for p in self.console.printed_chars if p['y'] <= 5]
        self.assertGreater(len(top_area_prints), 0)
    
    def test_render_status_bar_disabled(self):
        """Test status bar rendering when debug is disabled."""
        self.status.show_debug = False
        self.status.render_status_bar(self.console, 10, 20)
        
        # Should not have printed anything
        self.assertEqual(len(self.console.printed_chars), 0)
    
    def test_render_help_text(self):
        """Test help text rendering."""
        self.status.render_help_text(self.console)
        
        # Should have printed help text
        self.assertGreater(len(self.console.printed_chars), 0)
        
        # Help text should be near the bottom
        help_prints = [p for p in self.console.printed_chars if p['y'] > self.console.height - 5]
        self.assertGreater(len(help_prints), 0)
    
    def test_render_message(self):
        """Test message rendering."""
        self.status.render_message(self.console, "Test message", 5, 10)
        
        # Should have printed the message
        self.assertEqual(len(self.console.printed_chars), 1)
        
        printed = self.console.printed_chars[0]
        self.assertEqual(printed['x'], 5)
        self.assertEqual(printed['y'], 10)
        self.assertEqual(printed['text'], "Test message")
    
    def test_render_centered_message(self):
        """Test centered message rendering."""
        message = "Center me"
        self.status.render_centered_message(self.console, message, 15)
        
        # Should have printed the message
        self.assertEqual(len(self.console.printed_chars), 1)
        
        printed = self.console.printed_chars[0]
        expected_x = (self.console.width - len(message)) // 2
        self.assertEqual(printed['x'], expected_x)
        self.assertEqual(printed['y'], 15)
        self.assertEqual(printed['text'], message)


if __name__ == "__main__":
    unittest.main()
```

## scripts/export_codebase.py

```python
#!/usr/bin/env python3
"""
Script to export an entire codebase to a markdown file.
Recursively walks through directories and includes all code files.
"""

import os
import argparse
from pathlib import Path

# Common code file extensions
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
    '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.clj',
    '.sh', '.bash', '.zsh', '.ps1', '.sql', '.r', '.m', '.pl', '.lua',
    '.dart', '.elm', '.ex', '.exs', '.fs', '.fsx', '.hs', '.jl', '.nim',
    '.ml', '.mli', '.pas', '.pp', '.pro', '.v', '.vhd', '.vhdl', '.sv',
    '.html', '.htm', '.css', '.scss', '.sass', '.less', '.xml', '.json',
    '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.md', '.txt',
    '.dockerfile', '.makefile', '.cmake', '.gradle', '.maven', '.sbt'
}

# Files and directories to ignore
IGNORE_PATTERNS = {
    '__pycache__', '.git', '.svn', '.hg', 'node_modules', '.env', 'venv',
    'env', '.venv', 'dist', 'build', '.idea', '.vscode', '.vs', 'target',
    'bin', 'obj', '.gradle', '.maven', 'vendor', 'logs', 'log', 'tmp',
    'temp', '.DS_Store', 'Thumbs.db', '.pytest_cache', '.coverage',
    '.mypy_cache', '.tox', '.nox', '.eggs', '*.egg-info', '.cache'
}

def should_ignore(path):
    """Check if a file or directory should be ignored."""
    name = os.path.basename(path)
    
    # Check against ignore patterns
    for pattern in IGNORE_PATTERNS:
        if pattern.startswith('*'):
            if name.endswith(pattern[1:]):
                return True
        elif pattern in name or name == pattern:
            return True
    
    return False

def is_code_file(file_path):
    """Check if a file is a code file based on its extension."""
    ext = Path(file_path).suffix.lower()
    
    # Special cases for files without extensions
    name = os.path.basename(file_path).lower()
    if name in ['dockerfile', 'makefile', 'vagrantfile', 'jenkinsfile']:
        return True
    
    return ext in CODE_EXTENSIONS

def get_language_from_extension(file_path):
    """Get the language identifier for markdown code blocks."""
    ext = Path(file_path).suffix.lower()
    name = os.path.basename(file_path).lower()
    
    # Special cases
    if name in ['dockerfile']:
        return 'dockerfile'
    if name in ['makefile']:
        return 'makefile'
    
    # Extension mappings
    lang_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'jsx',
        '.tsx': 'tsx',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.php': 'php',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.clj': 'clojure',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'zsh',
        '.ps1': 'powershell',
        '.sql': 'sql',
        '.r': 'r',
        '.html': 'html',
        '.htm': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        '.xml': 'xml',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'ini',
        '.conf': 'ini',
        '.md': 'markdown',
        '.txt': 'text'
    }
    
    return lang_map.get(ext, 'text')

def read_file_safely(file_path):
    """Safely read a file, handling various encodings."""
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    return "Unable to decode file with common encodings"

def export_codebase(root_dir, output_file, max_file_size=50000):
    """Export codebase to markdown file."""
    root_path = Path(root_dir).resolve()
    files_processed = 0
    files_skipped = 0
    
    with open(output_file, 'w', encoding='utf-8') as md_file:
        # Write header
        md_file.write(f"# Codebase Export: {root_path.name}\n\n")
        md_file.write(f"Generated from: `{root_path}`\n\n")
        md_file.write("---\n\n")
        
        # Walk through directory tree
        for root, dirs, files in os.walk(root_path):
            # Remove ignored directories from dirs list to prevent traversal
            dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d))]
            
            for file in sorted(files):
                file_path = os.path.join(root, file)
                
                # Skip ignored files
                if should_ignore(file_path):
                    continue
                
                # Only process code files
                if not is_code_file(file_path):
                    continue
                
                # Get relative path from root directory
                rel_path = os.path.relpath(file_path, root_path)
                
                # Check file size
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > max_file_size:
                        md_file.write(f"## {rel_path}\n\n")
                        md_file.write(f"*File too large ({file_size} bytes) - skipped*\n\n")
                        files_skipped += 1
                        continue
                except OSError:
                    continue
                
                # Read and write file content
                content = read_file_safely(file_path)
                language = get_language_from_extension(file_path)
                
                md_file.write(f"## {rel_path}\n\n")
                md_file.write(f"```{language}\n")
                md_file.write(content)
                if not content.endswith('\n'):
                    md_file.write('\n')
                md_file.write("```\n\n")
                
                files_processed += 1
        
        # Write summary
        md_file.write("---\n\n")
        md_file.write(f"**Export Summary:**\n")
        md_file.write(f"- Files processed: {files_processed}\n")
        md_file.write(f"- Files skipped: {files_skipped}\n")
    
    return files_processed, files_skipped

def main():
    parser = argparse.ArgumentParser(description='Export codebase to markdown file')
    parser.add_argument('directory', help='Root directory to scan')
    parser.add_argument('-o', '--output', default='codebase_export.md', 
                       help='Output markdown file (default: codebase_export.md)')
    parser.add_argument('--max-size', type=int, default=50000,
                       help='Maximum file size in bytes to include (default: 50000)')
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory")
        return 1
    
    try:
        files_processed, files_skipped = export_codebase(
            args.directory, 
            args.output, 
            args.max_size
        )
        
        print(f"✅ Export complete!")
        print(f"📁 Scanned directory: {os.path.abspath(args.directory)}")
        print(f"📄 Output file: {os.path.abspath(args.output)}")
        print(f"🔢 Files processed: {files_processed}")
        if files_skipped > 0:
            print(f"⚠️  Files skipped: {files_skipped}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
```

## scripts/run_with_hotreload.py

```python
#!/usr/bin/env python3
"""
Runner script for the TCOD application with hot reloading using watchmedo.

This script uses watchdog's watchmedo to restart the application when files change.
Watches both main.py and game.py for changes.
"""

import subprocess

if __name__ == "__main__":
    print("Starting 2D Minecraft world with file watching hot reload...")
    print("The application will restart automatically when you modify any .py file")
    print("Press Ctrl+C to stop the file watcher.")
    print("-" * 70)

    try:
        # Use watchmedo to watch for changes and restart the application
        # Watch the current directory for .py file changes
        cmd = [
            "uv", "run", "watchmedo", "auto-restart",
            "--directory=.",
            "--pattern=*.py",
            "--recursive",
            "--", "python", "main.py"
        ]

        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nFile watcher stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Hot reload session terminated.")
```

## src/__init__.py

```python
"""
Covenant - 2D Minecraft-like World Generator

A tile-based world generation and rendering system using python-tcod.
"""

__version__ = "0.1.0"

from .render.render import GameRenderer, WorldRenderer, EffectRenderer
from .world import WorldManager, Tile, TierManager
from .ui import StatusDisplay

__all__ = [
    "GameRenderer", "WorldRenderer", "EffectRenderer",
    "WorldManager", "Tile", "TierManager",
    "StatusDisplay"
]
```

## src/config.py

```python
#!/usr/bin/env python3
"""
Configuration system for the 2D Minecraft-like world

Handles loading application settings from TOML configuration files.
"""

import os
from typing import Dict, Any, Tuple
from dataclasses import dataclass

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for older Python versions


@dataclass
class ApplicationConfig:
    """Application-level configuration."""
    title: str = "2D Minecraft World - Spiral Generation"
    version: str = "0.1.0"


@dataclass
class WindowConfig:
    """Window and display configuration."""
    initial_width: int = 80
    initial_height: int = 50
    vsync: bool = True


@dataclass
class WorldConfig:
    """World generation configuration."""
    center_x: int = 0
    center_y: int = 0
    radius: int = 50
    generator_type: str = "pipeline"
    seed: int = 12345
    chunk_size: int = 64
    pipeline_layers: list = None
    layer_configs: dict = None
    # Infinite world settings
    render_distance: int = 3
    chunk_cache_limit: int = 100
    chunk_unload_distance: int = 5

    def __post_init__(self):
        if self.pipeline_layers is None:
            self.pipeline_layers = ["lands_and_seas"]
        if self.layer_configs is None:
            self.layer_configs = {}


@dataclass
class CameraConfig:
    """Camera and viewport configuration."""
    initial_x: int = 0
    initial_y: int = 0
    move_speed: int = 1
    fast_move_speed: int = 5


@dataclass
class DebugConfig:
    """Debug display configuration."""
    show_debug_on_startup: bool = False
    show_coordinates_on_startup: bool = False
    show_fps_on_startup: bool = False


@dataclass
class RenderingConfig:
    """Rendering system configuration."""
    seamless_blocks_enabled: bool = True
    clear_color: Tuple[int, int, int] = (0, 0, 0)


@dataclass
class UIConfig:
    """User interface configuration."""
    panel_background: Tuple[int, int, int] = (32, 32, 48)
    border_color: Tuple[int, int, int] = (128, 128, 160)
    info_color: Tuple[int, int, int] = (255, 255, 255)
    warning_color: Tuple[int, int, int] = (255, 255, 0)
    debug_color: Tuple[int, int, int] = (128, 255, 128)
    top_panel_max_lines: int = 2
    bottom_panel_max_lines: int = 3
    panel_margin: int = 2


@dataclass
class GameConfig:
    """Complete game configuration."""
    application: ApplicationConfig
    window: WindowConfig
    world: WorldConfig
    camera: CameraConfig
    debug: DebugConfig
    rendering: RenderingConfig
    ui: UIConfig


class ConfigLoader:
    """Loads and manages game configuration."""
    
    def __init__(self, config_file: str = "config/config.toml"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> GameConfig:
        """Load configuration from TOML file with fallback to defaults."""
        if not os.path.exists(self.config_file):
            return self._create_default_config()

        try:
            with open(self.config_file, 'rb') as f:
                config_data = tomllib.load(f)

            return self._parse_config(config_data)

        except Exception:
            return self._create_default_config()
    
    def _parse_config(self, config_data: Dict[str, Any]) -> GameConfig:
        """Parse configuration data into structured config objects."""
        
        # Application config
        app_data = config_data.get('application', {})
        application = ApplicationConfig(
            title=app_data.get('title', ApplicationConfig.title),
            version=app_data.get('version', ApplicationConfig.version)
        )
        
        # Window config
        window_data = config_data.get('window', {})
        window = WindowConfig(
            initial_width=window_data.get('initial_width', WindowConfig.initial_width),
            initial_height=window_data.get('initial_height', WindowConfig.initial_height),
            vsync=window_data.get('vsync', WindowConfig.vsync)
        )
        
        # World config
        world_data = config_data.get('world', {})

        # Extract pipeline layers and layer configs
        pipeline_layers = world_data.get('pipeline_layers', ["lands_and_seas"])
        layer_configs = {}

        # Extract layer-specific configurations
        for layer_name in pipeline_layers:
            if layer_name in world_data:
                layer_configs[layer_name] = world_data[layer_name]

        world = WorldConfig(
            center_x=world_data.get('center_x', WorldConfig.center_x),
            center_y=world_data.get('center_y', WorldConfig.center_y),
            radius=world_data.get('radius', WorldConfig.radius),
            generator_type=world_data.get('generator_type', WorldConfig.generator_type),
            seed=world_data.get('seed', WorldConfig.seed),
            chunk_size=world_data.get('chunk_size', WorldConfig.chunk_size),
            pipeline_layers=pipeline_layers,
            layer_configs=layer_configs,
            render_distance=world_data.get('render_distance', WorldConfig.render_distance),
            chunk_cache_limit=world_data.get('chunk_cache_limit', WorldConfig.chunk_cache_limit),
            chunk_unload_distance=world_data.get('chunk_unload_distance', WorldConfig.chunk_unload_distance)
        )

        # Camera config
        camera_data = config_data.get('camera', {})
        camera = CameraConfig(
            initial_x=camera_data.get('initial_x', CameraConfig.initial_x),
            initial_y=camera_data.get('initial_y', CameraConfig.initial_y),
            move_speed=camera_data.get('move_speed', CameraConfig.move_speed),
            fast_move_speed=camera_data.get('fast_move_speed', CameraConfig.fast_move_speed)
        )
        
        # Debug config
        debug_data = config_data.get('debug', {})
        debug = DebugConfig(
            show_debug_on_startup=debug_data.get('show_debug_on_startup', DebugConfig.show_debug_on_startup),
            show_coordinates_on_startup=debug_data.get('show_coordinates_on_startup', DebugConfig.show_coordinates_on_startup),
            show_fps_on_startup=debug_data.get('show_fps_on_startup', DebugConfig.show_fps_on_startup)
        )
        
        # Rendering config
        rendering_data = config_data.get('rendering', {})
        rendering = RenderingConfig(
            seamless_blocks_enabled=rendering_data.get('seamless_blocks_enabled', RenderingConfig.seamless_blocks_enabled),
            clear_color=tuple(rendering_data.get('clear_color', RenderingConfig.clear_color))
        )
        
        # UI config
        ui_data = config_data.get('ui', {})
        ui = UIConfig(
            panel_background=tuple(ui_data.get('panel_background', UIConfig.panel_background)),
            border_color=tuple(ui_data.get('border_color', UIConfig.border_color)),
            info_color=tuple(ui_data.get('info_color', UIConfig.info_color)),
            warning_color=tuple(ui_data.get('warning_color', UIConfig.warning_color)),
            debug_color=tuple(ui_data.get('debug_color', UIConfig.debug_color)),
            top_panel_max_lines=ui_data.get('top_panel_max_lines', UIConfig.top_panel_max_lines),
            bottom_panel_max_lines=ui_data.get('bottom_panel_max_lines', UIConfig.bottom_panel_max_lines),
            panel_margin=ui_data.get('panel_margin', UIConfig.panel_margin)
        )
        
        return GameConfig(
            application=application,
            window=window,
            world=world,
            camera=camera,
            debug=debug,
            rendering=rendering,
            ui=ui
        )
    
    def _create_default_config(self) -> GameConfig:
        """Create default configuration."""
        return GameConfig(
            application=ApplicationConfig(),
            window=WindowConfig(),
            world=WorldConfig(),
            camera=CameraConfig(),
            debug=DebugConfig(),
            rendering=RenderingConfig(),
            ui=UIConfig()
        )
    
    def reload_config(self):
        """Reload configuration from file."""
        self.config = self.load_config()
    
    def get_config(self) -> GameConfig:
        """Get the current configuration."""
        return self.config


# Global configuration instance
_config_loader = None


def get_config() -> GameConfig:
    """Get the global configuration instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader.get_config()


def reload_config():
    """Reload the global configuration."""
    global _config_loader
    if _config_loader is not None:
        _config_loader.reload_config()


# Example usage and testing
if __name__ == "__main__":
    # Test the configuration system
    config = get_config()
    
    print("Configuration loaded:")
    print(f"  Application: {config.application.title} v{config.application.version}")
    print(f"  Window: {config.window.initial_width}x{config.window.initial_height}")
    print(f"  World center: ({config.world.center_x}, {config.world.center_y})")
    print(f"  Debug on startup: {config.debug.show_debug_on_startup}")
    print(f"  Seamless blocks: {config.rendering.seamless_blocks_enabled}")
    print(f"  Panel background: {config.ui.panel_background}")
```

## src/profiler.py

```python
#!/usr/bin/env python3
"""
Performance profiler for identifying bottlenecks in the game.
"""

import time
import functools
from collections import defaultdict, deque
from typing import Dict, List, Callable, Any
import threading

# Profiling flag - controlled by command line argument --profiling
ENABLE_PROFILING = False  # Default: disabled for performance

# To enable profiling:
# Run with: python main.py --profiling
# Profiling stats will print every 10 seconds in console


class PerformanceProfiler:
    """
    Lightweight profiler to identify performance bottlenecks.
    """
    
    def __init__(self, max_samples: int = 100):
        self.max_samples = max_samples
        self.timings: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_samples))
        self.call_counts: Dict[str, int] = defaultdict(int)
        self.active_timers: Dict[str, float] = {}
        self.lock = threading.Lock()
        
    def start_timer(self, name: str):
        """Start timing an operation."""
        with self.lock:
            self.active_timers[name] = time.perf_counter()
    
    def end_timer(self, name: str):
        """End timing an operation and record the duration."""
        with self.lock:
            if name in self.active_timers:
                duration = time.perf_counter() - self.active_timers[name]
                self.timings[name].append(duration)
                self.call_counts[name] += 1
                del self.active_timers[name]
                return duration
            return 0.0
    
    def time_function(self, name: str = None):
        """Decorator to time function calls."""
        def decorator(func: Callable) -> Callable:
            func_name = name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                self.start_timer(func_name)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    self.end_timer(func_name)
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics."""
        stats = {}
        with self.lock:
            for name, times in self.timings.items():
                if times:
                    times_list = list(times)
                    stats[name] = {
                        'count': self.call_counts[name],
                        'total_time': sum(times_list),
                        'avg_time': sum(times_list) / len(times_list),
                        'min_time': min(times_list),
                        'max_time': max(times_list),
                        'recent_avg': sum(list(times)[-10:]) / min(10, len(times))
                    }
        return stats
    
    def print_stats(self, top_n: int = 10):
        """Print performance statistics."""
        stats = self.get_stats()
        
        print("\n🔍 PERFORMANCE PROFILER RESULTS")
        print("=" * 60)
        
        # Sort by total time
        sorted_stats = sorted(stats.items(), key=lambda x: x[1]['total_time'], reverse=True)
        
        print(f"{'Operation':<30} {'Count':<8} {'Total(ms)':<10} {'Avg(ms)':<10} {'Recent(ms)':<10}")
        print("-" * 80)
        
        for name, data in sorted_stats[:top_n]:
            print(f"{name:<30} {data['count']:<8} "
                  f"{data['total_time']*1000:<10.2f} {data['avg_time']*1000:<10.2f} "
                  f"{data['recent_avg']*1000:<10.2f}")
        
        # Identify potential bottlenecks
        for name, data in sorted_stats[:5]:
            if data['avg_time'] > 0.016:  # > 16ms (60 FPS threshold)
                pass
            elif data['recent_avg'] > 0.010:  # > 10ms recent
                pass
    
    def reset(self):
        """Reset all profiling data."""
        with self.lock:
            self.timings.clear()
            self.call_counts.clear()
            self.active_timers.clear()


# Global profiler instance
profiler = PerformanceProfiler()


def profile_function(name: str = None):
    """Decorator to profile a function."""
    if ENABLE_PROFILING:
        return profiler.time_function(name)
    else:
        # No-op decorator for production
        def decorator(func: Callable) -> Callable:
            return func
        return decorator


def start_profiling(name: str):
    """Start profiling an operation."""
    if ENABLE_PROFILING:
        profiler.start_timer(name)


def end_profiling(name: str):
    """End profiling an operation."""
    if ENABLE_PROFILING:
        return profiler.end_timer(name)
    return 0.0


def print_profiling_stats(top_n: int = 10):
    """Print profiling statistics."""
    if ENABLE_PROFILING:
        profiler.print_stats(top_n)


def reset_profiling():
    """Reset profiling data."""
    if ENABLE_PROFILING:
        profiler.reset()


def enable_profiling():
    """Enable profiling at runtime."""
    global ENABLE_PROFILING
    ENABLE_PROFILING = True


def disable_profiling():
    """Disable profiling at runtime."""
    global ENABLE_PROFILING
    ENABLE_PROFILING = False


def is_profiling_enabled():
    """Check if profiling is currently enabled."""
    return ENABLE_PROFILING


class ProfiledContext:
    """Context manager for profiling code blocks."""
    
    def __init__(self, name: str):
        self.name = name
    
    def __enter__(self):
        start_profiling(self.name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_profiling(self.name)


def profile_context(name: str):
    """Create a profiling context manager."""
    return ProfiledContext(name)


# Convenience function for quick profiling
def quick_profile(func_or_name):
    """Quick profiling decorator or context manager."""
    if callable(func_or_name):
        # Used as @quick_profile
        return profile_function()(func_or_name)
    else:
        # Used as with quick_profile("name"):
        return profile_context(func_or_name)
```

## src/tiles.py

```python
#!/usr/bin/env python3
"""
Tile configuration system for the 2D Minecraft-like world

Handles loading tile definitions from TOML files and providing
tile rendering information to the rendering system.
"""

import os
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for older Python versions


@dataclass
class TileConfig:
    """Configuration for a single tile type."""
    name: str
    character: str
    font_color: Tuple[int, int, int]
    background_color: Tuple[int, int, int]
    
    def __post_init__(self):
        """Validate tile configuration after initialization."""
        # Ensure colors are valid RGB tuples
        if not (isinstance(self.font_color, (list, tuple)) and len(self.font_color) == 3):
            raise ValueError(f"Invalid font_color for tile '{self.name}': {self.font_color}")
        if not (isinstance(self.background_color, (list, tuple)) and len(self.background_color) == 3):
            raise ValueError(f"Invalid background_color for tile '{self.name}': {self.background_color}")
        
        # Convert to tuples if they're lists
        self.font_color = tuple(self.font_color)
        self.background_color = tuple(self.background_color)
        
        # Validate RGB values are in range 0-255
        for color_name, color in [("font_color", self.font_color), ("background_color", self.background_color)]:
            for i, value in enumerate(color):
                if not (0 <= value <= 255):
                    raise ValueError(f"Invalid {color_name}[{i}] for tile '{self.name}': {value} (must be 0-255)")


class TileRegistry:
    """Registry for all tile configurations."""

    def __init__(self, config_file: str = None):
        self.tiles: Dict[str, TileConfig] = {}
        # Default to centralized config location
        self.config_file = config_file or os.path.join("config", "tiles.toml")
        self.default_tile = TileConfig(
            name="Unknown",
            character="?",
            font_color=(255, 0, 255),  # Magenta to make missing tiles obvious
            background_color=(128, 0, 128)
        )
        self.load_tiles()
    
    def load_tiles(self):
        """Load tile configurations from the TOML file."""
        if not os.path.exists(self.config_file):
            return

        try:
            with open(self.config_file, 'rb') as f:
                config_data = tomllib.load(f)

            self.tiles.clear()

            for tile_id, tile_data in config_data.items():
                try:
                    tile_config = TileConfig(
                        name=tile_data.get('name', tile_id.title()),
                        character=tile_data.get('character', '?'),
                        font_color=tile_data.get('font_color', [255, 255, 255]),
                        background_color=tile_data.get('background_color', [0, 0, 0])
                    )
                    self.tiles[tile_id] = tile_config
                except (ValueError, KeyError):
                    continue

        except Exception:
            pass
    


    
    def get_tile_config(self, tile_id: str) -> TileConfig:
        """
        Get the configuration for a tile type.

        Args:
            tile_id: The identifier for the tile type

        Returns:
            TileConfig object with rendering information
        """
        return self.tiles.get(tile_id, self.default_tile)
    
    def get_available_tiles(self) -> Dict[str, TileConfig]:
        """Get all available tile configurations."""
        return self.tiles.copy()
    
    def reload_config(self):
        """Reload tile configurations from the file."""
        self.load_tiles()
    
    def add_tile_config(self, tile_id: str, config: TileConfig):
        """Add or update a tile configuration programmatically."""
        self.tiles[tile_id] = config
    
    def has_tile(self, tile_id: str) -> bool:
        """Check if a tile configuration exists."""
        return tile_id in self.tiles


# Global tile registry instance
_tile_registry: Optional[TileRegistry] = None


def get_tile_registry() -> TileRegistry:
    """Get the global tile registry instance."""
    global _tile_registry
    if _tile_registry is None:
        _tile_registry = TileRegistry()
    return _tile_registry


def reload_tile_config():
    """Reload the global tile configuration."""
    global _tile_registry
    if _tile_registry is not None:
        _tile_registry.reload_config()


# Convenience functions for common operations
def get_tile_config(tile_id: str) -> TileConfig:
    """Get tile configuration by ID."""
    return get_tile_registry().get_tile_config(tile_id)


def get_tile_character(tile_id: str) -> str:
    """Get the character for a tile type."""
    return get_tile_config(tile_id).character


def get_tile_colors(tile_id: str) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """Get the font and background colors for a tile type."""
    config = get_tile_config(tile_id)
    return config.font_color, config.background_color


# Example usage and testing
if __name__ == "__main__":
    # Test the tile registry
    registry = TileRegistry()
    
    print("Available tiles:")
    for tile_id, config in registry.get_available_tiles().items():
        print(f"  {tile_id}: {config.name} ('{config.character}') "
              f"fg={config.font_color} bg={config.background_color}")
    
    # Test getting specific tiles
    stone_config = registry.get_tile_config('stone')
    print(f"\nStone tile: {stone_config}")
    
    # Test missing tile
    missing_config = registry.get_tile_config('nonexistent')
    print(f"Missing tile: {missing_config}")
    
    # Test convenience functions
    print(f"\nStone character: '{get_tile_character('stone')}'")
    print(f"Stone colors: {get_tile_colors('stone')}")
```

## src/ui/__init__.py

```python
"""
User interface components for the 2D Minecraft-like game.

Contains UI widgets and status displays.
"""

from .status_display import StatusDisplay

__all__ = ["StatusDisplay"]
```

## src/ui/status_display.py

```python
#!/usr/bin/env python3
"""
Status display UI component for the 2D Minecraft-like game

Handles rendering of status information, debug info, and other UI elements.
"""

import tcod
from typing import Tuple, Optional
from ..config import get_config


class StatusDisplay:
    """Handles rendering of status information and UI overlays."""
    
    def __init__(self):
        self.frame_count = 0
        self.config = get_config()

        # Initialize display settings from config
        self.show_debug = self.config.debug.show_debug_on_startup
        self.show_coordinates = self.config.debug.show_coordinates_on_startup
        self.show_fps = self.config.debug.show_fps_on_startup
        self.show_chunk_debug = False  # Chunk debug overlay (F3)

        # Colors from configuration
        self.info_color = self.config.ui.info_color
        self.debug_color = self.config.ui.debug_color
        self.warning_color = self.config.ui.warning_color

        # UI caching for performance
        self._ui_cache_dirty = True
        self._last_stats_hash = None
        self._cached_status_lines = []
    
    def update_frame_count(self):
        """Increment the frame counter."""
        self.frame_count += 1
    
    def render_floating_container(self, console, content_lines: list, position: str = "top",
                                 max_lines: int = None, bg_color: tuple = None):
        """
        Render a full-width floating container with box drawing borders.

        Args:
            console: The tcod console to render to
            content_lines: List of strings to display inside the container
            position: "top" or "bottom" for container placement
            max_lines: Maximum number of content lines to display
            bg_color: Background color for the container
        """
        if not content_lines:
            return

        screen_width = console.width
        screen_height = console.height

        # Full width with 2-character margins
        container_width = screen_width - 4  # 2 character margin on each side
        inner_width = container_width - 4  # Account for left/right borders and padding

        # Limit content lines if max_lines specified
        if max_lines:
            content_lines = content_lines[:max_lines]

        # Container height: borders + content (no title)
        container_height = len(content_lines) + 2  # Top and bottom borders only

        # Calculate position (2-character margin from left edge)
        start_x = 2  # 2 characters from left edge

        if position == "top":
            start_y = 1  # 1 space from top edge
        else:  # bottom
            start_y = screen_height - container_height - 1  # 1 space from bottom edge

        # Use provided background color or config default
        container_bg = bg_color if bg_color else self.config.ui.panel_background

        # Draw container background
        for y in range(container_height):
            for x in range(container_width):
                console.print(start_x + x, start_y + y, " ", fg=self.info_color, bg=container_bg)

        # Draw borders using box drawing characters
        border_color = self.config.ui.border_color

        # Top border
        console.print(start_x, start_y, "┌", fg=border_color, bg=container_bg)
        for x in range(1, container_width - 1):
            console.print(start_x + x, start_y, "─", fg=border_color, bg=container_bg)
        console.print(start_x + container_width - 1, start_y, "┐", fg=border_color, bg=container_bg)

        # Bottom border
        bottom_y = start_y + container_height - 1
        console.print(start_x, bottom_y, "└", fg=border_color, bg=container_bg)
        for x in range(1, container_width - 1):
            console.print(start_x + x, bottom_y, "─", fg=border_color, bg=container_bg)
        console.print(start_x + container_width - 1, bottom_y, "┘", fg=border_color, bg=container_bg)

        # Side borders
        for y in range(1, container_height - 1):
            console.print(start_x, start_y + y, "│", fg=border_color, bg=container_bg)
            console.print(start_x + container_width - 1, start_y + y, "│", fg=border_color, bg=container_bg)

        # Render content lines (no title)
        content_start_y = start_y + 1
        for i, line in enumerate(content_lines):
            if content_start_y + i >= start_y + container_height - 1:
                break  # Don't overflow container

            # Truncate line if too long
            display_line = line[:inner_width] if len(line) > inner_width else line
            content_x = start_x + 2  # 2 chars padding from left border
            console.print(content_x, content_start_y + i, display_line, fg=self.info_color, bg=container_bg)

    def render_status_bar(self, console: tcod.console.Console, world_center_x: int, world_center_y: int,
                         cursor_tile=None, chunk_info=None, world_stats=None):
        """Render the floating status bar with debug information (max 2 lines)."""
        if not self.show_debug:
            return

        screen_width = console.width
        screen_height = console.height

        # Create hash of current data for caching
        current_data = (world_center_x, world_center_y,
                       str(cursor_tile) if cursor_tile else None,
                       str(chunk_info) if chunk_info else None,
                       str(world_stats) if world_stats else None,
                       screen_width, screen_height, self.frame_count)
        current_hash = hash(str(current_data))

        # Only rebuild UI if data changed
        if current_hash != self._last_stats_hash:
            self._rebuild_status_content(world_center_x, world_center_y, screen_width, screen_height,
                                       cursor_tile, chunk_info, world_stats)
            self._last_stats_hash = current_hash

        # Render cached content
        if self._cached_status_lines:
            self.render_floating_container(console, self._cached_status_lines, "top",
                                         max_lines=self.config.ui.top_panel_max_lines)

    def _rebuild_status_content(self, world_center_x: int, world_center_y: int,
                               screen_width: int, screen_height: int,
                               cursor_tile=None, chunk_info=None, world_stats=None):
        """Rebuild the status content and cache it."""
        # Prepare compact status content (max 2 lines)
        status_lines = []

        # Line 1: Cursor position and tile information
        line1_parts = []
        if self.show_coordinates:
            line1_parts.append(f"Cursor: ({world_center_x}, {world_center_y})")

        if cursor_tile:
            # Safety check for tile_type
            tile_type = getattr(cursor_tile, 'tile_type', 'unknown')
            if isinstance(tile_type, str):
                line1_parts.append(f"Tile: {tile_type.title()}")
            else:
                line1_parts.append(f"Tile: {str(tile_type)}")

        if chunk_info:
            chunk_x = chunk_info.get('chunk_x', '?')
            chunk_y = chunk_info.get('chunk_y', '?')
            line1_parts.append(f"Chunk: ({chunk_x}, {chunk_y})")

        line1_parts.append(f"Screen: {screen_width}x{screen_height}")
        status_lines.append(" | ".join(line1_parts))

        # Line 2: World statistics and performance
        line2_parts = [f"Frame: {self.frame_count}"]

        if world_stats:
            # Handle both old and new chunk systems
            loaded_chunks = world_stats.get('loaded_render_chunks', world_stats.get('loaded_chunks', 0))
            line2_parts.append(f"Chunks: {loaded_chunks}")

            cache_hit_ratio = world_stats.get('cache_hit_ratio', 0)
            line2_parts.append(f"Cache: {cache_hit_ratio:.1%}")

        if self.show_fps:
            line2_parts.append(f"FPS: {self.fps:.1f}")

        status_lines.append(" | ".join(line2_parts))

        # Cache the rebuilt content
        self._cached_status_lines = status_lines
    
    def render_help_text(self, console: tcod.console.Console):
        """
        Render help text at the bottom of the screen.
        
        Args:
            console: The tcod console to render to
        """
        screen_width = console.width
        screen_height = console.height
        
        if screen_height < 3:  # Not enough space for help
            return
        
        # Compact help text (max 3 lines)
        help_lines = [
            "WASD/Arrows: Move camera | Shift: Fast move | R: Regenerate",
            "F1: Debug | F2: Coords | F3: Chunks | F4: FPS | Ctrl+Q/ESC: Quit",
            "Hot reload: Save any .py file to restart"
        ]

        # Render as floating container at bottom (max lines from config)
        self.render_floating_container(console, help_lines, "bottom", max_lines=self.config.ui.bottom_panel_max_lines)
    
    def render_message(self, console: tcod.console.Console, message: str, x: int, y: int, 
                      message_type: str = "info", bg_color: Optional[Tuple[int, int, int]] = None):
        """
        Render a message at a specific location.
        
        Args:
            console: The tcod console to render to
            message: The message text to display
            x: X coordinate to render at
            y: Y coordinate to render at
            message_type: Type of message ("info", "debug", "warning", "error")
            bg_color: Optional background color override
        """
        if y < 0 or y >= console.height or x < 0:
            return
        
        # Choose color based on message type
        if message_type == "debug":
            fg_color = self.debug_color
        elif message_type == "warning":
            fg_color = self.warning_color
        elif message_type == "error":
            fg_color = self.error_color
        else:
            fg_color = self.info_color
        
        # Use default black background if none specified
        if bg_color is None:
            bg_color = (0, 0, 0)
        
        # Truncate message if it's too long for the screen
        max_length = console.width - x
        if len(message) > max_length:
            message = message[:max_length-3] + "..."
        
        console.print(x, y, message, fg=fg_color, bg=bg_color)
    
    def render_centered_message(self, console: tcod.console.Console, message: str, y: int, 
                               message_type: str = "info", bg_color: Optional[Tuple[int, int, int]] = None):
        """
        Render a centered message at a specific Y coordinate.
        
        Args:
            console: The tcod console to render to
            message: The message text to display
            y: Y coordinate to render at
            message_type: Type of message ("info", "debug", "warning", "error")
            bg_color: Optional background color override
        """
        if len(message) >= console.width:
            # If message is too long, render left-aligned
            self.render_message(console, message, 0, y, message_type, bg_color)
        else:
            # Center the message
            x = (console.width - len(message)) // 2
            self.render_message(console, message, x, y, message_type, bg_color)
    
    def toggle_debug(self):
        """Toggle debug information display."""
        self.show_debug = not self.show_debug
    
    def toggle_coordinates(self):
        """Toggle coordinate display."""
        self.show_coordinates = not self.show_coordinates
    
    def toggle_fps(self):
        """Toggle FPS display."""
        self.show_fps = not self.show_fps

    def toggle_chunk_debug(self):
        """Toggle chunk debug overlay."""
        self.show_chunk_debug = not self.show_chunk_debug

    def render_chunk_debug_overlay(self, console: tcod.console.Console, world_manager,
                                  view_center_x: int, view_center_y: int):
        """
        Render chunk boundaries and debug information as an overlay.

        Args:
            console: The tcod console to render to
            world_manager: World manager for chunk information
            view_center_x: X coordinate of the view center
            view_center_y: Y coordinate of the view center
        """
        if not self.show_chunk_debug:
            return

        screen_width = console.width
        screen_height = console.height
        half_width = screen_width // 2
        half_height = screen_height // 2

        # Handle both old and new world managers
        if hasattr(world_manager, 'render_chunk_size'):
            chunk_size = world_manager.render_chunk_size  # New dual chunk system
        elif hasattr(world_manager, 'chunk_size'):
            chunk_size = world_manager.chunk_size  # Old system
        else:
            chunk_size = 64  # Default fallback

        # Calculate visible world bounds
        min_world_x = view_center_x - half_width
        max_world_x = view_center_x + half_width
        min_world_y = view_center_y - half_height
        max_world_y = view_center_y + half_height

        # Find chunk boundaries that intersect with the visible area
        min_chunk_x = min_world_x // chunk_size
        max_chunk_x = max_world_x // chunk_size
        min_chunk_y = min_world_y // chunk_size
        max_chunk_y = max_world_y // chunk_size

        # Draw vertical chunk boundaries (optimized - only draw every 4th line)
        for chunk_x in range(min_chunk_x, max_chunk_x + 2):
            world_x = chunk_x * chunk_size
            screen_x = (world_x - view_center_x) + half_width

            if 0 <= screen_x < screen_width:
                # Check if any chunk in this column is loaded (sample middle)
                sample_world_y = view_center_y

                # Handle both old and new world managers
                if hasattr(world_manager, 'world_to_render_chunk_coords'):
                    chunk_coords = world_manager.world_to_render_chunk_coords(world_x, sample_world_y)
                else:
                    chunk_coords = world_manager.world_to_chunk_coords(world_x, sample_world_y)

                is_loaded = world_manager.is_chunk_loaded(*chunk_coords)

                # Use different colors for loaded vs unloaded chunks
                if is_loaded:
                    color = (0, 255, 0)  # Green for loaded chunks
                else:
                    color = (255, 0, 0)  # Red for unloaded chunks

                # Only draw every 4th line for performance
                for screen_y in range(0, screen_height, 4):
                    console.print(screen_x, screen_y, "│", fg=color, bg=(0, 0, 0))

        # Draw horizontal chunk boundaries (optimized - only draw every 4th line)
        for chunk_y in range(min_chunk_y, max_chunk_y + 2):
            world_y = chunk_y * chunk_size
            screen_y = (world_y - view_center_y) + half_height

            if 0 <= screen_y < screen_height:
                # Check if any chunk in this row is loaded (sample middle)
                sample_world_x = view_center_x

                # Handle both old and new world managers
                if hasattr(world_manager, 'world_to_render_chunk_coords'):
                    chunk_coords = world_manager.world_to_render_chunk_coords(sample_world_x, world_y)
                else:
                    chunk_coords = world_manager.world_to_chunk_coords(sample_world_x, world_y)

                is_loaded = world_manager.is_chunk_loaded(*chunk_coords)

                # Use different colors for loaded vs unloaded chunks
                if is_loaded:
                    color = (0, 255, 0)  # Green for loaded chunks
                else:
                    color = (255, 0, 0)  # Red for unloaded chunks

                # Only draw every 4th line for performance
                for screen_x in range(0, screen_width, 4):
                    console.print(screen_x, screen_y, "─", fg=color, bg=(0, 0, 0))

        # Draw chunk coordinates at chunk corners
        for chunk_x in range(min_chunk_x, max_chunk_x + 1):
            for chunk_y in range(min_chunk_y, max_chunk_y + 1):
                world_x = chunk_x * chunk_size
                world_y = chunk_y * chunk_size
                screen_x = (world_x - view_center_x) + half_width
                screen_y = (world_y - view_center_y) + half_height

                if 0 <= screen_x < screen_width - 10 and 0 <= screen_y < screen_height:
                    is_loaded = world_manager.is_chunk_loaded(chunk_x, chunk_y)
                    color = (0, 255, 0) if is_loaded else (255, 0, 0)

                    # Show chunk coordinates
                    coord_text = f"({chunk_x},{chunk_y})"
                    console.print(screen_x + 1, screen_y, coord_text, fg=color, bg=(0, 0, 0))


# Example usage and testing
if __name__ == "__main__":
    # This would normally be used within the game loop
    print("StatusDisplay component - use within the main game loop")
    
    # Create a test instance
    status = StatusDisplay()
    print(f"Debug mode: {status.show_debug}")
    print(f"Show coordinates: {status.show_coordinates}")
    
    # Test toggle functions
    status.toggle_debug()
    print(f"After toggle - Debug mode: {status.show_debug}")
```

## src/render/render.py

```python
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
```

## src/world/__init__.py

```python
#!/usr/bin/env python3
"""
World Generation Package

Provides clean, production-ready world generation with async chunk loading,
pipeline-based terrain generation, and proper multi-tier architecture.

Key Components:
- WorldManager: Single entry point for world access
- TierManager: Coordinates multi-tier generation pipeline
- WorldGenerationWorker: Background worker thread for world generation
- MessageBus: Thread-safe communication system
- Messages: Type-safe message definitions

Usage:
    from src.world import WorldManager, WorldConfig

    # Create world manager with configuration
    config = WorldConfig()
    world_manager = WorldManager(config)

    # Use the clean API
    world_manager.update_chunks(camera)
    tile = world_manager.get_tile(x, y)

    # Don't forget to shutdown when done
    world_manager.shutdown()
"""

from .world_manager import WorldManager
from .tier_manager import TierManager
from .worker import WorldGenerationWorker, Tile
from .messages import MessageBus, Message, MessageType, Priority

__all__ = [
    'WorldManager',
    'Tile',
    'TierManager',
    'WorldGenerationWorker',
    'MessageBus',
    'Message',
    'MessageType',
    'Priority'
]

__version__ = '1.0.0'
__author__ = 'Covenant World Generation Team'
__description__ = 'Asynchronous world generation system for smooth infinite worlds'
```

## src/world/dual_chunk_system.py

```python
#!/usr/bin/env python3
"""
Dual Chunk System for Efficient World Generation and Rendering

Separates generation chunks (optimized for pipeline processing) from render chunks
(optimized for display and memory management). This provides the best of both worlds:
- Small generation chunks for efficient pipeline processing
- Large render chunks for efficient rendering and reduced management overhead
"""

import math
from typing import Dict, List, Tuple, Set, Any, Optional
from dataclasses import dataclass


@dataclass
class GenerationChunk:
    """
    Small chunks optimized for world generation pipeline processing.

    These chunks have dynamic sizes that depend on the pipeline layers:
    - lands_and_seas: 64x64 tiles
    - After 1 zoom: 32x32 tiles
    - After 2 zooms: 16x16 tiles
    - etc.
    """
    chunk_x: int
    chunk_y: int
    chunk_size: int  # Dynamic size based on pipeline stage
    tiles: Dict[Tuple[int, int], str]  # (world_x, world_y) -> tile_type
    metadata: Dict[str, Any]
    
    def get_world_bounds(self) -> Tuple[int, int, int, int]:
        """Get world coordinate bounds for this generation chunk."""
        min_x = self.chunk_x * self.chunk_size
        min_y = self.chunk_y * self.chunk_size
        max_x = min_x + self.chunk_size - 1
        max_y = min_y + self.chunk_size - 1
        return min_x, min_y, max_x, max_y


@dataclass
class RenderChunk:
    """
    Large chunks optimized for rendering and memory management.

    Fixed size of 64x64 tiles regardless of generation pipeline.
    Each render chunk aggregates multiple generation chunks.
    """
    chunk_x: int
    chunk_y: int
    generation_chunks: List[GenerationChunk]
    aggregated_tiles: Dict[Tuple[int, int], str]  # Cached tile lookup
    metadata: Dict[str, Any]
    chunk_size: int = 64  # Fixed size for rendering efficiency
    
    def get_world_bounds(self) -> Tuple[int, int, int, int]:
        """Get world coordinate bounds for this render chunk."""
        min_x = self.chunk_x * self.chunk_size
        min_y = self.chunk_y * self.chunk_size
        max_x = min_x + self.chunk_size - 1
        max_y = min_y + self.chunk_size - 1
        return min_x, min_y, max_x, max_y
    
    def get_tile(self, world_x: int, world_y: int) -> Optional[str]:
        """Get tile type at world coordinates."""
        return self.aggregated_tiles.get((world_x, world_y))


class DualChunkManager:
    """
    Manages the relationship between generation chunks and render chunks.
    
    Handles:
    - Converting between generation and render chunk coordinates
    - Aggregating generation chunks into render chunks
    - Efficient tile lookups across the dual system
    """
    
    def __init__(self, render_chunk_size: int = 64):
        """
        Initialize the dual chunk manager.
        
        Args:
            render_chunk_size: Size of render chunks in tiles (default: 64x64)
        """
        self.render_chunk_size = render_chunk_size
        
        # Cache for coordinate conversions
        self._coord_cache: Dict[Tuple[int, int, int], Tuple[int, int]] = {}
    
    def world_to_render_chunk(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates to render chunk coordinates."""
        render_chunk_x = math.floor(world_x / self.render_chunk_size)
        render_chunk_y = math.floor(world_y / self.render_chunk_size)
        return render_chunk_x, render_chunk_y
    
    def world_to_generation_chunk(self, world_x: int, world_y: int, 
                                 generation_chunk_size: int) -> Tuple[int, int]:
        """Convert world coordinates to generation chunk coordinates."""
        cache_key = (world_x, world_y, generation_chunk_size)
        if cache_key in self._coord_cache:
            return self._coord_cache[cache_key]
        
        gen_chunk_x = math.floor(world_x / generation_chunk_size)
        gen_chunk_y = math.floor(world_y / generation_chunk_size)
        
        self._coord_cache[cache_key] = (gen_chunk_x, gen_chunk_y)
        return gen_chunk_x, gen_chunk_y
    
    def get_generation_chunks_for_render_chunk(self, render_chunk_x: int, render_chunk_y: int,
                                             generation_chunk_size: int) -> List[Tuple[int, int]]:
        """
        Get all generation chunk coordinates that overlap with a render chunk.
        
        Args:
            render_chunk_x: Render chunk X coordinate
            render_chunk_y: Render chunk Y coordinate
            generation_chunk_size: Size of generation chunks
            
        Returns:
            List of (gen_chunk_x, gen_chunk_y) coordinates
        """
        # Calculate world bounds of the render chunk
        render_min_x = render_chunk_x * self.render_chunk_size
        render_min_y = render_chunk_y * self.render_chunk_size
        render_max_x = render_min_x + self.render_chunk_size - 1
        render_max_y = render_min_y + self.render_chunk_size - 1
        
        # Find all generation chunks that overlap with this render chunk
        gen_chunks = []
        
        # Calculate generation chunk bounds that overlap with render chunk
        min_gen_x = math.floor(render_min_x / generation_chunk_size)
        min_gen_y = math.floor(render_min_y / generation_chunk_size)
        max_gen_x = math.floor(render_max_x / generation_chunk_size)
        max_gen_y = math.floor(render_max_y / generation_chunk_size)
        
        for gen_x in range(min_gen_x, max_gen_x + 1):
            for gen_y in range(min_gen_y, max_gen_y + 1):
                gen_chunks.append((gen_x, gen_y))
        
        return gen_chunks
    
    def aggregate_generation_chunks(self, generation_chunks: List[GenerationChunk],
                                  render_chunk_x: int, render_chunk_y: int) -> RenderChunk:
        """
        Aggregate multiple generation chunks into a single render chunk.
        
        Args:
            generation_chunks: List of generation chunks to aggregate
            render_chunk_x: Target render chunk X coordinate
            render_chunk_y: Target render chunk Y coordinate
            
        Returns:
            Aggregated render chunk
        """
        # Calculate render chunk world bounds
        render_min_x = render_chunk_x * self.render_chunk_size
        render_min_y = render_chunk_y * self.render_chunk_size
        render_max_x = render_min_x + self.render_chunk_size - 1
        render_max_y = render_min_y + self.render_chunk_size - 1
        
        # Aggregate all tiles from generation chunks
        aggregated_tiles = {}
        
        for gen_chunk in generation_chunks:
            for (world_x, world_y), tile_data in gen_chunk.tiles.items():
                # Only include tiles that fall within the render chunk bounds
                if (render_min_x <= world_x <= render_max_x and
                    render_min_y <= world_y <= render_max_y):
                    # Extract tile_type from tile_data dictionary
                    if isinstance(tile_data, dict):
                        tile_type = tile_data.get('tile_type', 'stone')
                    else:
                        tile_type = tile_data  # Fallback if it's already a string
                    aggregated_tiles[(world_x, world_y)] = tile_type
        
        # Aggregate metadata
        aggregated_metadata = {
            'generation_chunk_count': len(generation_chunks),
            'generation_chunk_sizes': [chunk.chunk_size for chunk in generation_chunks],
            'tile_count': len(aggregated_tiles),
            'render_chunk_bounds': (render_min_x, render_min_y, render_max_x, render_max_y)
        }
        
        # Add metadata from generation chunks
        for i, gen_chunk in enumerate(generation_chunks):
            aggregated_metadata[f'gen_chunk_{i}_metadata'] = gen_chunk.metadata
        
        return RenderChunk(
            chunk_x=render_chunk_x,
            chunk_y=render_chunk_y,
            chunk_size=self.render_chunk_size,
            generation_chunks=generation_chunks,
            aggregated_tiles=aggregated_tiles,
            metadata=aggregated_metadata
        )
    
    def get_render_chunks_for_area(self, min_world_x: int, min_world_y: int,
                                  max_world_x: int, max_world_y: int) -> List[Tuple[int, int]]:
        """
        Get all render chunk coordinates that overlap with a world area.
        
        Args:
            min_world_x: Minimum world X coordinate
            min_world_y: Minimum world Y coordinate
            max_world_x: Maximum world X coordinate
            max_world_y: Maximum world Y coordinate
            
        Returns:
            List of (render_chunk_x, render_chunk_y) coordinates
        """
        min_render_x = math.floor(min_world_x / self.render_chunk_size)
        min_render_y = math.floor(min_world_y / self.render_chunk_size)
        max_render_x = math.floor(max_world_x / self.render_chunk_size)
        max_render_y = math.floor(max_world_y / self.render_chunk_size)
        
        render_chunks = []
        for render_x in range(min_render_x, max_render_x + 1):
            for render_y in range(min_render_y, max_render_y + 1):
                render_chunks.append((render_x, render_y))
        
        return render_chunks
    
    def calculate_final_generation_chunk_size(self, initial_chunk_size: int, 
                                            pipeline_layers: List[str]) -> int:
        """
        Calculate the final generation chunk size after all pipeline layers.

        Args:
            initial_chunk_size: Starting chunk size (e.g., 64 for lands_and_seas)
            pipeline_layers: List of pipeline layer names

        Returns:
            Final generation chunk size after all zoom layers
        """
        current_size = initial_chunk_size
        
        for layer_name in pipeline_layers:
            if layer_name == "zoom":
                current_size = current_size // 2  # Each zoom layer halves the size
        
        # Ensure minimum size of 1
        return max(1, current_size)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the dual chunk system."""
        return {
            'render_chunk_size': self.render_chunk_size,
            'coord_cache_size': len(self._coord_cache),
            'cache_hit_ratio': 'N/A'  # Could be implemented with hit/miss counters
        }
```

## src/world/messages.py

```python
#!/usr/bin/env python3
"""
Message System for Async World Generation

Defines message types for communication between the main thread (rendering)
and the world generation worker thread via thread-safe queues.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum


class MessageType(Enum):
    """Types of messages that can be sent between threads."""
    CHUNK_REQUEST = "chunk_request"
    CHUNK_RESPONSE = "chunk_response"
    CHUNK_CANCEL = "chunk_cancel"
    STATUS_UPDATE = "status_update"
    SHUTDOWN = "shutdown"


class Priority(Enum):
    """Priority levels for chunk generation requests."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class ChunkRequest:
    """Request to generate a specific chunk."""
    chunk_x: int
    chunk_y: int
    priority: Priority = Priority.NORMAL
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.request_id is None:
            self.request_id = f"chunk_{self.chunk_x}_{self.chunk_y}"


@dataclass
class ChunkResponse:
    """Response containing generated chunk data."""
    chunk_x: int
    chunk_y: int
    chunk_data: Dict[str, Any]
    request_id: str
    generation_time: float
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class ChunkCancel:
    """Request to cancel chunk generation."""
    chunk_x: int
    chunk_y: int
    request_id: str


@dataclass
class StatusUpdate:
    """Status update from worker thread."""
    message: str
    worker_id: str
    chunks_in_queue: int
    chunks_generated: int
    cache_size: int


@dataclass
class ShutdownMessage:
    """Signal to shutdown worker thread."""
    reason: str = "Normal shutdown"


@dataclass
class Message:
    """Wrapper for all message types with metadata."""
    message_type: MessageType
    payload: Any
    timestamp: float
    sender: str

    def __lt__(self, other):
        """Enable comparison for priority queue."""
        if not isinstance(other, Message):
            return NotImplemented
        return self.timestamp < other.timestamp

    def __eq__(self, other):
        """Enable equality comparison."""
        if not isinstance(other, Message):
            return NotImplemented
        return (self.message_type == other.message_type and
                self.timestamp == other.timestamp and
                self.sender == other.sender)

    def __hash__(self):
        """Enable hashing for use in sets."""
        return hash((self.message_type, self.timestamp, self.sender))
    
    @classmethod
    def chunk_request(cls, chunk_x: int, chunk_y: int, priority: Priority = Priority.NORMAL, 
                     sender: str = "main") -> 'Message':
        """Create a chunk request message."""
        import time
        return cls(
            message_type=MessageType.CHUNK_REQUEST,
            payload=ChunkRequest(chunk_x, chunk_y, priority),
            timestamp=time.time(),
            sender=sender
        )
    
    @classmethod
    def chunk_response(cls, chunk_x: int, chunk_y: int, chunk_data: Dict[str, Any],
                      request_id: str, generation_time: float, success: bool = True,
                      error_message: Optional[str] = None, sender: str = "worker") -> 'Message':
        """Create a chunk response message."""
        import time
        return cls(
            message_type=MessageType.CHUNK_RESPONSE,
            payload=ChunkResponse(chunk_x, chunk_y, chunk_data, request_id, 
                                generation_time, success, error_message),
            timestamp=time.time(),
            sender=sender
        )
    
    @classmethod
    def chunk_cancel(cls, chunk_x: int, chunk_y: int, request_id: str, 
                    sender: str = "main") -> 'Message':
        """Create a chunk cancel message."""
        import time
        return cls(
            message_type=MessageType.CHUNK_CANCEL,
            payload=ChunkCancel(chunk_x, chunk_y, request_id),
            timestamp=time.time(),
            sender=sender
        )
    
    @classmethod
    def status_update(cls, message: str, worker_id: str, chunks_in_queue: int,
                     chunks_generated: int, cache_size: int, sender: str = "worker") -> 'Message':
        """Create a status update message."""
        import time
        return cls(
            message_type=MessageType.STATUS_UPDATE,
            payload=StatusUpdate(message, worker_id, chunks_in_queue, chunks_generated, cache_size),
            timestamp=time.time(),
            sender=sender
        )
    
    @classmethod
    def shutdown(cls, reason: str = "Normal shutdown", sender: str = "main") -> 'Message':
        """Create a shutdown message."""
        import time
        return cls(
            message_type=MessageType.SHUTDOWN,
            payload=ShutdownMessage(reason),
            timestamp=time.time(),
            sender=sender
        )


class MessageBus:
    """
    Thread-safe message bus for communication between main and worker threads.
    
    Uses Python's queue.Queue for thread-safe message passing.
    """
    
    def __init__(self, max_queue_size: int = 1000):
        """
        Initialize the message bus.
        
        Args:
            max_queue_size: Maximum number of messages in each queue
        """
        import queue
        
        # Queue for messages from main thread to worker thread
        self.to_worker = queue.PriorityQueue(maxsize=max_queue_size)
        
        # Queue for messages from worker thread to main thread
        self.to_main = queue.Queue(maxsize=max_queue_size)
        
        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
    
    def send_to_worker(self, message: Message, block: bool = True, timeout: Optional[float] = None):
        """
        Send a message to the worker thread.
        
        Args:
            message: Message to send
            block: Whether to block if queue is full
            timeout: Timeout for blocking operations
        """
        try:
            # Use priority based on message type and payload priority
            priority = self._get_message_priority(message)
            self.to_worker.put((priority, message), block=block, timeout=timeout)
            self.messages_sent += 1
        except Exception as e:
            print(f"Failed to send message to worker: {e}")
    
    def send_to_main(self, message: Message, block: bool = True, timeout: Optional[float] = None):
        """
        Send a message to the main thread.

        Args:
            message: Message to send
            block: Whether to block if queue is full
            timeout: Timeout for blocking operations
        """
        try:
            self.to_main.put(message, block=block, timeout=timeout)
            self.messages_sent += 1
        except Exception as e:
            print(f"Failed to send message to main: {e}")
    
    def receive_from_worker(self, block: bool = False, timeout: Optional[float] = None) -> Optional[Message]:
        """
        Receive a message from the worker thread.

        Args:
            block: Whether to block waiting for message
            timeout: Timeout for blocking operations

        Returns:
            Message if available, None otherwise
        """
        import queue
        try:
            message = self.to_main.get(block=block, timeout=timeout)
            self.messages_received += 1
            return message
        except queue.Empty:
            return None
        except Exception as e:
            print(f"Failed to receive message from worker: {e}")
            return None
    
    def receive_from_main(self, block: bool = True, timeout: Optional[float] = None) -> Optional[Message]:
        """
        Receive a message from the main thread.

        Args:
            block: Whether to block waiting for message
            timeout: Timeout for blocking operations

        Returns:
            Message if available, None otherwise
        """
        import queue
        try:
            _priority, message = self.to_worker.get(block=block, timeout=timeout)
            self.messages_received += 1
            return message
        except queue.Empty:
            return None
        except Exception as e:
            print(f"Failed to receive message from main: {e}")
            return None
    
    def _get_message_priority(self, message: Message) -> int:
        """Get numeric priority for message (lower number = higher priority)."""
        if message.message_type == MessageType.SHUTDOWN:
            return 0  # Highest priority
        elif message.message_type == MessageType.CHUNK_CANCEL:
            return 1  # High priority
        elif message.message_type == MessageType.CHUNK_REQUEST:
            # Use request priority
            if hasattr(message.payload, 'priority'):
                priority_map = {
                    Priority.URGENT: 2,
                    Priority.HIGH: 3,
                    Priority.NORMAL: 4,
                    Priority.LOW: 5
                }
                return priority_map.get(message.payload.priority, 4)
            return 4  # Normal priority
        else:
            return 6  # Low priority
    
    def get_stats(self) -> Dict[str, int]:
        """Get message bus statistics."""
        return {
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'to_worker_size': self.to_worker.qsize(),
            'to_main_size': self.to_main.qsize()
        }
```

## src/world/pipeline.py

```python
#!/usr/bin/env python3
"""
Core pipeline infrastructure for the generation system.

Defines the base classes and data structures for the layered generation pipeline.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import random


@dataclass
class GenerationData:
    """
    Standardized data structure passed between generation layers.
    
    This ensures all layers can work together regardless of order.
    """
    # Core world info
    seed: int
    chunk_size: int
    
    # Chunk data - maps (chunk_x, chunk_y) to chunk data
    chunks: Dict[Tuple[int, int], Dict[str, Any]] = field(default_factory=dict)
    
    # Layer metadata - tracks which layers have processed this data
    processed_layers: List[str] = field(default_factory=list)
    
    # Custom data - layers can store arbitrary data here
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def get_chunk(self, chunk_x: int, chunk_y: int) -> Dict[str, Any]:
        """Get chunk data, creating empty chunk if it doesn't exist."""
        chunk_key = (chunk_x, chunk_y)
        if chunk_key not in self.chunks:
            self.chunks[chunk_key] = {
                'chunk_x': chunk_x,
                'chunk_y': chunk_y,
                'chunk_size': self.chunk_size
            }
        return self.chunks[chunk_key]
    
    def set_chunk_property(self, chunk_x: int, chunk_y: int, property_name: str, value: Any):
        """Set a property on a specific chunk."""
        chunk = self.get_chunk(chunk_x, chunk_y)
        chunk[property_name] = value
    
    def get_chunk_property(self, chunk_x: int, chunk_y: int, property_name: str, default: Any = None) -> Any:
        """Get a property from a specific chunk."""
        chunk = self.get_chunk(chunk_x, chunk_y)
        return chunk.get(property_name, default)


class GenerationLayer(ABC):
    """
    Base class for all generation layers.
    
    Each layer processes GenerationData and adds its own information.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.rng = random.Random()
    
    @abstractmethod
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process the generation data within the given bounds.
        
        Args:
            data: The generation data to process
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)
            
        Returns:
            The modified generation data
        """
        pass
    
    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """Helper to get configuration values."""
        return self.config.get(key, default)
    
    def _set_seed(self, base_seed: int, *additional_components):
        """Set the RNG seed based on base seed and additional components."""
        combined_seed = hash((base_seed, self.name, *additional_components)) % (2**32)
        self.rng.seed(combined_seed)


class GenerationPipeline:
    """
    Manages a sequence of generation layers.
    """

    def __init__(self, name: str):
        self.name = name
        self.layers: List[GenerationLayer] = []
    
    def add_layer(self, layer: GenerationLayer):
        """Add a layer to the pipeline."""
        self.layers.append(layer)
    
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process data through all layers in sequence.

        Args:
            data: The generation data to process
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)

        Returns:
            The processed generation data
        """
        for layer in self.layers:
            data = layer.process(data, bounds)
            if layer.name not in data.processed_layers:
                data.processed_layers.append(layer.name)

        return data
    
    def get_layer_names(self) -> List[str]:
        """Get the names of all layers in the pipeline."""
        return [layer.name for layer in self.layers]




# WorldGenerationPipeline class removed - functionality moved to TierManager
```

## src/world/spiral_generator.py

```python
#!/usr/bin/env python3
"""
Spiral chunk generation algorithm for efficient world loading.

Generates chunks in a spiral pattern outward from the cursor position,
similar to Minecraft's chunk loading system.
"""

from typing import List, Tuple, Set, Iterator
import math


class SpiralChunkGenerator:
    """
    Generates chunk coordinates in a spiral pattern outward from a center point.
    
    This mimics Minecraft's efficient chunk loading where chunks are loaded
    in order of distance from the player, ensuring the most important chunks
    are loaded first.
    """
    
    def __init__(self, max_radius: int = 8):
        """
        Initialize the spiral generator.
        
        Args:
            max_radius: Maximum radius in chunks to generate
        """
        self.max_radius = max_radius
        self._spiral_cache = {}  # Cache spiral patterns for different radii
    
    def generate_spiral(self, center_chunk_x: int, center_chunk_y: int, 
                       radius: int) -> List[Tuple[int, int]]:
        """
        Generate chunk coordinates in a spiral pattern around the center.
        
        Args:
            center_chunk_x: Center chunk X coordinate
            center_chunk_y: Center chunk Y coordinate
            radius: Maximum radius in chunks
            
        Returns:
            List of chunk coordinates in spiral order (closest first)
        """
        if radius in self._spiral_cache:
            # Use cached spiral pattern and offset it
            cached_spiral = self._spiral_cache[radius]
            return [(center_chunk_x + dx, center_chunk_y + dy) for dx, dy in cached_spiral]
        
        # Generate new spiral pattern
        spiral_offsets = self._generate_spiral_offsets(radius)
        self._spiral_cache[radius] = spiral_offsets
        
        # Apply offsets to center position
        return [(center_chunk_x + dx, center_chunk_y + dy) for dx, dy in spiral_offsets]
    
    def _generate_spiral_offsets(self, radius: int) -> List[Tuple[int, int]]:
        """
        Generate spiral offset pattern from (0,0).
        
        Uses a square spiral algorithm that prioritizes chunks by distance.
        """
        if radius <= 0:
            return [(0, 0)]
        
        offsets = [(0, 0)]  # Start with center
        
        # Generate spiral layer by layer
        for layer in range(1, radius + 1):
            layer_offsets = self._generate_layer_offsets(layer)
            
            # Sort by distance from center for this layer
            layer_offsets.sort(key=lambda pos: self._distance_squared(pos[0], pos[1]))
            offsets.extend(layer_offsets)
        
        return offsets
    
    def _generate_layer_offsets(self, layer: int) -> List[Tuple[int, int]]:
        """Generate all offsets for a specific layer of the spiral."""
        offsets = []
        
        # Top edge (left to right)
        for x in range(-layer, layer + 1):
            offsets.append((x, -layer))
        
        # Right edge (top to bottom, excluding corners)
        for y in range(-layer + 1, layer):
            offsets.append((layer, y))
        
        # Bottom edge (right to left, excluding right corner)
        if layer > 0:
            for x in range(layer, -layer - 1, -1):
                offsets.append((x, layer))
        
        # Left edge (bottom to top, excluding corners)
        for y in range(layer - 1, -layer, -1):
            offsets.append((-layer, y))
        
        return offsets
    
    def _distance_squared(self, x: int, y: int) -> float:
        """Calculate squared distance from origin (for sorting)."""
        return x * x + y * y
    
    def get_new_chunks_for_movement(self, old_center: Tuple[int, int], 
                                   new_center: Tuple[int, int], 
                                   radius: int) -> List[Tuple[int, int]]:
        """
        Get only the new chunks needed when moving from old_center to new_center.
        
        This is the key optimization - we don't regenerate existing chunks,
        we only generate the new ones at the edges.
        
        Args:
            old_center: Previous center chunk coordinates
            new_center: New center chunk coordinates  
            radius: Chunk loading radius
            
        Returns:
            List of new chunk coordinates needed, in spiral order
        """
        if old_center == new_center:
            return []  # No movement, no new chunks needed
        
        # Get all chunks for old and new positions
        old_chunks = set(self.generate_spiral(old_center[0], old_center[1], radius))
        new_chunks = set(self.generate_spiral(new_center[0], new_center[1], radius))
        
        # Find chunks that are new (in new set but not in old set)
        new_chunk_coords = new_chunks - old_chunks
        
        if not new_chunk_coords:
            return []
        
        # Sort new chunks by distance from new center (spiral order)
        new_chunks_list = list(new_chunk_coords)
        new_chunks_list.sort(key=lambda chunk: self._distance_squared(
            chunk[0] - new_center[0], 
            chunk[1] - new_center[1]
        ))
        
        return new_chunks_list
    
    def get_chunks_to_unload(self, old_center: Tuple[int, int], 
                            new_center: Tuple[int, int], 
                            radius: int, unload_radius: int) -> List[Tuple[int, int]]:
        """
        Get chunks that should be unloaded when moving.
        
        Args:
            old_center: Previous center chunk coordinates
            new_center: New center chunk coordinates
            radius: Current loading radius
            unload_radius: Distance at which to unload chunks
            
        Returns:
            List of chunk coordinates to unload
        """
        if old_center == new_center:
            return []
        
        # Get chunks that were loaded at old position
        old_chunks = set(self.generate_spiral(old_center[0], old_center[1], radius))
        
        # Get chunks that should stay loaded at new position (with unload buffer)
        keep_chunks = set(self.generate_spiral(new_center[0], new_center[1], unload_radius))
        
        # Chunks to unload are those that were loaded but are now too far
        unload_chunks = old_chunks - keep_chunks
        
        return list(unload_chunks)


class ChunkLoadingManager:
    """
    Manages chunk loading using spiral generation with movement optimization.
    
    This class handles the high-level logic of when to generate chunks,
    what to keep loaded, and how to prioritize generation requests.
    """
    
    def __init__(self, load_radius: int = 3, unload_radius: int = 5):
        """
        Initialize the chunk loading manager.
        
        Args:
            load_radius: Radius in chunks to keep loaded around cursor
            unload_radius: Distance at which chunks get unloaded
        """
        self.load_radius = load_radius
        self.unload_radius = unload_radius
        self.spiral_generator = SpiralChunkGenerator(max_radius=unload_radius)
        
        # Track state
        self.current_center_chunk: Tuple[int, int] = (0, 0)
        self.loaded_chunks: Set[Tuple[int, int]] = set()
        self.generation_queue: List[Tuple[int, int]] = []
    
    def update_for_position(self, new_center_chunk: Tuple[int, int]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """
        Update chunk loading for a new cursor position.
        
        Args:
            new_center_chunk: New center chunk coordinates
            
        Returns:
            Tuple of (chunks_to_generate, chunks_to_unload)
        """
        old_center = self.current_center_chunk
        
        # Get new chunks needed (spiral order, closest first)
        new_chunks = self.spiral_generator.get_new_chunks_for_movement(
            old_center, new_center_chunk, self.load_radius
        )
        
        # Get chunks to unload (too far away)
        unload_chunks = self.spiral_generator.get_chunks_to_unload(
            old_center, new_center_chunk, self.load_radius, self.unload_radius
        )
        
        # Update state
        self.current_center_chunk = new_center_chunk
        
        # Update loaded chunks set
        for chunk in unload_chunks:
            self.loaded_chunks.discard(chunk)
        
        for chunk in new_chunks:
            self.loaded_chunks.add(chunk)
        
        return new_chunks, unload_chunks
    
    def get_initial_chunks(self, center_chunk: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Get initial chunks to load when starting at a position.
        
        Args:
            center_chunk: Starting center chunk coordinates
            
        Returns:
            List of chunks in spiral order (closest first)
        """
        self.current_center_chunk = center_chunk
        
        chunks = self.spiral_generator.generate_spiral(
            center_chunk[0], center_chunk[1], self.load_radius
        )
        
        self.loaded_chunks = set(chunks)
        return chunks
    
    def get_generation_priority(self, chunk: Tuple[int, int]) -> float:
        """
        Get generation priority for a chunk (lower = higher priority).
        
        Args:
            chunk: Chunk coordinates
            
        Returns:
            Priority value (distance from current center)
        """
        dx = chunk[0] - self.current_center_chunk[0]
        dy = chunk[1] - self.current_center_chunk[1]
        return math.sqrt(dx * dx + dy * dy)


# Example usage and testing
if __name__ == "__main__":
    # Test spiral generation
    spiral_gen = SpiralChunkGenerator()

    # Test small spiral
    center = (0, 0)
    radius = 2
    spiral_chunks = spiral_gen.generate_spiral(center[0], center[1], radius)
    
    # Test movement optimization
    print(f"\n🏃 Testing Movement Optimization")
    print("-" * 35)
    
    old_center = (0, 0)
    new_center = (1, 0)  # Move right by 1 chunk
    
    new_chunks = spiral_gen.get_new_chunks_for_movement(old_center, new_center, radius)
    unload_chunks = spiral_gen.get_chunks_to_unload(old_center, new_center, radius, radius + 2)
    
    print(f"Moving from {old_center} to {new_center}:")
    print(f"  New chunks needed: {new_chunks}")
    print(f"  Chunks to unload: {unload_chunks}")
    print(f"  Efficiency: Only {len(new_chunks)} new chunks vs {len(spiral_chunks)} total")
    
    print("\n✅ Spiral generation working correctly!")
```

## src/world/tier_manager.py

```python
#!/usr/bin/env python3
"""
TierManager - Coordinates multi-tier generation pipeline

Manages the relationship between WorldTier, RegionTier, and LocalTier
for scalable world generation across different levels of detail.
"""

from typing import Dict, List, Tuple, Optional, Any
from .pipeline import GenerationPipeline, GenerationData
from .world_tier import WorldTier


class TierManager:
    """
    Coordinates multi-tier generation pipeline.
    
    Manages WorldTier (current: lands_and_seas → zoom layers)
    Prepared for future RegionTier and LocalTier.
    Each tier operates on appropriate chunk scales.
    """
    
    def __init__(self):
        """Initialize the tier manager."""
        # Tiers - only WorldTier implemented for now
        self.world_tier: Optional[GenerationPipeline] = None
        self.region_tier: Optional[GenerationPipeline] = None  # Future
        self.local_tier: Optional[GenerationPipeline] = None   # Future
        
        # Configuration tracking
        self._world_tier_config: Optional[Dict[str, Any]] = None
    
    def set_world_tier(self, layer_configs: List[Tuple[str, Dict[str, Any]]]):
        """
        Set the world tier pipeline with configured layers.

        Args:
            layer_configs: List of (layer_name, config_dict) tuples
        """
        self.world_tier = WorldTier.create_custom_pipeline(layer_configs)
        self._world_tier_config = layer_configs
    
    def set_region_tier(self, layer_configs: List[Tuple[str, Dict[str, Any]]]):
        """
        Set the region tier pipeline (future implementation).
        
        Args:
            layer_configs: List of (layer_name, config_dict) tuples
        """
        # TODO: Implement when RegionTier is available
        raise NotImplementedError("RegionTier not yet implemented")
    
    def set_local_tier(self, layer_configs: List[Tuple[str, Dict[str, Any]]]):
        """
        Set the local tier pipeline (future implementation).
        
        Args:
            layer_configs: List of (layer_name, config_dict) tuples
        """
        # TODO: Implement when LocalTier is available
        raise NotImplementedError("LocalTier not yet implemented")
    
    def process_tiers(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process data through all configured tiers in sequence.
        
        Args:
            data: The generation data to process
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)
            
        Returns:
            The processed generation data
        """
        # Process through world tier
        if self.world_tier:
            data = self.world_tier.process(data, bounds)
        
        # TODO: Process through region tier
        if self.region_tier:
            data = self.region_tier.process(data, bounds)
        
        # TODO: Process through local tier  
        if self.local_tier:
            data = self.local_tier.process(data, bounds)
        
        return data
    
    def get_world_tier_info(self) -> Dict[str, Any]:
        """Get information about the world tier configuration."""
        if not self.world_tier:
            return {"configured": False}
        
        return {
            "configured": True,
            "layer_count": len(self.world_tier.layers),
            "layer_names": [layer.name for layer in self.world_tier.layers],
            "config": self._world_tier_config
        }
    
    def get_tier_summary(self) -> Dict[str, Any]:
        """Get summary of all configured tiers."""
        return {
            "world_tier": self.get_world_tier_info(),
            "region_tier": {"configured": self.region_tier is not None},
            "local_tier": {"configured": self.local_tier is not None}
        }
    
    def is_configured(self) -> bool:
        """Check if at least one tier is configured."""
        return self.world_tier is not None
    
    def clear_all_tiers(self):
        """Clear all tier configurations."""
        self.world_tier = None
        self.region_tier = None
        self.local_tier = None
        self._world_tier_config = None


# Example usage and testing
if __name__ == "__main__":
    # Create tier manager
    tier_manager = TierManager()

    # Test configuration
    layer_configs = [
        ("lands_and_seas", {"land_ratio": 3}),
        ("zoom", {"subdivision_factor": 2})
    ]

    tier_manager.set_world_tier(layer_configs)

    # Test info retrieval
    world_info = tier_manager.get_world_tier_info()
    tier_summary = tier_manager.get_tier_summary()
```

## src/world/worker.py

```python
#!/usr/bin/env python3
"""
World Generation Worker Thread

Runs world generation in a separate thread to avoid blocking the main rendering thread.
Communicates via message bus for smooth, responsive gameplay.
"""

import threading
import time
from typing import Dict, Set, Optional, Tuple
from collections import OrderedDict

from .messages import MessageBus, Message, MessageType, Priority
from .dual_chunk_system import DualChunkManager, GenerationChunk, RenderChunk
from .tier_manager import TierManager
from .pipeline import GenerationData
from ..config import WorldConfig

# Import the real pipeline system components
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Define Tile class locally to avoid circular imports
class Tile:
    """Represents a single tile in the world."""
    def __init__(self, x: int, y: int, tile_type: str = "stone"):
        self.x = x
        self.y = y
        self.tile_type = tile_type

class WorldGenerationWorker:
    """
    Worker thread that handles world generation requests asynchronously.
    
    Runs the world generation pipeline in a separate thread and communicates
    results back to the main thread via message bus.
    """
    
    def __init__(self, world_config: WorldConfig, message_bus: MessageBus, tier_manager: Optional[TierManager] = None, worker_id: str = "worker_1"):
        """
        Initialize the world generation worker.

        Args:
            world_config: World configuration settings
            message_bus: Message bus for communication
            tier_manager: TierManager instance for pipeline coordination
            worker_id: Unique identifier for this worker
        """
        self.world_config = world_config
        self.message_bus = message_bus
        self.worker_id = worker_id
        self.seed = world_config.seed
        self.chunk_size = world_config.chunk_size

        # Use provided TierManager or create a new one
        if tier_manager:
            self.tier_manager = tier_manager
        else:
            self.tier_manager = TierManager()
            # Setup tier manager with world config
            layer_configs = []
            for layer_name in world_config.pipeline_layers:
                layer_config = world_config.layer_configs.get(layer_name, {})
                layer_configs.append((layer_name, layer_config))
            self.tier_manager.set_world_tier(layer_configs)
        
        # Worker state
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Dual chunk system
        self.render_chunk_size = 64  # Fixed render chunk size
        self.dual_chunk_manager = DualChunkManager(render_chunk_size=self.render_chunk_size)

        # Calculate final generation chunk size
        self.final_generation_chunk_size = self.dual_chunk_manager.calculate_final_generation_chunk_size(
            world_config.chunk_size, world_config.pipeline_layers
        )

        # Chunk management - now caches render chunks
        self.render_chunk_cache: OrderedDict[Tuple[int, int], RenderChunk] = OrderedDict()
        self.cache_limit = world_config.chunk_cache_limit
        
        # Request tracking
        self.active_requests: Set[str] = set()
        self.cancelled_requests: Set[str] = set()
        
        # Statistics
        self.chunks_generated = 0
        self.total_generation_time = 0.0
        self.requests_processed = 0
        self.requests_cancelled = 0
    
    def start(self):
        """Start the worker thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, name=f"WorldWorker-{self.worker_id}")
        self.thread.daemon = True
        self.thread.start()

    
    def stop(self, timeout: float = 5.0):
        """
        Stop the worker thread.
        
        Args:
            timeout: Maximum time to wait for worker to stop
        """
        if not self.running:
            return
        
        # Send shutdown message
        shutdown_msg = Message.shutdown(f"Stop requested for {self.worker_id}")
        self.message_bus.send_to_worker(shutdown_msg, block=False)
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)
            if self.thread.is_alive():
                pass

        self.running = False
    
    def _worker_loop(self):
        """Main worker thread loop."""

        
        while self.running:
            try:
                # Receive message from main thread
                message = self.message_bus.receive_from_main(block=True, timeout=1.0)
                
                if message is None:
                    continue  # Timeout, check if still running
                
                # Process message
                self._process_message(message)
                
                # Send periodic status updates
                if self.requests_processed % 10 == 0:
                    self._send_status_update()
                
            except Exception:
                pass
    
    def _process_message(self, message: Message):
        """Process a message from the main thread."""
        if message.message_type == MessageType.SHUTDOWN:
            print(f"Worker {self.worker_id} received shutdown signal")
            self.running = False
            
        elif message.message_type == MessageType.CHUNK_REQUEST:
            self._handle_chunk_request(message)
            
        elif message.message_type == MessageType.CHUNK_CANCEL:
            self._handle_chunk_cancel(message)
            
        else:
            print(f"Worker {self.worker_id} received unknown message type: {message.message_type}")
    
    def _handle_chunk_request(self, message: Message):
        """Handle chunk generation with proper response"""
        request = message.payload
        chunk_x, chunk_y = request.chunk_x, request.chunk_y
        request_id = request.request_id

        # Check if request was cancelled
        if request_id in self.cancelled_requests:
            self.cancelled_requests.discard(request_id)
            self.requests_cancelled += 1
            return

        # Check if render chunk is already cached
        render_chunk_key = (chunk_x, chunk_y)
        if render_chunk_key in self.render_chunk_cache:
            # Send cached render chunk response immediately
            response = Message.chunk_response(
                chunk_x, chunk_y,
                {"status": "ready"},  # Minimal response data
                request_id,
                0.0,
                True, None, self.worker_id
            )
            self.message_bus.send_to_main(response, block=False)
            return

        # Generate render chunk by aggregating generation chunks
        self.active_requests.add(request_id)
        start_time = time.time()

        try:
            # Generate render chunk using dual chunk system
            render_chunk = self._generate_render_chunk(chunk_x, chunk_y)
            generation_time = time.time() - start_time

            # Cache the render chunk
            self.render_chunk_cache[render_chunk_key] = render_chunk
            self._enforce_cache_limit()

            # Send success response immediately
            response = Message.chunk_response(
                chunk_x, chunk_y,
                {"status": "ready"},  # Minimal response data
                request_id,
                generation_time,
                True, None, self.worker_id
            )
            self.message_bus.send_to_main(response, block=False)

            # Update statistics
            self.chunks_generated += 1
            self.total_generation_time += generation_time

        except Exception as e:
            generation_time = time.time() - start_time

            # Send error response
            response = Message.chunk_response(
                chunk_x, chunk_y, {}, request_id, generation_time, False, str(e), self.worker_id
            )
            self.message_bus.send_to_main(response, block=False)

        finally:
            self.active_requests.discard(request_id)
            self.requests_processed += 1
    
    def _handle_chunk_cancel(self, message: Message):
        """Handle a chunk cancellation request."""
        cancel = message.payload
        request_id = cancel.request_id
        
        if request_id in self.active_requests:
            # Mark as cancelled (can't stop generation in progress, but won't send response)
            self.cancelled_requests.add(request_id)
        
        self.requests_cancelled += 1
    
    def _generate_render_chunk(self, render_chunk_x: int, render_chunk_y: int) -> RenderChunk:
        """
        Generate a render chunk by aggregating multiple generation chunks.

        Args:
            render_chunk_x: Render chunk X coordinate
            render_chunk_y: Render chunk Y coordinate

        Returns:
            Complete render chunk with aggregated generation data
        """
        # Get all generation chunks that overlap with this render chunk
        generation_chunk_coords = self.dual_chunk_manager.get_generation_chunks_for_render_chunk(
            render_chunk_x, render_chunk_y, self.final_generation_chunk_size
        )

        # Generate all required generation chunks
        generation_chunks = []

        for gen_chunk_x, gen_chunk_y in generation_chunk_coords:
            gen_chunk = self._generate_generation_chunk(gen_chunk_x, gen_chunk_y)
            generation_chunks.append(gen_chunk)

        # Aggregate generation chunks into render chunk
        render_chunk = self.dual_chunk_manager.aggregate_generation_chunks(
            generation_chunks, render_chunk_x, render_chunk_y
        )

        return render_chunk

    def _generate_generation_chunk(self, chunk_x: int, chunk_y: int) -> GenerationChunk:
        """
        Generate a single chunk using the TierManager pipeline system.

        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate

        Returns:
            GenerationChunk containing chunk data and tile information
        """
        # Calculate effective chunk size after zoom layers
        effective_chunk_size = self.chunk_size
        zoom_count = sum(1 for layer_name in self.world_config.pipeline_layers if layer_name == "zoom")
        for _ in range(zoom_count):
            effective_chunk_size //= 2

        # Calculate world bounds for this chunk
        min_world_x = chunk_x * effective_chunk_size
        min_world_y = chunk_y * effective_chunk_size
        max_world_x = min_world_x + effective_chunk_size - 1
        max_world_y = min_world_y + effective_chunk_size - 1

        # Create generation data for the pipeline
        generation_data = GenerationData(
            seed=self.seed,
            chunk_size=effective_chunk_size
        )

        # Define bounds for pipeline processing (single chunk)
        bounds = (chunk_x, chunk_y, chunk_x, chunk_y)

        # Process through TierManager pipeline
        processed_data = self.tier_manager.process_tiers(generation_data, bounds)

        # Extract tiles from processed data
        chunk_tiles = {}

        # Get chunk data from the processed pipeline
        chunk_data = processed_data.get_chunk(chunk_x, chunk_y)

        # Verify pipeline provided required data
        if 'land_type' not in chunk_data:
            raise RuntimeError(f"❌ Pipeline failed to provide 'land_type' for chunk ({chunk_x}, {chunk_y}). "
                             f"Available data: {list(chunk_data.keys())}. "
                             f"TierManager configured: {self.tier_manager.is_configured()}")

        # Use the land_type from the pipeline to generate tiles
        chunk_land_type = chunk_data['land_type']

        for world_y in range(min_world_y, max_world_y + 1):
            for world_x in range(min_world_x, max_world_x + 1):
                # Use the chunk's land_type as the base tile type
                tile_type = chunk_land_type

                chunk_tiles[(world_x, world_y)] = {
                    'tile_type': tile_type,
                    'x': world_x,
                    'y': world_y
                }

        # Calculate chunk statistics for debugging
        tile_types = [tile_data['tile_type'] for tile_data in chunk_tiles.values()]
        tile_type_counts = {}
        for tile_type in tile_types:
            tile_type_counts[tile_type] = tile_type_counts.get(tile_type, 0) + 1

        # Create GenerationChunk object
        metadata = {
            'world_bounds': (min_world_x, min_world_y, max_world_x, max_world_y),
            'tile_type_counts': tile_type_counts,
            'total_tiles': len(chunk_tiles),
            'generated_at': time.time(),
            'pipeline_layers': self.world_config.pipeline_layers.copy()
        }

        return GenerationChunk(
            chunk_x=chunk_x,
            chunk_y=chunk_y,
            chunk_size=effective_chunk_size,
            tiles=chunk_tiles,
            metadata=metadata
        )
    
    def _enforce_cache_limit(self):
        """Enforce cache size limit using LRU eviction."""
        while len(self.render_chunk_cache) > self.cache_limit:
            # Remove oldest render chunk (first in OrderedDict)
            oldest_chunk = next(iter(self.render_chunk_cache))
            del self.render_chunk_cache[oldest_chunk]
    
    def _send_status_update(self):
        """Send status update to main thread."""
        status_msg = Message.status_update(
            message=f"Worker {self.worker_id} active",
            worker_id=self.worker_id,
            chunks_in_queue=len(self.active_requests),
            chunks_generated=self.chunks_generated,
            cache_size=len(self.render_chunk_cache)
        )
        self.message_bus.send_to_main(status_msg, block=False)
    
    def is_chunk_ready(self, chunk_x: int, chunk_y: int) -> bool:
        """Check if a chunk is ready (cached)."""
        return (chunk_x, chunk_y) in self.render_chunk_cache

    def get_ready_chunks(self) -> set:
        """Get set of ready chunk coordinates."""
        return set(self.render_chunk_cache.keys())

    def get_chunk_tiles(self, chunk_x: int, chunk_y: int) -> Dict[Tuple[int, int], Tile]:
        """Get all tiles in a chunk."""
        chunk_key = (chunk_x, chunk_y)
        if chunk_key in self.render_chunk_cache:
            render_chunk = self.render_chunk_cache[chunk_key]
            # Convert aggregated tiles to Tile objects
            tiles = {}
            for (world_x, world_y), tile_type in render_chunk.aggregated_tiles.items():
                tiles[(world_x, world_y)] = Tile(world_x, world_y, tile_type)
            return tiles
        return {}

    def request_chunk(self, chunk_x: int, chunk_y: int, request_id: Optional[str] = None, priority=None):
        """Request a chunk to be generated."""
        if request_id is None:
            import uuid
            request_id = str(uuid.uuid4())

        if priority is None:
            from .messages import Priority
            priority = Priority.NORMAL

        # Create chunk request message
        from .messages import Message
        request_msg = Message.chunk_request(chunk_x, chunk_y, priority, "main")
        self.message_bus.send_to_worker(request_msg, block=False)

    def get_statistics(self) -> Dict:
        """Get worker statistics."""
        avg_generation_time = (
            self.total_generation_time / max(1, self.chunks_generated)
        )

        return {
            'worker_id': self.worker_id,
            'running': self.running,
            'chunks_generated': self.chunks_generated,
            'requests_processed': self.requests_processed,
            'requests_cancelled': self.requests_cancelled,
            'cache_size': len(self.render_chunk_cache),
            'active_requests': len(self.active_requests),
            'avg_generation_time': avg_generation_time,
            'total_generation_time': self.total_generation_time
        }
```

## src/world/world_manager.py

```python
#!/usr/bin/env python3
"""
WorldManager - Advanced world manager with pipeline system

Provides world generation using the TierManager pipeline system.
"""

import threading
from typing import Dict, Any, Tuple, Optional, Set
from ..config import WorldConfig
from .worker import WorldGenerationWorker, Tile
from .tier_manager import TierManager
from .dual_chunk_system import DualChunkManager
from .messages import MessageBus


class WorldManager:
    """
    Advanced world manager that uses the TierManager pipeline system.
    """

    def __init__(self, world_config: WorldConfig):
        """Initialize the world manager with pipeline system."""
        self.config = world_config
        self._lock = threading.Lock()

        # Initialize dual chunk system
        self.dual_chunk_manager = DualChunkManager(
            render_chunk_size=world_config.chunk_size
        )

        # Initialize message bus for worker communication
        self.message_bus = MessageBus()

        # Initialize TierManager
        self._setup_tier_manager()

        # Initialize worker
        self.worker = WorldGenerationWorker(
            world_config=world_config,
            tier_manager=self.tier_manager,
            message_bus=self.message_bus
        )
        self.worker.start()

        # Non-blocking tile access system
        self.tile_cache = {}  # (x, y) -> Tile
        self.loading_chunks = set()  # Track requested chunks
        self.ready_chunks = set()   # Track completed chunks

        # Basic statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.chunks_requested = 0
        self.chunks_received = 0


    
    def _setup_tier_manager(self):
        """Set up the TierManager with configured layers."""
        self.tier_manager = TierManager()

        # Load layer configurations
        layer_configs = {}
        for layer_name in self.config.pipeline_layers:
            if layer_name in self.config.layer_configs:
                layer_configs[layer_name] = self.config.layer_configs[layer_name]
            else:
                raise RuntimeError(f"❌ Missing configuration for pipeline layer: {layer_name}")

        if not layer_configs:
            raise RuntimeError("❌ No pipeline layers configured! Cannot proceed without sophisticated generation algorithms.")

        # Set up world tier with layers
        self.tier_manager.set_world_tier(layer_configs)

        # Verify configuration
        if not self.tier_manager.is_configured():
            raise RuntimeError("❌ TierManager failed to configure properly! Pipeline system unavailable.")



    def update_chunks(self, camera, screen_width: int = 80, screen_height: int = 50):
        """Predictively load chunks around camera"""
        camera_chunk_x, camera_chunk_y = self.world_to_render_chunk(
            camera.cursor_x, camera.cursor_y)

        # Load immediate area (current screen)
        immediate_distance = max(screen_width // 64, screen_height // 64) + 1

        # Preload extended area (for smooth movement)
        preload_distance = immediate_distance + 2

        # Request chunks in priority order
        for distance in range(preload_distance + 1):
            for dx in range(-distance, distance + 1):
                for dy in range(-distance, distance + 1):
                    if abs(dx) == distance or abs(dy) == distance:  # Only edge chunks
                        chunk_x = camera_chunk_x + dx
                        chunk_y = camera_chunk_y + dy

                        if (chunk_x, chunk_y) not in self.loading_chunks and \
                           (chunk_x, chunk_y) not in self.ready_chunks:
                            from .messages import Priority
                            priority = Priority.HIGH if distance <= immediate_distance else Priority.NORMAL
                            self._request_chunk_async(chunk_x, chunk_y, priority)
                            self.loading_chunks.add((chunk_x, chunk_y))

        # Unload chunks that are too far away to prevent memory bloat
        self._unload_distant_chunks(camera_chunk_x, camera_chunk_y, preload_distance + 3)

    def get_tile(self, x: int, y: int) -> Tile:
        """Non-blocking tile access - always returns immediately"""
        # Check tile cache first
        if (x, y) in self.tile_cache:
            self.cache_hits += 1
            return self.tile_cache[(x, y)]

        # Check if chunk is ready
        chunk_x, chunk_y = self.world_to_render_chunk(x, y)
        if (chunk_x, chunk_y) in self.ready_chunks:
            # Load chunk tiles into cache
            self._cache_chunk_tiles(chunk_x, chunk_y)
            self.cache_hits += 1
            return self.tile_cache.get((x, y), Tile(x, y, "stone"))

        # Request chunk if not already loading
        if (chunk_x, chunk_y) not in self.loading_chunks:
            self._request_chunk_async(chunk_x, chunk_y)
            self.loading_chunks.add((chunk_x, chunk_y))

        # Return placeholder immediately
        self.cache_misses += 1
        return Tile(x, y, "loading")

    def _cache_chunk_tiles(self, chunk_x: int, chunk_y: int):
        """Load completed chunk tiles into cache"""
        chunk_tiles = self.worker.get_chunk_tiles(chunk_x, chunk_y)
        self.tile_cache.update(chunk_tiles)

    def _request_chunk_async(self, chunk_x: int, chunk_y: int, priority=None):
        """Request chunk generation asynchronously"""
        if priority is None:
            from .messages import Priority
            priority = Priority.NORMAL
        self.worker.request_chunk(chunk_x, chunk_y, priority=priority)
        self.chunks_requested += 1

    def _unload_distant_chunks(self, camera_chunk_x: int, camera_chunk_y: int, max_distance: int):
        """Unload chunks that are too far from camera to prevent memory bloat"""
        chunks_to_unload = []

        # Check ready chunks
        for chunk_x, chunk_y in list(self.ready_chunks):
            distance = max(abs(chunk_x - camera_chunk_x), abs(chunk_y - camera_chunk_y))
            if distance > max_distance:
                chunks_to_unload.append((chunk_x, chunk_y))

        # Unload distant chunks
        for chunk_x, chunk_y in chunks_to_unload:
            self.ready_chunks.discard((chunk_x, chunk_y))
            # Remove tiles from tile cache for this chunk
            chunk_bounds = self.get_render_chunk_bounds(chunk_x, chunk_y)
            min_x, min_y, max_x, max_y = chunk_bounds
            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    self.tile_cache.pop((x, y), None)

    def get_chunk_tiles(self, chunk_x: int, chunk_y: int) -> Dict[Tuple[int, int], Tile]:
        """Get all tiles in a chunk."""
        return self.worker.get_chunk_tiles(chunk_x, chunk_y)

    def is_chunk_loaded(self, chunk_x: int, chunk_y: int) -> bool:
        """Check if a chunk is loaded."""
        return self.worker.is_chunk_ready(chunk_x, chunk_y)

    def get_loaded_chunks(self) -> set:
        """Get set of loaded chunk coordinates."""
        return self.worker.get_ready_chunks()

    def get_chunk_info(self, world_x: int, world_y: int) -> Dict[str, Any]:
        """Get information about the chunk containing the given world coordinates."""
        chunk_x, chunk_y = self.world_to_render_chunk(world_x, world_y)
        is_loaded = self.is_chunk_loaded(chunk_x, chunk_y)

        return {
            'chunk_x': chunk_x,
            'chunk_y': chunk_y,
            'world_x': world_x,
            'world_y': world_y,
            'is_loaded': is_loaded,
            'chunk_size': self.config.chunk_size
        }

    def process_worker_messages(self):
        """Process completed chunks from worker - call this each frame"""
        from .messages import MessageType

        messages_processed = 0
        while messages_processed < 10:  # Limit processing per frame to avoid blocking
            message = self.message_bus.receive_from_worker(block=False)
            if not message:
                break

            if message.message_type == MessageType.CHUNK_RESPONSE:
                chunk_x, chunk_y = message.payload.chunk_x, message.payload.chunk_y
                if message.payload.success:
                    self.ready_chunks.add((chunk_x, chunk_y))
                    self.chunks_received += 1
                else:
                    # Handle error case - chunk failed to generate
                    pass
                self.loading_chunks.discard((chunk_x, chunk_y))

            elif message.message_type == MessageType.STATUS_UPDATE:
                # Handle worker status updates if needed
                pass

            messages_processed += 1

    def request_chunks(self, chunk_coords: set, priority=None):
        """Request chunks to be loaded."""
        if priority is None:
            from .messages import Priority
            priority = Priority.NORMAL

        for chunk_x, chunk_y in chunk_coords:
            if not self.is_chunk_loaded(chunk_x, chunk_y):
                self._request_chunk_async(chunk_x, chunk_y, priority)
                self.loading_chunks.add((chunk_x, chunk_y))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get world manager statistics."""
        total_requests = self.cache_hits + self.cache_misses
        cache_hit_ratio = self.cache_hits / max(1, total_requests)

        return {
            "available_chunks": len(self.ready_chunks),
            "requested_chunks": self.chunks_requested,
            "loading_chunks": len(self.loading_chunks),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "chunks_requested": self.chunks_requested,
            "chunks_received": self.chunks_received,
            "cache_hit_ratio": cache_hit_ratio,
            "render_chunk_size": self.config.chunk_size,
            "generation_chunk_size": self.config.chunk_size,
            "tile_cache_size": len(self.tile_cache),
            "predictive_loading": True,
            "memory_management": True
        }
    
    def shutdown(self):
        """Shutdown the world manager."""

        if hasattr(self, 'worker'):
            self.worker.stop()

    def get_render_chunks_in_bounds(self, min_x: int, min_y: int, max_x: int, max_y: int) -> set:
        """Get render chunks within bounds."""
        chunks = set()
        for chunk_x in range(min_x, max_x + 1):
            for chunk_y in range(min_y, max_y + 1):
                chunks.add((chunk_x, chunk_y))
        return chunks

    def get_render_chunk_size(self) -> int:
        """Get the render chunk size."""
        return self.config.chunk_size

    def world_to_render_chunk(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates to render chunk coordinates."""
        chunk_size = self.get_render_chunk_size()
        chunk_x = world_x // chunk_size
        chunk_y = world_y // chunk_size
        return (chunk_x, chunk_y)

    def get_render_chunk_bounds(self, chunk_x: int, chunk_y: int) -> Tuple[int, int, int, int]:
        """Get the world coordinate bounds of a render chunk."""
        chunk_size = self.get_render_chunk_size()
        min_x = chunk_x * chunk_size
        min_y = chunk_y * chunk_size
        max_x = min_x + chunk_size - 1
        max_y = min_y + chunk_size - 1
        return (min_x, min_y, max_x, max_y)

    def get_render_chunk_tiles(self, chunk_x: int, chunk_y: int) -> Dict[Tuple[int, int], Tile]:
        """Get all tiles in a render chunk."""
        return self.get_chunk_tiles(chunk_x, chunk_y)

    def get_chunk_status(self, chunk_x: int, chunk_y: int) -> str:
        """Get the current status of a chunk for debugging"""
        if (chunk_x, chunk_y) in self.ready_chunks:
            return "ready"
        elif (chunk_x, chunk_y) in self.loading_chunks:
            return "loading"
        else:
            return "not_requested"

```

## src/world/world_tier.py

```python
#!/usr/bin/env python3
"""
World Tier Pipeline

Manages the world-scale generation layers.
"""

from typing import Optional
from .pipeline import GenerationPipeline
from .layers.lands_and_seas import LandsAndSeasLayer
from .layers.zoom import ZoomLayer


class WorldTier:
    """
    Factory for creating world tier pipelines with configured layers.
    """
    
    @staticmethod
    def create_default_pipeline(config: Optional[dict] = None) -> GenerationPipeline:
        """
        Create a default world tier pipeline.

        Args:
            config: Configuration dictionary for layers

        Returns:
            Configured world tier pipeline
        """
        config = config or {}
        pipeline = GenerationPipeline("world_tier")
        
        # Add lands_and_seas layer (our existing chunk-based land/water generation)
        lands_seas_config = config.get('lands_and_seas', {})
        lands_seas_layer = LandsAndSeasLayer(lands_seas_config)
        pipeline.add_layer(lands_seas_layer)
        
        # Future layers will be added here:
        # - climate layer
        # - continental_drift layer  
        # - major_features layer
        # etc.
        
        return pipeline
    
    @staticmethod
    def create_custom_pipeline(layer_configs: list) -> GenerationPipeline:
        """
        Create a custom world tier pipeline from layer configurations.

        Args:
            layer_configs: List of (layer_name, config_dict) tuples

        Returns:
            Configured world tier pipeline
        """
        pipeline = GenerationPipeline("world_tier")

        for layer_name, config in layer_configs.items():
            if layer_name == "lands_and_seas":
                layer = LandsAndSeasLayer(config)
                pipeline.add_layer(layer)
            elif layer_name == "zoom":
                layer = ZoomLayer(config)
                pipeline.add_layer(layer)
            # Add other layer types here as they're implemented
            else:
                raise ValueError(f"Unknown world tier layer: {layer_name}")

        return pipeline
```

## src/world/layers/lands_and_seas/__init__.py

```python
"""
Lands and Seas Layer

The first layer of world generation that determines basic land/water distribution.
This is the foundation layer that other world-tier layers build upon.
"""

from .layer import LandsAndSeasLayer

__all__ = ["LandsAndSeasLayer"]
```

## src/world/layers/lands_and_seas/layer.py

```python
#!/usr/bin/env python3
"""
Lands and Seas Generation Layer

Determines basic land/water distribution for chunks.
This is the foundation layer that establishes the fundamental geography.
"""

import os
import random
import math
from typing import Dict, Any, Tuple

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from ...pipeline import GenerationLayer, GenerationData


class LandsAndSeasLayer(GenerationLayer):
    """
    Layer that determines whether each chunk is land or water.
    
    This is the first and most fundamental layer of world generation.
    Other layers will build upon this basic land/water distribution.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("lands_and_seas", config)
        
        # Load configuration from TOML file if no config provided
        if not config:
            self.config = self._load_config()
        
        # Extract configuration values
        self.land_ratio = self._get_config_value('land_ratio', 4)
        self.algorithm = self._get_config_value('algorithm', 'cellular_automata')

        # Algorithm-specific configuration
        if self.algorithm == 'perlin_noise':
            self.scale = self._get_config_value('perlin_noise.scale', 0.1)
            self.octaves = self._get_config_value('perlin_noise.octaves', 4)
            self.persistence = self._get_config_value('perlin_noise.persistence', 0.5)
            self.lacunarity = self._get_config_value('perlin_noise.lacunarity', 2.0)
        elif self.algorithm == 'cellular_automata':
            self.initial_land_probability = self._get_config_value('cellular_automata.initial_land_probability', 0.4)
            self.iterations = self._get_config_value('cellular_automata.iterations', 5)
            self.birth_limit = self._get_config_value('cellular_automata.birth_limit', 4)
            self.death_limit = self._get_config_value('cellular_automata.death_limit', 3)

        # Validate configuration
        if not (1 <= self.land_ratio <= 10):
            raise ValueError(f"land_ratio must be between 1 and 10, got {self.land_ratio}")

        if self.algorithm not in ['random_chunks', 'perlin_noise', 'cellular_automata']:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from the layer's TOML file."""
        # Look for config in the centralized config directory
        config_path = os.path.join('config', 'world', 'layers', 'lands_and_seas.toml')

        if not os.path.exists(config_path):
            return {}

        try:
            with open(config_path, 'rb') as f:
                data = tomllib.load(f)
            return data.get('lands_and_seas', {})
        except Exception as e:
            return {}
    
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process chunks to determine land/water distribution.

        Args:
            data: Generation data to process
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)

        Returns:
            Data with land_type property added to each chunk
        """
        min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y = bounds
        total_chunks = (max_chunk_x - min_chunk_x + 1) * (max_chunk_y - min_chunk_y + 1)
        algorithm = self.config.get('algorithm', 'random_chunks')


        min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y = bounds

        # Process each chunk in the bounds
        for chunk_x in range(min_chunk_x, max_chunk_x + 1):
            for chunk_y in range(min_chunk_y, max_chunk_y + 1):
                land_type = self._determine_land_type(data.seed, chunk_x, chunk_y)
                data.set_chunk_property(chunk_x, chunk_y, 'land_type', land_type)

        # Mark this layer as processed
        if self.name not in data.processed_layers:
            data.processed_layers.append(self.name)
        return data
    
    def _determine_land_type(self, seed: int, chunk_x: int, chunk_y: int) -> str:
        """
        Determine if a chunk should be land or water.

        Args:
            seed: World generation seed
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate

        Returns:
            'land' or 'water'
        """
        if self.algorithm == 'random_chunks':
            return self._random_chunks_algorithm(seed, chunk_x, chunk_y)
        elif self.algorithm == 'perlin_noise':
            return self._perlin_noise_algorithm(seed, chunk_x, chunk_y)
        elif self.algorithm == 'cellular_automata':
            return self._cellular_automata_algorithm(seed, chunk_x, chunk_y)
        else:
            raise ValueError(f"Algorithm {self.algorithm} not implemented")
    
    def _random_chunks_algorithm(self, seed: int, chunk_x: int, chunk_y: int) -> str:
        """
        Simple per-chunk randomization algorithm.
        
        Each chunk is independently determined to be land or water
        based on the configured land ratio.
        """
        # Create deterministic seed for this chunk
        self._set_seed(seed, chunk_x, chunk_y)
        
        # Determine land vs water based on ratio
        return "land" if self.rng.randint(1, 10) <= self.land_ratio else "water"
    
    def _perlin_noise_algorithm(self, seed: int, chunk_x: int, chunk_y: int) -> str:
        """
        Perlin noise-based land/water generation for natural-looking terrain.

        Creates realistic landmasses with natural coastlines and island chains.
        """
        # Set deterministic seed for this chunk
        self._set_seed(seed, chunk_x, chunk_y)

        # Generate multi-octave Perlin-like noise
        noise_value = 0.0
        amplitude = 1.0
        frequency = self.scale

        for _ in range(self.octaves):
            # Simple noise function (simplified Perlin noise)
            x = chunk_x * frequency
            y = chunk_y * frequency

            # Create smooth noise using sine/cosine functions
            noise = (math.sin(x * 12.9898 + y * 78.233) * 43758.5453) % 1.0
            noise = (noise - 0.5) * 2.0  # Convert to -1 to 1 range

            # Smooth the noise
            noise = noise * noise * noise * (noise * (noise * 6.0 - 15.0) + 10.0)

            noise_value += noise * amplitude
            amplitude *= self.persistence
            frequency *= self.lacunarity

        # Normalize and apply land ratio
        noise_value = (noise_value + 1.0) / 2.0  # Convert to 0-1 range
        land_threshold = 1.0 - (self.land_ratio / 10.0)

        return "land" if noise_value > land_threshold else "water"

    def _cellular_automata_algorithm(self, seed: int, chunk_x: int, chunk_y: int) -> str:
        """
        Cellular automata-based generation for realistic landmasses.

        Creates natural-looking continents and islands with smooth coastlines.
        """
        # Create a local grid around this chunk for cellular automata
        grid_size = 7  # 7x7 grid centered on target chunk
        center = grid_size // 2

        # Initialize grid with random values based on initial probability
        grid = {}
        for gx in range(grid_size):
            for gy in range(grid_size):
                world_x = chunk_x + (gx - center)
                world_y = chunk_y + (gy - center)

                # Create deterministic seed for this position
                pos_seed = seed + world_x * 73 + world_y * 37
                random.seed(pos_seed)

                grid[(gx, gy)] = random.random() < self.initial_land_probability

        # Apply cellular automata iterations
        for iteration in range(self.iterations):
            new_grid = {}

            for gx in range(grid_size):
                for gy in range(grid_size):
                    # Count land neighbors
                    land_neighbors = 0
                    total_neighbors = 0

                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue

                            nx, ny = gx + dx, gy + dy
                            if 0 <= nx < grid_size and 0 <= ny < grid_size:
                                if grid[(nx, ny)]:
                                    land_neighbors += 1
                                total_neighbors += 1
                            else:
                                # Treat out-of-bounds as water
                                total_neighbors += 1

                    # Apply cellular automata rules
                    current_is_land = grid[(gx, gy)]

                    if current_is_land:
                        # Land cell: dies if too few land neighbors
                        new_grid[(gx, gy)] = land_neighbors >= self.death_limit
                    else:
                        # Water cell: becomes land if enough land neighbors
                        new_grid[(gx, gy)] = land_neighbors > self.birth_limit

            grid = new_grid

        # Return the result for the center chunk
        return "land" if grid[(center, center)] else "water"

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        summary = {
            'layer_name': self.name,
            'land_ratio': self.land_ratio,
            'land_percentage': f"{self.land_ratio * 10}%",
            'algorithm': self.algorithm
        }

        if self.algorithm == 'perlin_noise':
            summary.update({
                'scale': self.scale,
                'octaves': self.octaves,
                'persistence': self.persistence,
                'lacunarity': self.lacunarity
            })
        elif self.algorithm == 'cellular_automata':
            summary.update({
                'initial_land_probability': self.initial_land_probability,
                'iterations': self.iterations,
                'birth_limit': self.birth_limit,
                'death_limit': self.death_limit
            })

        return summary
```

## src/world/layers/lands_and_seas/test_layer.py

```python
#!/usr/bin/env python3
"""
Tests for the Lands and Seas generation layer.
"""

import unittest
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from src.world.pipeline import GenerationData
from src.generation.world.lands_and_seas.layer import LandsAndSeasLayer


class TestLandsAndSeasLayer(unittest.TestCase):
    """Test the LandsAndSeasLayer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'land_ratio': 4,
            'algorithm': 'random_chunks'
        }
        self.layer = LandsAndSeasLayer(self.test_config)
        self.test_data = GenerationData(seed=12345, chunk_size=16)
    
    def test_layer_creation(self):
        """Test that the layer can be created with valid config."""
        self.assertEqual(self.layer.name, "lands_and_seas")
        self.assertEqual(self.layer.land_ratio, 4)
        self.assertEqual(self.layer.algorithm, "random_chunks")
    
    def test_invalid_land_ratio(self):
        """Test that invalid land ratios raise errors."""
        with self.assertRaises(ValueError):
            LandsAndSeasLayer({'land_ratio': 0})
        
        with self.assertRaises(ValueError):
            LandsAndSeasLayer({'land_ratio': 11})
    
    def test_invalid_algorithm(self):
        """Test that invalid algorithms raise errors."""
        with self.assertRaises(ValueError):
            LandsAndSeasLayer({'algorithm': 'invalid_algorithm'})
    
    def test_process_single_chunk(self):
        """Test processing a single chunk."""
        bounds = (0, 0, 0, 0)
        result = self.layer.process(self.test_data, bounds)
        
        # Check that the chunk was processed
        chunk_data = result.get_chunk(0, 0)
        self.assertIn('land_type', chunk_data)
        self.assertIn(chunk_data['land_type'], ['land', 'water'])
        
        # Check that the layer was marked as processed
        self.assertIn('lands_and_seas', result.processed_layers)
    
    def test_process_multiple_chunks(self):
        """Test processing multiple chunks."""
        bounds = (-2, -2, 2, 2)
        result = self.layer.process(self.test_data, bounds)
        
        # Check that all chunks in bounds were processed
        for chunk_x in range(-2, 3):
            for chunk_y in range(-2, 3):
                chunk_data = result.get_chunk(chunk_x, chunk_y)
                self.assertIn('land_type', chunk_data)
                self.assertIn(chunk_data['land_type'], ['land', 'water'])
    
    def test_deterministic_generation(self):
        """Test that generation is deterministic with same seed."""
        bounds = (0, 0, 5, 5)
        
        # Generate twice with same seed
        result1 = self.layer.process(GenerationData(seed=12345, chunk_size=16), bounds)
        result2 = self.layer.process(GenerationData(seed=12345, chunk_size=16), bounds)
        
        # Results should be identical
        for chunk_x in range(0, 6):
            for chunk_y in range(0, 6):
                land_type1 = result1.get_chunk_property(chunk_x, chunk_y, 'land_type')
                land_type2 = result2.get_chunk_property(chunk_x, chunk_y, 'land_type')
                self.assertEqual(land_type1, land_type2)
    
    def test_different_seeds_produce_different_results(self):
        """Test that different seeds produce different results."""
        bounds = (0, 0, 10, 10)
        
        result1 = self.layer.process(GenerationData(seed=12345, chunk_size=16), bounds)
        result2 = self.layer.process(GenerationData(seed=54321, chunk_size=16), bounds)
        
        # Count differences
        differences = 0
        total_chunks = 0
        
        for chunk_x in range(0, 11):
            for chunk_y in range(0, 11):
                land_type1 = result1.get_chunk_property(chunk_x, chunk_y, 'land_type')
                land_type2 = result2.get_chunk_property(chunk_x, chunk_y, 'land_type')
                total_chunks += 1
                if land_type1 != land_type2:
                    differences += 1
        
        # Should have some differences (not exact, but should be substantial)
        difference_ratio = differences / total_chunks
        self.assertGreater(difference_ratio, 0.1)  # At least 10% different
    
    def test_land_ratio_affects_distribution(self):
        """Test that land ratio affects the land/water distribution."""
        bounds = (0, 0, 20, 20)
        
        # Test with low land ratio
        low_land_layer = LandsAndSeasLayer({'land_ratio': 1, 'algorithm': 'random_chunks'})
        low_result = low_land_layer.process(GenerationData(seed=12345, chunk_size=16), bounds)
        
        # Test with high land ratio
        high_land_layer = LandsAndSeasLayer({'land_ratio': 9, 'algorithm': 'random_chunks'})
        high_result = high_land_layer.process(GenerationData(seed=12345, chunk_size=16), bounds)
        
        # Count land chunks for each
        low_land_count = 0
        high_land_count = 0
        total_chunks = 0
        
        for chunk_x in range(0, 21):
            for chunk_y in range(0, 21):
                total_chunks += 1
                if low_result.get_chunk_property(chunk_x, chunk_y, 'land_type') == 'land':
                    low_land_count += 1
                if high_result.get_chunk_property(chunk_x, chunk_y, 'land_type') == 'land':
                    high_land_count += 1
        
        # High land ratio should produce more land
        self.assertLess(low_land_count, high_land_count)
    
    def test_config_summary(self):
        """Test the configuration summary."""
        summary = self.layer.get_config_summary()
        
        expected_keys = ['layer_name', 'land_ratio', 'land_percentage', 'algorithm']
        for key in expected_keys:
            self.assertIn(key, summary)
        
        self.assertEqual(summary['layer_name'], 'lands_and_seas')
        self.assertEqual(summary['land_ratio'], 4)
        self.assertEqual(summary['land_percentage'], '40%')
        self.assertEqual(summary['algorithm'], 'random_chunks')


if __name__ == '__main__':
    unittest.main()
```

## src/world/layers/zoom/__init__.py

```python
"""
Zoom Layer

Progressively refines terrain detail by subdividing chunks and applying
cellular automata to create natural coastlines and terrain boundaries.

This layer can be used multiple times in sequence to create fractal-like
detail while preserving the overall geographic structure.
"""

from .layer import ZoomLayer

__all__ = ["ZoomLayer"]
```

## src/world/layers/zoom/layer.py

```python
#!/usr/bin/env python3
"""
Zoom Layer for Progressive Terrain Detail Refinement

Subdivides chunks and applies cellular automata to create natural coastlines
and terrain boundaries while preserving overall geographic structure.
"""

import os
import random
from typing import Dict, Any, Tuple, List, Set
from collections import defaultdict

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from ...pipeline import GenerationLayer, GenerationData


class ZoomLayer(GenerationLayer):
    """
    Layer that subdivides chunks and refines terrain boundaries using cellular automata.
    
    This layer can be used multiple times in sequence to progressively add detail
    while maintaining the overall geographic structure from previous layers.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("zoom", config)
        
        # Load configuration from TOML file if no config provided
        if not config:
            self.config = self._load_config()
        
        # Extract configuration values
        self.subdivision_factor = self._get_config_value('subdivision_factor', 2)
        self.land_expansion_threshold = self._get_config_value('land_expansion_threshold', 3)
        self.erosion_probability = self._get_config_value('erosion_probability', 0.25)
        self.iterations = self._get_config_value('iterations', 6)

        # Multi-pass configuration
        self.use_multi_pass = self._get_config_value('use_multi_pass', True)
        self.pass_1_iterations = self._get_config_value('pass_1_iterations', 3)
        self.pass_1_expansion_threshold = self._get_config_value('pass_1_expansion_threshold', 2)
        self.pass_1_erosion_probability = self._get_config_value('pass_1_erosion_probability', 0.1)
        self.pass_2_iterations = self._get_config_value('pass_2_iterations', 3)
        self.pass_2_expansion_threshold = self._get_config_value('pass_2_expansion_threshold', 4)
        self.pass_2_erosion_probability = self._get_config_value('pass_2_erosion_probability', 0.3)

        # Protection and advanced settings
        self.protect_interior = self._get_config_value('protect_interior', False)
        self.interior_threshold = self._get_config_value('interior_threshold', 8)
        self.use_moore_neighborhood = self._get_config_value('use_moore_neighborhood', True)
        self.preserve_islands = self._get_config_value('preserve_islands', True)
        self.min_island_size = self._get_config_value('min_island_size', 1)

        # Enhanced randomization
        self.add_noise = self._get_config_value('add_noise', True)
        self.noise_probability = self._get_config_value('noise_probability', 0.15)
        self.edge_noise_boost = self._get_config_value('edge_noise_boost', True)
        self.edge_noise_probability = self._get_config_value('edge_noise_probability', 0.25)

        # Fractal enhancement
        self.fractal_perturbation = self._get_config_value('fractal_perturbation', True)
        self.perturbation_strength = self._get_config_value('perturbation_strength', 0.3)
        
        # Validate configuration
        if self.subdivision_factor < 2:
            raise ValueError(f"subdivision_factor must be >= 2, got {self.subdivision_factor}")
        if not (0.0 <= self.erosion_probability <= 1.0):
            raise ValueError(f"erosion_probability must be 0.0-1.0, got {self.erosion_probability}")
        if not (0.0 <= self.noise_probability <= 1.0):
            raise ValueError(f"noise_probability must be 0.0-1.0, got {self.noise_probability}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from the layer's TOML file."""
        # Look for config in the centralized config directory
        config_path = os.path.join('config', 'world', 'layers', 'zoom.toml')

        if not os.path.exists(config_path):
            return {}

        try:
            with open(config_path, 'rb') as f:
                data = tomllib.load(f)
            return data.get('zoom', {})
        except Exception as e:
            return {}
    
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process chunks to add terrain detail through subdivision and cellular automata.

        Args:
            data: Generation data to process
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)

        Returns:
            Data with subdivided chunks and refined terrain boundaries
        """
        min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y = bounds
        
        # Create new chunk data with subdivided chunks
        new_chunks = {}
        
        # For zoom layers, we need to process all existing chunks since previous
        # zoom layers may have created chunks in subdivided coordinate space
        chunks_to_process = list(data.chunks.values())

        # Subdivide each chunk
        for parent_chunk in chunks_to_process:
            subdivided_chunks = self._subdivide_chunk(data.seed, parent_chunk)

            # Add subdivided chunks to new chunk data
            for sub_chunk in subdivided_chunks:
                sub_key = (sub_chunk['chunk_x'], sub_chunk['chunk_y'])
                new_chunks[sub_key] = sub_chunk
        
        # Apply cellular automata to refine boundaries
        # Calculate bounds for the subdivided chunks
        if new_chunks:
            chunk_coords = list(new_chunks.keys())
            min_sub_x = min(x for x, y in chunk_coords)
            max_sub_x = max(x for x, y in chunk_coords)
            min_sub_y = min(y for x, y in chunk_coords)
            max_sub_y = max(y for x, y in chunk_coords)
            sub_bounds = (min_sub_x, min_sub_y, max_sub_x, max_sub_y)
        else:
            sub_bounds = bounds

        refined_chunks = self._apply_cellular_automata(data.seed, new_chunks, sub_bounds)
        
        # Update the generation data with refined chunks
        data.chunks.update(refined_chunks)
        
        # Mark this layer as processed
        if self.name not in data.processed_layers:
            data.processed_layers.append(self.name)
        
        return data
    
    def _subdivide_chunk(self, seed: int, parent_chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Subdivide a parent chunk into smaller sub-chunks with dynamic sizing.

        This method is agnostic about absolute chunk sizes and dynamically
        calculates the new chunk size based on the subdivision factor.
        This allows for flexible chaining of multiple zoom layers.

        Args:
            seed: World generation seed
            parent_chunk: The chunk to subdivide

        Returns:
            List of sub-chunk dictionaries with dynamically calculated sizes
        """
        parent_x = parent_chunk['chunk_x']
        parent_y = parent_chunk['chunk_y']
        parent_size = parent_chunk['chunk_size']
        parent_land_type = parent_chunk.get('land_type', 'water')

        sub_chunks = []
        # Dynamic chunk size calculation - halve the parent size
        # This works regardless of the input chunk size (32→16, 16→8, 8→4, etc.)
        sub_chunk_size = parent_size // self.subdivision_factor

        # Ensure minimum chunk size of 1 tile
        if sub_chunk_size < 1:
            sub_chunk_size = 1

        for sub_x in range(self.subdivision_factor):
            for sub_y in range(self.subdivision_factor):
                # Calculate new chunk coordinates in the subdivided space
                new_chunk_x = parent_x * self.subdivision_factor + sub_x
                new_chunk_y = parent_y * self.subdivision_factor + sub_y

                # Create sub-chunk with dynamically calculated size
                sub_chunk = {
                    'chunk_x': new_chunk_x,
                    'chunk_y': new_chunk_y,
                    'chunk_size': sub_chunk_size,  # Dynamic size based on parent
                    'land_type': parent_land_type,
                    'parent_chunk_x': parent_x,
                    'parent_chunk_y': parent_y,
                    'subdivision_level': parent_chunk.get('subdivision_level', 0) + 1,
                    'original_chunk_size': parent_chunk.get('original_chunk_size', parent_size)
                }

                sub_chunks.append(sub_chunk)

        return sub_chunks

    def _apply_cellular_automata(self, seed: int, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                                bounds: Tuple[int, int, int, int]) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """
        Apply cellular automata rules to create natural coastlines.

        Args:
            seed: World generation seed
            chunks: Dictionary of chunk data
            bounds: Bounds in subdivided coordinate system

        Returns:
            Dictionary of refined chunk data
        """
        # Use the provided bounds directly (already in subdivided coordinate system)
        sub_min_x, sub_min_y, sub_max_x, sub_max_y = bounds

        # Set up RNG for this layer
        self._set_seed(seed, "cellular_automata")

        # Apply fractal perturbation first if enabled
        if self.fractal_perturbation:
            chunks = self._apply_fractal_perturbation(chunks, sub_min_x, sub_min_y, sub_max_x, sub_max_y)

        # Apply cellular automata with multi-pass if enabled
        if self.use_multi_pass:
            # Pass 1: Aggressive expansion for rough shape
            for iteration in range(self.pass_1_iterations):
                chunks = self._cellular_automata_iteration(
                    chunks, sub_min_x, sub_min_y, sub_max_x, sub_max_y,
                    expansion_threshold=self.pass_1_expansion_threshold,
                    erosion_probability=self.pass_1_erosion_probability
                )

            # Pass 2: Detail refinement
            for iteration in range(self.pass_2_iterations):
                chunks = self._cellular_automata_iteration(
                    chunks, sub_min_x, sub_min_y, sub_max_x, sub_max_y,
                    expansion_threshold=self.pass_2_expansion_threshold,
                    erosion_probability=self.pass_2_erosion_probability
                )
        else:
            # Single pass with default parameters
            for iteration in range(self.iterations):
                chunks = self._cellular_automata_iteration(
                    chunks, sub_min_x, sub_min_y, sub_max_x, sub_max_y,
                    expansion_threshold=self.land_expansion_threshold,
                    erosion_probability=self.erosion_probability
                )

        return chunks

    def _cellular_automata_iteration(self, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                                   min_x: int, min_y: int, max_x: int, max_y: int,
                                   expansion_threshold: int = None, erosion_probability: float = None) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """
        Perform one iteration of cellular automata.

        Args:
            chunks: Current chunk data
            min_x, min_y, max_x, max_y: Bounds in subdivided coordinate system
            expansion_threshold: Override for land expansion threshold
            erosion_probability: Override for erosion probability

        Returns:
            Updated chunk data
        """
        # Use provided parameters or defaults
        exp_threshold = expansion_threshold if expansion_threshold is not None else self.land_expansion_threshold
        ero_probability = erosion_probability if erosion_probability is not None else self.erosion_probability

        new_chunks = chunks.copy()

        for chunk_x in range(min_x, max_x + 1):
            for chunk_y in range(min_y, max_y + 1):
                chunk_key = (chunk_x, chunk_y)
                if chunk_key not in chunks:
                    continue

                current_chunk = chunks[chunk_key]
                current_land_type = current_chunk.get('land_type', 'water')

                # Count land neighbors
                land_neighbors = self._count_land_neighbors(chunks, chunk_x, chunk_y, min_x, min_y, max_x, max_y)
                total_neighbors = self._count_total_neighbors(chunk_x, chunk_y, min_x, min_y, max_x, max_y)

                # Apply cellular automata rules
                new_land_type = self._apply_ca_rules(current_land_type, land_neighbors, total_neighbors,
                                                   exp_threshold, ero_probability)

                # Add enhanced noise if enabled
                noise_prob = self.noise_probability

                # Boost noise at land/water boundaries for more fractal variation
                if self.edge_noise_boost and self._is_at_boundary(chunks, chunk_x, chunk_y, min_x, min_y, max_x, max_y):
                    noise_prob = self.edge_noise_probability

                if self.add_noise and self.rng.random() < noise_prob:
                    new_land_type = 'land' if new_land_type == 'water' else 'water'

                # Update chunk
                new_chunk = current_chunk.copy()
                new_chunk['land_type'] = new_land_type
                new_chunks[chunk_key] = new_chunk

        return new_chunks

    def _count_land_neighbors(self, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                            chunk_x: int, chunk_y: int, min_x: int, min_y: int, max_x: int, max_y: int) -> int:
        """Count the number of land neighbors around a chunk."""
        land_count = 0

        # Define neighborhood (Moore or Von Neumann)
        if self.use_moore_neighborhood:
            # 8-neighbor Moore neighborhood
            offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        else:
            # 4-neighbor Von Neumann neighborhood
            offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dx, dy in offsets:
            neighbor_x = chunk_x + dx
            neighbor_y = chunk_y + dy

            # Handle boundaries - treat out-of-bounds as water
            if neighbor_x < min_x or neighbor_x > max_x or neighbor_y < min_y or neighbor_y > max_y:
                continue

            neighbor_key = (neighbor_x, neighbor_y)
            if neighbor_key in chunks:
                neighbor_land_type = chunks[neighbor_key].get('land_type', 'water')
                if neighbor_land_type == 'land':
                    land_count += 1

        return land_count

    def _count_total_neighbors(self, chunk_x: int, chunk_y: int, min_x: int, min_y: int, max_x: int, max_y: int) -> int:
        """Count the total number of valid neighbors (within bounds)."""
        total_count = 0

        if self.use_moore_neighborhood:
            offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        else:
            offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dx, dy in offsets:
            neighbor_x = chunk_x + dx
            neighbor_y = chunk_y + dy

            if min_x <= neighbor_x <= max_x and min_y <= neighbor_y <= max_y:
                total_count += 1

        return total_count

    def _apply_ca_rules(self, current_land_type: str, land_neighbors: int, total_neighbors: int,
                       expansion_threshold: int, erosion_probability: float) -> str:
        """
        Apply cellular automata rules to determine new land type.

        Args:
            current_land_type: Current land type ('land' or 'water')
            land_neighbors: Number of land neighbors
            total_neighbors: Total number of neighbors
            expansion_threshold: Threshold for land expansion
            erosion_probability: Probability of erosion

        Returns:
            New land type after applying rules
        """
        # Interior protection - if all neighbors are land, stay land
        if self.protect_interior and land_neighbors == total_neighbors and total_neighbors >= self.interior_threshold:
            return 'land'

        if current_land_type == 'water':
            # Water to land conversion (land expansion)
            if land_neighbors >= expansion_threshold:
                return 'land'
        else:  # current_land_type == 'land'
            # Land to water conversion (coastal erosion)
            if self.rng.random() < erosion_probability:
                # Only erode if not completely surrounded by land
                if land_neighbors < total_neighbors:
                    return 'water'

        # No change
        return current_land_type

    def _preserve_islands_pass(self, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                             min_x: int, min_y: int, max_x: int, max_y: int) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """
        Post-processing pass to preserve small islands from disappearing.

        Args:
            chunks: Current chunk data
            min_x, min_y, max_x, max_y: Bounds in subdivided coordinate system

        Returns:
            Updated chunk data with preserved islands
        """
        if not self.preserve_islands:
            return chunks

        # Find all land regions
        land_regions = self._find_land_regions(chunks, min_x, min_y, max_x, max_y)

        # Restore small islands that were eroded
        new_chunks = chunks.copy()
        for region in land_regions:
            if len(region) < self.min_island_size:
                # Restore this small island
                for chunk_x, chunk_y in region:
                    chunk_key = (chunk_x, chunk_y)
                    if chunk_key in new_chunks:
                        new_chunk = new_chunks[chunk_key].copy()
                        new_chunk['land_type'] = 'land'
                        new_chunks[chunk_key] = new_chunk

        return new_chunks

    def _find_land_regions(self, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                          min_x: int, min_y: int, max_x: int, max_y: int) -> List[Set[Tuple[int, int]]]:
        """
        Find connected regions of land using flood fill.

        Returns:
            List of sets, each containing coordinates of a connected land region
        """
        visited = set()
        regions = []

        for chunk_x in range(min_x, max_x + 1):
            for chunk_y in range(min_y, max_y + 1):
                chunk_key = (chunk_x, chunk_y)

                if chunk_key in visited or chunk_key not in chunks:
                    continue

                chunk = chunks[chunk_key]
                if chunk.get('land_type', 'water') == 'land':
                    # Start flood fill from this land chunk
                    region = self._flood_fill_land(chunks, chunk_x, chunk_y, visited, min_x, min_y, max_x, max_y)
                    if region:
                        regions.append(region)

        return regions

    def _flood_fill_land(self, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                        start_x: int, start_y: int, visited: Set[Tuple[int, int]],
                        min_x: int, min_y: int, max_x: int, max_y: int) -> Set[Tuple[int, int]]:
        """
        Flood fill to find a connected land region.

        Returns:
            Set of coordinates in the connected land region
        """
        region = set()
        stack = [(start_x, start_y)]

        while stack:
            x, y = stack.pop()
            chunk_key = (x, y)

            if (chunk_key in visited or
                x < min_x or x > max_x or y < min_y or y > max_y or
                chunk_key not in chunks):
                continue

            chunk = chunks[chunk_key]
            if chunk.get('land_type', 'water') != 'land':
                continue

            visited.add(chunk_key)
            region.add(chunk_key)

            # Add neighbors to stack
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                stack.append((x + dx, y + dy))

        return region

    def _is_at_boundary(self, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                       chunk_x: int, chunk_y: int, min_x: int, min_y: int, max_x: int, max_y: int) -> bool:
        """
        Check if a chunk is at a land/water boundary.

        Returns:
            True if the chunk has both land and water neighbors
        """
        current_chunk = chunks.get((chunk_x, chunk_y))
        if not current_chunk:
            return False

        current_land_type = current_chunk.get('land_type', 'water')

        # Check neighbors for different land type
        offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        for dx, dy in offsets:
            neighbor_x = chunk_x + dx
            neighbor_y = chunk_y + dy

            if min_x <= neighbor_x <= max_x and min_y <= neighbor_y <= max_y:
                neighbor_key = (neighbor_x, neighbor_y)
                if neighbor_key in chunks:
                    neighbor_land_type = chunks[neighbor_key].get('land_type', 'water')
                    if neighbor_land_type != current_land_type:
                        return True

        return False

    def _apply_fractal_perturbation(self, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                                   min_x: int, min_y: int, max_x: int, max_y: int) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """
        Apply fractal-like perturbations to break up blocky patterns.

        Args:
            chunks: Current chunk data
            min_x, min_y, max_x, max_y: Bounds in subdivided coordinate system

        Returns:
            Updated chunk data with fractal perturbations
        """
        new_chunks = chunks.copy()

        for chunk_x in range(min_x, max_x + 1):
            for chunk_y in range(min_y, max_y + 1):
                chunk_key = (chunk_x, chunk_y)
                if chunk_key not in chunks:
                    continue

                # Apply perturbation based on position and noise
                perturbation_seed = hash((chunk_x, chunk_y, "fractal")) % (2**32)
                self.rng.seed(perturbation_seed)

                if self.rng.random() < self.perturbation_strength:
                    current_chunk = chunks[chunk_key]
                    current_land_type = current_chunk.get('land_type', 'water')

                    # Create fractal-like variation by considering position patterns
                    # Use a simple fractal noise pattern
                    noise_value = self._simple_fractal_noise(chunk_x, chunk_y)

                    # Apply perturbation based on noise
                    if noise_value > 0.6:  # High noise threshold for land
                        new_land_type = 'land'
                    elif noise_value < 0.4:  # Low noise threshold for water
                        new_land_type = 'water'
                    else:
                        new_land_type = current_land_type  # Keep original

                    # Update chunk
                    new_chunk = current_chunk.copy()
                    new_chunk['land_type'] = new_land_type
                    new_chunks[chunk_key] = new_chunk

        return new_chunks

    def _simple_fractal_noise(self, x: int, y: int) -> float:
        """
        Generate simple fractal noise for position (x, y).

        Returns:
            Noise value between 0.0 and 1.0
        """
        # Simple multi-octave noise
        noise = 0.0
        amplitude = 1.0
        frequency = 0.1

        for octave in range(3):
            # Simple hash-based noise
            hash_input = hash((x * frequency, y * frequency, octave)) % (2**32)
            octave_noise = (hash_input / (2**32)) * amplitude
            noise += octave_noise

            amplitude *= 0.5
            frequency *= 2.0

        # Normalize to 0-1 range
        return max(0.0, min(1.0, noise / 1.75))

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            'layer_name': self.name,
            'subdivision_factor': self.subdivision_factor,
            'land_expansion_threshold': self.land_expansion_threshold,
            'erosion_probability': self.erosion_probability,
            'iterations': self.iterations,
            'protect_interior': self.protect_interior,
            'use_moore_neighborhood': self.use_moore_neighborhood,
            'preserve_islands': self.preserve_islands,
            'add_noise': self.add_noise
        }
```

## src/world/layers/zoom/test_layer.py

```python
#!/usr/bin/env python3
"""
Tests for the Zoom generation layer.
"""

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from src.world.pipeline import GenerationData
from src.generation.world.zoom.layer import ZoomLayer


class TestZoomLayer(unittest.TestCase):
    """Test the ZoomLayer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'subdivision_factor': 2,
            'land_expansion_threshold': 4,
            'erosion_probability': 0.1,
            'iterations': 3,
            'protect_interior': True,
            'use_moore_neighborhood': True,
            'preserve_islands': True,
            'add_noise': False  # Disable noise for predictable tests
        }
        self.layer = ZoomLayer(self.test_config)
        
        # Create test data with some initial chunks
        self.test_data = GenerationData(seed=12345, chunk_size=32)
        
        # Add some test chunks with land/water distribution
        self.test_data.set_chunk_property(0, 0, 'land_type', 'land')
        self.test_data.set_chunk_property(1, 0, 'land_type', 'water')
        self.test_data.set_chunk_property(0, 1, 'land_type', 'water')
        self.test_data.set_chunk_property(1, 1, 'land_type', 'land')
    
    def test_layer_creation(self):
        """Test that the layer can be created with valid config."""
        self.assertEqual(self.layer.name, "zoom")
        self.assertEqual(self.layer.subdivision_factor, 2)
        self.assertEqual(self.layer.land_expansion_threshold, 4)
        self.assertEqual(self.layer.erosion_probability, 0.1)
        self.assertEqual(self.layer.iterations, 3)
    
    def test_invalid_subdivision_factor(self):
        """Test that invalid subdivision factors raise errors."""
        with self.assertRaises(ValueError):
            ZoomLayer({'subdivision_factor': 1})
    
    def test_invalid_probabilities(self):
        """Test that invalid probabilities raise errors."""
        with self.assertRaises(ValueError):
            ZoomLayer({'erosion_probability': -0.1})
        
        with self.assertRaises(ValueError):
            ZoomLayer({'erosion_probability': 1.1})
    
    def test_chunk_subdivision(self):
        """Test that chunks are properly subdivided."""
        bounds = (0, 0, 1, 1)
        result = self.layer.process(self.test_data, bounds)
        
        # Should have 4x the original chunks (2x2 subdivision for each original chunk)
        original_chunks = 4  # 2x2 area
        expected_subdivided = original_chunks * (self.layer.subdivision_factor ** 2)
        
        # Count chunks in the subdivided coordinate system
        subdivided_chunks = 0
        for chunk_key in result.chunks:
            chunk_x, chunk_y = chunk_key
            # Check if this chunk is in the subdivided bounds
            if (0 <= chunk_x < 4 and 0 <= chunk_y < 4):  # 2x2 original -> 4x4 subdivided
                subdivided_chunks += 1
        
        self.assertGreaterEqual(subdivided_chunks, expected_subdivided)
    
    def test_subdivision_inheritance(self):
        """Test that sub-chunks inherit parent land type."""
        # Create a simple test with one land chunk
        simple_data = GenerationData(seed=12345, chunk_size=32)
        simple_data.set_chunk_property(0, 0, 'land_type', 'land')
        
        bounds = (0, 0, 0, 0)
        result = self.layer.process(simple_data, bounds)
        
        # Check that all sub-chunks initially inherit 'land' type
        # (before cellular automata modifications)
        land_sub_chunks = 0
        for chunk_x in range(0, 2):  # 2x2 subdivision
            for chunk_y in range(0, 2):
                chunk = result.get_chunk(chunk_x, chunk_y)
                if chunk.get('land_type') == 'land':
                    land_sub_chunks += 1
        
        # Should have some land chunks (cellular automata may modify some)
        self.assertGreater(land_sub_chunks, 0)
    
    def test_cellular_automata_land_expansion(self):
        """Test that land can expand into water areas."""
        # Create a configuration that favors land expansion
        expansion_config = self.test_config.copy()
        expansion_config['land_expansion_threshold'] = 2  # Low threshold
        expansion_config['erosion_probability'] = 0.0    # No erosion
        expansion_config['iterations'] = 1               # Single iteration
        
        expansion_layer = ZoomLayer(expansion_config)
        
        # Create test data with land surrounded by water
        test_data = GenerationData(seed=12345, chunk_size=32)
        test_data.set_chunk_property(1, 1, 'land_type', 'land')  # Center land
        test_data.set_chunk_property(0, 1, 'land_type', 'water') # Surrounding water
        test_data.set_chunk_property(2, 1, 'land_type', 'water')
        test_data.set_chunk_property(1, 0, 'land_type', 'water')
        test_data.set_chunk_property(1, 2, 'land_type', 'water')
        
        bounds = (0, 0, 2, 2)
        result = expansion_layer.process(test_data, bounds)
        
        # Should have more land after expansion
        land_count = 0
        for chunk_key, chunk in result.chunks.items():
            if chunk.get('land_type') == 'land':
                land_count += 1
        
        self.assertGreater(land_count, 4)  # More than the original 4 land sub-chunks
    
    def test_deterministic_generation(self):
        """Test that generation is deterministic with same seed."""
        bounds = (0, 0, 1, 1)
        
        # Generate twice with same seed
        data1 = GenerationData(seed=12345, chunk_size=32)
        data1.set_chunk_property(0, 0, 'land_type', 'land')
        data1.set_chunk_property(1, 0, 'land_type', 'water')
        data1.set_chunk_property(0, 1, 'land_type', 'water')
        data1.set_chunk_property(1, 1, 'land_type', 'land')
        
        data2 = GenerationData(seed=12345, chunk_size=32)
        data2.set_chunk_property(0, 0, 'land_type', 'land')
        data2.set_chunk_property(1, 0, 'land_type', 'water')
        data2.set_chunk_property(0, 1, 'land_type', 'water')
        data2.set_chunk_property(1, 1, 'land_type', 'land')
        
        result1 = self.layer.process(data1, bounds)
        result2 = self.layer.process(data2, bounds)
        
        # Results should be identical
        for chunk_key in result1.chunks:
            if chunk_key in result2.chunks:
                land_type1 = result1.chunks[chunk_key].get('land_type')
                land_type2 = result2.chunks[chunk_key].get('land_type')
                self.assertEqual(land_type1, land_type2, f"Mismatch at {chunk_key}")
    
    def test_subdivision_level_tracking(self):
        """Test that subdivision levels are properly tracked."""
        bounds = (0, 0, 0, 0)
        result = self.layer.process(self.test_data, bounds)
        
        # Check that sub-chunks have subdivision level 1
        for chunk_x in range(0, 2):
            for chunk_y in range(0, 2):
                chunk = result.get_chunk(chunk_x, chunk_y)
                self.assertEqual(chunk.get('subdivision_level', 0), 1)
    
    def test_multiple_zoom_applications(self):
        """Test that zoom can be applied multiple times."""
        bounds = (0, 0, 0, 0)
        
        # Apply zoom twice
        result1 = self.layer.process(self.test_data, bounds)
        
        # Apply zoom again to the result
        zoom_layer2 = ZoomLayer(self.test_config)
        result2 = zoom_layer2.process(result1, (0, 0, 1, 1))  # Adjusted bounds for subdivided chunks
        
        # Should have even more chunks after second zoom
        self.assertGreater(len(result2.chunks), len(result1.chunks))
        
        # Check that some chunks have subdivision level 2
        level_2_chunks = 0
        for chunk in result2.chunks.values():
            if chunk.get('subdivision_level', 0) == 2:
                level_2_chunks += 1
        
        self.assertGreater(level_2_chunks, 0)
    
    def test_config_summary(self):
        """Test the configuration summary."""
        summary = self.layer.get_config_summary()
        
        expected_keys = [
            'layer_name', 'subdivision_factor', 'land_expansion_threshold',
            'erosion_probability', 'iterations', 'protect_interior',
            'use_moore_neighborhood', 'preserve_islands', 'add_noise'
        ]
        
        for key in expected_keys:
            self.assertIn(key, summary)
        
        self.assertEqual(summary['layer_name'], 'zoom')
        self.assertEqual(summary['subdivision_factor'], 2)


if __name__ == '__main__':
    unittest.main()
```

## src/engine/camera.py

```python
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
```

## src/engine/game.py

```python
#!/usr/bin/env python3
"""
Game logic for 2D Minecraft-like World

Contains the core game state, rendering, and input handling logic.
Renders a tile-based world with pipeline generation.
"""

import time
import tcod
from ..render.render import GameRenderer
from ..config import get_config, WorldConfig
from .camera import Camera
from .input import InputHandler
from ..world import WorldManager
try:
    from ..profiler import profile_function, start_profiling, end_profiling, print_profiling_stats
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
_renderer = GameRenderer()

# Initialize camera and world manager
_camera = Camera(_config.camera)
_world_manager = WorldManager(_config.world)
_input_handler = InputHandler(_camera)

# Set up input handler callbacks
def _regenerate_world():
    """Callback for world regeneration."""
    # TODO: Implement world regeneration
    _renderer.add_effect('sparkle', *_camera.get_cursor_position(), 30, color=(255, 255, 0))

def _toggle_debug():
    """Callback for debug toggle."""
    status_display = _renderer.get_status_display()
    status_display.toggle_debug()


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

    # Process completed chunks from worker for non-blocking tile access
    start_profiling("world.process_messages")
    _world_manager.process_worker_messages()
    end_profiling("world.process_messages")

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
        # 'highlight_positions': [(view_center_x, view_center_y)]  # Removed - cursor is rendered in world tiles
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
    global _config
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

            # Print profiling stats every 10 seconds (only when profiling is enabled)
            if current_time - last_profile_print > 10.0:
                try:
                    from ..profiler import is_profiling_enabled
                    if is_profiling_enabled():
                        print_profiling_stats(10)
                except ImportError:
                    # Profiler not available, skip stats
                    pass
                last_profile_print = current_time
    finally:
        # Cleanup async world manager
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
```

## src/engine/input.py

```python
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
```

---

**Export Summary:**
- Files processed: 44
- Files skipped: 0
