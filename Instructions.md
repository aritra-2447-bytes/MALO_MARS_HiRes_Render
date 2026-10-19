# NASA Mars Trek Level 5 Map Stitching & Web Application Instructions

This document provides complete technical documentation of the implementation plan, mathematical spatial arrangement, stitching pipeline, web application architectures, and step-by-step instructions for running and verifying both the **Standard Leaflet Web App** and the **Hardware GPU-Accelerated Web App**.

---

## 1. Dataset & Spatial Grid Specifications

### 1.1 Dataset Reference
* **Layer Identifier**: `Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw`
* **Dataset Name**: MGS MOLA and Mars Express HRSC Color Hillshade Blend
* **Projection**: Equirectangular (Plate Carrée), Mars IAU 2000 (`EPSG:104905`, central meridian = 0°)
* **Bounding Box**: Longitude `[-180.0, 180.0]`, Latitude `[-90.0, 90.0]`
* **Zoom Level**: 5

### 1.2 Grid Geometry (Level 5)
* **Matrix Width**: 64 columns (`col` = `0` to `63`, West to East)
* **Matrix Height**: 32 rows (`row` = `0` to `31`, North to South)
* **Total Tile Count**: $64 \times 32 = 2,048$ tiles
* **Individual Tile Size**: $256 \times 256$ pixels (JPEG format)
* **Total Composite Mosaic Size**:
  * Width: $64 \times 256 = 16,384$ pixels (16K horizontal)
  * Height: $32 \times 256 = 8,192$ pixels (8K vertical)
  * Total Resolution: $134,217,728$ pixels (~134.2 Megapixels)
* **Angular Extent per Tile**:
  * Longitude span per tile: $360^\circ / 64 = 5.625^\circ$
  * Latitude span per tile: $180^\circ / 32 = 5.625^\circ$
* **Resolution per Pixel**:
  * $\Delta\text{Lon} = 360^\circ / 16,384 \approx 0.02197265625^\circ\text{/px}$ ($\approx 1.30\text{ km/px}$ at equator)
  * $\Delta\text{Lat} = 180^\circ / 8,192 \approx 0.02197265625^\circ\text{/px}$

---

## 2. Spatial Arrangement & Placement Rules

Each tile is named according to the WMTS scheme: `5_{row}_{col}.jpg`.

### 2.1 Coordinate Mapping
* **Row Index (`row` $\in [0, 31]$)**:
  * `row = 0`: North Pole ($+90.0^\circ\text{N}$ down to $+84.375^\circ\text{N}$)
  * `row = 15`: Just north of Equator ($+5.625^\circ\text{N}$ down to $0.0^\circ$)
  * `row = 16`: Just south of Equator ($0.0^\circ$ down to $-5.625^\circ\text{S}$)
  * `row = 31`: South Pole ($-84.375^\circ\text{S}$ down to $-90.0^\circ\text{S}$)
  * **Pixel $Y$ Offset**: $Y = row \times 256$
* **Column Index (`col` $\in [0, 63]$)**:
  * `col = 0`: Far West ($-180.0^\circ\text{W}$ to $-174.375^\circ\text{W}$)
  * `col = 31`: Just west of Prime Meridian ($-5.625^\circ\text{W}$ to $0.0^\circ$)
  * `col = 32`: Just east of Prime Meridian ($0.0^\circ$ to $+5.625^\circ\text{E}$)
  * `col = 63`: Far East ($+174.375^\circ\text{E}$ to $+180.0^\circ\text{E}$)
  * **Pixel $X$ Offset**: $X = col \times 256$

### 2.2 Tile Matrix Map
```
 (0,0) [180°W, +90°N]                                                          (16384, 0) [180°E, +90°N]
   ┌───────────┬───────────┬┄┄┄┄┄┄┄┄┄┄┬───────────┬───────────┬┄┄┄┄┄┄┄┄┄┄┬───────────┐
   │   5_0_0   │   5_0_1   │   ...    │  5_0_31   │  5_0_32   │   ...    │  5_0_63   │  row 0 (North Pole)
   ├───────────┼───────────┼┄┄┄┄┄┄┄┄┄┄┼───────────┼───────────┼┄┄┄┄┄┄┄┄┄┄┼───────────┤
   │   5_1_0   │   5_1_1   │   ...    │  5_1_31   │  5_1_32   │   ...    │  5_1_63   │  row 1
   ├───────────┼───────────┼┄┄┄┄┄┄┄┄┄┄┼───────────┼───────────┼┄┄┄┄┄┄┄┄┄┄┼───────────┤
   │    ...    │    ...    │   ...    │    ...    │    ...    │   ...    │    ...    │
   ├───────────┼───────────┼┄┄┄┄┄┄┄┄┄┄┼───────────┼───────────┼┄┄┄┄┄┄┄┄┄┄┼───────────┤
   │  5_15_0   │  5_15_1   │   ...    │  5_15_31  │  5_15_32  │   ...    │  5_15_63  │  row 15
   ╞═══════════╪═══════════╪══════════╪═══════════╪═══════════╪══════════╪═══════════╡  EQUATOR (0° Lat)
   │  5_16_0   │  5_16_1   │   ...    │  5_16_31  │  5_16_32  │   ...    │  5_16_63  │  row 16
   ├───────────┼───────────┼┄┄┄┄┄┄┄┄┄┄┼───────────┼───────────┼┄┄┄┄┄┄┄┄┄┄┼───────────┤
   │    ...    │    ...    │   ...    │    ...    │    ...    │   ...    │    ...    │
   ├───────────┼───────────┼┄┄┄┄┄┄┄┄┄┄┼───────────┼───────────┼┄┄┄┄┄┄┄┄┄┄┼───────────┤
   │  5_31_0   │  5_31_1   │   ...    │  5_31_31  │  5_31_32  │   ...    │  5_31_63  │  row 31 (South Pole)
   └───────────┴───────────┴┄┄┄┄┄┄┄┄┄┄┴───────────┴───────────┴┄┄┄┄┄┄┄┄┄┄┴───────────┘
 (0, 8192) [180°W, -90°S]                                                     (16384, 8192) [180°E, -90°S]
                                            ▲           ▲
                                          col 31      col 32
                                          PRIME MERIDIAN (0° Lon)
```

---

## 3. Stitching & Assembly Pipeline

The assembly script is [`stitch_tiles.py`](file:///home/aritra/Hermes_Area/data/Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw/level_5/web_app/stitch_tiles.py).

### 3.1 Memory Buffer & Insertion
1. Allocates an RGB NumPy array `np.zeros((8192, 16384, 3), dtype=np.uint8)` (~402 MB in RAM).
2. Traverses all rows $r \in [0, 31]$ and columns $c \in [0, 63]$.
3. Opens `5_{r}_{c}.jpg` via GDAL `ds.ReadAsArray()`.
4. Copies pixel slice into `mosaic[r*256 : (r+1)*256, c*256 : (c+1)*256, :]`.

### 3.2 Output Artifacts Generated
1. **`mars_mola_level5_mosaic.jpg`**: High-quality 16K JPEG (quality=95, ~50.5 MB).
2. **`mars_mola_level5_mosaic.tif`**: Georeferenced GeoTIFF (~131.9 MB) with:
   * **GeoTransform**: `[-180.0, 360.0/16384, 0.0, 90.0, 0.0, -180.0/8192]`
   * **Spatial Reference**: `+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +a=3396190 +b=3396190 +units=m +no_defs`
   * **Tiling**: `TILED=YES, COMPRESS=JPEG, JPEG_QUALITY=95`
3. **`mars_mola_level5.vrt`**: GDAL Virtual Raster XML referencing all 2,048 tiles with geolocated bounding boxes for direct GIS ingestion (QGIS / ArcGIS).
4. **Automated Seam Continuity Verification**: Computes mean pixel step differences across all 31 horizontal row transitions and 63 vertical column transitions to mathematically guarantee seamless visual continuity.

---

## 4. Web Applications Architecture

Two complementary web viewing applications are provided:

### 4.1 Standard Leaflet Web App (`web_app`)
* **Location**: `data/Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw/level_5/web_app`
* **Default Port**: `8082`
* **Features**:
  * **Leaflet Engine**: Configured with `L.CRS.EPSG4326` (Mars Equirectangular projection).
  * **Dual-Layer Rendering**:
    1. Composite 16K image overlay (`mars_mola_level5_mosaic.jpg`).
    2. Dynamic local tile grid (`tiles/5_{row}_{col}.jpg` loaded on-demand as user zooms).
  * **Boundary Overlays**: Visual 2,048-cell tile matrix grid (`5_r_c`) and planetary graticule (Equator, Prime Meridian, parallels, meridians).
  * **Planetary Landmarks**: Quick-fly waypoints and popups for Olympus Mons, Valles Marineris, Gale Crater, Jezero Crater, Hellas Planitia, North and South Polar Caps.
  * **Planetary Inspector HUD**: Real-time cursor coordinates in Mars Lat/Lon, 0–360°E, active tile index, tile local pixel (0–255), and global 16K pixel.
  * **In-Browser HTML5 Canvas Stitcher Modal**: Client-side tile assembly tool with live progress bar and PNG export.

### 4.2 Hardware GPU-Accelerated Web App (`web_app_gpu`)
* **Location**: `data/Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw/level_5/web_app_gpu`
* **Default Port**: `8083`
* **Features**:
  * **WebGL2 / WebGL Hardware Engine**: Uses custom GLSL ES shaders (`prog2D`) executing directly on GPU hardware cores.
  * **Asynchronous Off-Thread Streaming**: Uses `createImageBitmap()` to offload JPEG decoding from the JavaScript main thread to background GPU/browser threads, completely eliminating scrolling/zooming stutter.
  * **Dynamic GPU Texture Cache**: LRU cache pooling up to 384 active WebGL textures in VRAM, recycling GPU allocations automatically.
  * **Frustum Culling**: Only tiles intersecting the active viewport are fetched and queued for GPU rendering.
  * **Instant Fallback LOD Base**: Global 16K composite base texture renders immediately underneath, preventing empty voids or white flickers during rapid panning.
  * **GPU Post-Processing Shaders**: Live real-time sliders for:
    * Brightness / Exposure adjustment
    * Contrast adjustment
    * Terrain Ridge Convolution Sharpening (Laplacian edge filter)
    * Tile Matrix Seam indicator
  * **Hardware Telemetry HUD**: Live frame rate (60 / 120 FPS), frame render time (ms), active textures in VRAM, and detected unmasked GPU adapter name (`WEBGL_debug_renderer_info`).

---

## 5. Step-by-Step Instructions to Run

### 5.1 Prerequisites
Ensure the system has Python 3 and GDAL installed:
```bash
python3 --version
python3 -c "from osgeo import gdal; print('GDAL:', gdal.__version__)"
```

---

### 5.2 Running the Automated Test Suites
Run the verification suites to confirm map arrangement accuracy, tile integrity, and asset health:

**Test the Standard Web App:**
```bash
python3 /home/aritra/Hermes_Area/data/Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw/level_5/web_app/test_webapp.py
```

**Test the GPU-Accelerated Web App:**
```bash
python3 /home/aritra/Hermes_Area/data/Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw/level_5/web_app_gpu/test_gpu_app.py
```

---

### 5.3 Starting the Web Servers

#### Option A: Running the GPU-Accelerated Viewer (Recommended for Performance)
```bash
cd /home/aritra/Hermes_Area/data/Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw/level_5/web_app_gpu
python3 serve.py 8083
```
Open in browser:
```
http://localhost:8083
```

#### Option B: Running the Standard Leaflet Viewer
```bash
cd /home/aritra/Hermes_Area/data/Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw/level_5/web_app
python3 serve.py 8082
```
Open in browser:
```
http://localhost:8082
```

#### Running Both in Background
To keep both servers running concurrently in the background:
```bash
nohup python3 /home/aritra/Hermes_Area/data/Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw/level_5/web_app/serve.py 8082 > /dev/null 2>&1 &
nohup python3 /home/aritra/Hermes_Area/data/Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw/level_5/web_app_gpu/serve.py 8083 > /dev/null 2>&1 &
```

To stop any running instance:
```bash
pkill -f "serve.py 8082"
pkill -f "serve.py 8083"
```

---

### 5.4 Re-running the Tile Stitcher (Optional)
If you wish to re-generate the composite JPEG, GeoTIFF, and VRT:
```bash
cd /home/aritra/Hermes_Area/data/Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw/level_5/web_app
python3 stitch_tiles.py
```

---

## 6. Directory Layout & File Reference

```
data/Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw/level_5/
├── 5_0_0.jpg ... 5_31_63.jpg         # 2,048 Level 5 raw tile fragments (256x256 px each)
├── Instructions.md                   # Complete implementation & usage documentation (this file)
│
├── web_app/                          # Standard Leaflet Interactive Viewer
│   ├── tiles -> ..                   # Symlink to raw tiles directory
│   ├── lib/
│   │   ├── leaflet.js                # Offline Leaflet v1.9.4 library
│   │   └── leaflet.css               # Offline Leaflet styling
│   ├── index.html                    # Standard web application frontend
│   ├── stitch_tiles.py               # GDAL/NumPy 2,048-tile assembly pipeline
│   ├── mars_mola_level5_mosaic.jpg   # 16,384 x 8,192 composite JPEG (~50.5 MB)
│   ├── mars_mola_level5_mosaic.tif   # Georeferenced GeoTIFF (IAU2000 Mars Eqc, ~131.9 MB)
│   ├── mars_mola_level5.vrt          # GDAL Virtual Raster XML
│   ├── serve.py                      # Local HTTP server (port 8082)
│   └── test_webapp.py                # Automated verification test suite
│
└── web_app_gpu/                      # Hardware GPU-Accelerated Viewer
    ├── tiles -> ..                   # Symlink to raw tiles directory
    ├── mars_mola_level5_mosaic.jpg -> ../web_app/mars_mola_level5_mosaic.jpg
    ├── index.html                    # WebGL2 GLSL-accelerated web application frontend
    ├── serve.py                      # Local HTTP server (port 8083)
    └── test_gpu_app.py               # GPU application verification suite
```

---

## 7. User Controls & Interaction Guide

| Action | Control (Mouse / Keyboard) | Result |
|---|---|---|
| **Pan / Navigate** | Left-click + Drag | Smoothly translates across Mars surface |
| **Zoom** | Mouse Wheel / Touch Pinch | Sub-pixel zoom from whole planet to high resolution |
| **Inspect Position** | Hover Mouse | Live HUD updates: Lat/Lon, $0\text{--}360^\circ\text{E}$, Tile index `5_r_c`, local and 16K global pixels |
| **Jump to Landmark** | Click any Landmark Chip | Smooth camera animation to Olympus Mons, Valles Marineris, Gale Crater, Jezero Crater, etc. |
| **Adjust Shaders (GPU)** | Sliders in Bottom-Right HUD | Real-time GLSL filter adjustments for Brightness, Contrast, and Terrain Ridge Sharpening |
| **Toggle Overlays** | Checkboxes in HUD | Toggle Mosaic, Direct Tile Grid, Seam Bounds, Graticule Lines, and Landmark Markers |
| **Reset View** | Click "Reset Camera" Button | Restores default whole-planet view centered at $(0^\circ\text{N}, 0^\circ\text{E})$ |
