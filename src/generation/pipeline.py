#!/usr/bin/env python3
"""
Core pipeline infrastructure for the generation system.

Defines the base classes and data structures for the layered generation pipeline.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import random
import time


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
            data: The generation data to process
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)

        Returns:
            The processed generation data
        """
        for i, layer in enumerate(self.layers):
            if self.visualize:
                print(f"\n🔄 Processing layer {i+1}/{len(self.layers)}: {layer.name}")

            data = layer.process(data, bounds)
            if layer.name not in data.processed_layers:
                data.processed_layers.append(layer.name)

            # Visualize after each layer if enabled
            if self.visualize:
                self._visualize_layer_result(data, layer.name)
                if i < len(self.layers) - 1:  # Don't delay after the last layer
                    print("⏱️  Waiting 1 second...")
                    time.sleep(1)

        return data
    
    def get_layer_names(self) -> List[str]:
        """Get the names of all layers in the pipeline."""
        return [layer.name for layer in self.layers]

    def _visualize_layer_result(self, data: GenerationData, layer_name: str):
        """Visualize the result of a layer."""
        if not data.chunks:
            print(f"📊 {layer_name}: No chunks generated")
            return

        # Analyze the data
        land_count = sum(1 for chunk in data.chunks.values() if chunk.get('land_type') == 'land')
        water_count = len(data.chunks) - land_count
        land_ratio = land_count / (land_count + water_count) if (land_count + water_count) > 0 else 0

        print(f"📊 {layer_name}: {len(data.chunks)} chunks, {land_count} land, {water_count} water ({land_ratio:.1%} land)")

        # Create a visual grid
        chunk_pattern = {}
        for chunk_key, chunk in data.chunks.items():
            chunk_x, chunk_y = chunk_key
            land_type = chunk.get('land_type', 'water')
            chunk_pattern[(chunk_x, chunk_y)] = '█' if land_type == 'land' else '~'

        if chunk_pattern:
            min_x = min(x for x, y in chunk_pattern.keys())
            max_x = max(x for x, y in chunk_pattern.keys())
            min_y = min(y for x, y in chunk_pattern.keys())
            max_y = max(y for x, y in chunk_pattern.keys())

            print(f"🗺️  Grid visualization ({max_x - min_x + 1}x{max_y - min_y + 1}):")
            for y in range(max_y, min_y - 1, -1):
                line = ''
                for x in range(min_x, max_x + 1):
                    line += chunk_pattern.get((x, y), '?')
                print(f"   {line}")

        print()  # Empty line for spacing


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
        Generate chunks within the given bounds.

        Args:
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)

        Returns:
            Generated data for all chunks in bounds
        """
        # Check cache first
        if bounds in self._generation_cache:
            return self._generation_cache[bounds]

        # Initialize generation data
        data = GenerationData(
            seed=self.seed,
            chunk_size=self.chunk_size
        )

        # Process through world tier
        if self.world_tier:
            data = self.world_tier.process(data, bounds)

        # TODO: Process through region tier
        # TODO: Process through local tier

        # Cache the result
        self._generation_cache[bounds] = data

        return data
    
    def get_chunk_data(self, chunk_x: int, chunk_y: int) -> Dict[str, Any]:
        """Get data for a single chunk, generating if necessary."""
        bounds = (chunk_x, chunk_y, chunk_x, chunk_y)
        data = self.generate_chunks(bounds)
        return data.get_chunk(chunk_x, chunk_y)
