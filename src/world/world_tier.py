#!/usr/bin/env python3
"""
World Tier Pipeline

Manages the world-scale generation layers.
"""

from typing import List, Tuple, Dict, Any

from .pipeline import GenerationPipeline
from .layers.continental import ContinentalLayer
from .layers.regional import RegionalLayer
from .layers.local import LocalLayer
from .layers.tiles import TilesLayer


class WorldTier:
    """
    Factory for creating world tier pipelines with multi-scale sampling layers.

    Creates pipelines using the new fixed-chunk system:
    - Continental: Region-level sampling (4x4 chunks)
    - Regional: Chunk-level sampling
    - Local: Sub-chunk sampling
    - Tiles: Final tile placement
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
            if layer_name == "continental":
                layer = ContinentalLayer(layer_name, config)
                pipeline.add_layer(layer)
            elif layer_name == "regional":
                layer = RegionalLayer(layer_name, config)
                pipeline.add_layer(layer)
            elif layer_name == "local":
                layer = LocalLayer(layer_name, config)
                pipeline.add_layer(layer)
            elif layer_name == "tiles":
                layer = TilesLayer(layer_name, config)
                pipeline.add_layer(layer)
            else:
                raise ValueError(f"Unknown world tier layer: {layer_name}. Available layers: continental, regional, local, tiles")

        return pipeline
