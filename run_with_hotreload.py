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
