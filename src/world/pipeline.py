#!/usr/bin/env python3
"""
Core pipeline infrastructure for the generation system.

Defines the base classes and data structures for the layered generation pipeline.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import random


@dataclass
class GenerationData:
    """
    Standardized data structure passed between generation layers.
    
    This ensures all layers can work together regardless of order.
    """
    # Core world info
    seed: int
    chunk_size: int
    
    # Chunk data - maps (chunk_x, chunk_y) to chunk data
    chunks: Dict[Tuple[int, int], Dict[str, Any]] = field(default_factory=dict)
    
    # Layer metadata - tracks which layers have processed this data
    processed_layers: List[str] = field(default_factory=list)
    
    # Custom data - layers can store arbitrary data here
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def get_chunk(self, chunk_x: int, chunk_y: int) -> Dict[str, Any]:
        """Get chunk data, creating empty chunk if it doesn't exist."""
        chunk_key = (chunk_x, chunk_y)
        if chunk_key not in self.chunks:
            self.chunks[chunk_key] = {
                'chunk_x': chunk_x,
                'chunk_y': chunk_y,
                'chunk_size': self.chunk_size
            }
        return self.chunks[chunk_key]
    
    def set_chunk_property(self, chunk_x: int, chunk_y: int, property_name: str, value: Any):
        """Set a property on a specific chunk."""
        chunk = self.get_chunk(chunk_x, chunk_y)
        chunk[property_name] = value
    
    def get_chunk_property(self, chunk_x: int, chunk_y: int, property_name: str, default: Any = None) -> Any:
        """Get a property from a specific chunk."""
        chunk = self.get_chunk(chunk_x, chunk_y)
        return chunk.get(property_name, default)


class GenerationLayer(ABC):
    """
    Base class for all generation layers.
    
    Each layer processes GenerationData and adds its own information.
    """
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.rng = random.Random()
    
    @abstractmethod
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process the generation data within the given bounds.
        
        Args:
            data: The generation data to process
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)
            
        Returns:
            The modified generation data
        """
        pass
    
    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """Helper to get configuration values."""
        return self.config.get(key, default)
    
    def _set_seed(self, base_seed: int, *additional_components):
        """Set the RNG seed based on base seed and additional components."""
        combined_seed = hash((base_seed, self.name, *additional_components)) % (2**32)
        self.rng.seed(combined_seed)


class GenerationPipeline:
    """
    Manages a sequence of generation layers.
    """

    def __init__(self, name: str):
        self.name = name
        self.layers: List[GenerationLayer] = []
    
    def add_layer(self, layer: GenerationLayer):
        """Add a layer to the pipeline."""
        self.layers.append(layer)
    
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process data through all layers in sequence.

        Args:
            data: The generation data to process
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)

        Returns:
            The processed generation data
        """
        for layer in self.layers:
            data = layer.process(data, bounds)
            if layer.name not in data.processed_layers:
                data.processed_layers.append(layer.name)

        return data
    
    def get_layer_names(self) -> List[str]:
        """Get the names of all layers in the pipeline."""
        return [layer.name for layer in self.layers]




# WorldGenerationPipeline class removed - functionality moved to TierManager
