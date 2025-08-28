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
