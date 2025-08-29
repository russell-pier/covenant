#!/usr/bin/env python3
"""
Lands and Seas Generation Layer

Determines basic land/water distribution for chunks.
This is the foundation layer that establishes the fundamental geography.
"""

import os
import random
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
        self.algorithm = self._get_config_value('algorithm', 'random_chunks')
        
        # Validate configuration
        if not (1 <= self.land_ratio <= 10):
            raise ValueError(f"land_ratio must be between 1 and 10, got {self.land_ratio}")
        
        if self.algorithm not in ['random_chunks']:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")

    def _get_config_value(self, key: str, default: Any) -> Any:
        """Get a configuration value with a default fallback."""
        return self.config.get(key, default)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from the layer's TOML file."""
        config_path = os.path.join(os.path.dirname(__file__), 'config.toml')
        
        if not os.path.exists(config_path):
            return {}
        
        try:
            with open(config_path, 'rb') as f:
                data = tomllib.load(f)
            return data.get('lands_and_seas', {})
        except Exception as e:
            print(f"Warning: Could not load lands_and_seas config: {e}")
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
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            'layer_name': self.name,
            'land_ratio': self.land_ratio,
            'land_percentage': f"{self.land_ratio * 10}%",
            'algorithm': self.algorithm
        }
