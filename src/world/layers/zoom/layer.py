#!/usr/bin/env python3
"""
Zoom Layer for Progressive Terrain Detail Refinement

Subdivides chunks and applies cellular automata to create natural coastlines
and terrain boundaries while preserving overall geographic structure.
"""

import os
import random
from typing import Dict, Any, Tuple, List, Set
from collections import defaultdict

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from ...pipeline import GenerationLayer, GenerationData


class ZoomLayer(GenerationLayer):
    """
    Layer that subdivides chunks and refines terrain boundaries using cellular automata.
    
    This layer can be used multiple times in sequence to progressively add detail
    while maintaining the overall geographic structure from previous layers.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("zoom", config)
        
        # Load configuration from TOML file if no config provided
        if not config:
            self.config = self._load_config()
        
        # Extract configuration values
        self.subdivision_factor = self._get_config_value('subdivision_factor', 2)
        self.land_expansion_threshold = self._get_config_value('land_expansion_threshold', 3)
        self.erosion_probability = self._get_config_value('erosion_probability', 0.25)
        self.iterations = self._get_config_value('iterations', 6)

        # Multi-pass configuration
        self.use_multi_pass = self._get_config_value('use_multi_pass', True)
        self.pass_1_iterations = self._get_config_value('pass_1_iterations', 3)
        self.pass_1_expansion_threshold = self._get_config_value('pass_1_expansion_threshold', 2)
        self.pass_1_erosion_probability = self._get_config_value('pass_1_erosion_probability', 0.1)
        self.pass_2_iterations = self._get_config_value('pass_2_iterations', 3)
        self.pass_2_expansion_threshold = self._get_config_value('pass_2_expansion_threshold', 4)
        self.pass_2_erosion_probability = self._get_config_value('pass_2_erosion_probability', 0.3)

        # Protection and advanced settings
        self.protect_interior = self._get_config_value('protect_interior', False)
        self.interior_threshold = self._get_config_value('interior_threshold', 8)
        self.use_moore_neighborhood = self._get_config_value('use_moore_neighborhood', True)
        self.preserve_islands = self._get_config_value('preserve_islands', True)
        self.min_island_size = self._get_config_value('min_island_size', 1)

        # Enhanced randomization
        self.add_noise = self._get_config_value('add_noise', True)
        self.noise_probability = self._get_config_value('noise_probability', 0.15)
        self.edge_noise_boost = self._get_config_value('edge_noise_boost', True)
        self.edge_noise_probability = self._get_config_value('edge_noise_probability', 0.25)

        # Fractal enhancement
        self.fractal_perturbation = self._get_config_value('fractal_perturbation', True)
        self.perturbation_strength = self._get_config_value('perturbation_strength', 0.3)
        
        # Validate configuration
        if self.subdivision_factor < 2:
            raise ValueError(f"subdivision_factor must be >= 2, got {self.subdivision_factor}")
        if not (0.0 <= self.erosion_probability <= 1.0):
            raise ValueError(f"erosion_probability must be 0.0-1.0, got {self.erosion_probability}")
        if not (0.0 <= self.noise_probability <= 1.0):
            raise ValueError(f"noise_probability must be 0.0-1.0, got {self.noise_probability}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from the layer's TOML file."""
        # Look for config in the centralized config directory
        config_path = os.path.join('config', 'world', 'layers', 'zoom.toml')

        if not os.path.exists(config_path):
            return {}

        try:
            with open(config_path, 'rb') as f:
                data = tomllib.load(f)
            return data.get('zoom', {})
        except Exception as e:
            return {}
    
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process chunks to add terrain detail through subdivision and cellular automata.

        Args:
            data: Generation data to process
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)

        Returns:
            Data with subdivided chunks and refined terrain boundaries
        """
        min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y = bounds
        
        # Create new chunk data with subdivided chunks
        new_chunks = {}
        
        # For zoom layers, we need to process all existing chunks since previous
        # zoom layers may have created chunks in subdivided coordinate space
        chunks_to_process = list(data.chunks.values())

        # Subdivide each chunk
        for parent_chunk in chunks_to_process:
            subdivided_chunks = self._subdivide_chunk(data.seed, parent_chunk)

            # Add subdivided chunks to new chunk data
            for sub_chunk in subdivided_chunks:
                sub_key = (sub_chunk['chunk_x'], sub_chunk['chunk_y'])
                new_chunks[sub_key] = sub_chunk
        
        # Apply cellular automata to refine boundaries
        # Calculate bounds for the subdivided chunks
        if new_chunks:
            chunk_coords = list(new_chunks.keys())
            min_sub_x = min(x for x, y in chunk_coords)
            max_sub_x = max(x for x, y in chunk_coords)
            min_sub_y = min(y for x, y in chunk_coords)
            max_sub_y = max(y for x, y in chunk_coords)
            sub_bounds = (min_sub_x, min_sub_y, max_sub_x, max_sub_y)
        else:
            sub_bounds = bounds

        refined_chunks = self._apply_cellular_automata(data.seed, new_chunks, sub_bounds)
        
        # Update the generation data with refined chunks
        data.chunks.update(refined_chunks)
        
        # Mark this layer as processed
        if self.name not in data.processed_layers:
            data.processed_layers.append(self.name)
        
        return data
    
    def _subdivide_chunk(self, seed: int, parent_chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Subdivide a parent chunk into smaller sub-chunks with dynamic sizing.

        This method is agnostic about absolute chunk sizes and dynamically
        calculates the new chunk size based on the subdivision factor.
        This allows for flexible chaining of multiple zoom layers.

        Args:
            seed: World generation seed
            parent_chunk: The chunk to subdivide

        Returns:
            List of sub-chunk dictionaries with dynamically calculated sizes
        """
        parent_x = parent_chunk['chunk_x']
        parent_y = parent_chunk['chunk_y']
        parent_size = parent_chunk['chunk_size']
        parent_land_type = parent_chunk.get('land_type', 'water')

        sub_chunks = []
        # Dynamic chunk size calculation - halve the parent size
        # This works regardless of the input chunk size (32→16, 16→8, 8→4, etc.)
        sub_chunk_size = parent_size // self.subdivision_factor

        # Ensure minimum chunk size of 1 tile
        if sub_chunk_size < 1:
            sub_chunk_size = 1

        for sub_x in range(self.subdivision_factor):
            for sub_y in range(self.subdivision_factor):
                # Calculate new chunk coordinates in the subdivided space
                new_chunk_x = parent_x * self.subdivision_factor + sub_x
                new_chunk_y = parent_y * self.subdivision_factor + sub_y

                # Create sub-chunk with dynamically calculated size
                sub_chunk = {
                    'chunk_x': new_chunk_x,
                    'chunk_y': new_chunk_y,
                    'chunk_size': sub_chunk_size,  # Dynamic size based on parent
                    'land_type': parent_land_type,
                    'parent_chunk_x': parent_x,
                    'parent_chunk_y': parent_y,
                    'subdivision_level': parent_chunk.get('subdivision_level', 0) + 1,
                    'original_chunk_size': parent_chunk.get('original_chunk_size', parent_size)
                }

                sub_chunks.append(sub_chunk)

        return sub_chunks

    def _apply_cellular_automata(self, seed: int, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                                bounds: Tuple[int, int, int, int]) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """
        Apply cellular automata rules to create natural coastlines.

        Args:
            seed: World generation seed
            chunks: Dictionary of chunk data
            bounds: Bounds in subdivided coordinate system

        Returns:
            Dictionary of refined chunk data
        """
        # Use the provided bounds directly (already in subdivided coordinate system)
        sub_min_x, sub_min_y, sub_max_x, sub_max_y = bounds

        # Set up RNG for this layer
        self._set_seed(seed, "cellular_automata")

        # Apply fractal perturbation first if enabled
        if self.fractal_perturbation:
            chunks = self._apply_fractal_perturbation(chunks, sub_min_x, sub_min_y, sub_max_x, sub_max_y)

        # Apply cellular automata with multi-pass if enabled
        if self.use_multi_pass:
            # Pass 1: Aggressive expansion for rough shape
            for iteration in range(self.pass_1_iterations):
                chunks = self._cellular_automata_iteration(
                    chunks, sub_min_x, sub_min_y, sub_max_x, sub_max_y,
                    expansion_threshold=self.pass_1_expansion_threshold,
                    erosion_probability=self.pass_1_erosion_probability
                )

            # Pass 2: Detail refinement
            for iteration in range(self.pass_2_iterations):
                chunks = self._cellular_automata_iteration(
                    chunks, sub_min_x, sub_min_y, sub_max_x, sub_max_y,
                    expansion_threshold=self.pass_2_expansion_threshold,
                    erosion_probability=self.pass_2_erosion_probability
                )
        else:
            # Single pass with default parameters
            for iteration in range(self.iterations):
                chunks = self._cellular_automata_iteration(
                    chunks, sub_min_x, sub_min_y, sub_max_x, sub_max_y,
                    expansion_threshold=self.land_expansion_threshold,
                    erosion_probability=self.erosion_probability
                )

        return chunks

    def _cellular_automata_iteration(self, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                                   min_x: int, min_y: int, max_x: int, max_y: int,
                                   expansion_threshold: int = None, erosion_probability: float = None) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """
        Perform one iteration of cellular automata.

        Args:
            chunks: Current chunk data
            min_x, min_y, max_x, max_y: Bounds in subdivided coordinate system
            expansion_threshold: Override for land expansion threshold
            erosion_probability: Override for erosion probability

        Returns:
            Updated chunk data
        """
        # Use provided parameters or defaults
        exp_threshold = expansion_threshold if expansion_threshold is not None else self.land_expansion_threshold
        ero_probability = erosion_probability if erosion_probability is not None else self.erosion_probability

        new_chunks = chunks.copy()

        for chunk_x in range(min_x, max_x + 1):
            for chunk_y in range(min_y, max_y + 1):
                chunk_key = (chunk_x, chunk_y)
                if chunk_key not in chunks:
                    continue

                current_chunk = chunks[chunk_key]
                current_land_type = current_chunk.get('land_type', 'water')

                # Count land neighbors
                land_neighbors = self._count_land_neighbors(chunks, chunk_x, chunk_y, min_x, min_y, max_x, max_y)
                total_neighbors = self._count_total_neighbors(chunk_x, chunk_y, min_x, min_y, max_x, max_y)

                # Apply cellular automata rules
                new_land_type = self._apply_ca_rules(current_land_type, land_neighbors, total_neighbors,
                                                   exp_threshold, ero_probability)

                # Add enhanced noise if enabled
                noise_prob = self.noise_probability

                # Boost noise at land/water boundaries for more fractal variation
                if self.edge_noise_boost and self._is_at_boundary(chunks, chunk_x, chunk_y, min_x, min_y, max_x, max_y):
                    noise_prob = self.edge_noise_probability

                if self.add_noise and self.rng.random() < noise_prob:
                    new_land_type = 'land' if new_land_type == 'water' else 'water'

                # Update chunk
                new_chunk = current_chunk.copy()
                new_chunk['land_type'] = new_land_type
                new_chunks[chunk_key] = new_chunk

        return new_chunks

    def _count_land_neighbors(self, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                            chunk_x: int, chunk_y: int, min_x: int, min_y: int, max_x: int, max_y: int) -> int:
        """Count the number of land neighbors around a chunk."""
        land_count = 0

        # Define neighborhood (Moore or Von Neumann)
        if self.use_moore_neighborhood:
            # 8-neighbor Moore neighborhood
            offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        else:
            # 4-neighbor Von Neumann neighborhood
            offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dx, dy in offsets:
            neighbor_x = chunk_x + dx
            neighbor_y = chunk_y + dy

            # Handle boundaries - treat out-of-bounds as water
            if neighbor_x < min_x or neighbor_x > max_x or neighbor_y < min_y or neighbor_y > max_y:
                continue

            neighbor_key = (neighbor_x, neighbor_y)
            if neighbor_key in chunks:
                neighbor_land_type = chunks[neighbor_key].get('land_type', 'water')
                if neighbor_land_type == 'land':
                    land_count += 1

        return land_count

    def _count_total_neighbors(self, chunk_x: int, chunk_y: int, min_x: int, min_y: int, max_x: int, max_y: int) -> int:
        """Count the total number of valid neighbors (within bounds)."""
        total_count = 0

        if self.use_moore_neighborhood:
            offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        else:
            offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dx, dy in offsets:
            neighbor_x = chunk_x + dx
            neighbor_y = chunk_y + dy

            if min_x <= neighbor_x <= max_x and min_y <= neighbor_y <= max_y:
                total_count += 1

        return total_count

    def _apply_ca_rules(self, current_land_type: str, land_neighbors: int, total_neighbors: int,
                       expansion_threshold: int, erosion_probability: float) -> str:
        """
        Apply cellular automata rules to determine new land type.

        Args:
            current_land_type: Current land type ('land' or 'water')
            land_neighbors: Number of land neighbors
            total_neighbors: Total number of neighbors
            expansion_threshold: Threshold for land expansion
            erosion_probability: Probability of erosion

        Returns:
            New land type after applying rules
        """
        # Interior protection - if all neighbors are land, stay land
        if self.protect_interior and land_neighbors == total_neighbors and total_neighbors >= self.interior_threshold:
            return 'land'

        if current_land_type == 'water':
            # Water to land conversion (land expansion)
            if land_neighbors >= expansion_threshold:
                return 'land'
        else:  # current_land_type == 'land'
            # Land to water conversion (coastal erosion)
            if self.rng.random() < erosion_probability:
                # Only erode if not completely surrounded by land
                if land_neighbors < total_neighbors:
                    return 'water'

        # No change
        return current_land_type

    def _preserve_islands_pass(self, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                             min_x: int, min_y: int, max_x: int, max_y: int) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """
        Post-processing pass to preserve small islands from disappearing.

        Args:
            chunks: Current chunk data
            min_x, min_y, max_x, max_y: Bounds in subdivided coordinate system

        Returns:
            Updated chunk data with preserved islands
        """
        if not self.preserve_islands:
            return chunks

        # Find all land regions
        land_regions = self._find_land_regions(chunks, min_x, min_y, max_x, max_y)

        # Restore small islands that were eroded
        new_chunks = chunks.copy()
        for region in land_regions:
            if len(region) < self.min_island_size:
                # Restore this small island
                for chunk_x, chunk_y in region:
                    chunk_key = (chunk_x, chunk_y)
                    if chunk_key in new_chunks:
                        new_chunk = new_chunks[chunk_key].copy()
                        new_chunk['land_type'] = 'land'
                        new_chunks[chunk_key] = new_chunk

        return new_chunks

    def _find_land_regions(self, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                          min_x: int, min_y: int, max_x: int, max_y: int) -> List[Set[Tuple[int, int]]]:
        """
        Find connected regions of land using flood fill.

        Returns:
            List of sets, each containing coordinates of a connected land region
        """
        visited = set()
        regions = []

        for chunk_x in range(min_x, max_x + 1):
            for chunk_y in range(min_y, max_y + 1):
                chunk_key = (chunk_x, chunk_y)

                if chunk_key in visited or chunk_key not in chunks:
                    continue

                chunk = chunks[chunk_key]
                if chunk.get('land_type', 'water') == 'land':
                    # Start flood fill from this land chunk
                    region = self._flood_fill_land(chunks, chunk_x, chunk_y, visited, min_x, min_y, max_x, max_y)
                    if region:
                        regions.append(region)

        return regions

    def _flood_fill_land(self, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                        start_x: int, start_y: int, visited: Set[Tuple[int, int]],
                        min_x: int, min_y: int, max_x: int, max_y: int) -> Set[Tuple[int, int]]:
        """
        Flood fill to find a connected land region.

        Returns:
            Set of coordinates in the connected land region
        """
        region = set()
        stack = [(start_x, start_y)]

        while stack:
            x, y = stack.pop()
            chunk_key = (x, y)

            if (chunk_key in visited or
                x < min_x or x > max_x or y < min_y or y > max_y or
                chunk_key not in chunks):
                continue

            chunk = chunks[chunk_key]
            if chunk.get('land_type', 'water') != 'land':
                continue

            visited.add(chunk_key)
            region.add(chunk_key)

            # Add neighbors to stack
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                stack.append((x + dx, y + dy))

        return region

    def _is_at_boundary(self, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                       chunk_x: int, chunk_y: int, min_x: int, min_y: int, max_x: int, max_y: int) -> bool:
        """
        Check if a chunk is at a land/water boundary.

        Returns:
            True if the chunk has both land and water neighbors
        """
        current_chunk = chunks.get((chunk_x, chunk_y))
        if not current_chunk:
            return False

        current_land_type = current_chunk.get('land_type', 'water')

        # Check neighbors for different land type
        offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        for dx, dy in offsets:
            neighbor_x = chunk_x + dx
            neighbor_y = chunk_y + dy

            if min_x <= neighbor_x <= max_x and min_y <= neighbor_y <= max_y:
                neighbor_key = (neighbor_x, neighbor_y)
                if neighbor_key in chunks:
                    neighbor_land_type = chunks[neighbor_key].get('land_type', 'water')
                    if neighbor_land_type != current_land_type:
                        return True

        return False

    def _apply_fractal_perturbation(self, chunks: Dict[Tuple[int, int], Dict[str, Any]],
                                   min_x: int, min_y: int, max_x: int, max_y: int) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """
        Apply fractal-like perturbations to break up blocky patterns.

        Args:
            chunks: Current chunk data
            min_x, min_y, max_x, max_y: Bounds in subdivided coordinate system

        Returns:
            Updated chunk data with fractal perturbations
        """
        new_chunks = chunks.copy()

        for chunk_x in range(min_x, max_x + 1):
            for chunk_y in range(min_y, max_y + 1):
                chunk_key = (chunk_x, chunk_y)
                if chunk_key not in chunks:
                    continue

                # Apply perturbation based on position and noise
                perturbation_seed = hash((chunk_x, chunk_y, "fractal")) % (2**32)
                self.rng.seed(perturbation_seed)

                if self.rng.random() < self.perturbation_strength:
                    current_chunk = chunks[chunk_key]
                    current_land_type = current_chunk.get('land_type', 'water')

                    # Create fractal-like variation by considering position patterns
                    # Use a simple fractal noise pattern
                    noise_value = self._simple_fractal_noise(chunk_x, chunk_y)

                    # Apply perturbation based on noise
                    if noise_value > 0.6:  # High noise threshold for land
                        new_land_type = 'land'
                    elif noise_value < 0.4:  # Low noise threshold for water
                        new_land_type = 'water'
                    else:
                        new_land_type = current_land_type  # Keep original

                    # Update chunk
                    new_chunk = current_chunk.copy()
                    new_chunk['land_type'] = new_land_type
                    new_chunks[chunk_key] = new_chunk

        return new_chunks

    def _simple_fractal_noise(self, x: int, y: int) -> float:
        """
        Generate simple fractal noise for position (x, y).

        Returns:
            Noise value between 0.0 and 1.0
        """
        # Simple multi-octave noise
        noise = 0.0
        amplitude = 1.0
        frequency = 0.1

        for octave in range(3):
            # Simple hash-based noise
            hash_input = hash((x * frequency, y * frequency, octave)) % (2**32)
            octave_noise = (hash_input / (2**32)) * amplitude
            noise += octave_noise

            amplitude *= 0.5
            frequency *= 2.0

        # Normalize to 0-1 range
        return max(0.0, min(1.0, noise / 1.75))

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            'layer_name': self.name,
            'subdivision_factor': self.subdivision_factor,
            'land_expansion_threshold': self.land_expansion_threshold,
            'erosion_probability': self.erosion_probability,
            'iterations': self.iterations,
            'protect_interior': self.protect_interior,
            'use_moore_neighborhood': self.use_moore_neighborhood,
            'preserve_islands': self.preserve_islands,
            'add_noise': self.add_noise
        }
