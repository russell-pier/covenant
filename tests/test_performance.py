#!/usr/bin/env python3
"""
Performance tests for the new multi-scale sampling world generation system.

Verifies that the fixed-chunk system provides linear scaling instead of exponential.
"""

import unittest
import time
from typing import Dict, Any, List

from src.world.pipeline import GenerationData
from src.world.world_tier import WorldTier


class TestPerformance(unittest.TestCase):
    """Test performance characteristics of the new system."""
    
    def setUp(self):
        """Set up test configuration."""
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
        self.pipeline = WorldTier.create_custom_pipeline(self.layer_configs)
    
    def _generate_chunks(self, chunk_count: int) -> float:
        """
        Generate a square area of chunks and measure time.
        
        Args:
            chunk_count: Number of chunks per side (total = chunk_count^2)
            
        Returns:
            Time taken in seconds
        """
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
        
        bounds = (0, 0, chunk_count - 1, chunk_count - 1)
        
        start_time = time.time()
        result = self.pipeline.process(data, bounds)
        end_time = time.time()
        
        return end_time - start_time
    
    def test_linear_scaling(self):
        """Test that generation time scales linearly with chunk count."""
        # Test different chunk counts
        chunk_counts = [2, 4, 8]  # 4, 16, 64 total chunks
        times = []
        
        for count in chunk_counts:
            generation_time = self._generate_chunks(count)
            times.append(generation_time)
            print(f"Generated {count}x{count} chunks in {generation_time:.4f} seconds")
        
        # Verify that scaling is roughly linear (not exponential)
        # Time ratio should be roughly proportional to area ratio
        time_ratio_4_to_16 = times[1] / times[0] if times[0] > 0 else float('inf')
        time_ratio_16_to_64 = times[2] / times[1] if times[1] > 0 else float('inf')
        
        area_ratio = 4  # Each step is 4x more chunks
        
        # Allow some variance but ensure it's not exponential (which would be much higher)
        max_acceptable_ratio = area_ratio * 2  # Allow 2x overhead
        
        self.assertLess(time_ratio_4_to_16, max_acceptable_ratio,
                       f"Scaling from 4 to 16 chunks took {time_ratio_4_to_16:.2f}x time, expected < {max_acceptable_ratio}x")
        self.assertLess(time_ratio_16_to_64, max_acceptable_ratio,
                       f"Scaling from 16 to 64 chunks took {time_ratio_16_to_64:.2f}x time, expected < {max_acceptable_ratio}x")
    
    def test_chunk_count_consistency(self):
        """Test that the number of generated chunks is consistent."""
        chunk_counts = [2, 4, 6]
        
        for count in chunk_counts:
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
            
            bounds = (0, 0, count - 1, count - 1)
            result = self.pipeline.process(data, bounds)
            
            expected_chunks = count * count
            actual_chunks = len(result.chunks)
            
            self.assertEqual(actual_chunks, expected_chunks,
                           f"Expected {expected_chunks} chunks, got {actual_chunks}")
    
    def test_memory_usage(self):
        """Test that memory usage is reasonable."""
        import sys
        
        # Generate a moderate number of chunks
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
        
        bounds = (0, 0, 7, 7)  # 8x8 = 64 chunks
        result = self.pipeline.process(data, bounds)
        
        # Check that we have reasonable data structures
        self.assertLess(len(result.continental_samples), 100,
                       "Too many continental samples - should be region-level")
        self.assertEqual(len(result.regional_samples), 64,
                        "Should have one regional sample per chunk")
        self.assertGreater(len(result.local_samples), 64,
                          "Should have multiple local samples per chunk")
        self.assertEqual(len(result.chunks), 64,
                        "Should have one chunk data per chunk")
        
        # Check chunk data structure
        for chunk_data in result.chunks.values():
            tiles = chunk_data.get('tiles', {})
            expected_tiles = 16 * 16  # 16x16 chunk
            self.assertEqual(len(tiles), expected_tiles,
                           f"Each chunk should have {expected_tiles} tiles")


class TestDeterminism(unittest.TestCase):
    """Test that generation is deterministic."""
    
    def setUp(self):
        """Set up test configuration."""
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
            ('tiles', {
                'default_land_tile': 'grass',
                'default_water_tile': 'water',
                'coastal_tile': 'sand',
                'deep_water_tile': 'deep_water'
            })
        ]
        self.pipeline = WorldTier.create_custom_pipeline(self.layer_configs)
    
    def test_same_seed_same_result(self):
        """Test that the same seed produces the same result."""
        seed = 54321
        bounds = (0, 0, 3, 3)
        
        # Generate twice with same seed
        data1 = GenerationData(
            seed=seed,
            chunk_size=16,
            continental_samples={},
            regional_samples={},
            local_samples={},
            chunks={},
            processed_layers=[],
            custom_data={}
        )
        result1 = self.pipeline.process(data1, bounds)
        
        data2 = GenerationData(
            seed=seed,
            chunk_size=16,
            continental_samples={},
            regional_samples={},
            local_samples={},
            chunks={},
            processed_layers=[],
            custom_data={}
        )
        result2 = self.pipeline.process(data2, bounds)
        
        # Results should be identical
        self.assertEqual(result1.continental_samples, result2.continental_samples)
        self.assertEqual(result1.regional_samples, result2.regional_samples)
        
        # Check that chunk tiles are identical
        for chunk_key in result1.chunks:
            tiles1 = result1.chunks[chunk_key].get('tiles', {})
            tiles2 = result2.chunks[chunk_key].get('tiles', {})
            self.assertEqual(tiles1, tiles2, f"Tiles differ for chunk {chunk_key}")
    
    def test_different_seed_different_result(self):
        """Test that different seeds produce different results."""
        bounds = (0, 0, 3, 3)
        
        # Generate with different seeds
        data1 = GenerationData(
            seed=11111,
            chunk_size=16,
            continental_samples={},
            regional_samples={},
            local_samples={},
            chunks={},
            processed_layers=[],
            custom_data={}
        )
        result1 = self.pipeline.process(data1, bounds)
        
        data2 = GenerationData(
            seed=22222,
            chunk_size=16,
            continental_samples={},
            regional_samples={},
            local_samples={},
            chunks={},
            processed_layers=[],
            custom_data={}
        )
        result2 = self.pipeline.process(data2, bounds)
        
        # Results should be different
        self.assertNotEqual(result1.continental_samples, result2.continental_samples)


if __name__ == '__main__':
    unittest.main()
