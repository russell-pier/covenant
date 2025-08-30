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
    Standardized data structure for fixed-chunk multi-scale sampling system.

    All chunks are always the same size (configurable, typically 16x16).
    Layers sample at different scales within these fixed chunks.
    """
    # Core world info
    seed: int
    chunk_size: int  # Fixed size for all chunks (e.g., 16)

    # Multi-scale sampling results
    continental_samples: Dict[Tuple[int, int], Any]  # Region coordinates (4x4 chunks)
    regional_samples: Dict[Tuple[int, int], Any]     # Chunk coordinates
    local_samples: Dict[Tuple[int, int], Any]        # Sub-chunk samples

    # Final chunk data - maps (chunk_x, chunk_y) to chunk data
    chunks: Dict[Tuple[int, int], Dict[str, Any]]

    # Layer metadata - tracks which layers have processed this data
    processed_layers: List[str]

    # Custom data - layers can store arbitrary data here
    custom_data: Dict[str, Any]

    def __post_init__(self):
        """Initialize empty collections if not provided."""
        if not hasattr(self, 'continental_samples') or self.continental_samples is None:
            self.continental_samples = {}
        if not hasattr(self, 'regional_samples') or self.regional_samples is None:
            self.regional_samples = {}
        if not hasattr(self, 'local_samples') or self.local_samples is None:
            self.local_samples = {}
        if not hasattr(self, 'chunks') or self.chunks is None:
            self.chunks = {}
        if not hasattr(self, 'processed_layers') or self.processed_layers is None:
            self.processed_layers = []
        if not hasattr(self, 'custom_data') or self.custom_data is None:
            self.custom_data = {}

    def get_chunk(self, chunk_x: int, chunk_y: int) -> Dict[str, Any]:
        """Get chunk data - fails if chunk doesn't exist."""
        chunk_key = (chunk_x, chunk_y)
        if chunk_key not in self.chunks:
            raise KeyError(f"❌ Chunk ({chunk_x}, {chunk_y}) does not exist in generation data. Available chunks: {list(self.chunks.keys())}")
        return self.chunks[chunk_key]
    
    def set_chunk_property(self, chunk_x: int, chunk_y: int, property_name: str, value: Any):
        """Set a property on a specific chunk, creating the chunk if it doesn't exist."""
        chunk_key = (chunk_x, chunk_y)
        if chunk_key not in self.chunks:
            # Create chunk with required basic properties
            self.chunks[chunk_key] = {
                'chunk_x': chunk_x,
                'chunk_y': chunk_y,
                'chunk_size': self.chunk_size
            }
        chunk = self.chunks[chunk_key]
        chunk[property_name] = value
    
    def get_chunk_property(self, chunk_x: int, chunk_y: int, property_name: str) -> Any:
        """Get a property from a specific chunk - fails if property doesn't exist."""
        chunk = self.get_chunk(chunk_x, chunk_y)
        if property_name not in chunk:
            raise KeyError(f"❌ Property '{property_name}' not found in chunk ({chunk_x}, {chunk_y}). Available properties: {list(chunk.keys())}")
        return chunk[property_name]

    # Multi-scale sampling helper methods
    def set_continental_sample(self, region_x: int, region_y: int, data: Any):
        """Set continental-level sample data for a region."""
        self.continental_samples[(region_x, region_y)] = data

    def get_continental_sample(self, region_x: int, region_y: int) -> Any:
        """Get continental-level sample data for a region."""
        return self.continental_samples.get((region_x, region_y))

    def set_regional_sample(self, chunk_x: int, chunk_y: int, data: Any):
        """Set regional-level sample data for a chunk."""
        self.regional_samples[(chunk_x, chunk_y)] = data

    def get_regional_sample(self, chunk_x: int, chunk_y: int) -> Any:
        """Get regional-level sample data for a chunk."""
        return self.regional_samples.get((chunk_x, chunk_y))

    def set_local_sample(self, sample_x: int, sample_y: int, data: Any):
        """Set local-level sample data for sub-chunk sampling."""
        self.local_samples[(sample_x, sample_y)] = data

    def get_local_sample(self, sample_x: int, sample_y: int) -> Any:
        """Get local-level sample data for sub-chunk sampling."""
        return self.local_samples.get((sample_x, sample_y))

    def get_region_for_chunk(self, chunk_x: int, chunk_y: int, region_size: int = 4) -> Tuple[int, int]:
        """Get the continental region coordinates for a given chunk."""
        return chunk_x // region_size, chunk_y // region_size


class GenerationLayer(ABC):
    """
    Base class for all generation layers.
    
    Each layer processes GenerationData and adds its own information.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        if config is None:
            raise ValueError(f"❌ Configuration is required for layer '{name}' - no fallback allowed")
        self.config = config
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
    
    def _get_config_value(self, key: str) -> Any:
        """Helper to get configuration values - fails if key doesn't exist."""
        if key not in self.config:
            raise KeyError(f"❌ Required configuration key '{key}' not found for layer '{self.name}'. Available keys: {list(self.config.keys())}")
        return self.config[key]
    
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
        if not self.layers:
            raise RuntimeError(f"❌ Pipeline '{self.name}' has no layers configured - cannot generate terrain")

        for layer in self.layers:
            data = layer.process(data, bounds)
            if layer.name not in data.processed_layers:
                data.processed_layers.append(layer.name)

        return data
    
    def get_layer_names(self) -> List[str]:
        """Get the names of all layers in the pipeline."""
        return [layer.name for layer in self.layers]




# WorldGenerationPipeline class removed - functionality moved to TierManager
