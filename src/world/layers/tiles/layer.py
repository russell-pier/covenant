#!/usr/bin/env python3
"""
Tiles Layer - Multi-Scale Sampling System

Converts multi-scale sampling data to final tile types. Places individual tiles
based on continental, regional, and local sampling results. Handles tile-specific
rules like ore placement, vegetation, etc.
"""

import math
from typing import Tuple, Dict, Any
from ...pipeline import GenerationLayer, GenerationData


class TilesLayer(GenerationLayer):
    """
    Final tile placement layer using multi-scale sampling results.
    
    Converts sampling data from all previous layers into actual tile types
    that can be rendered. Handles special tile placement rules.
    """
    
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process final tile placement.
        
        Args:
            data: Generation data with all sampling layers complete
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)
            
        Returns:
            Updated generation data with final tile assignments
        """
        self._set_seed(data.seed, "tiles")
        
        # Get configuration
        default_land_tile = self._get_config_value("default_land_tile")
        default_water_tile = self._get_config_value("default_water_tile")
        coastal_tile = self._get_config_value("coastal_tile")
        deep_water_tile = self._get_config_value("deep_water_tile")
        
        min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y = bounds
        
        # Process each chunk
        for chunk_x in range(min_chunk_x, max_chunk_x + 1):
            for chunk_y in range(min_chunk_y, max_chunk_y + 1):
                self._generate_chunk_tiles(
                    data, chunk_x, chunk_y, default_land_tile, default_water_tile,
                    coastal_tile, deep_water_tile
                )

        # Mark this layer as processed
        if self.name not in data.processed_layers:
            data.processed_layers.append(self.name)

        return data
    
    def _generate_chunk_tiles(self, data: GenerationData, chunk_x: int, chunk_y: int,
                            default_land_tile: str, default_water_tile: str,
                            coastal_tile: str, deep_water_tile: str):
        """
        Generate final tiles for a specific chunk.
        
        Args:
            data: Generation data with sampling results
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            default_land_tile: Default tile type for land
            default_water_tile: Default tile type for water
            coastal_tile: Tile type for coastal areas
            deep_water_tile: Tile type for deep water
        """
        chunk_size = data.chunk_size
        
        # Initialize chunk data if not exists
        chunk_key = (chunk_x, chunk_y)
        if chunk_key not in data.chunks:
            data.chunks[chunk_key] = {
                'chunk_x': chunk_x,
                'chunk_y': chunk_y,
                'chunk_size': chunk_size,
                'tiles': {}
            }
        
        chunk_data = data.chunks[chunk_key]
        
        # Generate tiles for each position in the chunk
        for tile_x in range(chunk_size):
            for tile_y in range(chunk_size):
                world_x = chunk_x * chunk_size + tile_x
                world_y = chunk_y * chunk_size + tile_y
                
                tile_type = self._determine_tile_type(
                    data, world_x, world_y, chunk_x, chunk_y,
                    default_land_tile, default_water_tile, coastal_tile, deep_water_tile
                )
                
                chunk_data['tiles'][(world_x, world_y)] = tile_type
    
    def _determine_tile_type(self, data: GenerationData, world_x: int, world_y: int,
                           chunk_x: int, chunk_y: int, default_land_tile: str,
                           default_water_tile: str, coastal_tile: str,
                           deep_water_tile: str) -> str:
        """
        Determine the final tile type for a specific world position.
        
        Args:
            data: Generation data with sampling results
            world_x: World X coordinate
            world_y: World Y coordinate
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            default_land_tile: Default land tile type
            default_water_tile: Default water tile type
            coastal_tile: Coastal tile type
            deep_water_tile: Deep water tile type
            
        Returns:
            Final tile type string
        """
        # Get terrain type from local sampling
        terrain_type = self._get_local_terrain(data, world_x, world_y)
        
        if terrain_type == 'land':
            # Check if this is coastal land
            if self._is_coastal_position(data, world_x, world_y):
                return coastal_tile
            else:
                return default_land_tile
        else:
            # Water terrain - check if deep water
            if self._is_deep_water(data, world_x, world_y, chunk_x, chunk_y):
                return deep_water_tile
            else:
                return default_water_tile
    
    def _get_local_terrain(self, data: GenerationData, world_x: int, world_y: int) -> str:
        """
        Get terrain type from local sampling data.
        
        Args:
            data: Generation data
            world_x: World X coordinate
            world_y: World Y coordinate
            
        Returns:
            'land' or 'water'
        """
        # Check if we have local sample data for this position
        local_sample = data.get_local_sample(world_x, world_y)
        if local_sample is not None:
            return local_sample['terrain_type']
        
        # Fall back to regional data
        chunk_size = data.chunk_size
        chunk_x = world_x // chunk_size
        chunk_y = world_y // chunk_size
        
        regional_sample = data.get_regional_sample(chunk_x, chunk_y)
        if regional_sample is not None:
            return regional_sample['terrain_type']
        
        # Final fallback to continental data
        region_size = 4  # Should get from config
        region_x = chunk_x // region_size
        region_y = chunk_y // region_size
        
        continental_sample = data.get_continental_sample(region_x, region_y)
        if continental_sample is not None:
            return 'land' if continental_sample['designation'] == 'continent' else 'water'
        
        # Ultimate fallback
        return 'water'
    
    def _is_coastal_position(self, data: GenerationData, world_x: int, world_y: int) -> bool:
        """
        Check if a land position is coastal (adjacent to water).
        
        Args:
            data: Generation data
            world_x: World X coordinate
            world_y: World Y coordinate
            
        Returns:
            True if position is coastal
        """
        # Check 8 neighbors for water
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                neighbor_x = world_x + dx
                neighbor_y = world_y + dy
                neighbor_terrain = self._get_local_terrain(data, neighbor_x, neighbor_y)
                
                if neighbor_terrain == 'water':
                    return True
        
        return False
    
    def _is_deep_water(self, data: GenerationData, world_x: int, world_y: int,
                      chunk_x: int, chunk_y: int) -> bool:
        """
        Check if a water position is deep water (far from land).
        
        Args:
            data: Generation data
            world_x: World X coordinate
            world_y: World Y coordinate
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            
        Returns:
            True if position is deep water
        """
        # Check if this chunk is in an ocean region
        region_size = 4  # Should get from config
        region_x = chunk_x // region_size
        region_y = chunk_y // region_size
        
        continental_sample = data.get_continental_sample(region_x, region_y)
        if continental_sample is None or continental_sample['designation'] != 'ocean':
            return False
        
        # Check if regional terrain is also water
        regional_sample = data.get_regional_sample(chunk_x, chunk_y)
        if regional_sample is None or regional_sample['terrain_type'] != 'water':
            return False
        
        # Check if no land in immediate vicinity (larger radius)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                neighbor_x = world_x + dx
                neighbor_y = world_y + dy
                neighbor_terrain = self._get_local_terrain(data, neighbor_x, neighbor_y)
                
                if neighbor_terrain == 'land':
                    return False
        
        return True
