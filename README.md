# MALO_MARS_HiRes_Render

High-resolution Mars planetary visualization platform and GIS engine, featuring a **3D WebGL2 interactive globe**, multi-tier progressive texture streaming (2K &rarr; 4K &rarr; 8K), **real-time NASA Mars solar ephemeris**, **live NASA rover traverse telemetry**, **landing site exploration markers**, **astronaut EVA route planning with Minetti metabolic expenditure analysis**, and direct **NASA PDS ODE / GDS REST API** orbital data integration.

Assembled from NASA Mars Trek Level 5 tiles (MGS MOLA + MEX HRSC Color Hillshade Blend at 200 m/px, 134.2 Megapixels).

---

## 🌟 What's New & Improvements (Compared to Base Repository)

Compared to the base repository ([`aritra-2447-bytes/MALO_MARS_HiRes_Render`](https://github.com/aritra-2447-bytes/MALO_MARS_HiRes_Render)), this repository has evolved from a static 2D tile-stitching project into a **comprehensive, production-grade 3D planetary exploration and scientific analytics platform**:

| Feature / Capability | Base Repository (`aritra-2447-bytes`) | Current Repository |
|----------------------|--------------------------------------|-------------------|
| **Visualization Engine** | 2D Flat Leaflet Viewer + Basic 2D WebGL Quad | **Interactive 3D WebGL2 Globe (Three.js)** + 2D Flat Mode fallback |
| **Texture Architecture** | Single 16K mosaic or raw Level 5 tiles | **Progressive Multi-Tier LOD Pipeline**: 2K instant preview &rarr; 4K sharp &rarr; 8K master texture |
| **Tile Seam / Quad Artifacts** | Close-range quad seam & square artifacts | **Fixed close-range rendering**; seamless surface continuity and mipmapping |
| **Camera & Navigation** | Basic pan/zoom; excessive zoom on landmark click | **Smooth OrbitControls** with damping; **bounds-aware landmark fly-to** preventing surface clipping |
| **Solar Lighting & Shadows** | Static ambient lighting | **Real-Time Allison & McEwen Mars24 Ephemeris**: dynamic Sun position, PCF soft shadows & night-side headlight |
| **Mars Telemetry & Time** | None | **Live Mars Sol Date (MSD)**, Coordinated Mars Time (MTC), Solar Longitude ($L_s$), and Solar Irradiance |
| **Rover Traverses** | None | **Real-time & historical waypoints** for Perseverance, Curiosity, Opportunity, Spirit & Zhurong |
| **NASA Live MMGIS Feed** | None | **Live JPL MMGIS API streaming** (`M20_waypoints.json`, `MSL_waypoints.json`) with continuous drive polylines |
| **Landing Sites & Landers** | None | **9 historical & active landing sites** with 3D pin beacons, needle stems, and ground target rings |
| **Exploration Sites Drawer** | Simple waypoint list | **Dual-tab drawer (📍 Landmarks / 🛬 Landings)** with status grouping, visibility toggles & hover corridor pulse |
| **Status Standardization** | Inconsistent | **Standardized color system**: 🟢 Active (`#22c55e`), ⚪ Completed (`#94a3b8`), 🔴 Failed (`#ef4444`) |
| **Astronaut EVA Route Planner** | None | **Great-Circle spherical router** with MOLA laser altimetry elevation profiling and hazard detection |
| **Bioenergetics Engine** | None | **Minetti Metabolic Cost Model** adapted for Mars 0.38g gravity, suit mass & walkback envelope |
| **NASA PDS API Integration** | None | **Direct proxy to NASA PDS ODE REST API** (CTX, HiRISE, CRISM) and **GDS MOLA altimetry** |
| **Backend Architecture** | Basic single-threaded HTTP server | **High-performance multi-threaded unified server (`server.py`)** with REST API and in-memory TTL caching |
| **Deployment Readiness** | Local execution only | **Turnkey Render.com deployment** (`render.yaml`) with zero external dependencies (Python standard library) |
| **Automated Testing** | 2D tile check script | **Comprehensive verification test suites** (`test_gpu_app.py`, `test_webapp.py`) covering all subsystems |

---

## 🚀 Key System Features

### 1. Interactive 3D Planetary Globe (Three.js & WebGL2)
- **Mathematical Spherical Mapping**: Converts Martian geodetic latitude and longitude ($\phi, \lambda$) directly into 3D Cartesian coordinates on the Mars 2000 reference sphere ($R = 3,396.19\text{ km}$).
- **Smooth Orbit Physics**: OrbitControls featuring inertia damping (`dampingFactor: 0.06`), clamped pitch and zoom, and continuous flight animations.
- **Bounds-Aware Fly-To (`getLandmarkZoomDist`)**: Dynamically computes optimal camera altitude based on feature scale (e.g., Olympus Mons vs. Jezero Crater) to eliminate over-zooming and ground clipping.
- **Deep Space Celestial Starfield**: Procedurally generated radial stars mapped onto a celestial sphere.
- **Dual-Engine Architecture**: Seamlessly switch between the **3D Globe Mode** and the high-performance **2D Flat Mode** (`index_2d_backup.html` / HTML5 Canvas).

### 2. Progressive Multi-Tier Texture Pipeline (LOD)
- **Tier 1 (2K Base LOD)**: `mars_mola_base_2k.jpg` (2048 &times; 1024, ~400 KB) loads in < 5 ms for instantaneous first-frame planet display without blank voids.
- **Tier 2 (4K Surface Map)**: `mars_mola_4k.jpg` enhances regional topographical details during orbital approach.
- **Tier 3 (8K Master Texture)**: `mars_mola_8k.jpg` provides crisp surface features across craters, scarps, and chasmata with automatic anisotropic filtering.
- **VRAM LRU Cache Management**: Prioritizes visible tiles and protects active viewport quads from eviction, preventing cache thrashing.

### 3. Real-Time Mars Solar Ephemeris & Day/Night Terminator (NASA Mars24)
Implements the **Allison & McEwen (2000)** planetary formulation:
- **Mars Sol Date (MSD)**: Continuous epoch calculation from Julian Date $JD_{TT}$:
  $$\text{MSD} = \frac{JD_{TT} - 2451549.5}{1.027491252} + 44796.0 - 0.00096$$
- **Coordinated Mars Time (MTC)**: Sub-second accurate planetary mean time ($\text{MTC} = 24 \times \text{MSD} \pmod{24}$).
- **Areocentric Solar Longitude ($L_s$)**: Real-time Martian seasonal cycle (Northern Spring: $0^\circ-90^\circ$, Summer: $90^\circ-180^\circ$, Autumn: $180^\circ-270^\circ$, Winter: $270^\circ-360^\circ$).
- **Subsolar Coordinates & Solar Irradiance**: Computes real-time Sun Zenith latitude/longitude and surface Total Solar Irradiance ($\text{TSI} \approx 590\text{ W/m}^2$).
- **Astronomical Lighting**: `THREE.DirectionalLight` aligned with the subsolar vector casting real-time PCF soft shadows, supplemented by an orbital night-side headlight ensuring topographic features remain visible on the dark hemisphere.

### 4. NASA Rover Exploration Traverses & Live Telemetry
- **Authoritative Waypoint History**: Full traverse profiles with sol counters, elevation, and odometry:
  - **Perseverance (Mars 2020)**: Jezero Crater (Octavia E. Butler Landing, Séítah Dunes, Kodiak Butte, Hawksbill Gap, Neretva Vallis, Belva Crater Rim)
  - **Curiosity (MSL)**: Gale Crater (Bradbury Landing, Yellowknife Bay, Bagnold Dunes, Vera Rubin Ridge, Sulfate-Bearing Valley, Gediz Vallis)
  - **Opportunity (MER-B)**: Meridiani Planum (Eagle Crater, Fram Crater, Purgatory Dune, Victoria Crater, Cape York, Perseverance Valley)
  - **Spirit (MER-A)**: Gusev Crater (Columbia Memorial, Bonneville Crater, West Spur, Husband Hill Summit, Home Plate, Troy Silica Sands)
  - **Zhurong (Tianwen-1)**: Utopia Planitia
- **Live NASA JPL MMGIS Feed Integration**:
  - Automatically queries live GeoJSON feeds (`M20_waypoints.json`, `M20_traverse.json`, `MSL_waypoints.json`, `MSL_traverse.json`).
  - Downsamples 36,000+ continuous drive vertices into smooth 3D paths with automatic fallback to verified PDS baselines when offline.
- **3D Traverse Tube Rendering**: Extruded emissive Catmull-Rom spline tubes (`THREE.TubeGeometry`) elevated above the terrain with surface projection lines and sol-indexed waypoint beacons.

### 5. Historical Landing Sites & Landers Dataset
- **Covered Missions**: InSight Lander, Phoenix Lander, Viking 1 Lander, Viking 2 Lander, Beagle 2, and all rovers.
- **Standardized Mission Status Palette**:
  - 🟢 **Active**: `#22c55e` (Perseverance, Curiosity)
  - ⚪ **Completed**: `#94a3b8` (Opportunity, Spirit, InSight, Phoenix, Viking 1 & 2, Zhurong)
  - 🔴 **Failed**: `#ef4444` (Beagle 2)
- **3D Pin Beacons**: Status-colored pin head spheres, vertical needle stems, and ground target rings.
- **Exploration Sites Drawer**:
  - Dual tabs: **📍 Landmarks** (IAU geodetic catalog) and **🛬 Landings** (sorted by status: Active &rarr; Completed &rarr; Failed).
  - Checkboxes for per-mission visibility toggling in both 3D scene and 2D canvas.
  - Hover corridor pulse effect highlighting the corresponding 3D path on hover.
  - Instant "Fly" action buttons for orbital transit.

### 6. Astronaut EVA Route Planner & Minetti Bioenergetics Engine
- **Preset Human Corridors**:
  - Jezero Western Delta & Belva Crater Traverse
  - Gale Crater: Mount Sharp (Aeolis Mons) Expedition
  - Valles Marineris (Melas Chasma) Rim-to-Floor Descent
- **Great-Circle Spherical Geodesics**: High-precision spherical distance calculation across Mars surface coordinates.
- **Elevation Cross-Sections**: Derived from MOLA laser altimetry interpolation.
- **Hazard Classification**:
  - **SAFE** ($\le 12^\circ$ slope)
  - **CAUTION STEEP** ($12^\circ - 18^\circ$, wheel slip / low gear)
  - **CRITICAL SLOPE** ($> 18^\circ$, impassable / roll risk)
- **Minetti Metabolic Model**: Energy expenditure calibrated for Mars 0.38g gravity and 120 kg astronaut + EMU spacesuit system:
  $$\text{Energy Rate} = 3.2 + \left(\frac{\text{slope}^\circ}{10}\right) \times 2.1 \quad [\text{kcal/km}]$$
- **Walkback Envelope**: Real-time safety validation against an 8-hour EVA limit and 12.5 km maximum safe walkback radius.

### 7. NASA PDS ODE & GDS REST API Microservices
Integrated into `server.py` with zero third-party dependencies:
- **NASA ODE REST API Proxy (`/api/nasa/ode`)**: Searches MRO CTX, HiRISE, and CRISM orbital observation products at current camera coordinates with footprint WKT retrieval.
- **NASA Browse Streamer (`/api/nasa/browse`)**: Proxies and caches high-resolution browse imagery directly from NASA PDS archives.
- **NASA GDS MOLA Altimetry Proxy (`/api/nasa/mola-elevation`)**: Fetches MOLA PEDR laser altimetry point clouds on-the-fly.
- **In-Memory TTL Caching**: 1-hour cache layer mitigating external rate limits and ensuring sub-millisecond response times.

---

## 📡 REST API Reference

The unified backend (`server.py` / `web_app_gpu/serve.py`) provides the following endpoints:

| Endpoint | Method | Query Parameters | Description |
|----------|--------|------------------|-------------|
| `/api/landmarks` | `GET` | None | Returns authoritative IAU Martian landmarks (volcanoes, canyons, basins, polar caps). |
| `/api/rover/missions` | `GET` | None | Returns live NASA JPL MMGIS & historical PDS rover telemetry waypoints and paths. |
| `/api/eva/presets` | `GET` | None | Returns preset human EVA exploration expedition routes. |
| `/api/eva/plan` | `GET` | `waypoints` (JSON) | Computes Great-Circle distance, MOLA elevation profile, slope gradients, and Minetti metabolic cost. |
| `/api/mars/ephemeris` | `GET` | None | Calculates live Mars Sol Date, MTC, $L_s$, subsolar coordinates, season, and solar irradiance. |
| `/api/nasa/ode` | `GET` | `lat`, `lon`, `radius`, `instrument` (`CTX`\|`HIRISE`\|`CRISM`) | Queries NASA PDS ODE REST API for orbital observation footprints and metadata. |
| `/api/nasa/browse` | `GET` | `pdsid` | Streams cached high-resolution browse images from NASA PDS archives. |
| `/api/nasa/mola-elevation` | `GET` | `lat`, `lon`, `box` | Retrieves granular MOLA PEDR laser altimetry point clouds from NASA PDS GDS. |

---

## 🗺️ Raw Dataset & Level 5 Mosaic Specifications

### NASA Mars Trek WMTS Source
- **Layer**: `Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw`
- **Projection**: Equirectangular / Plate Carrée (`EPSG:104905`, Mars IAU 2000, central meridian = $0^\circ$)
- **Coverage**: Global $[-180^\circ, -90^\circ]$ to $[+180^\circ, +90^\circ]$
- **Tile Matrix**: Level 5 (64 columns &times; 32 rows = **2,048 tiles**)
- **Tile Size**: 256 &times; 256 px JPEG (`5_{row}_{col}.jpg`)
- **Total Composite Size**: 16,384 &times; 8,192 px (134.2 Megapixels)
- **Equatorial Resolution**: ~200 m/pixel ($0.02197265625^\circ$/px)

### Mathematical Coordinate Mapping
```
# Tile row and column ranges
row ∈ [0, 31]   # 0 = North pole (+90°), 31 = South pole (-90°)
col ∈ [0, 63]   # 0 = West (-180°),      63 = East (+180°)

# Geographic bounds per tile
lat_top    =  90 - row * 5.625
lat_bottom =  90 - (row + 1) * 5.625
lon_left   = -180 + col * 5.625
lon_right  = -180 + (col + 1) * 5.625

# Pixel placement in 16384×8192 mosaic
x_start = col * 256
y_start = row * 256
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.8+ (No external packages required for runtime — runs entirely on Python standard library!)
- Optional: `pip install -r requirements.txt` (only needed for server-side tile assembly scripts)

### 2. Launching the Applications

#### Unified 3D GPU Planetary Explorer (Recommended)
```bash
python3 server.py 8083
```
Open your browser at: **`http://localhost:8083`**

### 3. Running Automated Test Suites
Confirm file integrity, 3D WebGL scenes, GeoJSON schemas, and server routes:
```bash
# Verify 3D Planetary Explorer, server routes, and GeoJSON datasets
python3 dataset/web_app_gpu/test_gpu_app.py

# Verify 2D Level 5 mosaic artifacts (requires GDAL & NumPy)
python3 dataset/web_app/test_webapp.py
```

---

## 📁 Repository Structure

```
.
├── server.py                                  # Unified high-performance multi-threaded server & NASA API backend
├── render.yaml                                # Turnkey deployment configuration for Render.com
├── requirements.txt                           # Optional Python dependencies (runtime is zero-dependency)
├── README.md                                  # Complete technical documentation & architecture guide
│
└── dataset/
    ├── 5_0_0.jpg ... 5_31_63.jpg              # 2,048 Level 5 NASA tiles (256×256 each, 16K global grid)
    ├── report.md                              # WebGL visual pipeline & HTTP server fix report
    │
    ├── web_app_gpu/                           # 🚀 MAIN APPLICATION: 3D Planetary Explorer & GPU Engine
    │   ├── index.html                         # Interactive 3D globe (Three.js), ephemeris HUD, docks & shaders
    │   ├── index_2d_backup.html               # Dedicated 2D high-performance WebGL2 fallback viewer
    │   ├── Instructions.md                    # Technical spatial arrangements & mathematical derivations
    │   ├── serve.py                           # Standalone multi-threaded server (identical to root server.py)
    │   ├── test_gpu_app.py                    # Automated test suite for 3D/2D apps, GeoJSON & server
    │   ├── mars_mola_base_2k.jpg              # Tier 1 instant 2K LOD base texture (~400 KB)
    │   ├── mars_mola_4k.jpg                   # Tier 2 sharp 4K planetary surface map (~1.9 MB)
    │   ├── mars_mola_8k.jpg                   # Tier 3 ultra-crisp 8K master texture (~9.8 MB)
    │   ├── mars_mola_level5_mosaic.jpg -> ... # Relative symlink to 16K composite mosaic
    │   ├── tiles -> ..                        # Symlink to raw Level 5 tiles
    │   ├── data/
    │   │   └── astronaut_paths.geojson        # 13 verified missions (traverses, landing sites & landers)
    │   └── lib/
    │       ├── three.min.js                   # Three.js 3D WebGL engine
    │       └── OrbitControls.js               # Orbital navigation physics controller
    │
    └── web_app/                               # 🗺️ REFERENCE APPLICATION: 2D Leaflet Viewer & GIS Pipeline
        ├── index.html                         # Leaflet 1.9.4 viewer with tile matrix grid & rover tracks
        ├── serve.py                           # Lightweight HTTP server (port 8082)
        ├── stitch_tiles.py                    # GDAL / NumPy mosaic assembly & seam continuity pipeline
        ├── mars_mola_level5_mosaic.jpg        # 16K stitched JPEG (~50.5 MB)
        ├── mars_mola_level5_mosaic.tif        # Georeferenced GeoTIFF with Mars 2000 Datum (~131.9 MB)
        ├── mars_mola_level5.vrt               # GDAL Virtual Raster referencing all 2,048 tiles
        ├── test_webapp.py                     # GDAL / NumPy verification test suite
        ├── tiles -> ..                        # Symlink to raw Level 5 tiles
        └── data/
            └── astronaut_paths.geojson        # Exploration paths dataset
```

---

## 🔬 Credits & Data Attributions
- **NASA Planetary Data System (PDS)** & **Mars Trek**: Mars Global Surveyor (MGS) MOLA altimetry and Mars Express (MEX) HRSC color hillshade blend.
- **NASA / JPL-Caltech**: Mars 2020 (Perseverance), Mars Science Laboratory (Curiosity), Mars Exploration Rovers (Spirit & Opportunity), and MMGIS telemetry.
- **Washington University in St. Louis (WUSTL)**: PDS Geosciences Node Orbital Data Explorer (ODE) and Geosciences Data Services (GDS).
