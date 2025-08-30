#!/usr/bin/env python3
"""
Regional Layer - Multi-Scale Sampling System

Samples noise at individual chunk level to create major land/water boundaries
within continental regions. Biases sampling based on continental designation.
"""

import math
from typing import Tuple, Dict, Any
from ...pipeline import GenerationLayer, GenerationData


class RegionalLayer(GenerationLayer):
    """
    Regional-scale terrain generation using chunk-level sampling.
    
    Operates on individual chunks to create land/water boundaries within
    continental regions. Uses continental designation to bias the sampling.
    """
    
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process regional-level terrain generation.
        
        Args:
            data: Generation data with continental samples
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)
            
        Returns:
            Updated generation data with regional samples
        """
        self._set_seed(data.seed, "regional")
        
        # Get configuration
        noise_scale = self._get_config_value("noise_scale")
        land_bias_from_continental = self._get_config_value("land_bias_from_continental")
        coastal_variation = self._get_config_value("coastal_variation")
        
        min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y = bounds
        
        # Generate regional samples for each chunk
        for chunk_x in range(min_chunk_x, max_chunk_x + 1):
            for chunk_y in range(min_chunk_y, max_chunk_y + 1):
                terrain_type = self._sample_regional_terrain(
                    data, chunk_x, chunk_y, noise_scale, 
                    land_bias_from_continental, coastal_variation
                )
                data.set_regional_sample(chunk_x, chunk_y, {
                    'terrain_type': terrain_type,
                    'chunk_x': chunk_x,
                    'chunk_y': chunk_y
                })

        # Mark this layer as processed
        if self.name not in data.processed_layers:
            data.processed_layers.append(self.name)

        return data
    
    def _sample_regional_terrain(self, data: GenerationData, chunk_x: int, chunk_y: int,
                               noise_scale: float, land_bias: float, 
                               coastal_variation: float) -> str:
        """
        Sample regional terrain type for a chunk based on continental context.
        
        Args:
            data: Generation data with continental samples
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            noise_scale: Scale factor for noise sampling
            land_bias: How much continental designation influences sampling
            coastal_variation: Amount of variation in coastal regions
            
        Returns:
            'land' or 'water'
        """
        # Get continental designation for this chunk
        continental_designation = self._get_continental_designation(data, chunk_x, chunk_y)
        
        # Sample noise for this chunk
        noise_value = self._simple_noise(chunk_x * noise_scale, chunk_y * noise_scale)
        
        # Calculate base threshold based on continental designation
        if continental_designation == 'continent':
            base_threshold = 0.3  # Favor land in continental regions
        else:
            base_threshold = 0.7  # Favor water in ocean regions
        
        # Apply continental bias
        biased_threshold = base_threshold * land_bias + (1 - land_bias) * 0.5
        
        # Add coastal variation for more interesting boundaries
        variation = (self._simple_noise(chunk_x * 0.3, chunk_y * 0.3) - 0.5) * coastal_variation
        final_threshold = biased_threshold + variation
        
        return 'land' if noise_value > final_threshold else 'water'
    
    def _get_continental_designation(self, data: GenerationData, chunk_x: int, chunk_y: int) -> str:
        """Get continental designation for a chunk."""
        # This should use the continental layer's method, but for now we'll duplicate logic
        region_size = 4  # Should get from continental layer config
        region_x = chunk_x // region_size
        region_y = chunk_y // region_size
        
        sample = data.get_continental_sample(region_x, region_y)
        if sample is None:
            return 'ocean'
        
        return sample['designation']
    
    def _simple_noise(self, x: float, y: float) -> float:
        """
        Simple deterministic noise function for regional sampling.
        
        Args:
            x: X coordinate (scaled)
            y: Y coordinate (scaled)
            
        Returns:
            Noise value between 0 and 1
        """
        # Simple hash-based noise - replace with proper noise in production
        hash_val = hash((int(x * 1000), int(y * 1000), self.rng.getstate()[1][0])) % (2**32)
        return (hash_val % 10000) / 10000.0
    
    def get_regional_terrain(self, data: GenerationData, chunk_x: int, chunk_y: int) -> str:
        """
        Get the regional terrain type for a specific chunk.
        
        Args:
            data: Generation data containing regional samples
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            
        Returns:
            'land' or 'water'
        """
        sample = data.get_regional_sample(chunk_x, chunk_y)
        if sample is None:
            # Default to water if no sample available
            return 'water'
        
        return sample['terrain_type']
