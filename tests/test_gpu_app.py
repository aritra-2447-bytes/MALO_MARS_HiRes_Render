#!/usr/bin/env python3
"""
Automated Verification Suite for Mars Unified Server
Validates 3D Globe Viewer, 2D Leaflet Viewer, GeoJSON Exploration Dataset,
Landing Site Markers, Status Color System, Server API Endpoints, and Live HTTP Responses.
"""
import os
import sys
import json
import urllib.request
import threading
import time
import unittest

def run_tests():
    print("=" * 65)
    print("RUNNING AUTOMATED TESTS: MARS UNIFIED SERVER")
    print("=" * 65)

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    public_dir = os.path.join(root_dir, "public")
    data_dir = os.path.join(root_dir, "data")
    tiles_dir = os.path.join(root_dir, "tiles")
    web_app_2d_dir = os.path.join(root_dir, "web_app_2d")
    server_dir = os.path.join(root_dir, "server")

    index_html = os.path.join(public_dir, "index.html")
    index_2d_html = os.path.join(public_dir, "index_2d_backup.html")
    web_app_2d_index = os.path.join(web_app_2d_dir, "index.html")
    server_py = os.path.join(server_dir, "server.py")
    geojson = os.path.join(data_dir, "astronaut_paths.geojson")

    # Test 1: File Existence
    print("\n[Test 1] Verifying File Structure...")
    assert os.path.exists(index_html), f"index.html missing in {public_dir}"
    assert os.path.exists(index_2d_html), f"index_2d_backup.html missing in {public_dir}"
    assert os.path.exists(web_app_2d_index), f"web_app_2d/index.html missing"
    assert os.path.exists(server_py), f"server/server.py missing"
    assert os.path.exists(geojson), f"data/astronaut_paths.geojson missing"
    assert os.path.exists(tiles_dir), f"tiles/ directory missing"
    print(f"  PASS: All core files and directories exist")

    # Test 2: Tile Access Verification (All 2,048 tiles)
    print("\n[Test 2] Verifying Access to All 2,048 Level 5 Tiles...")
    for r in range(32):
        for c in range(64):
            t_path = os.path.join(tiles_dir, f"5_{r}_{c}.jpg")
            assert os.path.exists(t_path) and os.path.getsize(t_path) > 0, f"Missing/empty tile: {t_path}"
    print("  PASS: All 2,048 tiles (5_0_0.jpg through 5_31_63.jpg) verified accessible.")

    # Test 3: GeoJSON Exploration Dataset Verification
    print("\n[Test 3] Verifying GeoJSON Exploration Dataset (18 Features)...")
    with open(geojson, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("type") == "FeatureCollection", "Dataset must be a FeatureCollection"
    features = data.get("features", [])
    assert len(features) == 18, f"Expected 18 features in dataset, found {len(features)}"

    statuses = {f["properties"].get("status") for f in features}
    assert "Active" in statuses, "Missing 'Active' status missions"
    assert "Completed" in statuses, "Missing 'Completed' status missions"
    assert "Failed" in statuses, "Missing 'Failed' status missions"
    assert "Proposed" in statuses, "Missing 'Proposed' status missions"

    point_count = sum(1 for f in features if f["geometry"]["type"] == "Point")
    linestring_count = sum(1 for f in features if f["geometry"]["type"] == "LineString")
    assert point_count >= 10, f"Expected at least 10 Point features, got {point_count}"
    assert linestring_count >= 8, f"Expected 8 LineString traverse features, got {linestring_count}"

    for f in features:
        props = f["properties"]
        geom = f["geometry"]
        assert "id" in props and "name" in props and "status" in props, f"Missing core properties in {f}"
        coords = geom["coordinates"]
        if geom["type"] == "Point":
            assert len(coords) >= 2, f"Invalid Point coordinate format in {props['name']}"
        elif geom["type"] == "LineString":
            assert len(coords) >= 2, f"LineString requires >= 2 points in {props['name']}"
    print(f"  PASS: 18 features verified (8 traverses, 10 landers) across Active, Completed, Failed, and Proposed statuses.")

    # Test 4: Validate 3D Viewer Implementation in public/index.html
    print("\n[Test 4] Verifying 3D Viewer Implementation in public/index.html...")
    with open(index_html, "r", encoding="utf-8") as f:
        html = f.read()

    # Three.js & Groups
    assert "THREE.WebGLRenderer" in html, "Three.js WebGLRenderer missing"
    assert "astroPathsGroup" in html, "astroPathsGroup missing in 3D scene"
    assert "landingSiteMarkersGroup" in html, "landingSiteMarkersGroup missing in 3D scene"
    assert "corridorHighlightGroup" in html, "corridorHighlightGroup missing in 3D scene"

    # Status-based colors
    assert "STATUS_COLORS" in html, "STATUS_COLORS dictionary missing"
    assert "getStatusColor" in html, "getStatusColor function missing"
    assert "0x22c55e" in html and "0x94a3b8" in html and "0xef4444" in html, "Status color codes missing"

    # Exploration paths & Landing site markers
    assert "loadAstroPaths" in html, "loadAstroPaths function missing"
    assert "renderAstroPaths" in html, "renderAstroPaths function missing"
    assert "populateAstroPathsLegend" in html, "populateAstroPathsLegend function missing"
    assert "renderLandingSiteMarkers" in html, "renderLandingSiteMarkers function missing"
    assert "DEFAULT_LANDING_SITES" in html, "DEFAULT_LANDING_SITES missing"

    # Hover detection & Corridor Highlighting
    assert "highlightMissionCorridor" in html, "highlightMissionCorridor function missing"
    assert "clearCorridorHighlight" in html, "clearCorridorHighlight function missing"
    assert "corridorClearTimeout" in html, "corridorClearTimeout debounce missing"
    assert "geom.coordinates" in html, "Point coordinate extraction from geometry missing"
    assert "interactivePins" in html, "Raycaster interactivePins collection missing"

    # UI controls (Legend panel removed & integrated into Landings tab)
    assert "legend-panel" not in html, "Legend panel container should be removed"
    assert "btn-toggle-legend" not in html, "Legend toggle button should be removed"
    assert "tab-landings" in html, "Landing sites drawer tab missing"
    assert "landings-list" in html, "Landings list container missing"
    assert "landing-vis-chk" in html, "Landings visibility toggle checkboxes missing"
    assert "landing-fly-btn" in html, "Landings fly action buttons missing"
    assert "statusOrder" in html, "Status ordering (Active -> Completed -> Failed) missing"
    assert "landing-group-header" in html, "Landing status group headers missing"
    print("  PASS: 3D paths, landing markers, status colors, corridor pulse, and hover detection verified.")

    # Test 5: Validate 2D WebGL Viewer in public/index_2d_backup.html
    print("\n[Test 5] Verifying 2D WebGL Viewer Implementation...")
    with open(index_2d_html, "r", encoding="utf-8") as f:
        html_2d = f.read()

    assert "loadTextureFromFile" in html_2d, "loadTextureFromFile missing in 2D viewer"
    assert "mars_mola_base_2k" in html_2d, "MOLA base texture reference missing"
    assert "mars_sim3292_geology_4k" in html_2d, "Geology texture reference missing"
    print("  PASS: 2D WebGL viewer textures and layer toggle verified.")

    # Test 6: Validate 2D Leaflet Viewer in web_app_2d/index.html
    print("\n[Test 6] Verifying 2D Leaflet Viewer Implementation...")
    with open(web_app_2d_index, "r", encoding="utf-8") as f:
        html_leaflet = f.read()

    assert "L.CRS.Simple" in html_leaflet, "Mars CRS missing in Leaflet viewer"
    assert "createTileLayer" in html_leaflet, "Tile layer factory missing"
    assert "/tiles/5_{y}_{x}.jpg" in html_leaflet, "Level 5 tile template missing"
    assert "/sim3292_tiles/tile_r{row}_c{col}.jpg" in html_leaflet, "SIM 3292 tile template missing"
    assert "astronaut_paths.geojson" in html_leaflet, "GeoJSON data reference missing"
    assert "layer-mola" in html_leaflet, "MOLA layer toggle missing"
    assert "layer-geology" in html_leaflet, "Geology layer toggle missing"
    assert "layer-traverses" in html_leaflet, "Traverses layer toggle missing"
    assert "layer-landers" in html_leaflet, "Landers layer toggle missing"
    print("  PASS: 2D Leaflet viewer tile templates, GeoJSON, and layer toggles verified.")

    # Test 7: Verify Server Architecture in server/server.py
    print("\n[Test 7] Verifying Server Architecture in server/server.py...")
    with open(server_py, "r", encoding="utf-8") as f:
        serve_code = f.read()

    assert "do_OPTIONS" in serve_code, "do_OPTIONS CORS preflight handler missing"
    assert "APIHandler" in serve_code, "APIHandler missing"
    assert "translate_path" in serve_code, "translate_path function missing"
    assert "ThreadingServer" in serve_code, "ThreadingServer missing"
    print("  PASS: Server CORS preflight, API routing, threading, and path translation verified.")

    # Test 8: Verify Modular Server Core
    print("\n[Test 8] Verifying Modular Server Core...")
    core_dir = os.path.join(server_dir, "core")
    assert os.path.exists(os.path.join(core_dir, "mars_data.py")), "mars_data.py missing"
    assert os.path.exists(os.path.join(core_dir, "ephemeris.py")), "ephemeris.py missing"
    assert os.path.exists(os.path.join(core_dir, "eva_engine.py")), "eva_engine.py missing"
    assert os.path.exists(os.path.join(core_dir, "nasa_proxy.py")), "nasa_proxy.py missing"
    assert os.path.exists(os.path.join(core_dir, "tile_server.py")), "tile_server.py missing"
    assert os.path.exists(os.path.join(core_dir, "handlers.py")), "handlers.py missing"
    print("  PASS: All modular core modules present.")

    # Test 9: Live Server HTTP Integration Tests
    print("\n[Test 9] Verifying Live HTTP Server and API Endpoints...")
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    from server.server import MarsHandler, ThreadingServer
    import socket

    # Bind to ephemeral port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        test_port = s.getsockname()[1]

    httpd = ThreadingServer(("127.0.0.1", test_port), MarsHandler)
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.2)

    try:
        base_url = f"http://127.0.0.1:{test_port}"

        # 1. Root index
        with urllib.request.urlopen(f"{base_url}/", timeout=5) as resp:
            assert resp.status == 200, f"Root returned {resp.status}"
            assert b"Mars 3D Explorer" in resp.read()

        # 2. Ephemeris API
        with urllib.request.urlopen(f"{base_url}/api/mars/ephemeris", timeout=5) as resp:
            assert resp.status == 200, f"Ephemeris API returned {resp.status}"
            data = json.loads(resp.read().decode("utf-8"))
            assert data.get("status") == "success"
            assert "mars_sol_date" in data

        # 3. Landmarks API
        with urllib.request.urlopen(f"{base_url}/api/landmarks", timeout=5) as resp:
            assert resp.status == 200, f"Landmarks API returned {resp.status}"
            data = json.loads(resp.read().decode("utf-8"))
            assert data.get("status") == "success"
            assert len(data.get("landmarks", [])) >= 10

        # 4. Rover Missions API
        with urllib.request.urlopen(f"{base_url}/api/rover/missions", timeout=5) as resp:
            assert resp.status == 200, f"Rover missions API returned {resp.status}"
            data = json.loads(resp.read().decode("utf-8"))
            assert data.get("status") == "success"
            assert data.get("count", 0) >= 4

        # 5. EVA Presets & Route Plan API
        with urllib.request.urlopen(f"{base_url}/api/eva/presets", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert len(data.get("routes", [])) >= 3

        with urllib.request.urlopen(f"{base_url}/api/eva/plan", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data.get("status") == "success"

        # 6. Geology dataset API
        with urllib.request.urlopen(f"{base_url}/api/sim3292/data", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "geologic_units" in data

        # 7. Static Tile and Texture check
        with urllib.request.urlopen(f"{base_url}/tiles/5_0_0.jpg", timeout=5) as resp:
            assert resp.status == 200
            assert resp.headers.get("Content-Type") == "image/jpeg"

        with urllib.request.urlopen(f"{base_url}/textures/mars_mola_base_2k.jpg", timeout=5) as resp:
            assert resp.status == 200
            assert resp.headers.get("Content-Type") == "image/jpeg"

        # 8. Web App 2D alias route
        with urllib.request.urlopen(f"{base_url}/web_app_2d", timeout=5) as resp:
            assert resp.status == 200
            assert b"Mars Level 5" in resp.read()

        # 9. Geology Atlas route & documents
        with urllib.request.urlopen(f"{base_url}/geology_atlas.html", timeout=5) as resp:
            assert resp.status == 200

        with urllib.request.urlopen(f"{base_url}/README.txt", timeout=5) as resp:
            assert resp.status == 200
            assert b"USGS SCIENTIFIC INVESTIGATIONS MAP 3292" in resp.read()

        # 10. CORS Preflight
        req = urllib.request.Request(f"{base_url}/api/landmarks", method="OPTIONS")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            assert resp.headers.get("Access-Control-Allow-Origin") == "*"

        # 11. Rover Traverses API
        with urllib.request.urlopen(f"{base_url}/api/rover/traverses", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data.get("status") == "success"
            assert "missions" in data

        # 12. ARES-OS Science & Mission Control API
        with urllib.request.urlopen(f"{base_url}/api/atlas/missions", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data.get("status") == "success"
            assert data.get("count", 0) >= 15

        with urllib.request.urlopen(f"{base_url}/api/atlas/landmarks", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data.get("status") == "success"
            assert data.get("count", 0) >= 40

        with urllib.request.urlopen(f"{base_url}/api/minerals", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data.get("status") == "success"
            assert "classes" in data

        with urllib.request.urlopen(f"{base_url}/api/terrain/slope?lat=18.44&lon=77.45&size=0.03", timeout=10) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data.get("status") == "success"
            assert "slope" in data and "elevation" in data

        post_req = urllib.request.Request(
            f"{base_url}/api/scouting/plan",
            data=json.dumps({
                "start": {"lat": 18.4446, "lon": 77.4508},
                "target": {"lat": 18.51, "lon": 77.35},
                "max_iterations": 4
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(post_req, timeout=15) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data.get("status") == "success"
            assert "outcome" in data and "proof" in data

        with urllib.request.urlopen(f"{base_url}/api/mars/time?lon=77.45", timeout=5) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data.get("status") == "success"
            assert "ltst" in data and "lmst" in data

        print("  PASS: Live server HTTP requests, API routes, CORS, textures, traverses, and ARES-OS verified.")
    finally:
        httpd.shutdown()
        httpd.server_close()

    print("\n" + "=" * 65)
    print("ALL TESTS PASSED! MARS EXPLORATION SUITE FULLY OPERATIONAL.")
    print("=" * 65)


class MarsServerTestCase(unittest.TestCase):
    def test_all_mars_subsystems(self):
        run_tests()


if __name__ == "__main__":
    run_tests()
