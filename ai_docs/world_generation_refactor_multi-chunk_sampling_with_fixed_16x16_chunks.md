# World Generation Refactor: Multi-Chunk Sampling with Fixed 16x16 Chunks

## Current Problems to Solve

1. **Exponential chunk growth** - zoom layers create 4x more chunks each time
2. **Dynamic coordinate systems** - chunk sizes change (64→32→16→8) causing cache misalignment
3. **Poor performance** - O(n²) islands layer processing on exponentially growing chunk counts
4. **Coordinate confusion** - generation chunks vs render chunks mismatch

## Target Architecture

### Fixed Chunk System
- All chunks are **always 16x16 tiles** for both generation and rendering
- No coordinate system changes throughout pipeline
- Consistent cache alignment between generation and rendering
- Linear scaling instead of exponential

### Multi-Scale Sampling Within Fixed Chunks
- **Continental Layer**: Sample at region level (4x4 chunk regions = 64x64 tiles)
- **Regional Layer**: Sample at chunk level (16x16 tiles)
- **Local Layer**: Sample at sub-chunk level (4x4 or 8x8 within each chunk)
- **Tile Layer**: Final individual tile placement

## Implementation Plan

### Phase 1: Core Architecture Changes

#### 1.1 Remove Dynamic Chunk Sizing
**Files to Modify:**
- `src/world/dual_chunk_system.py` - Remove generation vs render chunk distinction
- `src/world/worker.py` - Simplify to single chunk type
- `src/world/world_manager.py` - Use consistent 16x16 chunks throughout

**Changes:**
- Delete `DualChunkManager` class
- Remove `calculate_final_generation_chunk_size()` logic
- Simplify chunk coordinate systems to single 16x16 grid

#### 1.2 Update Configuration
**Files to Modify:**
- `config/config.toml` - Simplify pipeline configuration

**Changes:**
```toml
# Replace dynamic zoom pipeline
pipeline_layers = [
    "continental",
    "regional", 
    "local",
    "tiles"
]

[world.continental]
region_size = 4  # 4x4 chunks per continental region
noise_scale = 0.01
continent_threshold = 0.3

[world.regional]
noise_scale = 0.1
land_bias_from_continental = 0.7

[world.local]
sampling_resolution = 8  # 8x8 samples within each chunk
noise_scale = 0.5
coastal_detail_iterations = 3

[world.tiles]
# Final tile placement rules
```

### Phase 2: Rewrite Generation Layers

#### 2.1 Continental Layer (Replaces lands_and_seas)
**New File:** `src/world/layers/continental/layer.py`

**Responsibilities:**
- Sample noise at 4x4 chunk region scale
- Assign continent/ocean designation to entire regions
- Ensure landmasses are minimum 4x4 chunks (64x64 tiles)

**Key Methods:**
```python
def get_continental_designation(self, chunk_x: int, chunk_y: int) -> str:
    region_x = chunk_x // 4
    region_y = chunk_y // 4
    return sample_continental_noise(region_x, region_y)
```

#### 2.2 Regional Layer (Replaces first zoom)
**New File:** `src/world/layers/regional/layer.py`

**Responsibilities:**
- Sample noise at individual chunk level
- Create major land/water boundaries within continental regions
- Bias sampling based on continental designation

#### 2.3 Local Layer (Replaces subsequent zooms + islands)
**New File:** `src/world/layers/local/layer.py`

**Responsibilities:**
- Sample at 8x8 or 16x16 resolution within each chunk
- Generate detailed coastlines and terrain boundaries
- Apply coastal erosion/expansion rules within chunk boundaries

#### 2.4 Tiles Layer (New)
**New File:** `src/world/layers/tiles/layer.py`

**Responsibilities:**
- Convert sampling data to final tile types
- Place individual tiles based on multi-scale sampling results
- Handle tile-specific rules (ore placement, vegetation, etc.)

### Phase 3: Update Pipeline System

#### 3.1 Modify GenerationData Structure
**File:** `src/world/pipeline.py`

**Changes:**
- Remove dynamic chunk_size from GenerationData
- Add multi-scale sampling storage:
```python
@dataclass
class GenerationData:
    seed: int
    chunk_size: int = 16  # Always 16x16
    
    # Multi-scale sampling results
    continental_samples: Dict[Tuple[int, int], Any]  # Region coordinates
    regional_samples: Dict[Tuple[int, int], Any]     # Chunk coordinates  
    local_samples: Dict[Tuple[int, int], Any]        # Sub-chunk samples
    
    # Final chunk data
    chunks: Dict[Tuple[int, int], Dict[str, Any]]
```

#### 3.2 Update Layer Base Class
**File:** `src/world/pipeline.py`

**Changes:**
- Remove coordinate bounds complexity
- Simplify layer interface for fixed-size chunks
- Add sampling utilities for multi-scale access

### Phase 4: Worker and Manager Updates

#### 4.1 Simplify WorldGenerationWorker
**File:** `src/world/worker.py`

**Changes:**
- Remove dual chunk system
- Generate only 16x16 chunks
- Simplify tile extraction to 1:1 mapping
- Remove coordinate conversion complexity

#### 4.2 Update WorldManager
**File:** `src/world/world_manager.py`

**Changes:**
- Remove dual chunk manager
- Use consistent 16x16 chunk coordinates
- Simplify cache management
- Remove coordinate conversion methods

### Phase 5: Configuration Migration

#### 5.1 Create Migration Script
**New File:** `scripts/migrate_config.py`

**Purpose:**
- Convert existing zoom-based configuration to sampling-based
- Preserve user's intended terrain characteristics
- Provide sensible defaults for new layer system

#### 5.2 Update Documentation
**Files to Update:**
- `README.md` - Update architecture description
- `config/world/layers/` - Create new layer documentation

## Testing Strategy

### Unit Tests
- Test each new layer independently with known inputs
- Verify continental regions are coherent across 4x4 chunk boundaries
- Test that sampling produces deterministic results with same seed

### Integration Tests
- Generate test worlds with new pipeline
- Verify continent sizes meet minimum requirements
- Check for visual artifacts at chunk boundaries
- Performance testing vs old system

### Migration Tests
- Test config migration script with existing configurations
- Verify migrated worlds produce reasonable terrain
- A/B test visual quality vs old system

## Expected Performance Improvements

- **Chunk Generation**: Linear scaling instead of exponential (4x improvement per zoom layer)
- **Memory Usage**: Fixed memory footprint per area instead of growing cache
- **Rendering**: Direct 1:1 mapping between generation and render coordinates
- **Cache Efficiency**: No coordinate conversion overhead

## Risks and Mitigation

### Risk: Less Fractal Detail
The new system might produce less chaotic coastlines than the cellular automata approach.

**Mitigation**: Use multiple octaves of noise in local layer and add controlled randomization.

### Risk: Grid Artifacts
Continental regions aligned to 4x4 boundaries might create visible patterns.

**Mitigation**: Offset sampling points and add boundary noise to break up regularity.

### Risk: Migration Complexity
Existing configurations and saved worlds might not translate well.

**Mitigation**: Create comprehensive migration tools and fallback to default configurations.

## Implementation Order

1. **Phase 1**: Core architecture (removes exponential scaling)
2. **Phase 2**: Continental and regional layers (gets basic functionality working)
3. **Phase 4**: Worker updates (gets full pipeline operational) 
4. **Phase 2**: Local and tiles layers (adds detail and polish)
5. **Phase 5**: Migration and documentation (production readiness)

This approach prioritizes getting the performance issues resolved first, then progressively adds back the detail and features.