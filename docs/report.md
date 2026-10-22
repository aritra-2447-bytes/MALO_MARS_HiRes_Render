# MALO_MARS_HiRes_Render — Implementation Report

> **Purpose:** Brief implementation reference for adapting the 3D Mars Globe architecture to a separate map tile system.

---

## Project Overview

A **production-grade 3D planetary exploration platform** for Mars. The core is a WebGL2 interactive globe (Three.js) served by a zero-dependency Python HTTP backend. It evolved from a static 2D tile-stitcher into a full scientific analytics engine with live NASA data integration.

---

## Repository Structure

```
MALO_MARS_HiRes_Render/
├── server.py                        # Root unified multi-threaded server (port 8083)
├── render.yaml                      # Render.com deployment config
├── requirements.txt                 # Runtime: zero deps; Pillow optional for tile tools
├── README.md                        # Full technical documentation
└── dataset/
    ├── 5_{row}_{col}.jpg            # 2,048 Level 5 NASA Mars Trek tiles (256×256 each)
    ├── report.md                    # This file (WebGL pipeline & server report)
    │
    ├── web_app_gpu/                 # ★ MAIN APP: 3D GPU Planetary Explorer
    │   ├── index.html               # Full 3D globe + 2D flat mode (2,621 lines)
    │   ├── index_2d_backup.html     # Standalone 2D WebGL2 fallback viewer
    │   ├── serve.py                 # Standalone server (identical to root server.py)
    │   ├── test_gpu_app.py          # Automated test suite (3D, GeoJSON, server routes)
    │   ├── Instructions.md          # Mathematical derivations & spatial arrangements
    │   ├── mars_mola_base_2k.jpg    # LOD Tier 1 — 2K instant preview (~400 KB)
    │   ├── mars_mola_4k.jpg         # LOD Tier 2 — 4K surface detail (~1.9 MB)
    │   ├── mars_mola_8k.jpg         # LOD Tier 3 — 8K master texture (~9.8 MB)
    │   ├── data/
    │   │   └── astronaut_paths.geojson  # 18 GeoJSON features (8 traverses, 10 landers)
    │   └── lib/
    │       ├── three.min.js         # Three.js r152 WebGL engine (vendored)
    │       └── OrbitControls.js     # Orbital camera physics (vendored)
    │
    └── web_app/                     # Reference 2D Leaflet viewer & GIS pipeline
        ├── index.html               # Leaflet 1.9.4 tile-grid viewer
        ├── serve.py                 # Lightweight HTTP server (port 8082)
        ├── stitch_tiles.py          # GDAL/NumPy mosaic assembly pipeline
        ├── mars_mola_level5_mosaic.jpg  # 16K stitched JPEG (~50.5 MB)
        ├── mars_mola_level5_mosaic.tif  # Georeferenced GeoTIFF (~131.9 MB)
        ├── mars_mola_level5.vrt     # GDAL Virtual Raster (references all 2,048 tiles)
        └── test_webapp.py           # GDAL/NumPy verification suite
```

---

## Raw Tile Dataset

| Property | Value |
|---|---|
| **Source** | NASA Mars Trek WMTS — `Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw` |
| **Projection** | Equirectangular / Plate Carrée (`EPSG:104905`, Mars IAU 2000) |
| **Coverage** | Global: −180° to +180° lon, −90° to +90° lat |
| **Tile Matrix** | Level 5 — **64 columns × 32 rows = 2,048 tiles** |
| **Tile Size** | 256 × 256 px JPEG, named `5_{row}_{col}.jpg` |
| **Full Resolution** | 16,384 × 8,192 px (134.2 Megapixels) |
| **Ground Sampling** | ~200 m/pixel (0.02197265625°/px) |

**Tile → Geographic coordinate mapping:**
```
lat_top    =  90 - row × 5.625°
lat_bottom =  90 - (row+1) × 5.625°
lon_left   = -180 + col × 5.625°
lon_right  = -180 + (col+1) × 5.625°
pixel_x    = col × 256
pixel_y    = row × 256
```

---

## 3D Globe Architecture

### Scene Setup (`index.html` — JS block)

| Component | Implementation |
|---|---|
| **Engine** | Three.js r152 (`three.min.js`) + `OrbitControls.js` |
| **Globe Geometry** | `THREE.SphereGeometry(1.0, 128 segments, 64 rings)` |
| **Camera** | `THREE.PerspectiveCamera(45°, aspect, near=0.01, far=250)` |
| **Renderer** | `THREE.WebGLRenderer` — antialiased, `high-performance`, pixel ratio ≤ 2 |
| **Shadows** | PCF Soft Shadow Map, `2048×2048` shadow map |
| **Controls** | `OrbitControls` — damping `0.06`, zoom `[1.03, 8.5]`, pan disabled |

### Coordinate Transformation

Geodetic lat/lon → 3D Cartesian (right-handed, Y-up):
```js
function latLonToVector3(lat, lon, radius = 1.0) {
  const phi   = (90 - lat) * (Math.PI / 180);  // polar angle from Y-axis
  const theta = (lon + 180) * (Math.PI / 180); // azimuthal angle
  const x = -(radius * Math.sin(phi) * Math.cos(theta));
  const z =  (radius * Math.sin(phi) * Math.sin(theta));
  const y =  (radius * Math.cos(phi));
  return new THREE.Vector3(x, y, z);
}
```
Mars reference radius used for altitude computation: **R = 3,396.19 km**.

### Progressive Texture Pipeline (LOD)

Textures load in sequence — each replaces the previous on the GPU:

| Tier | File | Size | Purpose |
|---|---|---|---|
| 1 (Base) | `mars_mola_base_2k.jpg` | ~400 KB | Instant first-frame, no blank void |
| 2 (Sharp) | `mars_mola_4k.jpg` | ~1.9 MB | Regional topographic detail |
| 3 (Master) | `mars_mola_8k.jpg` | ~9.8 MB | Full crisp surface with mipmaps |

```js
textureLoader.load('/mars_mola_base_2k.jpg', (tex2k) => {
  marsMaterial.map = tex2k;
  marsMaterial.needsUpdate = true;
  textureLoader.load('/mars_mola_8k.jpg', (tex8k) => {
    tex8k.generateMipmaps = true;
    tex8k.minFilter = THREE.LinearMipmapLinearFilter;
    marsMaterial.map = tex8k;
    marsMaterial.needsUpdate = true;
  });
});
```

### GPU Decontourification Shader

Injected into `MeshStandardMaterial.onBeforeCompile` — replaces the standard `#include <map_fragment>`:

- **5-tap cross convolution** — samples center + 4 cardinal neighbors
- **Laplacian ridge extraction** — sharpens MOLA elevation ridges
- **Bilateral anti-banding blend** — smooths discrete contour artifacts (blend weight `0.22`)
- **Contrast enhancement** — `u_contrast = 1.08` for geomorphological visibility
- Toggle via `u_decontour` uniform (`1.0` = active, `0.0` = raw)

### Lighting Architecture

| Light | Type | Role |
|---|---|---|
| `ambientLight` | `AmbientLight(0xffffff, 0.48)` | Prevents total night-side blackout |
| `sunLight` | `DirectionalLight(0xffeedd, 1.35)` | Astronomical sun; casts PCF soft shadows |
| `cameraHeadlight` | `DirectionalLight(0xffffff, 0.22)` | Viewport-tracking fill for dark hemisphere |

Sun position is driven by the live **Mars24 ephemeris** — placed at the computed subsolar lat/lon on a sphere of radius 6.0 (well beyond camera orbit).

### Atmosphere Layer

A back-face sphere at `radius × 1.018` with a custom `ShaderMaterial`:
- Fresnel-style limb glow: `intensity = pow(0.65 - dot(vNormal, vec3(0,0,1)), 2.0)`
- Mars dust color: `vec4(0.85, 0.42, 0.22, 1.0) × intensity × 0.7`
- `AdditiveBlending`, `BackSide`, transparent

### Starfield

2,400 points on a spherical shell at r ∈ [140, 180] (beyond all camera positions), with procedurally generated radial gradient point sprites and `AdditiveBlending`.

### Scene Groups

| Group | Contents |
|---|---|
| `markersGroup` | IAU landmark beacon pins (sphere + stem + ring) |
| `routesGroup` | Active route traverse tube + surface track line |
| `astroPathsGroup` | GeoJSON-driven traverse tubes and lander points |
| `landingSiteMarkersGroup` | 16 status-colored mission landing pins |
| `corridorHighlightGroup` | Hover-animated corridor highlight tube |

---

## Landmark & Landing Site Markers

### IAU Landmark Beacons

Each landmark renders 3 Three.js meshes grouped:
1. **Pin head** — `SphereGeometry(0.008)` at `radius × 1.002 + 0.016` — category-colored
2. **Stem** — `CylinderGeometry(0.0008, 0.0008, 0.018)` aligned to surface normal
3. **Ring** — `RingGeometry(0.006, 0.009)` flush with surface, semi-transparent

Category color palette: volcano → `#f4a261`, canyon → `#d4a373`, polar cap → `#b0c4de`, landing site → `#5eead4`, basin → `#93c5fd`.

### Landing Site Mission Markers (16 sites)

4-tier status color system:
- 🟢 **Active** `#22c55e` — Perseverance, Curiosity
- ⚪ **Completed** `#94a3b8` — Opportunity, Spirit, InSight, Phoenix, Viking 1 & 2, Pathfinder, Zhurong
- 🔴 **Failed** `#ef4444` — Beagle 2, Mars 3, Mars 6, Mars Polar Lander, Schiaparelli EDM
- 🔵 **Proposed** `#38bdf8` — Melas Chasma Human Habitat

Each marker: emissive `SphereGeometry` head (`emissiveIntensity: 0.75`) + slender white `CylinderGeometry` stem + translucent `RingGeometry` ground ring.

---

## Traverse & Route Rendering

### GeoJSON Dataset (`astronaut_paths.geojson`)

18 `FeatureCollection` features:
- **8 `LineString` traverses** — 5 rover missions + 3 human EVA corridors
- **10 `Point` landers** — static touchdown sites

Each traverse feature carries: `id`, `name`, `type` (`rover_traverse`|`human_eva`), `status`, `color`, `total_odometry_km`, `sol_range`, `waypoints[]` (with per-waypoint `sol`, `elev_m`, `hazard`).

### 3D Tube Rendering

For `LineString` features, coordinates `[lon, lat, elev]` → `latLonToVector3` with elevation offset:
```js
radius_offset = MARS_RADIUS + (elev_m / 3_396_190.0) * 1.5 + 0.0006
```

Rendered as:
1. **Emissive `TubeGeometry`** — `CatmullRomCurve3` spline, `MeshStandardMaterial` with `emissiveIntensity: 0.45`
2. **Surface projection line** — `LineBasicMaterial` at `radius × 1.0005`, opacity 0.7

Rover tubes: radius `0.0004`; EVA tubes: `0.00055`.

### Corridor Hover Highlight

On hover in the Landings list, a separate `TubeGeometry` (radius `0.0006`) is created in `corridorHighlightGroup` with `emissiveIntensity` pulsing via `sin(time × 0.006)` in the animation loop.

---

## Smooth Camera Fly-To

Uses linear interpolation with a **cubic ease in-out** (Hermite):
```js
ease = t < 0.5 ? 4t³ : 1 - (-2t+2)³/2
camera.position.lerpVectors(startPos, targetPos, ease)
```
Duration: `1,200 ms`. Target camera distance is feature-aware (`DEFAULT_LANDMARK_CAM_DIST = 1.95`, `POLAR_CAP_CAM_DIST = 2.40`).

---

## Raycaster Interaction

`THREE.Raycaster` fires on `mousemove`, intersecting meshes across 4 groups: `markersGroup`, `landingSiteMarkersGroup`, `astroPathsGroup`, `routesGroup`. On click (`pointerup` with drag distance < 6px) the globe flies to the selected feature.

---

## Real-Time Mars Ephemeris (Allison & McEwen 2000)

Implemented **client-side** in JS (mirrored on server-side in Python):

| Quantity | Formula |
|---|---|
| Julian Date | `JD_UT = 2440587.5 + timestamp/86400` |
| Terrestrial Time | `JD_TT = JD_UT + 69.184/86400` |
| Mean Anomaly M | `(19.387 + 0.52402075 × d2000) mod 360` |
| Solar Longitude Ls | `(alpha_FMS + perturbations) mod 360` |
| Mars Sol Date | `(JD_TT - 2451549.5) / 1.027491252 + 44796 - 0.00096` |
| MTC | `(24 × MSD) mod 24` (hours) |
| Subsolar lat | `asin(sin(25.19°) × sin(Ls))` |
| Solar irradiance | `1361 / r_AU²` W/m² |

Sun vector updated every **1 second** via `setInterval`. The `DirectionalLight` position is updated in `updateLiveMarsEphemeris()`.

---

## EVA Route Planner & Minetti Bioenergetics Engine

Computed server-side at `/api/eva/plan`:

1. **Spherical great-circle distance** (Haversine) between waypoints
2. **Elevation profile** via IDW interpolation from MOLA landmark geodetic anchors (or linear interpolation if PDS elevations are supplied)
3. **Slope gradient** per sample: `arctan(Δelev / step_dist_m)`
4. **Hazard classification**: SAFE (≤12°), CAUTION_STEEP (12–18°), CRITICAL_SLOPE (>18°)
5. **Minetti metabolic cost**: `3.2 + (slope° / 10) × 2.1 kcal/km` (Mars 0.38g, 120 kg system)
6. **Walkback envelope**: 12.5 km max safe radius from habitat (8-hour EVA)

Bottom dock renders a Canvas2D elevation chart with gradient fill and grid lines.

---

## 2D Flat Mode

A plain HTML5 Canvas (`flat-canvas`) draws `mars_mola_8k.jpg` with pan (`flatPanX/Y`) and zoom (`flatZoom`), then overlays visible `LineString` features from `astronaut_paths.geojson` using an equirectangular projection:
```js
const to2D = (lon, lat) => ({
  x: drawX + ((lon + 180) / 360) * drawW,
  y: drawY + ((90 - lat) / 180) * drawH
});
```

---

## Backend Server (`server.py` / `web_app_gpu/serve.py`)

Both files are identical — the root `server.py` auto-detects `GPU_DIR` via a candidate-path search.

**Architecture:** `ThreadingMixIn + HTTPServer` — multi-threaded, `daemon_threads = True`.

**REST API endpoints:**

| Endpoint | Handler | Description |
|---|---|---|
| `GET /api/landmarks` | embedded data | 10 IAU landmark geodetic objects |
| `GET /api/eva/presets` | embedded data | 3 preset human EVA corridors |
| `GET /api/rover/missions` | `handle_rover_missions` | Historical PDS + live NASA MMGIS feeds |
| `GET /api/eva/plan` | `handle_eva_plan` | Great-circle, MOLA elevation, hazard, Minetti |
| `GET /api/mars/ephemeris` | `handle_mars_ephemeris` | Mars24 MSD, MTC, Ls, subsolar, irradiance |
| `GET /api/nasa/ode` | `handle_ode_proxy` | Proxies PDS ODE REST API (`/live2`) |
| `GET /api/nasa/browse` | `handle_browse_proxy` | Streams NASA browse imagery |
| `GET /api/nasa/mola-elevation` | `handle_mola_proxy` | Proxies GDS MOLA PEDR altimetry |

**Static file routing** in `translate_path`:
- `/` → `web_app_gpu/index.html`
- `/tiles/{name}` → `dataset/` directory
- `5_{row}_{col}.jpg` → auto-resolved to `dataset/`
- `/lib/`, `/data/`, `/web_app_gpu/`, `/web_app/` all routed to their respective directories

**Caching:** In-memory `CACHE` dict with `CACHE_TTL = 3600 s` for ODE/GDS/rover responses.

### Live NASA MMGIS Integration

On `/api/rover/missions`, the server attempts:
1. `https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_waypoints.json` — Perseverance waypoints
2. `https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_traverse.json` — continuous drive polyline (36,000+ vertices, downsampled to ~240)
3. Same pattern for Curiosity (`MSL_waypoints.json`, `MSL_traverse.json`)

Falls back silently to the embedded PDS baseline if the live feed is unreachable.

---

## Deployment

**Local:**
```bash
python3 server.py 8083     # serves at http://localhost:8083
```

**Render.com (`render.yaml`):**
```yaml
services:
  - type: web
    name: mars-gpu-viewer
    runtime: python3
    startCommand: "python3 server.py $PORT"
    envVars:
      - key: PYTHON_VERSION
        value: "3.11.0"
    healthCheckPath: /
    autoDeploy: true
```

Zero external Python dependencies at runtime — pure standard library.

---

## Key Architectural Patterns for Adapting to a New Map Tile System

When replacing the Mars MOLA textures with a different map tile source, these are the critical integration points:

1. **Texture swap** — Replace the 3-tier `mars_mola_*.jpg` LOD files or swap the progressive `textureLoader.load` chain with a tile-streaming approach.
2. **`latLonToVector3`** — The coordinate math is generic; only the reference radius (currently `MARS_RADIUS = 1.0` normalized) needs adjustment if true-scale altimetry exaggeration is desired.
3. **`translate_path`** in the server — The tile filename pattern (`5_{row}_{col}.jpg`) and WMTS naming convention must be updated to match the new tile schema.
4. **Decontourification shader** — The 5-tap convolution operates on `vUv` texture space; it is map-source agnostic and can be retained or dropped independently.
5. **GeoJSON `astronaut_paths.geojson`** — The `LineString` / `Point` schema and the tube rendering pipeline are independent of the basemap; they can be repopulated with new feature data without touching the globe core.
6. **`MARS_LANDMARKS` + `interpolate_mola_elevation`** — The MOLA IDW elevation interpolation is Mars-specific; for a different body, this must be replaced with a body-appropriate DEM or elevation service.
7. **Ephemeris engine** — Entirely Mars-specific (Allison & McEwen formulation); must be replaced or removed for non-Mars targets.

---

## Data Attributions

- **NASA Planetary Data System (PDS) / Mars Trek** — MGS MOLA altimetry & MEX HRSC color hillshade
- **NASA JPL-Caltech** — Mars 2020 (Perseverance), MSL (Curiosity), MER (Spirit & Opportunity), MMGIS telemetry
- **CNSA / CSNA** — Tianwen-1 (Zhurong)
- **ESA** — Mars Express (Beagle 2), ExoMars (Schiaparelli EDM)
- **Washington University in St. Louis (WUSTL)** — PDS Geosciences Node ODE & GDS
