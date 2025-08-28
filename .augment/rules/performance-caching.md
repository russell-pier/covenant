---
type: "agent_requested"
description: "Rules for optimizing performance, implementing caching strategies, and managing memory in the generation system"
---

# Performance and Caching Rules

## Caching Rules

- Cache results by bounds tuple: `(min_x, min_y, max_x, max_y)`
- Use `_generation_cache` in `WorldGenerationPipeline`
- Check cache before running pipeline
- Generate 4x4 regions, not individual chunks
- Clear cache when memory limits reached

## Performance Rules

- Use seeded random generators for deterministic results
- Batch process chunks in regions for efficiency
- Implement lazy loading - only generate when requested
- Use efficient neighbor counting algorithms
- Minimize chunk copying - update in-place when possible

## Memory Rules

- Implement cache size limits to prevent unlimited growth
- Use LRU eviction when cache exceeds limits
- Clean up temporary data after processing
- Use appropriate data structures for sparse vs dense data

## Coordinate System Rules

- Use `math.floor()` for world-to-chunk coordinate conversion
- Handle negative coordinates correctly
- Cache coordinate calculations when possible
- Use efficient point-in-chunk testing for subdivided chunks
