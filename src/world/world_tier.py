#!/usr/bin/env python3
"""
World Tier Pipeline

Manages the world-scale generation layers.
"""

from typing import Optional, List, Tuple, Dict, Any

from src.world.layers.add_islands.layer import IslandsLayer
from .pipeline import GenerationPipeline
from .layers.lands_and_seas import LandsAndSeasLayer
from .layers.zoom import ZoomLayer


class WorldTier:
    """
    Factory for creating world tier pipelines with configured layers.
    """
    
    @staticmethod
    def create_default_pipeline(config: Optional[dict] = None) -> GenerationPipeline:
        """
        Create a default world tier pipeline.

        Args:
            config: Configuration dictionary for layers

        Returns:
            Configured world tier pipeline
        """
        config = config or {}
        pipeline = GenerationPipeline("world_tier")
        
        # Add lands_and_seas layer (our existing chunk-based land/water generation)
        lands_seas_config = config.get('lands_and_seas', {})
        lands_seas_layer = LandsAndSeasLayer(lands_seas_config)
        pipeline.add_layer(lands_seas_layer)
        
        # Add zoom layer for cellular automata-based refinement
        zoom_config_1 = config.get('zoom', {})
        zoom_layer_1 = ZoomLayer(zoom_config_1)
        pipeline.add_layer(zoom_layer_1)
        
        # Add islands layer for creating small islands
        islands_config = config.get('islands', {})
        islands_layer = IslandsLayer(islands_config)
        pipeline.add_layer(islands_layer)
        
        # Add second zoom layer for additional refinement
        zoom_config_2 = config.get('zoom_2', {})
        zoom_layer_2 = ZoomLayer(zoom_config_2)
        pipeline.add_layer(zoom_layer_2)
        
        # Future layers will be added here:
        # - climate layer
        # - continental_drift layer  
        # - major_features layer
        # etc.
        
        return pipeline
    
    @staticmethod
    def create_custom_pipeline(layer_configs: List[Tuple[str, Dict[str, Any]]]) -> GenerationPipeline:
        """
        Create a custom world tier pipeline from layer configurations.

        Args:
            layer_configs: List of (layer_name, config_dict) tuples

        Returns:
            Configured world tier pipeline
        """
        pipeline = GenerationPipeline("world_tier")

        for layer_name, config in layer_configs:
            if layer_name == "lands_and_seas":
                layer = LandsAndSeasLayer(config)
                pipeline.add_layer(layer)
            elif layer_name == "zoom":
                layer = ZoomLayer(config)
                pipeline.add_layer(layer)
            elif layer_name == "islands":
                layer = IslandsLayer(config)
                pipeline.add_layer(layer)
            # Add other layer types here as they're implemented
            else:
                raise ValueError(f"Unknown world tier layer: {layer_name}")

        return pipeline
