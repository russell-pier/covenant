# 2D Minecraft-like World Generator

A tile-based 2D world generation and rendering system using python-tcod with hot reloading support.

## Features

- **Spiral World Generation**: Counter-clockwise spiral tile generation pattern
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
│   │   └── spiral.py      # Spiral pattern generator
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
- **R**: Regenerate world with new spiral pattern
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
- **`src/generators/`** - World generation algorithms (spiral pattern)
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