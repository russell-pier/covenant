#!/usr/bin/env python3
"""
Lands and Seas Generation Layer

Determines basic land/water distribution for chunks.
This is the foundation layer that establishes the fundamental geography.
"""

import os
import random
import math
from typing import Dict, Any, Tuple

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from ...pipeline import GenerationLayer, GenerationData


class LandsAndSeasLayer(GenerationLayer):
    """
    Layer that determines whether each chunk is land or water.
    
    This is the first and most fundamental layer of world generation.
    Other layers will build upon this basic land/water distribution.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("lands_and_seas", config)
        
        # Load configuration from TOML file if no config provided
        if not config:
            self.config = self._load_config()
        
        # Extract configuration values
        self.land_ratio = self._get_config_value('land_ratio', 4)
        self.algorithm = self._get_config_value('algorithm', 'cellular_automata')

        # Algorithm-specific configuration
        if self.algorithm == 'perlin_noise':
            self.scale = self._get_config_value('perlin_noise.scale', 0.1)
            self.octaves = self._get_config_value('perlin_noise.octaves', 4)
            self.persistence = self._get_config_value('perlin_noise.persistence', 0.5)
            self.lacunarity = self._get_config_value('perlin_noise.lacunarity', 2.0)
        elif self.algorithm == 'cellular_automata':
            self.initial_land_probability = self._get_config_value('cellular_automata.initial_land_probability', 0.4)
            self.iterations = self._get_config_value('cellular_automata.iterations', 5)
            self.birth_limit = self._get_config_value('cellular_automata.birth_limit', 4)
            self.death_limit = self._get_config_value('cellular_automata.death_limit', 3)

        # Validate configuration
        if not (1 <= self.land_ratio <= 10):
            raise ValueError(f"land_ratio must be between 1 and 10, got {self.land_ratio}")

        if self.algorithm not in ['random_chunks', 'perlin_noise', 'cellular_automata']:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from the layer's TOML file."""
        # Look for config in the centralized config directory
        config_path = os.path.join('config', 'world', 'layers', 'lands_and_seas.toml')

        if not os.path.exists(config_path):
            return {}

        try:
            with open(config_path, 'rb') as f:
                data = tomllib.load(f)
            return data.get('lands_and_seas', {})
        except Exception as e:
            return {}
    
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process chunks to determine land/water distribution.

        Args:
            data: Generation data to process
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)

        Returns:
            Data with land_type property added to each chunk
        """
        min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y = bounds
        total_chunks = (max_chunk_x - min_chunk_x + 1) * (max_chunk_y - min_chunk_y + 1)
        algorithm = self.config.get('algorithm', 'random_chunks')


        min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y = bounds

        # Process each chunk in the bounds
        for chunk_x in range(min_chunk_x, max_chunk_x + 1):
            for chunk_y in range(min_chunk_y, max_chunk_y + 1):
                land_type = self._determine_land_type(data.seed, chunk_x, chunk_y)
                data.set_chunk_property(chunk_x, chunk_y, 'land_type', land_type)

        # Mark this layer as processed
        if self.name not in data.processed_layers:
            data.processed_layers.append(self.name)
        return data
    
    def _determine_land_type(self, seed: int, chunk_x: int, chunk_y: int) -> str:
        """
        Determine if a chunk should be land or water.

        Args:
            seed: World generation seed
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate

        Returns:
            'land' or 'water'
        """
        if self.algorithm == 'random_chunks':
            return self._random_chunks_algorithm(seed, chunk_x, chunk_y)
        elif self.algorithm == 'perlin_noise':
            return self._perlin_noise_algorithm(seed, chunk_x, chunk_y)
        elif self.algorithm == 'cellular_automata':
            return self._cellular_automata_algorithm(seed, chunk_x, chunk_y)
        else:
            raise ValueError(f"Algorithm {self.algorithm} not implemented")
    
    def _random_chunks_algorithm(self, seed: int, chunk_x: int, chunk_y: int) -> str:
        """
        Simple per-chunk randomization algorithm.
        
        Each chunk is independently determined to be land or water
        based on the configured land ratio.
        """
        # Create deterministic seed for this chunk
        self._set_seed(seed, chunk_x, chunk_y)
        
        # Determine land vs water based on ratio
        return "land" if self.rng.randint(1, 10) <= self.land_ratio else "water"
    
    def _perlin_noise_algorithm(self, seed: int, chunk_x: int, chunk_y: int) -> str:
        """
        Perlin noise-based land/water generation for natural-looking terrain.

        Creates realistic landmasses with natural coastlines and island chains.
        """
        # Set deterministic seed for this chunk
        self._set_seed(seed, chunk_x, chunk_y)

        # Generate multi-octave Perlin-like noise
        noise_value = 0.0
        amplitude = 1.0
        frequency = self.scale

        for _ in range(self.octaves):
            # Simple noise function (simplified Perlin noise)
            x = chunk_x * frequency
            y = chunk_y * frequency

            # Create smooth noise using sine/cosine functions
            noise = (math.sin(x * 12.9898 + y * 78.233) * 43758.5453) % 1.0
            noise = (noise - 0.5) * 2.0  # Convert to -1 to 1 range

            # Smooth the noise
            noise = noise * noise * noise * (noise * (noise * 6.0 - 15.0) + 10.0)

            noise_value += noise * amplitude
            amplitude *= self.persistence
            frequency *= self.lacunarity

        # Normalize and apply land ratio
        noise_value = (noise_value + 1.0) / 2.0  # Convert to 0-1 range
        land_threshold = 1.0 - (self.land_ratio / 10.0)

        return "land" if noise_value > land_threshold else "water"

    def _cellular_automata_algorithm(self, seed: int, chunk_x: int, chunk_y: int) -> str:
        """
        Cellular automata-based generation for realistic landmasses.

        Creates natural-looking continents and islands with smooth coastlines.
        """
        # Create a local grid around this chunk for cellular automata
        grid_size = 7  # 7x7 grid centered on target chunk
        center = grid_size // 2

        # Initialize grid with random values based on initial probability
        grid = {}
        for gx in range(grid_size):
            for gy in range(grid_size):
                world_x = chunk_x + (gx - center)
                world_y = chunk_y + (gy - center)

                # Create deterministic seed for this position
                pos_seed = seed + world_x * 73 + world_y * 37
                random.seed(pos_seed)

                grid[(gx, gy)] = random.random() < self.initial_land_probability

        # Apply cellular automata iterations
        for iteration in range(self.iterations):
            new_grid = {}

            for gx in range(grid_size):
                for gy in range(grid_size):
                    # Count land neighbors
                    land_neighbors = 0
                    total_neighbors = 0

                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue

                            nx, ny = gx + dx, gy + dy
                            if 0 <= nx < grid_size and 0 <= ny < grid_size:
                                if grid[(nx, ny)]:
                                    land_neighbors += 1
                                total_neighbors += 1
                            else:
                                # Treat out-of-bounds as water
                                total_neighbors += 1

                    # Apply cellular automata rules
                    current_is_land = grid[(gx, gy)]

                    if current_is_land:
                        # Land cell: dies if too few land neighbors
                        new_grid[(gx, gy)] = land_neighbors >= self.death_limit
                    else:
                        # Water cell: becomes land if enough land neighbors
                        new_grid[(gx, gy)] = land_neighbors > self.birth_limit

            grid = new_grid

        # Return the result for the center chunk
        return "land" if grid[(center, center)] else "water"

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        summary = {
            'layer_name': self.name,
            'land_ratio': self.land_ratio,
            'land_percentage': f"{self.land_ratio * 10}%",
            'algorithm': self.algorithm
        }

        if self.algorithm == 'perlin_noise':
            summary.update({
                'scale': self.scale,
                'octaves': self.octaves,
                'persistence': self.persistence,
                'lacunarity': self.lacunarity
            })
        elif self.algorithm == 'cellular_automata':
            summary.update({
                'initial_land_probability': self.initial_land_probability,
                'iterations': self.iterations,
                'birth_limit': self.birth_limit,
                'death_limit': self.death_limit
            })

        return summary
