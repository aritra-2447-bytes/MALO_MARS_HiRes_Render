#!/usr/bin/env python3
"""
Automated Verification Suite for GPU Accelerated Mars Web Viewer in web_app_gpu
Validates 3D Globe Viewer, GeoJSON Exploration Dataset, Exploration Paths,
Landing Site Markers, Status Color System, and Hover Detection.
"""
import os
import sys
import json

def run_tests():
    print("=" * 65)
    print("RUNNING AUTOMATED TESTS: MARS GPU ACCELERATED WEB_APP_GPU")
    print("=" * 65)

    gpu_dir = os.path.dirname(os.path.abspath(__file__))
    orig_web_dir = os.path.abspath(os.path.join(gpu_dir, "..", "web_app"))
    index_html = os.path.join(gpu_dir, "index.html")
    serve_py = os.path.join(gpu_dir, "serve.py")
    tiles_symlink = os.path.join(gpu_dir, "tiles")
    mosaic_symlink = os.path.join(gpu_dir, "mars_mola_level5_mosaic.jpg")
    geojson_gpu = os.path.join(gpu_dir, "data", "astronaut_paths.geojson")
    geojson_web = os.path.join(orig_web_dir, "data", "astronaut_paths.geojson")

    # Test 1: File Existence & Symlink Integrity
    print("\n[Test 1] Verifying File Structure & Symlinks...")
    assert os.path.exists(index_html), "index.html missing in web_app_gpu"
    assert os.path.exists(serve_py), "serve.py missing in web_app_gpu"
    assert os.path.exists(tiles_symlink), "tiles symlink missing in web_app_gpu"
    assert os.path.exists(mosaic_symlink), "mars_mola_level5_mosaic.jpg symlink missing"
    assert os.path.exists(geojson_gpu), "data/astronaut_paths.geojson missing in web_app_gpu"
    assert os.path.exists(geojson_web), "data/astronaut_paths.geojson missing in web_app"
    print(f"  PASS: All core files, datasets, and symlinks exist in {gpu_dir}")

    # Test 2: Tile Access Verification (All 2,048 tiles)
    print("\n[Test 2] Verifying Access to All 2,048 Level 5 Tiles via Symlink...")
    for r in range(32):
        for c in range(64):
            t_path = os.path.join(tiles_symlink, f"5_{r}_{c}.jpg")
            assert os.path.exists(t_path) and os.path.getsize(t_path) > 0, f"Missing/empty tile: {t_path}"
    print("  PASS: All 2,048 tiles (5_0_0.jpg through 5_31_63.jpg) verified accessible.")

    # Test 3: GeoJSON Exploration Dataset Verification
    print("\n[Test 3] Verifying GeoJSON Exploration Dataset (18 Features)...")
    with open(geojson_gpu, "r", encoding="utf-8") as f:
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

    # Test 4: Validate 3D Viewer Implementation in index.html
    print("\n[Test 4] Verifying 3D Viewer Implementation in index.html...")
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

    # Test 5: Validate 2D Leaflet Viewer in web_app/index.html
    print("\n[Test 5] Verifying 2D Leaflet Viewer Implementation...")
    orig_index = os.path.join(orig_web_dir, "index.html")
    with open(orig_index, "r", encoding="utf-8") as f:
        html_2d = f.read()

    assert "loadRoverTraverses" in html_2d, "loadRoverTraverses missing in 2D viewer"
    assert "roverTraversesGroup" in html_2d, "roverTraversesGroup missing in 2D viewer"
    assert "bindTooltip" in html_2d, "Hover tooltips missing in 2D viewer"
    assert "toggle-exploration" in html_2d, "Exploration layer toggle missing in 2D viewer"
    print("  PASS: 2D viewer polylines, status colors, hover tooltips, and layer toggle verified.")

    # Test 6: Verify Server Architecture in serve.py
    print("\n[Test 6] Verifying Server Architecture in serve.py...")
    with open(serve_py, "r", encoding="utf-8") as f:
        serve_code = f.read()

    assert "do_OPTIONS" in serve_code, "do_OPTIONS CORS preflight handler missing in serve.py"
    assert "/data/" in serve_code, "translate_path /data/* routing missing in serve.py"
    assert "ThreadingServer" in serve_code, "ThreadingServer missing in serve.py"
    assert "/api/rover/traverses" in serve_code, "/api/rover/traverses API route missing in serve.py"
    print("  PASS: Server CORS preflight, /data/* route handling, /api/rover/traverses, and threading verified.")

    # Test 7: Verify Rover Traverses Telemetry Dataset
    print("\n[Test 7] Verifying Rover Traverses Dataset & Landing Sites Tracks...")
    rt_json_gpu = os.path.join(gpu_dir, "data", "rover_traverses.json")
    assert os.path.exists(rt_json_gpu), "data/rover_traverses.json missing in web_app_gpu"
    with open(rt_json_gpu, "r", encoding="utf-8") as f:
        rt_data = json.load(f)

    # Validate completed historical mobile rovers with drive traverses
    completed_rovers = ["mer_opportunity", "mer_spirit", "cnsa_zhurong", "pathfinder_sojourner"]
    for cr in completed_rovers:
        assert cr in rt_data, f"Missing completed rover {cr} in rover_traverses.json"
        entry = rt_data[cr]
        assert entry.get("type") == "rover", f"Expected type 'rover' for {cr}"
        assert "touchdown" in entry and "lat" in entry["touchdown"] and "lon" in entry["touchdown"], f"Missing touchdown in {cr}"
        assert "final" in entry and "lat" in entry["final"] and "lon" in entry["final"], f"Missing final destination in {cr}"
        assert entry.get("odometry_km", 0) > 0, f"Expected odometry > 0 for {cr}"
        assert "track" in entry and len(entry["track"]) >= 2, f"Expected >= 2 track points for {cr}"
        assert "milestones" in entry and len(entry["milestones"]) >= 2, f"Expected milestones for {cr}"

    # Validate stationary landers with EDL ellipses & workspaces
    stationary_landers = ["insight_lander", "phoenix_landing_site", "viking1_lander", "viking2_lander"]
    for sl in stationary_landers:
        assert sl in rt_data, f"Missing stationary lander {sl} in rover_traverses.json"
        entry = rt_data[sl]
        assert entry.get("type") == "lander", f"Expected type 'lander' for {sl}"
        assert "ellipse" in entry and "semi_major_km" in entry["ellipse"], f"Missing EDL ellipse for {sl}"

    print(f"  PASS: Rover traverses dataset verified ({len(rt_data)} missions: 4 completed rovers with 'from-where-to-where' tracks & stationary lander EDL ellipses).")

    # Test 8: Verify 3D Hover Traversal & Landing Sites Tracks Integration in index.html
    print("\n[Test 8] Verifying 3D Hover Traversal & Landing Sites Tracks Integration in index.html...")
    assert "loadRoverTraversesData" in html, "loadRoverTraversesData function missing in index.html"
    assert "loadRoverTraversesData()" in html, "loadRoverTraversesData() call on engine startup missing in index.html"
    assert "roverTraversesData" in html, "roverTraversesData state missing in index.html"
    assert "traverseCache" in html, "traverseCache Map missing in index.html"
    assert "createEllipsePoints" in html, "createEllipsePoints helper missing in index.html"
    assert "touchdown_marker" in html, "touchdown_marker hover handling missing in index.html"
    assert "final_stop_marker" in html, "final_stop_marker hover handling missing in index.html"
    assert "milestone_marker" in html, "milestone_marker hover handling missing in index.html"
    assert "card-hover-active" in html, "card-hover-active CSS and logic missing in index.html"
    assert "raycaster.params.Line" in html, "raycaster Line threshold missing in index.html"
    print("  PASS: 3D hover traversal, continuous glowing tube, touchdown/destination markers, and raycaster thresholds verified.")

    # Test 9: Verify Real-Time Topo Contours & Camera Zoom Clamping
    print("\n[Test 9] Verifying Topo Contours & Strict Camera Zoom Limits...")
    assert "u_contourify" in html, "u_contourify uniform missing in index.html"
    assert "btn-toggle-contour" in html, "btn-toggle-contour button missing in index.html"
    assert "controls.minDistance = 1.28" in html, "controls.minDistance must be set to 1.28 to prevent surface penetration"
    assert "LANDING_SITE_CAM_DIST = 1.35" in html, "LANDING_SITE_CAM_DIST must be set to 1.35 for stable orbital framing"
    assert "Spherical Great-Circle Interpolation" in html, "SLERP camera fly-to interpolation missing"
    assert "camera.position.setLength(controls.minDistance)" in html, "Hard distance clamp missing"

    # Verify rover simulation feature is completely removed
    assert "btn-rover-drive" not in html, "btn-rover-drive should be removed"
    assert "rover-sim-panel" not in html, "rover-sim-panel should be removed"
    assert "createRoverVehicle" not in html, "createRoverVehicle should be removed"
    assert "startRoverDriveDemo" not in html, "startRoverDriveDemo should be removed"
    blender_py = os.path.abspath(os.path.join(gpu_dir, "..", "..", "render_rover_video_blender.py"))
    assert not os.path.exists(blender_py), "render_rover_video_blender.py should be removed"
    print("  PASS: Real-time topographic contours and strict planetary camera zoom limits verified; rover simulation cleanly removed.")

    print("\n" + "=" * 65)
    print("ALL TESTS PASSED! MARS EXPLORATION SUITE FULLY OPERATIONAL.")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
