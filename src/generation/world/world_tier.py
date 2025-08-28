#!/usr/bin/env python3
"""
World Tier Pipeline

Manages the world-scale generation layers.
"""

from ..pipeline import GenerationPipeline
from .lands_and_seas import LandsAndSeasLayer
from .zoom import ZoomLayer


class WorldTier:
    """
    Factory for creating world tier pipelines with configured layers.
    """
    
    @staticmethod
    def create_default_pipeline(config: dict = None, visualize: bool = False) -> GenerationPipeline:
        """
        Create a default world tier pipeline.

        Args:
            config: Configuration dictionary for layers
            visualize: Whether to enable visualization between layers

        Returns:
            Configured world tier pipeline
        """
        config = config or {}
        pipeline = GenerationPipeline("world_tier", visualize=visualize)
        
        # Add lands_and_seas layer (our existing chunk-based land/water generation)
        lands_seas_config = config.get('lands_and_seas', {})
        lands_seas_layer = LandsAndSeasLayer(lands_seas_config)
        pipeline.add_layer(lands_seas_layer)
        
        # Future layers will be added here:
        # - climate layer
        # - continental_drift layer  
        # - major_features layer
        # etc.
        
        return pipeline
    
    @staticmethod
    def create_custom_pipeline(layer_configs: list, visualize: bool = False) -> GenerationPipeline:
        """
        Create a custom world tier pipeline from layer configurations.

        Args:
            layer_configs: List of (layer_name, config_dict) tuples
            visualize: Whether to enable visualization between layers

        Returns:
            Configured world tier pipeline
        """
        pipeline = GenerationPipeline("world_tier", visualize=visualize)
        
        for layer_name, config in layer_configs:
            if layer_name == "lands_and_seas":
                layer = LandsAndSeasLayer(config)
                pipeline.add_layer(layer)
            elif layer_name == "zoom":
                layer = ZoomLayer(config)
                pipeline.add_layer(layer)
            # Add other layer types here as they're implemented
            else:
                raise ValueError(f"Unknown world tier layer: {layer_name}")
        
        return pipeline
