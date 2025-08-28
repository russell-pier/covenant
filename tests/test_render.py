#!/usr/bin/env python3
"""
Tests for rendering components

Unit tests for the rendering system and coordinate conversion.
"""

import unittest
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.render import GameRenderer, WorldRenderer, EffectRenderer
from src.generators.spiral import Tile, WorldGenerator


class MockConsole:
    """Mock console for testing rendering without tcod dependency."""
    
    def __init__(self, width=80, height=50):
        self.width = width
        self.height = height
        self.printed_chars = []
        self.cleared = False
    
    def print(self, x, y, text, fg=None, bg=None):
        """Mock print method that records what was printed."""
        self.printed_chars.append({
            'x': x, 'y': y, 'text': text, 'fg': fg, 'bg': bg
        })
    
    def clear(self, fg=None, bg=None):
        """Mock clear method."""
        self.cleared = True
        self.printed_chars.clear()


class MockWorldGenerator:
    """Mock world generator for testing."""

    def __init__(self):
        self.tiles = {}
        self.default_tile = Tile(0, 0, "stone")

    def get_tile(self, x, y):
        """Return a test tile."""
        return self.tiles.get((x, y), self.default_tile)

    def add_tile(self, x, y, tile):
        """Add a tile for testing."""
        self.tiles[(x, y)] = tile


class TestWorldRenderer(unittest.TestCase):
    """Test the WorldRenderer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.renderer = WorldRenderer()
        self.console = MockConsole(10, 10)
        self.world_gen = MockWorldGenerator()
    
    def test_renderer_creation(self):
        """Test that renderer can be created."""
        self.assertIsInstance(self.renderer, WorldRenderer)
    
    def test_render_world_basic(self):
        """Test basic world rendering."""
        # Add a special tile at world position (0, 0)
        special_tile = Tile(0, 0, "center_marker")
        self.world_gen.add_tile(0, 0, special_tile)

        # Render with view centered at (0, 0)
        self.renderer.render_world(self.console, self.world_gen, 0, 0)

        # Should have printed something for each console position
        self.assertEqual(len(self.console.printed_chars), 100)  # 10x10 console

        # The center tile (5, 5) should be our special tile
        center_print = next(p for p in self.console.printed_chars
                           if p['x'] == 5 and p['y'] == 5)
        self.assertEqual(center_print['text'], '.')  # center_marker character
        self.assertEqual(center_print['fg'], (255, 255, 0))  # yellow
        self.assertEqual(center_print['bg'], (128, 128, 128))  # gray
    
    def test_render_tile_at_screen_pos(self):
        """Test rendering a tile at a specific screen position."""
        tile = Tile(0, 0, "center_marker")
        self.renderer.render_tile_at_screen_pos(self.console, tile, 3, 4)

        self.assertEqual(len(self.console.printed_chars), 1)
        printed = self.console.printed_chars[0]
        self.assertEqual(printed['x'], 3)
        self.assertEqual(printed['y'], 4)
        self.assertEqual(printed['text'], '.')  # center_marker character
    
    def test_render_highlight(self):
        """Test rendering a highlight at a world position."""
        self.renderer.render_highlight_at_world_pos(
            self.console, 2, 3, 0, 0, "!", (255, 0, 255)
        )
        
        # World (2, 3) with view center (0, 0) should map to screen (7, 8)
        # Screen center is (5, 5), so (2, 3) -> (5+2, 5+3) = (7, 8)
        self.assertEqual(len(self.console.printed_chars), 1)
        printed = self.console.printed_chars[0]
        self.assertEqual(printed['x'], 7)
        self.assertEqual(printed['y'], 8)
        self.assertEqual(printed['text'], '!')
        self.assertEqual(printed['fg'], (255, 0, 255))


class TestEffectRenderer(unittest.TestCase):
    """Test the EffectRenderer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.effect_renderer = EffectRenderer()
        self.console = MockConsole(10, 10)
    
    def test_effect_renderer_creation(self):
        """Test that effect renderer can be created."""
        self.assertIsInstance(self.effect_renderer, EffectRenderer)
        self.assertEqual(len(self.effect_renderer.effects), 0)
    
    def test_add_effect(self):
        """Test adding an effect."""
        self.effect_renderer.add_effect('sparkle', 5, 5, 10, color=(255, 255, 0))
        
        self.assertEqual(len(self.effect_renderer.effects), 1)
        effect = self.effect_renderer.effects[0]
        self.assertEqual(effect['type'], 'sparkle')
        self.assertEqual(effect['x'], 5)
        self.assertEqual(effect['y'], 5)
        self.assertEqual(effect['duration'], 10)
        self.assertEqual(effect['remaining'], 10)
    
    def test_update_effects(self):
        """Test updating effects."""
        self.effect_renderer.add_effect('sparkle', 0, 0, 3)
        
        # Update effects
        self.effect_renderer.update_effects()
        self.assertEqual(self.effect_renderer.effects[0]['remaining'], 2)
        
        self.effect_renderer.update_effects()
        self.assertEqual(self.effect_renderer.effects[0]['remaining'], 1)
        
        self.effect_renderer.update_effects()
        # Effect should be removed when remaining reaches 0
        self.assertEqual(len(self.effect_renderer.effects), 0)
    
    def test_render_effects(self):
        """Test rendering effects."""
        self.effect_renderer.add_effect('sparkle', 0, 0, 5, color=(255, 255, 0))
        
        # Render with view center at (0, 0)
        self.effect_renderer.render_effects(self.console, 0, 0)
        
        # Should render at screen center (5, 5)
        self.assertEqual(len(self.console.printed_chars), 1)
        printed = self.console.printed_chars[0]
        self.assertEqual(printed['x'], 5)
        self.assertEqual(printed['y'], 5)
        self.assertIn(printed['text'], ['*', '+'])  # Sparkle alternates
        self.assertEqual(printed['fg'], (255, 255, 0))


class TestGameRenderer(unittest.TestCase):
    """Test the GameRenderer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_renderer = GameRenderer()
        self.console = MockConsole(20, 20)
        self.world_gen = MockWorldGenerator()
    
    def test_game_renderer_creation(self):
        """Test that game renderer can be created."""
        self.assertIsInstance(self.game_renderer, GameRenderer)
        self.assertIsInstance(self.game_renderer.world_renderer, WorldRenderer)
        self.assertIsInstance(self.game_renderer.effect_renderer, EffectRenderer)
    
    def test_coordinate_conversion(self):
        """Test world to screen and screen to world coordinate conversion."""
        # Test world to screen
        screen_x, screen_y = self.game_renderer.world_to_screen(5, 3, 0, 0, 20, 20)
        self.assertEqual(screen_x, 15)  # 10 + 5
        self.assertEqual(screen_y, 13)  # 10 + 3
        
        # Test screen to world
        world_x, world_y = self.game_renderer.screen_to_world(15, 13, 0, 0, 20, 20)
        self.assertEqual(world_x, 5)
        self.assertEqual(world_y, 3)
    
    def test_render_frame(self):
        """Test rendering a complete frame."""
        # Add a test tile
        test_tile = Tile(1, 1, "center_marker")
        self.world_gen.add_tile(1, 1, test_tile)

        # Render frame
        self.game_renderer.render_frame(self.console, self.world_gen, 0, 0)

        # Console should be cleared
        self.assertTrue(self.console.cleared)

        # Should have rendered tiles (20x20 = 400 tiles)
        tile_prints = [p for p in self.console.printed_chars if p['text'] in ['.', '█']]
        self.assertGreater(len(tile_prints), 0)
    
    def test_add_effect(self):
        """Test adding effects through the game renderer."""
        self.game_renderer.add_effect('sparkle', 10, 10, 5)
        
        self.assertEqual(len(self.game_renderer.effect_renderer.effects), 1)
        effect = self.game_renderer.effect_renderer.effects[0]
        self.assertEqual(effect['x'], 10)
        self.assertEqual(effect['y'], 10)


if __name__ == "__main__":
    unittest.main()
