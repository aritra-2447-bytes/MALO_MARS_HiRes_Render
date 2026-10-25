#!/usr/bin/env python3
"""
Automated Verification Suite for NASA Mars Trek Level 5 Tile Assembly
Verifies the 2,048 Level 5 tiles and the stitching scripts.
"""
import os
import sys

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    from osgeo import gdal
    HAS_GDAL = True
except ImportError:
    HAS_GDAL = False
    gdal = None

def run_tests():
    print("=" * 65)
    print("RUNNING AUTOMATED TESTS: MARS LEVEL 5 TILE VERIFICATION")
    print("=" * 65)

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    tiles_dir = os.path.join(root_dir, "tiles")
    scripts_dir = os.path.join(root_dir, "scripts")

    # Test 1: Check all 2,048 tile fragments
    print("\n[Test 1] Verifying All 2,048 Tile Fragments...")
    assert os.path.exists(tiles_dir), f"Tiles directory not found: {tiles_dir}"
    missing = []
    for r in range(32):
        for c in range(64):
            t_path = os.path.join(tiles_dir, f"5_{r}_{c}.jpg")
            if not os.path.exists(t_path) or os.path.getsize(t_path) == 0:
                missing.append(t_path)
    assert len(missing) == 0, f"Missing/empty tiles: {missing[:5]}..."
    print(f"  PASS: All 2,048 tile files (5_0_0.jpg through 5_31_63.jpg) present and non-empty.")

    # Test 2: Check Stitching Scripts
    print("\n[Test 2] Verifying Stitching Scripts...")
    stitch_script = os.path.join(scripts_dir, "stitch_tiles.py")
    stitcher_script = os.path.join(scripts_dir, "sim3292_chunk_stitcher.py")
    assert os.path.exists(stitch_script), f"stitch_tiles.py missing in {scripts_dir}"
    assert os.path.exists(stitcher_script), f"sim3292_chunk_stitcher.py missing in {scripts_dir}"
    print(f"  PASS: Both stitching scripts present.")

    # Test 3: If GDAL and numpy available, verify tile dimensions and basic properties
    if HAS_GDAL and HAS_NUMPY:
        gdal.SetConfigOption("GDAL_ERROR_ON_LIBJPEG_WARNING", "FALSE")
        
        print("\n[Test 3] Verifying Tile Properties (GDAL)...")
        sample_tile = os.path.join(tiles_dir, "5_0_0.jpg")
        ds = gdal.Open(sample_tile)
        assert ds is not None, "Failed to open sample tile with GDAL"
        assert ds.RasterXSize == 256, f"Expected tile width 256, got {ds.RasterXSize}"
        assert ds.RasterYSize == 256, f"Expected tile height 256, got {ds.RasterYSize}"
        assert ds.RasterCount == 3, f"Expected 3 bands (RGB), got {ds.RasterCount}"
        ds = None
        print(f"  PASS: Sample tile is 256x256x3 (RGB).")

        # Test 4: Verify seam boundary continuity (sample check)
        print("\n[Test 4] Verifying Seam Continuity (Sample Check)...")
        # Check a few horizontal seams
        h_seam_diffs = []
        for r in [1, 8, 16, 24, 31]:
            y = r * 256
            # Load two adjacent tiles
            tile_top = os.path.join(tiles_dir, f"5_{r-1}_0.jpg")
            tile_bot = os.path.join(tiles_dir, f"5_{r}_0.jpg")
            ds_top = gdal.Open(tile_top)
            ds_bot = gdal.Open(tile_bot)
            arr_top = ds_top.ReadAsArray()
            arr_bot = ds_bot.ReadAsArray()
            diff = np.abs(arr_top[:, -1, :].astype(np.float32) - arr_bot[:, 0, :].astype(np.float32)).mean()
            h_seam_diffs.append(diff)
            ds_top = None
            ds_bot = None
        
        mean_h = np.mean(h_seam_diffs)
        print(f"  Horizontal internal seams (sample) mean pixel step: {mean_h:.2f} / 255")
        assert mean_h < 20.0, f"Horizontal seams show abnormally high step difference: {mean_h}"
        print("  PASS: Sample boundary cuts blend with natural topography gradient.")
    elif not HAS_GDAL:
        print("\n[Test 3] Skipping GDAL tests (GDAL not installed)")
    elif not HAS_NUMPY:
        print("\n[Test 3] Skipping GDAL/Numpy tests (numpy not installed)")

    # Test 5: Verify script content
    print("\n[Test 5] Verifying Stitch Script Content...")
    with open(stitch_script, "r") as f:
        stitch_content = f.read()
    assert "gdal" in stitch_content.lower(), "stitch_tiles.py missing GDAL reference"
    assert "16384" in stitch_content, "stitch_tiles.py missing output width"
    assert "8192" in stitch_content, "stitch_tiles.py missing output height"
    print("  PASS: Stitch script references correct output dimensions.")

    print("\n" + "=" * 65)
    print("ALL TESTS PASSED! LEVEL 5 TILE VERIFICATION COMPLETE.")
    print("=" * 65)

import unittest

class MarsWebappTestCase(unittest.TestCase):
    def test_tile_verification(self):
        run_tests()

if __name__ == "__main__":
    run_tests()