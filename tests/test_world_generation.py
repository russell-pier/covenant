#!/usr/bin/env python3
"""
Comprehensive test suite for the new multi-scale sampling world generation system.

Tests the fixed-chunk system with continental, regional, local, and tiles layers.
"""

import unittest
import tempfile
import os
from typing import Dict, Any, Tuple

# Import the world generation components
from src.world.pipeline import GenerationData, GenerationPipeline
from src.world.layers.continental import ContinentalLayer
from src.world.layers.regional import RegionalLayer
from src.world.layers.local import LocalLayer
from src.world.layers.tiles import TilesLayer
from src.world.world_tier import WorldTier


class TestGenerationData(unittest.TestCase):
    """Test the GenerationData structure for multi-scale sampling."""
    
    def setUp(self):
        """Set up test data."""
        self.seed = 12345
        self.chunk_size = 16
        self.data = GenerationData(
            seed=self.seed,
            chunk_size=self.chunk_size,
            continental_samples={},
            regional_samples={},
            local_samples={},
            chunks={},
            processed_layers=[],
            custom_data={}
        )
    
    def test_initialization(self):
        """Test GenerationData initialization."""
        self.assertEqual(self.data.seed, self.seed)
        self.assertEqual(self.data.chunk_size, self.chunk_size)
        self.assertIsInstance(self.data.continental_samples, dict)
        self.assertIsInstance(self.data.regional_samples, dict)
        self.assertIsInstance(self.data.local_samples, dict)
        self.assertIsInstance(self.data.chunks, dict)
        self.assertIsInstance(self.data.processed_layers, list)
        self.assertIsInstance(self.data.custom_data, dict)
    
    def test_continental_sampling(self):
        """Test continental sampling methods."""
        region_x, region_y = 1, 2
        sample_data = {'designation': 'continent', 'test': 'data'}
        
        # Set and get continental sample
        self.data.set_continental_sample(region_x, region_y, sample_data)
        retrieved = self.data.get_continental_sample(region_x, region_y)
        
        self.assertEqual(retrieved, sample_data)
        self.assertIsNone(self.data.get_continental_sample(99, 99))
    
    def test_regional_sampling(self):
        """Test regional sampling methods."""
        chunk_x, chunk_y = 5, 7
        sample_data = {'terrain_type': 'land', 'test': 'data'}
        
        # Set and get regional sample
        self.data.set_regional_sample(chunk_x, chunk_y, sample_data)
        retrieved = self.data.get_regional_sample(chunk_x, chunk_y)
        
        self.assertEqual(retrieved, sample_data)
        self.assertIsNone(self.data.get_regional_sample(99, 99))
    
    def test_local_sampling(self):
        """Test local sampling methods."""
        sample_x, sample_y = 100, 200
        sample_data = {'terrain_type': 'water', 'test': 'data'}
        
        # Set and get local sample
        self.data.set_local_sample(sample_x, sample_y, sample_data)
        retrieved = self.data.get_local_sample(sample_x, sample_y)
        
        self.assertEqual(retrieved, sample_data)
        self.assertIsNone(self.data.get_local_sample(999, 999))
    
    def test_region_calculation(self):
        """Test region coordinate calculation."""
        # Test with default region size (4)
        self.assertEqual(self.data.get_region_for_chunk(0, 0), (0, 0))
        self.assertEqual(self.data.get_region_for_chunk(3, 3), (0, 0))
        self.assertEqual(self.data.get_region_for_chunk(4, 4), (1, 1))
        self.assertEqual(self.data.get_region_for_chunk(7, 15), (1, 3))
        
        # Test with custom region size
        self.assertEqual(self.data.get_region_for_chunk(0, 0, 2), (0, 0))
        self.assertEqual(self.data.get_region_for_chunk(3, 3, 2), (1, 1))


class TestContinentalLayer(unittest.TestCase):
    """Test the continental layer."""
    
    def setUp(self):
        """Set up test configuration."""
        self.config = {
            'region_size': 4,
            'noise_scale': 0.01,
            'continent_threshold': 0.3,
            'land_ratio': 0.3
        }
        self.layer = ContinentalLayer('continental', self.config)
        self.data = GenerationData(
            seed=12345,
            chunk_size=16,
            continental_samples={},
            regional_samples={},
            local_samples={},
            chunks={},
            processed_layers=[],
            custom_data={}
        )
    
    def test_layer_initialization(self):
        """Test layer initialization."""
        self.assertEqual(self.layer.name, 'continental')
        self.assertEqual(self.layer.config, self.config)
    
    def test_continental_processing(self):
        """Test continental layer processing."""
        bounds = (0, 0, 7, 7)  # 8x8 chunks = 2x2 regions
        
        result = self.layer.process(self.data, bounds)
        
        # Check that continental samples were generated
        self.assertGreater(len(result.continental_samples), 0)
        self.assertIn('continental', result.processed_layers)
        
        # Check that all regions in bounds have samples
        for region_x in range(2):
            for region_y in range(2):
                sample = result.get_continental_sample(region_x, region_y)
                self.assertIsNotNone(sample)
                self.assertIn('designation', sample)
                self.assertIn(sample['designation'], ['continent', 'ocean'])
    
    def test_deterministic_generation(self):
        """Test that generation is deterministic with same seed."""
        bounds = (0, 0, 3, 3)
        
        result1 = self.layer.process(self.data, bounds)
        
        # Reset data and process again
        data2 = GenerationData(
            seed=12345,  # Same seed
            chunk_size=16,
            continental_samples={},
            regional_samples={},
            local_samples={},
            chunks={},
            processed_layers=[],
            custom_data={}
        )
        result2 = self.layer.process(data2, bounds)
        
        # Results should be identical
        self.assertEqual(result1.continental_samples, result2.continental_samples)


class TestRegionalLayer(unittest.TestCase):
    """Test the regional layer."""
    
    def setUp(self):
        """Set up test configuration and data."""
        self.continental_config = {
            'region_size': 4,
            'noise_scale': 0.01,
            'continent_threshold': 0.3,
            'land_ratio': 0.3
        }
        self.regional_config = {
            'noise_scale': 0.1,
            'land_bias_from_continental': 0.7,
            'coastal_variation': 0.3
        }
        
        # Set up data with continental samples
        self.data = GenerationData(
            seed=12345,
            chunk_size=16,
            continental_samples={},
            regional_samples={},
            local_samples={},
            chunks={},
            processed_layers=[],
            custom_data={}
        )
        
        # Add some continental samples
        continental_layer = ContinentalLayer('continental', self.continental_config)
        self.data = continental_layer.process(self.data, (0, 0, 7, 7))
        
        self.regional_layer = RegionalLayer('regional', self.regional_config)
    
    def test_regional_processing(self):
        """Test regional layer processing."""
        bounds = (0, 0, 7, 7)  # 8x8 chunks
        
        result = self.regional_layer.process(self.data, bounds)
        
        # Check that regional samples were generated
        self.assertGreater(len(result.regional_samples), 0)
        self.assertIn('regional', result.processed_layers)
        
        # Check that all chunks in bounds have samples
        for chunk_x in range(8):
            for chunk_y in range(8):
                sample = result.get_regional_sample(chunk_x, chunk_y)
                self.assertIsNotNone(sample)
                self.assertIn('terrain_type', sample)
                self.assertIn(sample['terrain_type'], ['land', 'water'])


class TestPipelineIntegration(unittest.TestCase):
    """Test the complete pipeline integration."""
    
    def setUp(self):
        """Set up complete pipeline configuration."""
        self.layer_configs = [
            ('continental', {
                'region_size': 4,
                'noise_scale': 0.01,
                'continent_threshold': 0.3,
                'land_ratio': 0.3
            }),
            ('regional', {
                'noise_scale': 0.1,
                'land_bias_from_continental': 0.7,
                'coastal_variation': 0.3
            }),
            ('local', {
                'sampling_resolution': 8,
                'noise_scale': 0.5,
                'coastal_detail_iterations': 3,
                'erosion_probability': 0.1,
                'expansion_probability': 0.2
            }),
            ('tiles', {
                'default_land_tile': 'grass',
                'default_water_tile': 'water',
                'coastal_tile': 'sand',
                'deep_water_tile': 'deep_water'
            })
        ]
    
    def test_complete_pipeline(self):
        """Test the complete world generation pipeline."""
        # Create pipeline
        pipeline = WorldTier.create_custom_pipeline(self.layer_configs)
        
        # Create generation data
        data = GenerationData(
            seed=12345,
            chunk_size=16,
            continental_samples={},
            regional_samples={},
            local_samples={},
            chunks={},
            processed_layers=[],
            custom_data={}
        )
        
        # Process through pipeline
        bounds = (0, 0, 3, 3)  # 4x4 chunks
        result = pipeline.process(data, bounds)
        
        # Verify all layers processed
        expected_layers = ['continental', 'regional', 'local', 'tiles']
        for layer_name in expected_layers:
            self.assertIn(layer_name, result.processed_layers)
        
        # Verify samples exist
        self.assertGreater(len(result.continental_samples), 0)
        self.assertGreater(len(result.regional_samples), 0)
        self.assertGreater(len(result.local_samples), 0)
        self.assertGreater(len(result.chunks), 0)
        
        # Verify chunk data structure
        for chunk_key, chunk_data in result.chunks.items():
            self.assertIn('chunk_x', chunk_data)
            self.assertIn('chunk_y', chunk_data)
            self.assertIn('chunk_size', chunk_data)
            self.assertIn('tiles', chunk_data)
            self.assertEqual(chunk_data['chunk_size'], 16)


if __name__ == '__main__':
    unittest.main()
