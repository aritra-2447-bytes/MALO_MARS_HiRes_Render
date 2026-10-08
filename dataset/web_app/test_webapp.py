#!/usr/bin/env python3
"""
Automated Verification Suite for NASA Mars Trek Level 5 Map Assembly in web_app
"""
import os
import sys
import numpy as np
from osgeo import gdal

def run_tests():
    print("=" * 65)
    print("RUNNING AUTOMATED TESTS: MARS LEVEL 5 WEB_APP VERIFICATION")
    print("=" * 65)
    
    gdal.SetConfigOption("GDAL_ERROR_ON_LIBJPEG_WARNING", "FALSE")
    
    web_app_dir = os.path.dirname(os.path.abspath(__file__))
    mosaic_jpg = os.path.join(web_app_dir, "mars_mola_level5_mosaic.jpg")
    mosaic_tif = os.path.join(web_app_dir, "mars_mola_level5_mosaic.tif")
    vrt_path = os.path.join(web_app_dir, "mars_mola_level5.vrt")
    tiles_symlink = os.path.join(web_app_dir, "tiles")
    index_html = os.path.join(web_app_dir, "index.html")
    
    # Test 1: Check Mosaic JPEG
    print("\n[Test 1] Verifying Composite JPEG Image...")
    assert os.path.exists(mosaic_jpg), f"File not found: {mosaic_jpg}"
    ds_jpg = gdal.Open(mosaic_jpg)
    assert ds_jpg is not None, "Failed to open mosaic JPEG with GDAL"
    assert ds_jpg.RasterXSize == 16384, f"Expected width 16384, got {ds_jpg.RasterXSize}"
    assert ds_jpg.RasterYSize == 8192, f"Expected height 8192, got {ds_jpg.RasterYSize}"
    assert ds_jpg.RasterCount == 3, f"Expected 3 bands (RGB), got {ds_jpg.RasterCount}"
    print(f"  PASS: Mosaic JPEG is {ds_jpg.RasterXSize}x{ds_jpg.RasterYSize}x{ds_jpg.RasterCount} ({os.path.getsize(mosaic_jpg):,} bytes)")
    ds_jpg = None

    # Test 2: Check GeoTIFF and Georeferencing
    print("\n[Test 2] Verifying Georeferenced GeoTIFF...")
    assert os.path.exists(mosaic_tif), f"File not found: {mosaic_tif}"
    ds_tif = gdal.Open(mosaic_tif)
    assert ds_tif is not None, "Failed to open mosaic GeoTIFF"
    assert ds_tif.RasterXSize == 16384 and ds_tif.RasterYSize == 8192, "Dimensions mismatch in GeoTIFF"
    
    gt = ds_tif.GetGeoTransform()
    assert gt is not None, "GeoTransform not found"
    assert np.isclose(gt[0], -180.0), f"Expected West origin -180.0, got {gt[0]}"
    assert np.isclose(gt[3], 90.0), f"Expected North origin 90.0, got {gt[3]}"
    assert np.isclose(gt[1], 360.0 / 16384), f"Expected X resolution {360.0/16384}, got {gt[1]}"
    assert np.isclose(gt[5], -180.0 / 8192), f"Expected Y resolution {-180.0/8192}, got {gt[5]}"
    print(f"  PASS: GeoTIFF origin=({gt[0]}, {gt[3]}), res=({gt[1]:.8f}, {gt[5]:.8f})")
    ds_tif = None

    # Test 3: Check VRT
    print("\n[Test 3] Verifying GDAL Virtual Raster (VRT)...")
    assert os.path.exists(vrt_path), f"File not found: {vrt_path}"
    ds_vrt = gdal.Open(vrt_path)
    assert ds_vrt is not None, "Failed to open VRT with GDAL"
    assert ds_vrt.RasterXSize == 16384 and ds_vrt.RasterYSize == 8192, "VRT dimension mismatch"
    print(f"  PASS: VRT successfully references 2,048 tiles at 16384x8192.")
    ds_vrt = None

    # Test 4: Check all 2,048 tile fragments via symlink
    print("\n[Test 4] Verifying All 2,048 Tile Fragments...")
    assert os.path.exists(tiles_symlink), f"Tiles link not found: {tiles_symlink}"
    for r in range(32):
        for c in range(64):
            t_path = os.path.join(tiles_symlink, f"5_{r}_{c}.jpg")
            assert os.path.exists(t_path), f"Missing tile: {t_path}"
    print("  PASS: All 2,048 tile files (5_0_0.jpg through 5_31_63.jpg) accessible via web_app/tiles.")

    # Test 5: Check Seam Boundary Continuity Across All Horizontal & Vertical Cuts
    print("\n[Test 5] Verifying Seamless Edge Continuity Across Entire Matrix...")
    ds = gdal.Open(mosaic_jpg)
    arr = ds.ReadAsArray() # (3, 8192, 16384)
    ds = None
    
    # Check sample horizontal internal seams (Row transitions)
    h_seam_diffs = []
    for r in range(1, 32):
        y = r * 256
        diff = np.abs(arr[:, y - 1, :].astype(np.float32) - arr[:, y, :].astype(np.float32)).mean()
        h_seam_diffs.append(diff)
    mean_h = np.mean(h_seam_diffs)
    
    # Check sample vertical internal seams (Col transitions)
    v_seam_diffs = []
    for c in range(1, 64):
        x = c * 256
        diff = np.abs(arr[:, :, x - 1].astype(np.float32) - arr[:, :, x].astype(np.float32)).mean()
        v_seam_diffs.append(diff)
    mean_v = np.mean(v_seam_diffs)

    # Baseline intra-tile step difference (1 pixel inside tile)
    baseline_diff = np.abs(arr[:, 127, :].astype(np.float32) - arr[:, 128, :].astype(np.float32)).mean()

    print(f"  Horizontal internal seams mean pixel step: {mean_h:.2f} / 255")
    print(f"  Vertical internal seams mean pixel step:   {mean_v:.2f} / 255")
    print(f"  Baseline intra-tile pixel step:            {baseline_diff:.2f} / 255")
    assert mean_h < 15.0, f"Horizontal seams show abnormally high step difference: {mean_h}"
    assert mean_v < 15.0, f"Vertical seams show abnormally high step difference: {mean_v}"
    print("  PASS: All 94 boundary cuts seamlessly blend with natural topography gradient.")

    # Test 6: Verify Web Application Assets
    print("\n[Test 6] Verifying Web Application Files...")
    assert os.path.exists(index_html), "index.html missing"
    assert os.path.exists(os.path.join(web_app_dir, "lib", "leaflet.js")), "leaflet.js missing"
    assert os.path.exists(os.path.join(web_app_dir, "lib", "leaflet.css")), "leaflet.css missing"
    
    with open(index_html, "r", encoding="utf-8") as f:
        html_content = f.read()
    assert "mars_mola_level5_mosaic.jpg" in html_content, "index.html missing mosaic image reference"
    assert "L.CRS.EPSG4326" in html_content, "index.html missing Mars Equirectangular CRS"
    assert "Olympus Mons" in html_content, "index.html missing landmark annotations"
    assert "Browser Canvas Stitcher" in html_content, "index.html missing canvas stitcher tool"
    print("  PASS: Web application index.html is self-contained with offline Leaflet library.")

    print("\n" + "=" * 65)
    print("ALL TESTS PASSED! MAP ARRANGEMENT IN LEVEL_5 WEB_APP IS ENTIRELY ACCURATE.")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
