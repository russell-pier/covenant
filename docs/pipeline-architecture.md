# Pipeline Architecture

The world generation system uses a highly tunable, layered pipeline architecture that allows for flexible and extensible terrain generation.

## Overview

The pipeline system consists of three tiers:
- **World Tier**: Large-scale features (lands/seas, climate, continental layouts)
- **Region Tier**: Medium-scale features (biomes, terrain types) - *Future*
- **Local Tier**: Small-scale features (structures, details) - *Future*

Currently, only the World Tier is implemented.

## Architecture Components

### Core Classes

#### `GenerationData`
Standardized data structure passed between layers:
```python
@dataclass
class GenerationData:
    seed: int                                    # World generation seed
    chunk_size: int                             # Size of each chunk in tiles
    chunks: Dict[Tuple[int, int], Dict[str, Any]]  # Chunk data by coordinates
    processed_layers: List[str]                 # Layers that have processed this data
    custom_data: Dict[str, Any]                 # Layer-specific data storage
```

#### `GenerationLayer`
Base class for all generation layers:
```python
class GenerationLayer(ABC):
    def __init__(self, name: str, config: Dict[str, Any])
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData
```

#### `GenerationPipeline`
Manages a sequence of generation layers:
```python
class GenerationPipeline:
    def __init__(self, name: str, visualize: bool = False)
    def add_layer(self, layer: GenerationLayer)
    def process(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData
```

#### `WorldGenerationPipeline`
Main coordinator for all generation tiers:
```python
class WorldGenerationPipeline:
    def __init__(self, seed: int, chunk_size: int)
    def set_world_tier(self, pipeline: GenerationPipeline)
    def generate_chunks(self, bounds: Tuple[int, int, int, int]) -> GenerationData
```

## World Tier Layers

### Available Layers

1. **lands_and_seas**: Determines basic land/water distribution
2. **zoom**: Subdivides chunks and applies cellular automata for detailed coastlines

### Layer Configuration

Layers are configured via TOML files and can be arranged in any order:

```toml
[world]
pipeline_layers = [
    "lands_and_seas",
    "zoom",
    "zoom"
]

[world.lands_and_seas]
land_ratio = 1
algorithm = "random_chunks"

[world.zoom]
subdivision_factor = 2
land_expansion_threshold = 6
iterations = 2
```

## Data Flow

1. **Initialization**: `GenerationData` created with seed and chunk size
2. **Layer Processing**: Each layer processes data sequentially:
   - Receives `GenerationData` and bounds
   - Modifies chunk data
   - Adds itself to `processed_layers`
   - Returns modified data
3. **Caching**: Results cached by bounds to prevent redundant processing
4. **Tile Lookup**: Individual tiles retrieved from processed chunk data

## Integration

### Game Integration

The pipeline integrates with the existing game through `PipelineWorldGenerator`:

```python
generator = WorldGenerator(
    generator_type="pipeline",
    seed=12345,
    chunk_size=16,
    pipeline_layers=["lands_and_seas", "zoom"],
    layer_configs={"lands_and_seas": {...}, "zoom": {...}}
)
```

### Configuration Loading

Pipeline configuration is loaded from `config.toml`:
- `pipeline_layers`: List of layer names to execute
- `[world.layer_name]`: Configuration for each layer

## Visualization

The pipeline supports optional visualization:
- Set `visualize=True` to see layer-by-layer progression
- Each layer's result displayed with 1-second delays
- Shows chunk counts, land ratios, and visual grids

## Extensibility

### Adding New Layers

1. Create layer class inheriting from `GenerationLayer`
2. Implement `process()` method
3. Add layer to `WorldTier.create_custom_pipeline()`
4. Create configuration section in TOML
5. Add documentation

### Adding New Tiers

1. Create tier-specific pipeline
2. Add to `WorldGenerationPipeline`
3. Update processing order in `generate_chunks()`

## Performance

- **Efficient Caching**: Results cached by bounds to prevent redundant processing
- **Batch Processing**: Chunks generated in regions (4x4) for efficiency
- **Lazy Loading**: Only generates chunks when requested
- **Memory Management**: Caches can be cleared when memory is needed

## Future Enhancements

- **Region Tier**: Biome generation, climate patterns
- **Local Tier**: Structure placement, resource distribution
- **Parallel Processing**: Multi-threaded layer execution
- **Streaming**: Generate chunks on-demand for infinite worlds
- **Persistence**: Save/load generated chunks to disk
