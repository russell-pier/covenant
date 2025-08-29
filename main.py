#!/usr/bin/env python3
"""
Main entry point for 2D Minecraft-like World Application

Simple entry point that imports and runs the game.
Separated from game logic for better organization.
"""

import argparse
import sys
from src.game import run_game


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
        print("🔍 Performance profiling enabled")

    try:
        run_game()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Exiting gracefully...")
    except Exception as e:
        print(f"An error occurred: {e}")
        return 1
    finally:
        print("Application terminated.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
