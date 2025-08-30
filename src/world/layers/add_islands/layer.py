#!/usr/bin/env python3
"""
Islands Generation Layer

Converts isolated water chunks (completely surrounded by land) into land chunks.
This creates small islands and fills in water gaps within landmasses for more
natural-looking terrain.
"""

import os
from typing import Dict, Any, Tuple, Set

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from ...pipeline import GenerationLayer, GenerationData


class IslandsLayer(GenerationLayer):
    """
    Layer that converts isolated water chunks into small islands.
    
    This layer identifies water chunks that are completely surrounded by land
    and converts them into land chunks, creating small islands and filling
    water gaps within landmasses for more natural terrain.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("islands", config)
        
        # Load configuration from TOML file if no config provided
        if not config:
            self.config = self._load_config()
        
        # Extract configuration values
        self.conversion_probability = self._get_config_value('conversion_probability', 0.8)
        self.use_moore_neighborhood = self._get_config_value('use_moore_neighborhood', True)
        self.min_land_neighbors = self._get_config_value('min_land_neighbors', 8)
        self.require_all_neighbors = self._get_config_value('require_all_neighbors', True)
        
        # Validate configuration
        if not (0.0 <= self.conversion_probability <= 1.0):
            raise ValueError(f"conversion_probability must be 0.0-1.0, got {self.conversion_probability}")
        
        if self.use_moore_neighborhood:
            max_neighbors = 8
        else:
            max_neighbors = 4
            
        if self.min_land_neighbors > max_neighbors:
            raise ValueError(f"min_land_neighbors ({self.min_land_neighbors}) cannot be greater than maximum possible neighbors ({max_neighbors})")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from the layer's TOML file."""
        # Look for config in the centralized config directory
        config_path = os.path.join('config', 'world', 'layers', 'islands.toml')

        if not os.path.exists(config_path):
            return {}

        try:
            with open(config_path, 'rb') as f:
                data = tomllib.load(f)
            return data.get('islands', {})
        except Exception as e:
            return {}
    
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process chunks to convert isolated water into islands.

        Args:
            data: Generation data to process
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)

        Returns:
            Data with isolated water chunks converted to land
        """
        min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y = bounds
        
        # Find all water chunks that are candidates for island conversion
        island_candidates = self._find_island_candidates(data, bounds)
        
        # Convert candidates to islands based on probability
        conversions_made = 0
        for chunk_x, chunk_y in island_candidates:
            # Set deterministic seed for this chunk
            self._set_seed(data.seed, chunk_x, chunk_y, "island_conversion")
            
            # Apply conversion probability
            if self.rng.random() < self.conversion_probability:
                data.set_chunk_property(chunk_x, chunk_y, 'land_type', 'land')
                conversions_made += 1
        
        # Store island layer metadata
        data.custom_data['islands_layer'] = {
            'candidates_found': len(island_candidates),
            'conversions_made': conversions_made,
            'conversion_rate': conversions_made / max(1, len(island_candidates))
        }
        
        # Mark this layer as processed
        if self.name not in data.processed_layers:
            data.processed_layers.append(self.name)
        
        return data
    
    def _find_island_candidates(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> Set[Tuple[int, int]]:
        """
        Find all water chunks that are completely surrounded by land.

        Args:
            data: Generation data to analyze
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)

        Returns:
            Set of (chunk_x, chunk_y) coordinates that are island candidates
        """
        min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y = bounds
        candidates = set()
        
        # Check each water chunk to see if it's surrounded by land
        for chunk_x in range(min_chunk_x, max_chunk_x + 1):
            for chunk_y in range(min_chunk_y, max_chunk_y + 1):
                chunk_key = (chunk_x, chunk_y)
                
                # Skip if chunk doesn't exist
                if chunk_key not in data.chunks:
                    continue
                
                # Only consider water chunks
                current_land_type = data.get_chunk_property(chunk_x, chunk_y, 'land_type', 'water')
                if current_land_type != 'water':
                    continue
                
                # Check if this water chunk is surrounded by land
                if self._is_surrounded_by_land(data, chunk_x, chunk_y, bounds):
                    candidates.add((chunk_x, chunk_y))
        
        return candidates
    
    def _is_surrounded_by_land(self, data: GenerationData, chunk_x: int, chunk_y: int, 
                              bounds: Tuple[int, int, int, int]) -> bool:
        """
        Check if a water chunk is completely surrounded by land.

        Args:
            data: Generation data to analyze
            chunk_x: X coordinate of chunk to check
            chunk_y: Y coordinate of chunk to check
            bounds: World bounds to respect

        Returns:
            True if the chunk is surrounded by land
        """
        min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y = bounds
        
        # Define neighborhood based on configuration
        if self.use_moore_neighborhood:
            # 8-neighbor Moore neighborhood (includes diagonals)
            offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        else:
            # 4-neighbor Von Neumann neighborhood (orthogonal only)
            offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        land_neighbors = 0
        valid_neighbors = 0
        
        for dx, dy in offsets:
            neighbor_x = chunk_x + dx
            neighbor_y = chunk_y + dy
            
            # Skip neighbors outside bounds
            if (neighbor_x < min_chunk_x or neighbor_x > max_chunk_x or
                neighbor_y < min_chunk_y or neighbor_y > max_chunk_y):
                if not self.require_all_neighbors:
                    # If we don't require all neighbors to exist, skip out-of-bounds
                    continue
                else:
                    # If we require all neighbors, treat out-of-bounds as non-land
                    valid_neighbors += 1
                    continue
            
            valid_neighbors += 1
            neighbor_key = (neighbor_x, neighbor_y)
            
            # Check if neighbor chunk exists and is land
            if neighbor_key in data.chunks:
                neighbor_land_type = data.get_chunk_property(neighbor_x, neighbor_y, 'land_type', 'water')
                if neighbor_land_type == 'land':
                    land_neighbors += 1
            # If neighbor doesn't exist, treat as water (not land)
        
        # Determine if surrounded by land based on configuration
        if self.require_all_neighbors and valid_neighbors < len(offsets):
            # If we require all neighbors but some are missing/out-of-bounds, not surrounded
            return False
        
        # Check if we have enough land neighbors
        if self.require_all_neighbors:
            # All existing neighbors must be land
            return land_neighbors == valid_neighbors and valid_neighbors > 0
        else:
            # Just need minimum number of land neighbors
            return land_neighbors >= self.min_land_neighbors
    
    def _count_land_neighbors(self, data: GenerationData, chunk_x: int, chunk_y: int,
                             bounds: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """
        Count land neighbors around a chunk.

        Args:
            data: Generation data to analyze
            chunk_x: X coordinate of chunk to check
            chunk_y: Y coordinate of chunk to check
            bounds: World bounds to respect

        Returns:
            Tuple of (land_neighbors, total_valid_neighbors)
        """
        min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y = bounds
        
        if self.use_moore_neighborhood:
            offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        else:
            offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        land_neighbors = 0
        valid_neighbors = 0
        
        for dx, dy in offsets:
            neighbor_x = chunk_x + dx
            neighbor_y = chunk_y + dy
            
            # Skip neighbors outside bounds
            if (neighbor_x < min_chunk_x or neighbor_x > max_chunk_x or
                neighbor_y < min_chunk_y or neighbor_y > max_chunk_y):
                continue
            
            valid_neighbors += 1
            neighbor_key = (neighbor_x, neighbor_y)
            
            if neighbor_key in data.chunks:
                neighbor_land_type = data.get_chunk_property(neighbor_x, neighbor_y, 'land_type', 'water')
                if neighbor_land_type == 'land':
                    land_neighbors += 1
        
        return land_neighbors, valid_neighbors
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            'layer_name': self.name,
            'conversion_probability': self.conversion_probability,
            'use_moore_neighborhood': self.use_moore_neighborhood,
            'min_land_neighbors': self.min_land_neighbors,
            'require_all_neighbors': self.require_all_neighbors,
            'max_possible_neighbors': 8 if self.use_moore_neighborhood else 4
        }
    
    def get_layer_statistics(self, data: GenerationData) -> Dict[str, Any]:
        """
        Get statistics about island layer processing.

        Args:
            data: Generation data that was processed

        Returns:
            Dictionary of layer statistics
        """
        island_data = data.custom_data.get('islands_layer', {})
        
        return {
            'layer_name': self.name,
            'candidates_found': island_data.get('candidates_found', 0),
            'conversions_made': island_data.get('conversions_made', 0),
            'conversion_rate': island_data.get('conversion_rate', 0.0),
            'was_processed': self.name in data.processed_layers
        }