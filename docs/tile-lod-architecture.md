# Mars 3D Globe — Dynamic Tile-Based LOD Architecture

## Problem Statement

The current implementation loads **monolithic 8K textures** (8192×4096) for each layer (MOLA, Zoom 5). This approach:
- Consumes ~256 MB GPU memory per layer
- Cannot leverage higher-resolution tiles (Level 6–8) at close range
- Loads entire sphere texture regardless of camera frustum

## Proposed Solution: Frustum-Culled Tile Pyramid

Replace single textures with a **quad-tree tile pyramid** projected onto the sphere, loading only visible tiles at the appropriate LOD.

---

## Tile Scheme

| Level | Grid (rows × cols) | Tile Size | Coverage per Tile | Use Case |
|-------|-------------------|-----------|-------------------|----------|
| 2     | 8 × 16            | 256²      | 22.5° × 22.5°     | Orbital view |
| 3     | 16 × 32           | 256²      | 11.25° × 11.25°   | Regional |
| 4     | 32 × 64           | 256²      | 5.625° × 5.625°   | Sub-regional |
| **5** | **32 × 64**       | **256²**  | **5.625° × 5.625°** | **Current base (2,048 tiles)** |
| 6     | 64 × 128          | 256²      | 2.81° × 2.81°     | Local terrain |
| 7     | 128 × 256         | 256²      | 1.4° × 1.4°       | High-res local |
| 8     | 256 × 512         | 256²      | 0.7° × 0.7°       | Surface skim |

**Tile naming:** `{level}_{row}_{col}.jpg` (e.g., `6_45_123.jpg`)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      GlobeTileLayer                         │
│  (extends THREE.Group)                                      │
├─────────────────────────────────────────────────────────────┤
│  • tileCache: Map<key, {mesh, texture, level, lastUsed}>   │
│  • loading: Set<key>                                        │
│  • currentLevel: number                                     │
│  • maxLevel: 8                                              │
├─────────────────────────────────────────────────────────────┤
│  + update(camera)          → Called each frame              │
│  + computeTargetLevel()    → Distance → LOD mapping         │
│  + getVisibleTileKeys()    → Frustum-sphere intersection    │
│  + loadTile(key)           → Async texture + mesh creation  │
│  + createTileMesh()        → Spherical quad geometry        │
│  + evictOldTiles()         → LRU cache eviction             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Server (serve.py)                        │
│  GET /tiles/{level}_{row}_{col}.jpg                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Algorithms

### 1. Distance → LOD Mapping

```javascript
computeTargetLevel(camera) {
  const dist = camera.position.length(); // distance from sphere center (radius=1.0)
  if (dist > 4.0) return 3;
  if (dist > 2.0) return 5;
  if (dist > 1.3) return 7;
  return 8;
}
```

### 2. Frustum Culling on Sphere

```javascript
getVisibleTileKeys(camera, level) {
  const frustum = new THREE.Frustum();
  frustum.setFromProjectionMatrix(
    camera.projectionMatrix.clone().multiply(camera.matrixWorldInverse)
  );
  
  // For each tile at this level, compute sphere-projected AABB
  // Test against frustum → return Set of visible tile keys
}
```

### 3. Spherical Quad Geometry

Each tile = 4 vertices on sphere surface at tile corners, UV-mapped to [0,1]×[0,1]. Subdivide (e.g., 4×4) for curvature fidelity at high LOD.

---

## Cache Management

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Max tiles in memory | 200 | ~200 × 256² × 4 bytes ≈ 50 MB |
| Max tile age | 30 s | Evict tiles not recently in frustum |
| Eviction trigger | > 70% capacity | Batch evict LRU entries |

---

## Integration Plan

### Phase 1: Server Endpoints (Low Effort)
**File:** `dataset/web_app_gpu/serve.py`
- Add route `GET /tiles/<level>_<row>_<col>.jpg`
- Serve from `zoom_{level}/` directories (already exist)

### Phase 2: Client Tile Layer (Medium Effort)
**File:** `dataset/web_app_gpu/index.html`
- Add `GlobeTileLayer` class (≈200 lines)
- Replace texture loading (lines 1174–1230) with:
  ```javascript
  const tileLayer = new GlobeTileLayer({ baseUrl: '/tiles', maxLevel: 8 });
  scene.add(tileLayer);
  ```
- In `animate()`: `tileLayer.update(camera)`

### Phase 3: Polish (Low Effort)
- Add LOD indicator to status HUD
- Tune distance thresholds
- Add loading placeholder for tiles in flight

---

## Future Enhancement: Virtual Texture (Single Draw Call)

If draw-call count becomes a bottleneck, implement a **virtual texture** in the fragment shader:
- Pack tiles into texture atlas or use `TEXTURE_2D_ARRAY`
- Shader computes `tileCoord = uv * 2^lod`, samples atlas
- Single `Mesh` with custom `onBeforeCompile` shader
- More complex; only needed if tile count > ~500 visible

---

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `serve.py` | Add | Tile serving endpoint |
| `index.html` | Replace | Monolithic texture → `GlobeTileLayer` |
| `index.html` | Add | `tileLayer.update(camera)` in render loop |

---

## Testing Checklist

- [ ] Level 5 tiles load at default camera distance (3.2)
- [ ] Zooming in triggers Level 6→7→8 loads
- [ ] Zooming out unloads high-LOD tiles (LRU)
- [ ] No visual seams at tile boundaries
- [ ] GPU memory stays < 200 MB
- [ ] 60 FPS maintained during LOD transitions