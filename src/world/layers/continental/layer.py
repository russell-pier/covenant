#!/usr/bin/env python3
"""
Continental Layer - Multi-Scale Sampling System

Samples noise at region level (4x4 chunk regions = 64x64 tiles) to assign
continent/ocean designation to entire regions. Ensures landmasses are 
minimum 4x4 chunks in size.
"""

import math
from typing import Tuple, Dict, Any
from ...pipeline import GenerationLayer, GenerationData


class ContinentalLayer(GenerationLayer):
    """
    Continental-scale terrain generation using region-level sampling.
    
    Operates on 4x4 chunk regions (configurable) to create large-scale
    continent/ocean patterns. Each region gets a single designation
    that influences all chunks within it.
    """
    
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process continental-level terrain generation.
        
        Args:
            data: Generation data with fixed-size chunks
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)
            
        Returns:
            Updated generation data with continental samples
        """
        self._set_seed(data.seed, "continental")
        
        # Get configuration
        region_size = self._get_config_value("region_size")
        noise_scale = self._get_config_value("noise_scale")
        continent_threshold = self._get_config_value("continent_threshold")
        land_ratio = self._get_config_value("land_ratio")
        
        min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y = bounds
        
        # Calculate region bounds that cover all chunks
        min_region_x = min_chunk_x // region_size
        min_region_y = min_chunk_y // region_size
        max_region_x = max_chunk_x // region_size
        max_region_y = max_chunk_y // region_size
        
        # Generate continental samples for each region
        for region_x in range(min_region_x, max_region_x + 1):
            for region_y in range(min_region_y, max_region_y + 1):
                designation = self._sample_continental_noise(
                    region_x, region_y, noise_scale, continent_threshold, land_ratio
                )
                data.set_continental_sample(region_x, region_y, {
                    'designation': designation,
                    'region_x': region_x,
                    'region_y': region_y,
                    'region_size': region_size
                })

        # Mark this layer as processed
        if self.name not in data.processed_layers:
            data.processed_layers.append(self.name)

        return data
    
    def _sample_continental_noise(self, region_x: int, region_y: int, 
                                noise_scale: float, continent_threshold: float,
                                land_ratio: float) -> str:
        """
        Sample noise to determine continental designation for a region.
        
        Args:
            region_x: Region X coordinate
            region_y: Region Y coordinate
            noise_scale: Scale factor for noise sampling
            continent_threshold: Threshold for continent vs ocean
            land_ratio: Target ratio of land regions
            
        Returns:
            'continent' or 'ocean'
        """
        # Use simple noise function based on coordinates
        # In a real implementation, you'd use proper noise like Perlin/Simplex
        noise_value = self._simple_noise(region_x * noise_scale, region_y * noise_scale)
        
        # Adjust threshold based on desired land ratio
        adjusted_threshold = continent_threshold + (0.5 - land_ratio)
        
        return 'continent' if noise_value > adjusted_threshold else 'ocean'
    
    def _simple_noise(self, x: float, y: float) -> float:
        """
        Simple deterministic noise function for continental sampling.
        
        Args:
            x: X coordinate (scaled)
            y: Y coordinate (scaled)
            
        Returns:
            Noise value between 0 and 1
        """
        # Simple hash-based noise - replace with proper noise in production
        hash_val = hash((int(x * 1000), int(y * 1000), self.rng.getstate()[1][0])) % (2**32)
        return (hash_val % 10000) / 10000.0
    
    def get_continental_designation(self, data: GenerationData, chunk_x: int, chunk_y: int) -> str:
        """
        Get the continental designation for a specific chunk.
        
        Args:
            data: Generation data containing continental samples
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            
        Returns:
            'continent' or 'ocean'
        """
        region_size = self._get_config_value("region_size")
        region_x = chunk_x // region_size
        region_y = chunk_y // region_size
        
        sample = data.get_continental_sample(region_x, region_y)
        if sample is None:
            # Default to ocean if no sample available
            return 'ocean'
        
        return sample['designation']
