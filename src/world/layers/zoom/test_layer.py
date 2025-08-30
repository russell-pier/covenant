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
