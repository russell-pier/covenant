#!/usr/bin/env python3
"""
Generation Pipeline System

Core classes for the world generation pipeline architecture.
"""

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional


@dataclass
class GenerationData:
    """
    Standardized data structure passed between generation layers.
    """
    seed: int
    chunk_size: int
    chunks: Dict[Tuple[int, int], List[List[str]]] = field(default_factory=dict)
    processed_layers: List[str] = field(default_factory=list)
    custom_data: Dict[Any, Any] = field(default_factory=dict)

    def set_chunk_property(self, chunk_x: int, chunk_y: int, property_name: str, value: Any):
        """Set a property for a chunk."""
        chunk_key = (chunk_x, chunk_y)
        if chunk_key not in self.custom_data:
            self.custom_data[chunk_key] = {}
        self.custom_data[chunk_key][property_name] = value

    def get_chunk_property(self, chunk_x: int, chunk_y: int, property_name: str, default: Any = None) -> Any:
        """Get a property for a chunk."""
        chunk_key = (chunk_x, chunk_y)
        if chunk_key in self.custom_data and property_name in self.custom_data[chunk_key]:
            return self.custom_data[chunk_key][property_name]
        return default


class GenerationLayer(ABC):
    """
    Base class for all generation layers.

    Each layer processes GenerationData and adds its own modifications
    while preserving data from previous layers.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.rng = random.Random()

    @abstractmethod
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process the generation data within the specified bounds.

        Args:
            data: Current generation data
            bounds: (min_x, min_y, max_x, max_y) chunk coordinates

        Returns:
            Modified generation data
        """
        pass

    def _set_seed(self, base_seed: int, *additional_components):
        """Set the RNG seed based on base seed and additional components."""
        combined_seed = hash((base_seed, self.name, *additional_components)) % (2**32)
        self.rng.seed(combined_seed)


class GenerationPipeline:
    """
    Manages a sequence of generation layers.
    """

    def __init__(self, name: str, visualize: bool = False):
        self.name = name
        self.layers: List[GenerationLayer] = []
        self.visualize = visualize

    def add_layer(self, layer: GenerationLayer):
        """Add a layer to the pipeline."""
        self.layers.append(layer)

    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process data through all layers in sequence.

        Args:
            data: Initial generation data
            bounds: Chunk bounds to process

        Returns:
            Processed generation data
        """
        current_data = data

        for layer in self.layers:
            if self.visualize:
                print(f"Processing layer: {layer.name}")

            current_data = layer.process(current_data, bounds)

            # Track which layers have processed this data
            if layer.name not in current_data.processed_layers:
                current_data.processed_layers.append(layer.name)

        return current_data


class WorldGenerationPipeline:
    """
    Main world generation pipeline that coordinates all tiers.

    Currently only implements the World tier, but designed to support
    Region and Local tiers in the future.
    """

    def __init__(self, seed: int, chunk_size: int):
        self.seed = seed
        self.chunk_size = chunk_size

        # Tiers (only World tier implemented for now)
        self.world_tier: Optional[GenerationPipeline] = None
        self.region_tier: Optional[GenerationPipeline] = None  # Future
        self.local_tier: Optional[GenerationPipeline] = None   # Future

        # Cache for generated data
        self._generation_cache: Dict[Tuple[int, int, int, int], GenerationData] = {}

    def set_world_tier(self, pipeline: GenerationPipeline):
        """Set the world tier pipeline."""
        self.world_tier = pipeline

    def generate_chunks(self, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Generate chunks within the specified bounds.

        Args:
            bounds: (min_x, min_y, max_x, max_y) chunk coordinates

        Returns:
            Generated data for the specified bounds
        """
        # Check cache first
        if bounds in self._generation_cache:
            return self._generation_cache[bounds]

        # Create initial generation data
        data = GenerationData(
            seed=self.seed,
            chunk_size=self.chunk_size
        )

        # Process through world tier
        if self.world_tier:
            data = self.world_tier.process(data, bounds)

        # Future: Process through region and local tiers

        # Cache the result
        self._generation_cache[bounds] = data

        return data

    def clear_cache(self):
        """Clear the generation cache to free memory."""
        self._generation_cache.clear()