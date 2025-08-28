#!/usr/bin/env python3
"""
Tests for world generators

Unit tests for the spiral generator and other world generation components.
"""

import unittest
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from generators.spiral import Tile, SpiralGenerator, WorldGenerator


class TestTile(unittest.TestCase):
    """Test the Tile class."""
    
    def test_tile_creation(self):
        """Test basic tile creation."""
        tile = Tile(5, 10)
        self.assertEqual(tile.x, 5)
        self.assertEqual(tile.y, 10)
        self.assertEqual(tile.tile_type, "stone")

    def test_tile_with_custom_values(self):
        """Test tile creation with custom values."""
        tile = Tile(1, 2, "water")
        self.assertEqual(tile.x, 1)
        self.assertEqual(tile.y, 2)
        self.assertEqual(tile.tile_type, "water")


class TestSpiralGenerator(unittest.TestCase):
    """Test the SpiralGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = SpiralGenerator()
    
    def test_generator_creation(self):
        """Test that generator can be created."""
        self.assertIsInstance(self.generator, SpiralGenerator)
        self.assertEqual(len(self.generator.tiles), 0)
    
    def test_generate_single_tile(self):
        """Test generating a single tile at the center."""
        tiles = self.generator.generate_spiral(0, 0, 0)
        self.assertEqual(len(tiles), 1)
        self.assertIn((0, 0), tiles)
        
        tile = tiles[(0, 0)]
        self.assertEqual(tile.x, 0)
        self.assertEqual(tile.y, 0)
        self.assertEqual(tile.tile_type, "center_marker")
    
    def test_generate_small_spiral(self):
        """Test generating a small spiral."""
        tiles = self.generator.generate_spiral(0, 0, 2)
        
        # Should have center tile plus spiral tiles
        self.assertGreater(len(tiles), 1)
        self.assertIn((0, 0), tiles)  # Center should always be present
        
        # Check that all tiles are within the expected radius
        for (x, y), tile in tiles.items():
            self.assertLessEqual(abs(x), 2)
            self.assertLessEqual(abs(y), 2)
            self.assertIn(tile.tile_type, ["stone", "center_marker"])
    
    def test_get_tile_existing(self):
        """Test getting an existing tile."""
        self.generator.generate_spiral(0, 0, 1)
        tile = self.generator.get_tile(0, 0)
        self.assertEqual(tile.tile_type, "center_marker")
    
    def test_get_tile_nonexistent(self):
        """Test getting a non-existent tile returns void."""
        self.generator.generate_spiral(0, 0, 1)
        tile = self.generator.get_tile(100, 100)
        self.assertEqual(tile.tile_type, "void")
        self.assertEqual(tile.x, 100)
        self.assertEqual(tile.y, 100)
    
    def test_get_tiles_in_bounds(self):
        """Test getting tiles within specific bounds."""
        self.generator.generate_spiral(0, 0, 3)
        tiles = self.generator.get_tiles_in_bounds(-1, -1, 1, 1)
        
        # Should get tiles in a 3x3 area around center
        self.assertGreater(len(tiles), 0)
        for tile in tiles:
            self.assertGreaterEqual(tile.x, -1)
            self.assertLessEqual(tile.x, 1)
            self.assertGreaterEqual(tile.y, -1)
            self.assertLessEqual(tile.y, 1)


class TestWorldGenerator(unittest.TestCase):
    """Test the WorldGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.world_gen = WorldGenerator()
    
    def test_world_generator_creation(self):
        """Test that world generator can be created."""
        self.assertIsInstance(self.world_gen, WorldGenerator)
        self.assertIsInstance(self.world_gen.spiral_generator, SpiralGenerator)
    
    def test_generate_world(self):
        """Test world generation."""
        tiles = self.world_gen.generate_world(5, 5, 3)
        self.assertGreater(len(tiles), 0)
        self.assertIn((5, 5), tiles)  # Center should be present
    
    def test_get_tile(self):
        """Test getting a tile from the world."""
        self.world_gen.generate_world(0, 0, 2)
        tile = self.world_gen.get_tile(0, 0)
        self.assertEqual(tile.tile_type, "center_marker")
    
    def test_get_tiles_in_view(self):
        """Test getting tiles in view."""
        self.world_gen.generate_world(0, 0, 10)
        tiles = self.world_gen.get_tiles_in_view(0, 0, 6, 6)
        
        # Should get some tiles
        self.assertGreater(len(tiles), 0)


if __name__ == "__main__":
    unittest.main()
