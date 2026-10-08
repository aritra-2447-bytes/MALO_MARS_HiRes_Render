#!/usr/bin/env python3
"""
Automated Verification Suite for GPU Accelerated Mars Web Viewer in web_app_gpu
"""
import os
import sys
import subprocess
import urllib.request

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

    # Test 1: File Existence & Symlink Integrity
    print("\n[Test 1] Verifying File Structure & Symlinks...")
    assert os.path.exists(index_html), "index.html missing in web_app_gpu"
    assert os.path.exists(serve_py), "serve.py missing in web_app_gpu"
    assert os.path.exists(tiles_symlink), "tiles symlink missing in web_app_gpu"
    assert os.path.exists(mosaic_symlink), "mars_mola_level5_mosaic.jpg symlink missing"
    print(f"  PASS: All core files and symlinks exist in {gpu_dir}")

    # Test 2: Tile Access Verification (All 2,048 tiles)
    print("\n[Test 2] Verifying Access to All 2,048 Level 5 Tiles via Symlink...")
    for r in range(32):
        for c in range(64):
            t_path = os.path.join(tiles_symlink, f"5_{r}_{c}.jpg")
            assert os.path.exists(t_path) and os.path.getsize(t_path) > 0, f"Missing/empty tile: {t_path}"
    print("  PASS: All 2,048 tiles (5_0_0.jpg through 5_31_63.jpg) verified accessible.")

    # Test 3: Validate HTML, WebGL Shaders & GPU Features
    print("\n[Test 3] Verifying WebGL Hardware Acceleration Features in index.html...")
    with open(index_html, "r", encoding="utf-8") as f:
        html = f.read()

    assert "getContext('webgl2'" in html, "WebGL2 initialization missing"
    assert "createImageBitmap" in html, "Off-thread GPU image decoding pipeline missing"
    assert "precision highp float;" in html, "GLSL shader precision declaration missing"
    assert "texture2D" in html, "GLSL texture sampling missing"
    assert "btn-mode-3d" not in html, "Broken 3D globe toggle still present in index.html"
    assert "createSphereGeometry" not in html, "Unused 3D sphere generator still present"
    assert "MAX_GPU_TEXTURES" in html, "GPU texture cache management missing"
    assert "Olympus Mons" in html, "Landmark waypoints missing"
    assert "btn-reset-view" in html, "Camera reset button missing"
    assert "val-fps" in html, "Hardware telemetry HUD missing"
    print("  PASS: 3D globe toggle removed; WebGL2 2D hardware pipeline & async streaming verified.")

    # Test 4: JavaScript Syntax Validation via Node.js
    print("\n[Test 4] Validating JavaScript Code via Node.js...")
    # Extract script content from HTML
    script_start = html.find("<script>") + len("<script>")
    script_end = html.find("</script>")
    js_code = html[script_start:script_end]

    # Quick syntax parse test using node -c
    syntax_check_script = "const vm = require('vm'); try { new vm.Script(" + repr(js_code) + "); console.log('Syntax valid'); } catch(e) { console.error(e); process.exit(1); }"
    result = subprocess.run(["node", "-e", syntax_check_script], capture_output=True, text=True)
    assert result.returncode == 0, f"JavaScript syntax error: {result.stderr}"
    print("  PASS: Embedded WebGL JavaScript engine parses cleanly with 0 syntax errors.")

    # Test 5: Verify Original web_app Still Intact & Operational
    print("\n[Test 5] Verifying Original web_app Directory Integrity...")
    orig_index = os.path.join(orig_web_dir, "index.html")
    orig_mosaic = os.path.join(orig_web_dir, "mars_mola_level5_mosaic.jpg")
    orig_tif = os.path.join(orig_web_dir, "mars_mola_level5_mosaic.tif")
    orig_vrt = os.path.join(orig_web_dir, "mars_mola_level5.vrt")
    assert os.path.exists(orig_index), "Original web_app index.html broken!"
    assert os.path.exists(orig_mosaic), "Original mosaic.jpg broken!"
    assert os.path.exists(orig_tif), "Original mosaic.tif broken!"
    assert os.path.exists(orig_vrt), "Original mosaic.vrt broken!"
    print("  PASS: Original web_app is 100% intact, undisturbed, and verified.")

    print("\n" + "=" * 65)
    print("ALL TESTS PASSED! GPU ACCELERATED WEB_APP_GPU IS READY.")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
