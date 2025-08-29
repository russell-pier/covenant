#!/usr/bin/env python3
"""
Main entry point for 2D Minecraft-like World Application

Simple entry point that imports and runs the game.
Separated from game logic for better organization.
"""

from src.engine import run_game


if __name__ == "__main__":
    try:
        run_game()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Exiting gracefully...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Application terminated.")
