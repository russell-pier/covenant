#!/usr/bin/env python3
"""
Local Layer - Multi-Scale Sampling System

Samples at sub-chunk resolution (8x8 or 16x16 within each chunk) to generate
detailed coastlines and terrain boundaries. Applies coastal erosion/expansion
rules within chunk boundaries.
"""

import math
from typing import Tuple, Dict, Any, List
from ...pipeline import GenerationLayer, GenerationData


class LocalLayer(GenerationLayer):
    """
    Local-scale terrain generation using sub-chunk sampling.
    
    Operates at high resolution within each chunk to create detailed
    coastlines and terrain features. Uses regional terrain as context.
    """
    
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process local-level terrain generation.
        
        Args:
            data: Generation data with regional samples
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)
            
        Returns:
            Updated generation data with local samples
        """
        self._set_seed(data.seed, "local")
        
        # Get configuration
        sampling_resolution = self._get_config_value("sampling_resolution")
        noise_scale = self._get_config_value("noise_scale")
        coastal_detail_iterations = self._get_config_value("coastal_detail_iterations")
        erosion_probability = self._get_config_value("erosion_probability")
        expansion_probability = self._get_config_value("expansion_probability")
        
        min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y = bounds
        
        # Generate local samples for each chunk
        for chunk_x in range(min_chunk_x, max_chunk_x + 1):
            for chunk_y in range(min_chunk_y, max_chunk_y + 1):
                local_samples = self._generate_local_samples(
                    data, chunk_x, chunk_y, sampling_resolution, noise_scale,
                    coastal_detail_iterations, erosion_probability, expansion_probability
                )
                
                # Store samples for each sub-chunk position
                for sample_x, sample_y, sample_data in local_samples:
                    data.set_local_sample(sample_x, sample_y, sample_data)
        
        return data
    
    def _generate_local_samples(self, data: GenerationData, chunk_x: int, chunk_y: int,
                              sampling_resolution: int, noise_scale: float,
                              coastal_iterations: int, erosion_prob: float,
                              expansion_prob: float) -> List[Tuple[int, int, Dict[str, Any]]]:
        """
        Generate high-resolution samples within a chunk.
        
        Args:
            data: Generation data with regional samples
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            sampling_resolution: Number of samples per chunk dimension
            noise_scale: Scale factor for noise sampling
            coastal_iterations: Number of coastal detail iterations
            erosion_prob: Probability of erosion in coastal areas
            expansion_prob: Probability of expansion in coastal areas
            
        Returns:
            List of (sample_x, sample_y, sample_data) tuples
        """
        # Get regional terrain type for this chunk
        regional_terrain = self._get_regional_terrain(data, chunk_x, chunk_y)
        
        samples = []
        chunk_size = data.chunk_size
        
        # Calculate sample positions within the chunk
        for local_x in range(sampling_resolution):
            for local_y in range(sampling_resolution):
                # Convert to world coordinates
                sample_x = chunk_x * chunk_size + (local_x * chunk_size) // sampling_resolution
                sample_y = chunk_y * chunk_size + (local_y * chunk_size) // sampling_resolution
                
                # Generate base terrain from noise
                base_terrain = self._sample_local_terrain(
                    sample_x, sample_y, noise_scale, regional_terrain
                )
                
                sample_data = {
                    'terrain_type': base_terrain,
                    'chunk_x': chunk_x,
                    'chunk_y': chunk_y,
                    'local_x': local_x,
                    'local_y': local_y,
                    'world_x': sample_x,
                    'world_y': sample_y
                }
                
                samples.append((sample_x, sample_y, sample_data))
        
        # Apply coastal detail iterations
        for iteration in range(coastal_iterations):
            samples = self._apply_coastal_detail(
                samples, sampling_resolution, erosion_prob, expansion_prob
            )
        
        return samples
    
    def _sample_local_terrain(self, world_x: int, world_y: int, noise_scale: float,
                            regional_terrain: str) -> str:
        """
        Sample local terrain type based on regional context and noise.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            noise_scale: Scale factor for noise sampling
            regional_terrain: Regional terrain type ('land' or 'water')
            
        Returns:
            'land' or 'water'
        """
        # Sample noise at high resolution
        noise_value = self._simple_noise(world_x * noise_scale, world_y * noise_scale)
        
        # Bias based on regional terrain
        if regional_terrain == 'land':
            threshold = 0.3  # Favor land in land regions
        else:
            threshold = 0.7  # Favor water in water regions
        
        return 'land' if noise_value > threshold else 'water'
    
    def _apply_coastal_detail(self, samples: List[Tuple[int, int, Dict[str, Any]]],
                            resolution: int, erosion_prob: float, 
                            expansion_prob: float) -> List[Tuple[int, int, Dict[str, Any]]]:
        """
        Apply coastal erosion and expansion for detailed coastlines.
        
        Args:
            samples: List of sample data
            resolution: Sampling resolution
            erosion_prob: Probability of erosion
            expansion_prob: Probability of expansion
            
        Returns:
            Updated samples with coastal detail applied
        """
        # Create a grid for easier neighbor checking
        sample_grid = {}
        for sample_x, sample_y, sample_data in samples:
            local_x = sample_data['local_x']
            local_y = sample_data['local_y']
            sample_grid[(local_x, local_y)] = sample_data
        
        # Apply erosion and expansion
        updated_samples = []
        for sample_x, sample_y, sample_data in samples:
            local_x = sample_data['local_x']
            local_y = sample_data['local_y']
            current_terrain = sample_data['terrain_type']
            
            # Count neighbors
            land_neighbors = 0
            water_neighbors = 0
            
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    
                    neighbor_x = local_x + dx
                    neighbor_y = local_y + dy
                    
                    if (neighbor_x, neighbor_y) in sample_grid:
                        neighbor_terrain = sample_grid[(neighbor_x, neighbor_y)]['terrain_type']
                        if neighbor_terrain == 'land':
                            land_neighbors += 1
                        else:
                            water_neighbors += 1
            
            # Apply coastal rules
            new_terrain = current_terrain
            if current_terrain == 'land' and water_neighbors > 0:
                # Coastal land - might erode
                if self.rng.random() < erosion_prob:
                    new_terrain = 'water'
            elif current_terrain == 'water' and land_neighbors > 0:
                # Coastal water - might become land
                if self.rng.random() < expansion_prob:
                    new_terrain = 'land'
            
            # Update sample data
            updated_data = sample_data.copy()
            updated_data['terrain_type'] = new_terrain
            updated_samples.append((sample_x, sample_y, updated_data))
        
        return updated_samples
    
    def _get_regional_terrain(self, data: GenerationData, chunk_x: int, chunk_y: int) -> str:
        """Get regional terrain type for a chunk."""
        sample = data.get_regional_sample(chunk_x, chunk_y)
        if sample is None:
            return 'water'
        return sample['terrain_type']
    
    def _simple_noise(self, x: float, y: float) -> float:
        """Simple deterministic noise function."""
        hash_val = hash((int(x * 1000), int(y * 1000), self.rng.getstate()[1][0])) % (2**32)
        return (hash_val % 10000) / 10000.0
