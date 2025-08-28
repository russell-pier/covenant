# Lands and Seas Layer

The `lands_and_seas` layer is the foundation layer of world generation that determines basic land/water distribution across chunks.

## Purpose

This layer establishes the fundamental geography by deciding whether each chunk should be land or water. It provides the base terrain that other layers build upon.

## Configuration

### Location
- **Code**: `src/generation/world/lands_and_seas/layer.py`
- **Config**: `src/generation/world/lands_and_seas/config.toml`
- **Tests**: `src/generation/world/lands_and_seas/test_layer.py`

### Parameters

```toml
[lands_and_seas]
# Land ratio out of 10 (1 = 10% land, 5 = 50% land)
land_ratio = 1

# Algorithm to use for land/water determination
algorithm = "random_chunks"

# Future algorithm configurations
[lands_and_seas.perlin_noise]
scale = 0.1
octaves = 4
persistence = 0.5
lacunarity = 2.0

[lands_and_seas.cellular_automata]
initial_land_probability = 0.4
iterations = 5
birth_limit = 4
death_limit = 3
```

## Algorithms

### Random Chunks (Current)

The simplest algorithm that determines each chunk independently:

```python
def _random_chunks_algorithm(self, seed: int, chunk_x: int, chunk_y: int) -> str:
    self._set_seed(seed, chunk_x, chunk_y)
    return "land" if self.rng.randint(1, 10) <= self.land_ratio else "water"
```

**Characteristics:**
- **Deterministic**: Same seed produces same results
- **Independent**: Each chunk determined separately
- **Configurable**: Land ratio controls overall distribution
- **Fast**: O(1) per chunk

### Future Algorithms

**Perlin Noise**: Smooth, natural-looking terrain with configurable frequency and amplitude.

**Cellular Automata**: Organic shapes with connected landmasses and realistic coastlines.

## Input/Output

### Input
- **GenerationData**: Empty or minimal chunk data
- **Bounds**: `(min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)`

### Output
- **GenerationData**: Chunks with `land_type` property set to "land" or "water"

### Data Structure
```python
chunk_data = {
    'chunk_x': int,
    'chunk_y': int, 
    'chunk_size': int,
    'land_type': str  # "land" or "water"
}
```

## Usage Examples

### Basic Usage
```python
from src.generation.world.lands_and_seas import LandsAndSeasLayer

layer = LandsAndSeasLayer({
    'land_ratio': 3,  # 30% land
    'algorithm': 'random_chunks'
})

data = layer.process(generation_data, bounds=(0, 0, 10, 10))
```

### In Pipeline
```toml
[world]
pipeline_layers = ["lands_and_seas"]

[world.lands_and_seas]
land_ratio = 2  # 20% land
algorithm = "random_chunks"
```

## Land Ratio Guidelines

- **land_ratio = 1**: 10% land - Archipelago world with scattered islands
- **land_ratio = 2**: 20% land - Island world with moderate landmasses  
- **land_ratio = 3**: 30% land - Balanced world with good land/water mix
- **land_ratio = 5**: 50% land - Continental world with large landmasses
- **land_ratio = 7**: 70% land - Mostly land with lakes and seas
- **land_ratio = 9**: 90% land - Desert world with rare water

## Performance

- **Time Complexity**: O(n) where n is number of chunks in bounds
- **Space Complexity**: O(n) for chunk storage
- **Deterministic**: Same inputs always produce same outputs
- **Cacheable**: Results can be cached indefinitely

## Testing

The layer includes comprehensive tests:

```bash
python src/generation/world/lands_and_seas/test_layer.py
```

**Test Coverage:**
- Layer creation and configuration validation
- Deterministic generation with same seeds
- Different seeds produce different results
- Land ratio affects distribution correctly
- Bounds handling and chunk processing

## Integration

### With Zoom Layers

The lands_and_seas layer provides the foundation that zoom layers refine:

```toml
pipeline_layers = [
    "lands_and_seas",  # Creates base land/water distribution
    "zoom",            # Adds detail and natural coastlines
    "zoom"             # Further refinement
]
```

### With Future Layers

Future layers can build upon the land_type property:
- **Climate layers**: Different climates for land vs water chunks
- **Biome layers**: Forest, desert, etc. on land chunks
- **Resource layers**: Ore deposits on land, fish in water

## Troubleshooting

### Common Issues

**No land generated**: Check that `land_ratio > 0` and bounds include multiple chunks.

**Too much/little land**: Adjust `land_ratio` parameter (1-10 scale).

**Non-deterministic results**: Ensure same seed is used for reproducible generation.

**Performance issues**: Consider caching results for frequently accessed areas.

### Debug Information

Enable layer visualization to see generation results:
```python
layer = LandsAndSeasLayer(config)
# Results will show chunk counts and land ratios
```

## Future Enhancements

- **Noise-based algorithms**: Perlin noise, simplex noise for natural terrain
- **Constraint-based generation**: Ensure minimum landmass sizes
- **Template-based generation**: Predefined continent shapes
- **Erosion simulation**: Realistic coastline formation
- **Tectonic simulation**: Continental drift and mountain formation
