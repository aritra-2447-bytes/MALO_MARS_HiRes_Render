# NASA Mars Trek Level 5 Web Application Fix Report

## 1. Executive Summary

When running `python3 web_app_gpu/serve.py 8080`, two critical issues occurred:
1. The server console logged multiple **HTTP 404 (File Not Found)** errors.
2. The web application suffered from **degraded visual rendering**: flickering tiles, missing terrain sections (black voids), infinite fetch storms, and erratic mouse drag sensitivity.

All root causes were diagnosed and resolved. Both test suites (`test_gpu_app.py` and `test_webapp.py`) now pass with 100% compliance, and all HTTP endpoints respond with **HTTP 200 OK** in 1–5 ms.

---

## 2. Problem Analysis & Root Causes

### Problem 1: Broken Symlink on Composite Mosaic (HTTP 404)
- **Symptom**: Requests to `/mars_mola_level5_mosaic.jpg` failed with `404 File not found`.
- **Root Cause**: `web_app_gpu/mars_mola_level5_mosaic.jpg` was an absolute symbolic link pointing to a non-existent path (`/home/aritra/Hermes_Area/...`) from an earlier workspace clone, rather than a relative link pointing to the local file `../web_app/mars_mola_level5_mosaic.jpg` (50.5 MB).
- **Consequence**: `loadBaseComposite()` threw an unhandled decoding error on the 404 response body, leaving `baseTexture` as `null`.

### Problem 2: Texture Cache Thrashing & Tile Request Flood
- **Symptom**: Black rectangular holes across Mars, high CPU/GPU utilization, and an endless loop of tile fetches.
- **Root Cause**:
  - Because `baseTexture` was `null`, the viewer attempted to render all Level 5 tiles.
  - At whole-planet overview (`zoom = 1.0`), all **2,048 tiles** ($64 \times 32$) fell within the visible frustum.
  - The WebGL texture pool was capped at `MAX_GPU_TEXTURES = 384`.
  - When tile 385 loaded, it evicted tile 1 using standard LRU. Because tile 1 was still in the active viewport, `render2D()` immediately re-requested tile 1. This evicted tile 2, which was re-requested, triggering an **infinite thrashing cascade** across all 2,048 tiles.

### Problem 3: Single-Threaded HTTP Server Bottleneck & Missing Endpoints
- **Symptom**: Network requests stalled, connection resets occurred, and browser consoles logged 404 errors for `/favicon.ico` and `/web_app_gpu/`.
- **Root Cause**:
  - `web_app_gpu/serve.py` used `socketserver.TCPServer`, which is strictly single-threaded. Parallel tile fetch requests queued sequentially behind large file transfers.
  - Missing route handlers for `/favicon.ico`, bare directory aliases (`/web_app_gpu`), and direct root tile requests (`/5_r_c.jpg`) generated avoidable 404 errors.

### Problem 4: Mouse Drag Coordinate Scaling Mismatch
- **Symptom**: Mouse panning felt slippery and disconnected from the cursor.
- **Root Cause**: The drag delta calculation in `mousemove` was:
  ```javascript
  const degPerPixelX = (360.0 / (camera2D.zoom * 2.0 * canvas.clientHeight));
  ```
  It divided by `canvas.clientHeight * 2.0` instead of `canvas.clientWidth`, causing horizontal panning speed to diverge significantly from mouse travel.

### Problem 5: Missing Longitude Antimeridian Seam Wrapping
- **Symptom**: Panning past $-180^\circ$ or $+180^\circ$ longitude caused the terrain to cut off into black void space.
- **Root Cause**: The base quad was only drawn once at coordinates $[-180, 180]$, lacking horizontal modular repeat passes.

---

## 3. Implemented Solutions

### 3.1 Symlink Repair & Instant 2K LOD Overview
1. Relinked `web_app_gpu/mars_mola_level5_mosaic.jpg` using a relative path:
   ```bash
   ln -sf ../web_app/mars_mola_level5_mosaic.jpg web_app_gpu/mars_mola_level5_mosaic.jpg
   ```
2. Generated an optimized 400 KB base overview texture (`web_app_gpu/mars_mola_base_2k.jpg`, $2048 \times 1024$) using `gdal_translate`.
3. Updated `loadBaseComposite()` to load the 2K thumbnail in ~2 ms for instant first-frame planetary display, seamlessly backed by the full 16K master.

### 3.2 High-Performance Multi-Threaded HTTP Server (`web_app_gpu/serve.py`)
1. Switched from `socketserver.TCPServer` to a multi-threaded server (`socketserver.ThreadingMixIn`, `http.server.HTTPServer`) with `allow_reuse_address = True`. Tile streaming now serves dozens of concurrent connections in parallel without head-of-line blocking.
2. Implemented intelligent URL routing in `Handler.translate_path()`:
   - `/favicon.ico` / `/favicon.svg`: Serves an embedded Mars SVG icon with `200 OK` (no more 404 logs).
   - `/web_app_gpu` / `/web_app_gpu/`: Automatically aliases to `index.html`.
   - `/web_app/*`: Seamlessly serves files from the sibling Leaflet viewer.
   - `/tiles/5_r_c.jpg` and `/5_r_c.jpg`: Directly routes to dataset tile fragments.
   - `/mars_mola_level5_mosaic.jpg`: Serves the composite master with local fallback.
   - Full CORS headers (`Access-Control-Allow-Origin: *`) and cache-control headers enabled.

### 3.3 LOD Frustum Culling & Anti-Thrashing Eviction (`web_app_gpu/index.html`)
1. **LOD Zoom Threshold**:
   - At overview levels (`camera2D.zoom < 1.6` or frustum tiles $> 512$), the application renders the complete global 16K base mosaic. It no longer floods the browser with 2,048 tile requests.
   - When zoomed in (`camera2D.zoom >= 1.6`), high-resolution Level 5 tiles stream asynchronously.
2. **Priority-Protected Cache Eviction**:
   - Expanded texture pool to `MAX_GPU_TEXTURES = 512`.
   - The eviction algorithm checks whether a cached tile is within the active viewport:
     ```javascript
     const isVis = (tr >= currentMinRow && tr <= currentMaxRow && tc >= currentMinCol && tc <= currentMaxCol);
     const score = isVis ? (v.lastUsed + 1e12) : v.lastUsed;
     ```
   - Off-screen tiles are always evicted first. Visible tiles are protected from eviction, completely stopping the re-fetch loop.
3. **Bounded Horizontal Navigation (No Looping)**:
   - Eliminated horizontal map repeating/looping by removing modular offset quads. The Mars map is rendered strictly within its physical longitude bounds $[-180^\circ, 180^\circ]$.
   - Horizontal drag panning (`camera2D.centerLon`) is clamped to $[-180^\circ, 180^\circ]$, stopping cleanly at the edges without looping.
4. **Tile Matrix Seam Overlay Disabled by Default**:
   - Updated the UI toggle to be unchecked by default (`<input type="checkbox" id="toggle-grid">`) and set `shaderParams.showGrid = false` on initial load for a clean, uninterrupted topographical view.
5. **1:1 Mouse & Touch Dragging**:
   - Corrected pixel-to-degree formulas:
     ```javascript
     const degPerPixelX = 360.0 / (camera2D.zoom * canvas.clientWidth);
     const degPerPixelY = 180.0 / (camera2D.zoom * canvas.clientHeight);
     ```
   - Added touch event handlers for touchscreen and mobile panning.

---

## 4. Verification & Testing

### 4.1 Automated Test Suites
Both verification suites run and pass:
```bash
# 1. GPU Accelerated Viewer Test Suite
python3 web_app_gpu/test_gpu_app.py
# Result: ALL TESTS PASSED! GPU ACCELERATED WEB_APP_GPU IS READY.

# 2. Standard Leaflet Viewer Test Suite
python3 web_app/test_webapp.py
# Result: ALL TESTS PASSED! MAP ARRANGEMENT IN LEVEL_5 WEB_APP IS ENTIRELY ACCURATE.
```

### 4.2 Endpoint HTTP Status Matrix
Tested on `http://localhost:8080`:

| Request Path | Status | Response Size | Latency | Note |
|---|---|---|---|---|
| `GET /` | **200 OK** | 34.1 KB | 0.006s | GPU Viewer HTML |
| `GET /favicon.ico` | **200 OK** | 265 B | 0.001s | Mars SVG Icon (Fixed 404) |
| `GET /mars_mola_base_2k.jpg` | **200 OK** | 409.9 KB | 0.002s | Instant 2K LOD |
| `GET /mars_mola_level5_mosaic.jpg` | **200 OK** | 50.5 MB | 0.048s | 16K Master Composite (Fixed 404) |
| `GET /tiles/5_0_0.jpg` | **200 OK** | 26.9 KB | 0.002s | Level 5 Tile Fragment |
| `GET /tiles/5_15_31.jpg` | **200 OK** | 61.4 KB | 0.002s | Equator/Prime Meridian Tile |
| `GET /web_app_gpu/index.html` | **200 OK** | 34.1 KB | 0.002s | Directory Alias Route |
| `GET /web_app/index.html` | **200 OK** | 26.8 KB | 0.001s | Standard Leaflet App Route |
| `GET /5_31_63.jpg` | **200 OK** | 24.6 KB | 0.002s | Direct Root Tile Route |

---

## 5. How to Run the Web Applications

### 5.1 Option A: Hardware GPU-Accelerated Viewer (Recommended)
From the dataset root directory:
```bash
python3 web_app_gpu/serve.py 8080
```
Open in browser:
```
http://localhost:8080
```

#### Features & Controls:
- **Pan**: Click and drag with mouse (or single-finger touch drag).
- **Zoom**: Mouse wheel scroll (or pinch-to-zoom).
- **Quick Fly-To**: Click chips in the top-left HUD (Olympus Mons, Valles Marineris, Gale Crater, Jezero Crater, Hellas Planitia, North/South Poles).
- **Real-Time GLSL Post-Processing**: Sliders in the bottom-right panel adjust Brightness, Contrast, and Terrain Ridge Sharpening (Laplacian filter).
- **Seam Overlay**: Checkbox toggles tile matrix boundary seams.
- **Hardware Telemetry**: Top-right HUD displays live FPS (60+ FPS), render latency (ms), active VRAM texture count, and GPU renderer.

---

### 5.2 Option B: Standard Leaflet Viewer
From the dataset root directory:
```bash
python3 web_app/serve.py 8082
```
Open in browser:
```
http://localhost:8082
```
*(Can also be accessed directly through the GPU server at `http://localhost:8080/web_app/`)*

---

### 5.3 Stopping the Servers
To terminate any running server instance:
```bash
pkill -f "serve.py"
```
