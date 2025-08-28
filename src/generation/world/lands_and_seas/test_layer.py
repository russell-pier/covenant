#!/usr/bin/env python3
"""
Tests for the Lands and Seas generation layer.
"""

import unittest
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from src.generation.pipeline import GenerationData
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
