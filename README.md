# MALO_MARS_HiRes_Render

A high-resolution Mars planetary visualization platform, scientific GIS engine, and research cartography suite. Powered by an **interactive 3D WebGL2 globe**, multi-tier progressive texture streaming (2K &rarr; 4K &rarr; 8K master texture), a **high-precision 2D research flat map**, **real-time Allison & McEwen Mars24 solar ephemeris**, **authentic NASA/international rover traverses**, **scale-invariant precision point landing markers**, **astronaut EVA route planning with Minetti metabolic bioenergetics**, and direct **NASA PDS ODE / GDS REST API** microservices.

Synthesized from NASA Mars Trek Level 5 global data (MGS MOLA + MEX HRSC Color Hillshade Blend at 200 m/px, 134.2 Megapixels).

**ARES-OS Mission Control** is the science and autonomy layer built on top of the explorer: a historical Mars atlas with namesake biographies, aqueous-mineral target overlays, real USGS DEM slope-hazard analysis, live Mars chronometry, and a cooperative follower/scout informative path planner with optimality proofs and convergence charts.

---

## 🌟 Key Capabilities & Architectural Highlights

| Subsystem / Capability | Technical Implementation | Purpose & Benefit |
|------------------------|--------------------------|-------------------|
| **3D Planetary Globe** | WebGL2 / Three.js on Mars 2000 Sphere ($R = 3,396.19\text{ km}$) with real-time decontourification shader | High-fidelity interactive globe visualization with smooth OrbitControls physics and inertia damping |
| **Surface Detail & Zoom Control** | Distance clamped at orbital threshold (`minDistance = 1.08`, ~270 km altitude) | Strict camera altitude limiting prevents texture pixelation and maintains crisp crater topography |
| **2D Research Flat Map** | GPU/Canvas-accelerated high-resolution equirectangular map with clamped scale ($1.0\times - 3.5\times$) | Research-grade flat map section with fluid drag-pan navigation and synchronized rover drive tracks |
| **Single-Line Rover Pathways** | Razor-sharp continuous cartographic pathways (`THREE.Line`, `linewidth: 2`, `opacity: 0.95`) | Replaced bulky 3D tube geometries; paths sit directly on terrain without obscuring geological features |
| **Precision Point Landing Markers** | Scale-invariant discrete circular points (`THREE.Points`, `sizeAttenuation: false`, `size: 7`) | Replaced large 3D spheres, needle stems, and 30 km wide ground rings; unblocks view of rover starting tracks |
| **Rover Traverses & Odometry** | 6,918 lines of telemetry in `data/rover_traverses.json` with sol ranges, distances, and waypoints | Full drive routes for Perseverance, Curiosity, Opportunity, Spirit, Zhurong, and Sojourner |
| **Targeted EDL Landing Ellipses** | Parametric semi-major/minor dispersion ellipses derived from NASA entry, descent & landing reports | Accurate engineering landing envelopes for InSight, Phoenix, Viking 1, Viking 2, and Beagle 2 |
| **Mars24 Solar Ephemeris** | Allison & McEwen (2000) planetary formulation calculating MSD, MTC, $L_s$, and subsolar coordinates | Real-time solar illumination, PCF shadow terminator, and areocentric seasons |
| **Exploration Sites Drawer** | Dual-tab drawer (📍 Landmarks / 🛬 Landings) with status grouping and per-mission layer toggles | Rapid access to 16+ audited historical landing sites, volcanoes, canyons, and polar caps |
| **EVA Route Planning & Bioenergetics** | Great-circle spherical distance, MOLA altimetry cross-sections, and Minetti metabolic cost model | Human exploration route validation, slope hazard profiling, and 8-hour walkback safety envelope |
| **NASA PDS API Integration** | Built-in proxy for NASA PDS ODE (CTX, HiRISE, CRISM) and GDS MOLA laser altimetry | Live orbital footprints, browse image streaming, and in-memory TTL caching with zero external dependencies |
| **Unified Backend Server** | Multi-threaded Python server (`server.py` / `serve.py`) with REST API and CORS preflight | Zero-dependency deployment ready for local workstations and production cloud hosting (Render.com) |

---

## 🛰️ ARES-OS Mission Control

Open the **ARES-OS** panel on the right side of the explorer. The six-cell chronometer strip across the top reports MTC, MSD, Ls/season, Perseverance and Curiosity local solar times, the cursor's local solar time, and Earth UTC.

| Tab | What it does |
|-----|--------------|
| **Atlas** | Searchable registry of 18 historical landers/rovers and 48 IAU landmarks. Hover any marker for its namesake biography and scientific significance; expand a card for the full mission dossier, then fly to the site. |
| **Minerals** | Eight aqueous-mineral classes (Fe/Mg and Al phyllosilicates, poly/monohydrated sulfates, carbonates, hydrated silica, hematite, chlorides) draped as an additive equirectangular probability layer. Toggle classes, opacity, site rings, and query live CRISM/OMEGA/HiRISE footprints through NASA PDS ODE. |
| **Terrain** | Real USGS Astrogeology STAC COG DTM analysis (CTX ~20 m/px or HiRISE ~1 m/px). Classifies 0–15° safe, 15–30° caution, and >30° no-go cells; renders a 3D hazard patch, a local hazard mini-map, vertical exaggeration, and brightness/contrast/saturation controls. Also submits asynchronous MOLA PEDR jobs to the NASA PDS Geosciences Node. |
| **Scout** | Cooperative follower/scout informative path planning. The follower solves a feasible route on known terrain; the scout chooses information-gain viewpoints and reveals a connected sensor swath along each sortie. The panel reports feasible vs. optimistic route length, optimality gap, known-terrain fraction, scout distance/sorties, an animated local AOI map, an elevation/slope profile, and a cost-convergence chart. Certificates of optimality or infeasibility are shown explicitly. |
| **Clock** | Full Mars24 readout: MSD, MTC, Ls, equation of time, subsolar point, solar irradiance, and local solar time/phase for Perseverance and Curiosity. The cursor readout updates as you move over the globe or flat map. |

### Cooperative scouting method
1. Read a DEM window, compute slope at native resolution, then block-aggregate to the planning grid (mean elevation, max slope).
2. Build an optimistic route with A* on the full terrain model; this is a lower bound for any feasible route.
3. Build a feasible route using only terrain already revealed by the scout; unrevealed cells are impassable/unknown.
4. Score candidate scout viewpoints by unknown-cell gain and connectivity, reveal the sensor swath along the flight leg, and repeat until the feasible and optimistic costs converge.
5. Emit `OPTIMAL_PROVEN`, `INFEASIBILITY_PROVEN`, or `MAX_ITERATIONS` with the corresponding proof text and convergence history.

### Optional full-DEM mode
The backend is standard-library-first. Without `numpy`/`rasterio`, ARES-OS uses a deterministic MOLA-anchored fractal fallback for slope analysis. Install the optional scientific stack to read real USGS CTX/HiRISE COG DTMs over HTTP range requests:

```bash
python3 -m venv .venv
.venv/bin/pip install numpy rasterio
.venv/bin/python server.py 8000
```

Real-DEM responses identify their source (for example `USGS STAC CTX DTM`) and include the STAC item id and native resolution. Network access is required for STAC, ODE, GDS, and browse-image queries; the rest of the app works offline.

---

## 🚀 System Architecture & Modules

### 1. Interactive 3D Planetary Globe & Viewport Limiting
- **Geodetic Coordinate Mapping**: Converts Martian geodetic latitude and longitude ($\phi, \lambda$) directly into 3D Cartesian coordinates on the Mars IAU 2000 reference sphere ($R = 3,396.19\text{ km}$).
- **Decontourification Shader Architecture**: Custom GLSL shader smooths elevation stepping artifacts across color-coded hillshade mosaics.
- **Strict Camera Altitude Clamping**: `controls.minDistance` is enforced at `1.08` (~270 km above surface datum). Fly-to animations clamp via `safeDist = Math.max(controls.minDistance, targetDist)`, eliminating texture over-magnification and terrain pixelation.
- **Deep Space Celestial Starfield**: Procedurally generated stars mapped onto a distant celestial sphere.

### 2. High-Precision 2D Research Flat Map
- **Hardware-Accelerated Canvas Engine**: Renders high-resolution equirectangular surface projection directly onto an optimized 2D canvas.
- **Interactive Pan & Clamped Zoom**: Supports mouse-drag panning and bounded scroll zoom ($1.0\times$ to $3.5\times$ zoom bounds), ensuring underlying map resolution remains crisp and non-stretched.
- **Overlay Synchronization**: Simultaneously displays active rover traverse tracks, touchdown points, and final destinations in true planetary coordinates.

### 3. Authentic Rover Traverses & Single-Line Pathways
- **Single-Line Cartographic Geometry**: Rover drive paths are rendered using razor-sharp `THREE.Line` geometry directly along surface elevation ($R_{\text{Mars}} \times 1.0006$).
- **Complete Mission Telemetry Dataset (`data/rover_traverses.json`)**:
  - **Perseverance (Mars 2020)**: Touchdown at Octavia E. Butler Landing $\rightarrow$ Séítah Dunes $\rightarrow$ Kodiak Butte $\rightarrow$ Hawksbill Gap $\rightarrow$ Neretva Vallis $\rightarrow$ Belva Crater Rim (~28+ km).
  - **Curiosity (MSL)**: Touchdown at Bradbury Landing $\rightarrow$ Yellowknife Bay $\rightarrow$ Bagnold Dunes $\rightarrow$ Vera Rubin Ridge $\rightarrow$ Gediz Vallis Debris Flow Ridge (~32+ km).
  - **Opportunity (MER-B)**: Touchdown at Challenger Memorial Station (Eagle Crater) $\rightarrow$ Endurance Crater $\rightarrow$ Victoria Crater $\rightarrow$ Perseverance Valley at Endeavour Crater (~45.16 km).
  - **Spirit (MER-A)**: Touchdown at Columbia Memorial Station $\rightarrow$ Bonneville Crater $\rightarrow$ Husband Hill Summit $\rightarrow$ Home Plate $\rightarrow$ Troy Silica Sands (~7.73 km).
  - **Zhurong (Tianwen-1)**: Southern Utopia Planitia touchdown to southern hibernation site (~1.92 km).
  - **Pathfinder / Sojourner**: Carl Sagan Memorial Station at Ares Vallis to Yogi Rock (~0.13 km).

### 4. Precision Point Landing Markers
- **Scale-Invariant Visual Points**: Landing sites are marked with discrete `THREE.Points` (`sizeAttenuation: false`, `size: 7`) with a custom smooth circular alpha mask (`createPointDotTexture()`).
- **Zero Obstruction**: Completely eliminated large 3D spheres, needle poles, and wide ground target rings that previously covered rover landing zones.
- **Responsive Raycasting**: Invisible spherical hitboxes (`SphereGeometry(0.0008)`) with `raycaster.params.Points = { threshold: 0.005 }` allow intuitive hover tooltips and click-to-fly navigation from any camera angle.
- **Standardized Status Palette**:
  - 🟢 **Active**: `#22c55e` (Perseverance, Curiosity)
  - ⚪ **Completed**: `#94a3b8` (Opportunity, Spirit, InSight, Phoenix, Viking 1 & 2, Pathfinder, Zhurong)
  - 🔴 **Failed**: `#ef4444` (Beagle 2, Mars 3, Mars 6, Mars Polar Lander, Schiaparelli EDM)
  - 🔵 **Proposed**: `#38bdf8` (Melas Chasma Human Habitat Candidate, science corridors)

### 5. Real-Time Mars24 Solar Ephemeris Engine
Implements the planetary formulation of **Allison & McEwen (2000)**:
- **Mars Sol Date (MSD)**: Continuous epoch calculation from Julian Date $JD_{TT}$:
  $$\text{MSD} = \frac{JD_{TT} - 2451549.5}{1.027491252} + 44796.0 - 0.00096$$
- **Coordinated Mars Time (MTC)**: Sub-second accurate planetary mean time ($\text{MTC} = 24 \times \text{MSD} \pmod{24}$).
- **Areocentric Solar Longitude ($L_s$)**: Real-time Martian seasonal cycle (Northern Spring: $0^\circ-90^\circ$, Summer: $90^\circ-180^\circ$, Autumn: $180^\circ-270^\circ$, Winter: $270^\circ-360^\circ$).
- **Subsolar Coordinates & Diurnal Illumination**: Computes dynamic Sun Zenith coordinates with directional lighting casting PCF soft shadows and a soft night-side headlight ensuring geological visibility.

### 6. Astronaut EVA Route Planner & Minetti Bioenergetics
- **Preset Human Exploration Corridors**:
  - Jezero Western Delta & Belva Crater Traverse
  - Gale Crater: Mount Sharp (Aeolis Mons) Expedition
  - Valles Marineris (Melas Chasma) Rim-to-Floor Descent
- **Great-Circle Spherical Geodesics**: High-precision spherical distance calculation across Mars surface coordinates.
- **Slope Hazard Classification**:
  - **SAFE** ($\le 12^\circ$ slope)
  - **CAUTION STEEP** ($12^\circ - 18^\circ$, wheel slip / low gear)
  - **CRITICAL SLOPE** ($> 18^\circ$, impassable / roll risk)
- **Minetti Metabolic Model**: Energy expenditure calibrated for Mars $0.38g$ gravity and 120 kg astronaut + EMU suit system:
  $$\text{Energy Rate} = 3.2 + \left(\frac{\text{slope}^\circ}{10}\right) \times 2.1 \quad [\text{kcal/km}]$$
- **Walkback Envelope**: Real-time safety validation against an 8-hour EVA limit and 12.5 km maximum safe walkback radius.

---

## 📡 REST API Reference

The unified backend (`server.py` / `dataset/web_app_gpu/serve.py`) exposes the following endpoints:

| Endpoint | Method | Query Parameters | Description |
|----------|--------|------------------|-------------|
| `/api/rover/traverses` | `GET` | None | Returns verified rover traverses, odometry, milestones, and EDL ellipses from `rover_traverses.json`. |
| `/api/landmarks` | `GET` | None | Returns IAU Martian landmarks (volcanoes, canyons, impact basins, polar caps). |
| `/api/rover/missions` | `GET` | None | Returns NASA JPL MMGIS and historical PDS rover telemetry waypoints and paths. |
| `/api/eva/presets` | `GET` | None | Returns preset human EVA exploration routes. |
| `/api/eva/plan` | `GET` | `waypoints` (JSON) | Computes Great-Circle distance, elevation cross-section, slope hazards, and Minetti metabolic expenditure. |
| `/api/mars/ephemeris` | `GET` | None | Calculates live Mars Sol Date, MTC, $L_s$, subsolar coordinates, Martian season, and solar irradiance. |
| `/api/nasa/ode` | `GET` | `lat`, `lon`, `radius`, `instrument` | Queries NASA PDS ODE REST API for orbital observation footprints (CTX, HiRISE, CRISM). |
| `/api/nasa/browse` | `GET` | `pdsid` | Streams cached high-resolution browse images from NASA PDS archives. |
| `/api/nasa/mola-elevation` | `GET` | `lat`, `lon`, `box` | Retrieves granular MOLA PEDR laser altimetry point clouds from NASA PDS GDS. |
| `/api/atlas/missions` | `GET` | None | Historical mission registry with exact coordinates, status, namesake biography, and scientific significance. |
| `/api/atlas/landmarks` | `GET` | None | Curated IAU landmark registry enriched with namesake biographies and geology notes. |
| `/api/minerals` | `GET` | `lat`, `lon`, `radius`, `instrument` (optional) | Aqueous-mineral classes and target sites; optional proximity filter. |
| `/api/terrain/slope` | `GET` | `lat`, `lon`, `size`, `resolution`, `prefer`, `n` | Real USGS STAC COG DTM window, slope grid, 0–15/15–30/>30° hazard classes, and source metadata. |
| `/api/scouting/plan` | `GET`/`POST` | `start_lat`, `start_lon`, `target_lat`, `target_lon`, `sensor_radius`, `max_iterations` | Cooperative follower/scout IPP with feasible and optimistic paths, convergence history, and proofs. |
| `/api/mars/time` | `GET` | `lon` | Cursor-local Mars time, LMST/LTST, solar elevation, and MTC. |
| `/api/nasa/features` | `GET` | `query`, `featurename` | NASA PDS ODE feature/geometry query proxy. |
| `/api/nasa/gds/jobs` | `GET` | `action=submit\|status\|list\|abort`, `jobid`, bbox (`minlat`, `maxlat`, `westernlon`, `easternlon`) | Asynchronous MOLA PEDR job manager with state, notes, and result files. |

---

## 🗺️ Raw Dataset & Level 5 Mosaic Specifications

- **WMTS Source Layer**: `Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw`
- **Projection**: Equirectangular / Plate Carrée (`EPSG:104905`, Mars IAU 2000, central meridian = $0^\circ$)
- **Coverage**: Global $[-180^\circ, -90^\circ]$ to $[+180^\circ, +90^\circ]$
- **Tile Matrix**: Level 5 (64 columns &times; 32 rows = **2,048 tiles**)
- **Tile Size**: 256 &times; 256 px JPEG (`5_{row}_{col}.jpg`)
- **Total Composite Size**: 16,384 &times; 8,192 px (134.2 Megapixels)
- **Equatorial Resolution**: ~200 m/pixel ($0.02197265625^\circ$/px)

### Coordinate Conversion Formulas
```python
# Tile indices from grid bounds
row in [0, 31]   # 0 = North pole (+90°), 31 = South pole (-90°)
col in [0, 63]   # 0 = West (-180°),      63 = East (+180°)

# Geographic boundaries
lat_top    =  90.0 - row * 5.625
lat_bottom =  90.0 - (row + 1) * 5.625
lon_left   = -180.0 + col * 5.625
lon_right  = -180.0 + (col + 1) * 5.625

# Mosaic pixel coordinates (16,384 x 8,192 px)
x_pixel = col * 256
y_pixel = row * 256
```

---

## ⚡ Quick Start & Verification

### 1. Requirements
- Python 3.8+ (standard-library runtime)
- Modern WebGL2-compatible browser (Chrome, Firefox, Safari, Edge)
- Optional for real DEM slope analysis: `numpy` + `rasterio` (see the ARES-OS section)

### 2. Launching the Application
```bash
# Zero-dependency mode (synthetic terrain fallback)
python3 server.py 8083

# Full ARES-OS mode with real USGS DEM windows
python3 -m venv .venv
.venv/bin/pip install numpy rasterio
.venv/bin/python server.py 8000
```
Open **`http://localhost:8083`** for zero-dependency mode, or **`http://localhost:8000`** after the full-DEM setup above. The explorer loads immediately; open the **ARES-OS** panel on the right and use the Atlas, Minerals, Terrain, Scout, and Clock tabs. The same backend can be started from the deployment copy with `python3 dataset/web_app_gpu/serve.py 8000`; it resolves the shared `ares/` package automatically.

### 3. Running Automated Test Suites
```bash
# Run comprehensive automated test suite for 3D/2D engines, telemetry datasets & server
python3 dataset/web_app_gpu/test_gpu_app.py

# Verify Python syntax across all modules
python3 -m compileall ares/ dataset/ server.py
```

---

## 📁 Repository Structure

```
.
├── ares/                                     # ARES-OS science package (catalog, Mars24, DEM, IPP, ODE, GDS)
├── server.py                                  # Unified multi-threaded server & NASA REST API backend
├── render.yaml                                # Turnkey deployment configuration for Render.com
├── requirements.txt                           # Optional Python dependencies (runtime is zero-dependency)
├── README.md                                  # Complete technical documentation & architecture guide
├── changes.md                                 # Change log & release history
├── rover_paths.md                             # Rover traverses & landing sites specification
│
├── dataset/
│   ├── 5_0_0.jpg ... 5_31_63.jpg              # 2,048 Level 5 NASA tiles (256×256 each, 16K global grid)
│   │
│   ├── web_app_gpu/                           # 🚀 MAIN APPLICATION: 3D Planetary Explorer & GPU Engine
│   │   ├── index.html                         # Interactive 3D globe (Three.js), ephemeris HUD, docks & shaders
│   │   ├── mission_control.js                 # ARES-OS UI, overlays, charts, hover cards & map picking
│   │   ├── mission_control.css                # ARES-OS panel, chronometer, atlas/scout styling
│   │   ├── serve.py                           # Standalone multi-threaded server (shared ares/ package)
│   │   ├── test_gpu_app.py                    # Automated test suite for 3D/2D apps, GeoJSON & server
│   │   ├── mars_mola_base_2k.jpg              # Tier 1 instant 2K LOD base texture (~400 KB)
│   │   ├── mars_mola_4k.jpg                   # Tier 2 sharp 4K planetary surface map (~1.9 MB)
│   │   ├── mars_mola_8k.jpg                   # Tier 3 ultra-crisp 8K master texture (~9.8 MB)
│   │   ├── tiles -> ..                        # Symlink to raw Level 5 tiles
│   │   ├── data/
│   │   │   ├── rover_traverses.json           # Comprehensive drive paths, odometry & landing ellipses (6,918 lines)
│   │   │   ├── astronaut_paths.geojson        # Verified exploration traverses and landers
│   │   │   └── mars-traverses/                # Individual mission track coordinates
│   │   │       ├── opportunity.json
│   │   │       ├── sojourner.json
│   │   │       ├── spirit.json
│   │   │       └── zhurong.json
│   │   └── lib/
│   │       ├── three.min.js                   # Three.js 3D WebGL engine
│   │       └── OrbitControls.js               # Orbital navigation physics controller
│   │
│   └── web_app/                               # 🗺️ 2D Reference Viewer & Tile GIS Pipeline
│       ├── index.html                         # Leaflet 1.9.4 viewer with tile matrix grid & rover tracks
│       ├── serve.py                           # Lightweight HTTP server
│       ├── stitch_tiles.py                    # GDAL / NumPy mosaic assembly script
│       ├── test_webapp.py                     # GDAL / NumPy verification test suite
│       ├── tiles -> ..                        # Symlink to raw Level 5 tiles
│       └── data/
│           ├── rover_traverses.json           # Rover traverses telemetry dataset
│           ├── astronaut_paths.geojson        # Exploration paths dataset
│           └── mars-traverses/                # Rover coordinate files
│
└── .github/
    ├── CODEOWNERS                             # Code ownership definitions
    └── workflows/
        ├── syntax-check.yml                   # CI: HTMLHint, Python syntax & JavaScript validation
        └── validate-promotion.yml             # Promotion rule: validates PR promotion path to official/dev
```

---

## 🌿 Branching Strategy & Promotion Path

This repository employs a multi-tier branch protection and promotion workflow:

```
feature/*  ───►  preview/rover-tracks  ───►  official/preview  ───►  official/dev
```

1. **`official/preview`**: Staging and preview branch where features are integrated, visually inspected, and validated against CI workflows (`syntax-check.yml`).
2. **`official/dev`**: Protected core development branch. Pull requests targeting `official/dev` are strictly restricted by workflow policy (`validate-promotion.yml`) to originate from `official/preview`.

---

## 🔬 Credits & Data Attributions

- **NASA Planetary Data System (PDS) & Mars Trek**: Mars Global Surveyor (MGS) MOLA laser altimetry and Mars Express (MEX) HRSC color hillshade blend.
- **NASA / JPL-Caltech**: Mars 2020 (*Perseverance*), Mars Science Laboratory (*Curiosity*), Mars Exploration Rovers (*Spirit* & *Opportunity*), and MMGIS telemetry.
- **China National Space Administration (CNSA)**: Tianwen-1 (*Zhurong* rover) landing and traverse coordinates.
- **Washington University in St. Louis (WUSTL)**: PDS Geosciences Node Orbital Data Explorer (ODE) and Geosciences Data Services (GDS).
