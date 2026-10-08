# MALO_MARS_HiRes_Render

High-resolution Mars global mosaic assembled from NASA Mars Trek Level 5 tiles (MGS MOLA + MEX HRSC Color Hillshade Blend at 200 m/px).

**Main Deployed Application:** `dataset/web_app_gpu/` — Hardware GPU-Accelerated WebGL2 Viewer  
**Reference Application:** `dataset/web_app/` — Standard Leaflet Viewer with full GIS outputs

---

## Data Source

**NASA Mars Trek WMTS API**  
Endpoint: `https://api.nasa.gov/mars-wmts/catalog/{layer}/1.0.0/{style}/{tileMatrixSet}/{tileMatrix}/{tileRow}/{tileCol}.jpg`

| Parameter | Value |
|-----------|-------|
| **Layer** | `Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw` |
| **Style** | `default` |
| **TileMatrixSet** | `default028mm` (Equirectangular, 5.625°/tile at Level 5) |
| **TileMatrix (Zoom)** | `5` |
| **Format** | JPEG |
| **Coverage** | Global: [-180°, -90°] to [180°, 90°] |

*Capabilities XML: `https://api.nasa.gov/mars-wmts/catalog/Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw/1.0.0/WMTSCapabilities.xml`*

---

## Tile Grid Specification (Level 5)

| Property | Value |
|----------|-------|
| **Tile Size** | 256 × 256 px |
| **Grid** | 64 columns × 32 rows = **2,048 tiles** |
| **Longitude Step** | 360° / 64 = **5.625°** per column |
| **Latitude Step** | 180° / 32 = **5.625°** per row |
| **Tile Naming** | `5_{row}_{col}.jpg` (row 0–31 N→S, col 0–63 W→E) |

---

## Output Mosaic

| Property | Value |
|----------|-------|
| **Dimensions** | 16,384 × 8,192 px (134.2 MP) |
| **Projection** | Equirectangular / Plate Carrée (EPSG:104905, IAU2000:49900) |
| **Datum** | Mars 2000 Sphere (a = b = 3,396,190 m) |
| **GeoTransform** | `[-180.0, 0.02197265625, 0, 90.0, 0, -0.02197265625]` |
| **Pixel Resolution** | 0.02197265625° ≈ **200 m/px** at equator |
| **Outputs** | JPEG (95% quality), GeoTIFF (JPEG-compressed, tiled), GDAL VRT |

---

## Mathematical & Computational Engineering

### 1. Coordinate Mapping (Tile → Global Pixel)

```
# Tile grid indices
row ∈ [0, 31]   # 0 = North pole (+90°), 31 = South pole (-90°)
col ∈ [0, 63]   # 0 = -180°, 63 = +180°

# Geographic bounds per tile
lat_top    =  90 - row * 5.625
lat_bottom =  90 - (row + 1) * 5.625
lon_left   = -180 + col * 5.625
lon_right  = -180 + (col + 1) * 5.625

# Pixel placement in 16384×8192 mosaic
x_start = col * 256
y_start = row * 256
x_end   = (col + 1) * 256
y_end   = (row + 1) * 256
```

### 2. GeoTransform Derivation

```
pixel_width  = 360° / 16384 = 0.02197265625°  (≈ 200 m at equator)
pixel_height = 180° / 8192  = 0.02197265625°  (≈ 200 m)

GeoTransform = [
    -180.0,                    # Top-left longitude (West)
    pixel_width,               # Pixel width in degrees
    0.0,                       # Rotation (none)
    90.0,                      # Top-left latitude (North)
    0.0,                       # Rotation (none)
    -pixel_height              # Negative = North-up
]
```

### 3. Spatial Reference (PROJ.4)

```
+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 
    +a=3396190 +b=3396190 +units=m +no_defs
```
- `eqc` = Equirectangular (Plate Carrée)
- `a = b = 3396190` = Mars 2000 sphere radius (meters)
- No flattening (spherical body)

### 4. Stitching Algorithm (`web_app/stitch_tiles.py`)

```python
# 1. Pre-allocate composite buffer (NumPy)
mosaic = np.zeros((8192, 16384, 3), dtype=np.uint8)  # ~402 MB

# 2. Row-major tile placement
for r in range(32):
    for c in range(64):
        tile = gdal.Open(f"5_{r}_{c}.jpg").ReadAsArray()  # (3, 256, 256)
        tile_rgb = np.transpose(tile[:3], (1, 2, 0))       # → (256, 256, 3)
        mosaic[r*256:(r+1)*256, c*256:(c+1)*256] = tile_rgb

# 3. Write outputs via GDAL
#    - JPEG: CreateCopy from MEM driver (QUALITY=95)
#    - GeoTIFF: CreateCopy + SetGeoTransform + SetProjection
#    - VRT: XML with 2,048 <SimpleSource> entries referencing source tiles
```

### 5. Seam Continuity Verification

Pipeline validates adjacent tile edges match within natural topography variation:

| Seam Type | Test | Threshold |
|-----------|------|-----------|
| **Horizontal** (row transitions) | Mean |Δ| at 31 internal boundaries | < 15/255 vs baseline |
| **Vertical** (col transitions) | Mean |Δ| at 63 internal boundaries | < 15/255 vs baseline |
| **Baseline** | Intra-tile pixel step (y=127→128) | Reference |

All 94 internal boundaries verified seamless (differences ≈ intra-tile noise).

### 6. GDAL Virtual Raster (VRT)

Encodes mosaic as logical 16384×8192 dataset without duplicating pixel data:

```xml
<VRTDataset rasterXSize="16384" rasterYSize="8192">
  <SRS>+proj=eqc +a=3396190 +b=3396190 ...</SRS>
  <GeoTransform>-180.0, 0.02197265625, 0.0, 90.0, 0.0, -0.02197265625</GeoTransform>
  <VRTRasterBand band="1" dataType="Byte">
    <ColorInterp>Red</ColorInterp>
    <SimpleSource>
      <SourceFilename relativeToVRT="1">../5_0_0.jpg</SourceFilename>
      <SourceBand>1</SourceBand>
      <SrcRect xOff="0" yOff="0" xSize="256" ySize="256"/>
      <DstRect xOff="0" yOff="0" xSize="256" ySize="256"/>
    </SimpleSource>
    ... (2,048 sources × 3 bands)
  </VRTRasterBand>
</VRTDataset>
```

---

## Web Applications

### 1. GPU-Accelerated Viewer (Primary — `web_app_gpu/`)

**Port:** 8083 | **Engine:** WebGL2 / GLSL ES Shaders | **Runtime:** Hardware GPU cores

| Feature | Implementation |
|---------|----------------|
| **Rendering** | Custom `prog2D` vertex/fragment shaders; planetary Lon/Lat → NDC transform in GPU |
| **Texture Streaming** | `createImageBitmap()` off-thread decoding → WebGL texture upload; eliminates main-thread jank |
| **GPU Texture Cache** | LRU pool (512 textures max); prioritizes on-screen tiles, evicts off-screen |
| **Frustum Culling** | Viewport bounding box → tile row/col range → only visible quads fetched/rendered |
| **Base LOD Fallback** | 2K downscaled composite (`mars_mola_base_2k.jpg`) renders instantly underneath |
| **Post-Processing Shaders** | Real-time sliders: Brightness, Contrast, Laplacian Ridge Sharpening, Tile Seam Overlay |
| **Hardware Telemetry** | Live FPS, frame time (ms), GPU renderer string (`WEBGL_debug_renderer_info`), VRAM texture count, async streams in-flight |
| **Interaction** | Pan (drag), Zoom (wheel), Landmark fly-to (eased animation), Planetary Inspector HUD |

**Coordinate Inspector (HUD):** Mars Lat/Lon, 0–360°E, Tile Matrix (Row/Col), Local Pixel (0–255), Global 16K Pixel

### 2. Standard Leaflet Viewer (Reference — `web_app/`)

**Port:** 8082 | **Engine:** Leaflet 1.9.4 (`L.CRS.EPSG4326`)

| Feature | Implementation |
|---------|----------------|
| **Layers** | Composite mosaic overlay + Dynamic local tile grid (on-demand) |
| **Overlays** | Tile matrix grid (2,048 cells), Graticule (Equator, Prime Meridian, ±30°/±60°), Landmark markers |
| **HUD** | Real-time coordinate inspector (same as GPU viewer) |
| **Canvas Stitcher** | In-browser HTML5 Canvas assembles all 2,048 tiles → 16384×8192 PNG export |
| **GIS Outputs** | Generates GeoTIFF + VRT for QGIS/ArcGIS ingestion |

---

## Quick Start

```bash
# 1. Run verification tests (both apps)
python3 dataset/web_app/test_webapp.py
python3 dataset/web_app_gpu/test_gpu_app.py

# 2. Start GPU-Accelerated Viewer (recommended)
cd dataset/web_app_gpu
python3 serve.py 8083
# Open http://localhost:8083

# 3. Or start Standard Leaflet Viewer
cd dataset/web_app
python3 serve.py 8082
# Open http://localhost:8082

# 4. Re-generate mosaic artifacts (optional)
cd dataset/web_app
python3 stitch_tiles.py
```

---

## Project Structure

```
dataset/
├── 5_0_0.jpg ... 5_31_63.jpg         # 2,048 Level 5 raw tiles (256×256 each)
│
├── web_app/                          # Standard Leaflet Viewer + Stitching Pipeline
│   ├── tiles -> ..                   # Symlink to raw tiles
│   ├── lib/                          # Offline Leaflet CSS/JS
│   ├── index.html                    # Leaflet frontend
│   ├── stitch_tiles.py               # GDAL/NumPy assembly pipeline
│   ├── mars_mola_level5_mosaic.jpg   # 16K composite JPEG (~50 MB)
│   ├── mars_mola_level5_mosaic.tif   # Georeferenced GeoTIFF (~132 MB)
│   ├── mars_mola_level5.vrt          # GDAL Virtual Raster (1.6 MB)
│   ├── serve.py                      # HTTP server (port 8082)
│   └── test_webapp.py                # Verification suite
│
└── web_app_gpu/                      # GPU-Accelerated WebGL2 Viewer (MAIN)
    ├── tiles -> ..                   # Symlink to raw tiles
    ├── mars_mola_level5_mosaic.jpg -> ../web_app/mars_mola_level5_mosaic.jpg
    ├── mars_mola_base_2k.jpg         # 2K LOD base texture for instant fallback
    ├── index.html                    # WebGL2/GLSL frontend (1,050 lines)
    ├── serve.py                      # Threaded HTTP server (port 8083)
    └── test_gpu_app.py               # GPU app verification suite
```

---

## License

NASA Mars Trek data: Public domain (US Government work).  
Code: MIT License.