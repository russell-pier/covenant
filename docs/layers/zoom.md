# Zoom Layer

The `zoom` layer progressively refines terrain detail by subdividing chunks and applying cellular automata to create natural coastlines and terrain boundaries.

## Purpose

The zoom layer transforms blocky, low-resolution terrain into detailed, fractal-like landscapes while preserving the overall geographic structure from previous layers. It can be applied multiple times in sequence for progressive detail enhancement.

## Configuration

### Location
- **Code**: `src/generation/world/zoom/layer.py`
- **Config**: `src/generation/world/zoom/config.toml`
- **Tests**: `src/generation/world/zoom/test_layer.py`

### Parameters

```toml
[zoom]
# Core subdivision settings
subdivision_factor = 2              # How many sub-chunks per dimension (2 = 2x2 = 4 sub-chunks)

# Cellular automata parameters
land_expansion_threshold = 6        # Minimum land neighbors for water→land conversion
erosion_probability = 0.1          # Chance of land→water conversion at coastlines
iterations = 2                     # Number of cellular automata iterations

# Multi-pass refinement
use_multi_pass = false             # Apply multiple passes with different parameters
pass_1_iterations = 4              # First pass: aggressive expansion
pass_1_expansion_threshold = 1
pass_1_erosion_probability = 0.02
pass_2_iterations = 3              # Second pass: detail refinement
pass_2_expansion_threshold = 3
pass_2_erosion_probability = 0.08

# Advanced features
protect_interior = false           # Protect landlocked tiles from erosion
interior_threshold = 8             # All 8 neighbors must be land to be considered interior
use_moore_neighborhood = true      # Use 8-neighbor Moore neighborhood (vs 4-neighbor Von Neumann)
preserve_islands = true            # Prevent small islands from disappearing
min_island_size = 1               # Minimum size to preserve islands

# Fractal enhancement
fractal_perturbation = false       # Add fractal-like perturbations
perturbation_strength = 0.3        # Strength of fractal perturbations (0.0-1.0)
edge_noise_boost = false          # Extra noise along land/water boundaries
edge_noise_probability = 0.2       # Higher noise probability at edges
add_noise = false                 # Add randomness to prevent perfect patterns
noise_probability = 0.1           # Chance of random land/water flip per iteration
```

## Core Functionality

### Subdivision Process

1. **Input Analysis**: Takes existing chunks with `land_type` property
2. **Subdivision**: Each chunk becomes NxN sub-chunks (default 2x2)
3. **Inheritance**: Sub-chunks inherit parent's land type as starting point
4. **Cellular Automata**: Applies rules to create natural boundaries
5. **Output**: Detailed chunks with fractal coastlines

### Cellular Automata Rules

The layer uses configurable cellular automata to create natural terrain:

```python
def _apply_ca_rules(self, current_land_type: str, land_neighbors: int, total_neighbors: int,
                   expansion_threshold: int, erosion_probability: float) -> str:
    # Land expansion: water becomes land if enough land neighbors
    if current_land_type == 'water':
        if land_neighbors >= expansion_threshold:
            return 'land'
    
    # Coastal erosion: land becomes water with probability
    else:  # current_land_type == 'land'
        if self.rng.random() < erosion_probability:
            if land_neighbors < total_neighbors:  # Not completely surrounded
                return 'water'
    
    return current_land_type  # No change
```

## Input/Output

### Input
- **GenerationData**: Chunks with `land_type` property from previous layers
- **Bounds**: Area to process (may be adjusted for subdivided coordinates)

### Output
- **GenerationData**: Subdivided chunks with refined `land_type` and additional properties

### Data Structure
```python
chunk_data = {
    'chunk_x': int,
    'chunk_y': int,
    'chunk_size': int,           # Size of subdivided chunk
    'land_type': str,            # "land" or "water"
    'parent_chunk_x': int,       # Original chunk coordinates
    'parent_chunk_y': int,
    'subdivision_level': int     # How many zoom layers have processed this
}
```

## Usage Examples

### Single Zoom Layer
```python
from src.generation.world.zoom import ZoomLayer

layer = ZoomLayer({
    'subdivision_factor': 2,
    'land_expansion_threshold': 4,
    'erosion_probability': 0.1,
    'iterations': 3
})

data = layer.process(generation_data, bounds)
```

### Multiple Zoom Layers
```toml
[world]
pipeline_layers = [
    "lands_and_seas",
    "zoom",      # First refinement: 1→4 chunks
    "zoom"       # Second refinement: 4→16 chunks
]

[world.zoom]
subdivision_factor = 2
land_expansion_threshold = 6  # Conservative expansion
iterations = 2
```

### Progressive Detail Pipeline
```toml
pipeline_layers = ["lands_and_seas", "zoom", "zoom", "zoom"]
# Result: 1 → 4 → 16 → 64 chunks with fractal detail
```

## Expansion Control

### Conservative Expansion (Recommended)
```toml
land_expansion_threshold = 6    # High threshold = limited expansion
erosion_probability = 0.1       # Low erosion = stable coastlines
iterations = 2                  # Few iterations = controlled growth
```

### Aggressive Expansion
```toml
land_expansion_threshold = 1    # Low threshold = rapid expansion
erosion_probability = 0.02      # Minimal erosion = land dominates
iterations = 6                  # Many iterations = extensive growth
```

### Balanced Natural Coastlines
```toml
land_expansion_threshold = 3    # Moderate expansion
erosion_probability = 0.15      # Balanced erosion
iterations = 4                  # Good detail level
fractal_perturbation = true     # Natural variation
```

## Multi-Pass Processing

Enable multi-pass for sophisticated coastline generation:

```toml
use_multi_pass = true

# Pass 1: Rough shape formation
pass_1_iterations = 3
pass_1_expansion_threshold = 2
pass_1_erosion_probability = 0.05

# Pass 2: Detail refinement
pass_2_iterations = 3
pass_2_expansion_threshold = 4
pass_2_erosion_probability = 0.2
```

## Performance

- **Time Complexity**: O(n × i × s²) where n=chunks, i=iterations, s=subdivision_factor
- **Space Complexity**: O(n × s²) for subdivided chunks
- **Scaling**: Each zoom layer multiplies chunk count by subdivision_factor²
- **Optimization**: Efficient neighbor counting and boundary detection

## Progressive Detail Levels

### Single Zoom (4x detail)
- **Input**: 1 chunk
- **Output**: 4 chunks (2x2)
- **Use case**: Moderate detail enhancement

### Double Zoom (16x detail)
- **Input**: 1 chunk  
- **Output**: 16 chunks (4x4)
- **Use case**: High detail for important areas

### Triple Zoom (64x detail)
- **Input**: 1 chunk
- **Output**: 64 chunks (8x8)
- **Use case**: Maximum detail for close-up views

## Integration

### With Lands and Seas
```toml
pipeline_layers = ["lands_and_seas", "zoom"]
# lands_and_seas provides base 10% land
# zoom refines coastlines without aggressive expansion
```

### With Future Layers
- **Biome layers**: Apply different biomes to refined land areas
- **Resource layers**: Place resources based on detailed terrain
- **Structure layers**: Use coastline detail for placement decisions

## Troubleshooting

### Common Issues

**Land takes over everything**: Reduce `land_expansion_threshold` or increase `erosion_probability`

**No detail added**: Check that `subdivision_factor > 1` and `iterations > 0`

**Jagged coastlines**: Enable `fractal_perturbation` and increase `iterations`

**Performance issues**: Reduce `subdivision_factor` or limit number of zoom layers

### Debug Visualization

Enable visualization to see layer effects:
```python
# In pipeline configuration
visualize = True  # Shows before/after grids with 1-second delays
```

## Testing

Run comprehensive tests:
```bash
python src/generation/world/zoom/test_layer.py
```

**Test Coverage:**
- Subdivision correctness and inheritance
- Cellular automata rule application
- Multiple zoom layer application
- Deterministic generation
- Configuration validation

## Future Enhancements

- **Adaptive subdivision**: Variable subdivision based on terrain complexity
- **Biome-aware rules**: Different CA rules for different biomes
- **Elevation integration**: 3D terrain with height-based rules
- **River generation**: Carved waterways through land
- **Erosion simulation**: Realistic weathering effects
- **Tidal zones**: Dynamic land/water boundaries
