#!/usr/bin/env python3
"""
World Tier Pipeline

Manages the world-scale generation layers.
"""

from typing import List, Tuple, Dict, Any

from src.world.layers.add_islands.layer import IslandsLayer
from .pipeline import GenerationPipeline
from .layers.lands_and_seas import LandsAndSeasLayer
from .layers.zoom import ZoomLayer


class WorldTier:
    """
    Factory for creating world tier pipelines with configured layers.
    """
    

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
