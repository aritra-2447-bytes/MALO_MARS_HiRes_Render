#!/usr/bin/env python3
"""
NASA Mars Trek Level 6 (32K Composite / 100 m/px) LOD Pyramid & Inset Engine
Layer: Mars MOLA + HRSC Level 6 Composite (32,768 x 16,384 px)
Tiling Grid: 128 columns x 64 rows = 8,192 tiles (256x256 px each)
Resolution: ~100 m/pixel at equator (0.010986328125 deg/px)
"""

import os
import sys
import json
import time
from PIL import Image

# Global constants for Level 6 WMTS grid
L6_COLS = 128
L6_ROWS = 64
TILE_SIZE = 256
GLOBAL_WIDTH = L6_COLS * TILE_SIZE   # 32768 px
GLOBAL_HEIGHT = L6_ROWS * TILE_SIZE  # 16384 px
DEG_PER_COL = 360.0 / L6_COLS        # 2.8125 degrees
DEG_PER_ROW = 180.0 / L6_ROWS        # 2.8125 degrees

TIFF_CANDIDATE_PATHS = [
    "/run/media/nilavra/New Volume/All Projects/Mars Map Making(NASA)/mars_mola_level6_mosaic.tif",
    os.path.join(os.path.dirname(__file__), "..", "..", "mars_mola_level6_mosaic.tif"),
    os.path.join(os.path.dirname(__file__), "mars_mola_level6_mosaic.tif")
]

LANDING_INSET_TARGETS = [
    {
        "id": "jezero_crater",
        "name": "Jezero Crater (Perseverance / Mars 2020)",
        "mission": "m20_perseverance",
        "lat": 18.4446,
        "lon": 77.4508,
        "deg_span": 2.2,
        "resolution_m_px": "100m/px L6 Composite + HiRISE Inset",
        "features": ["Western Delta", "Belva Crater", "Séítah Dunes", "Kodiak Butte"]
    },
    {
        "id": "gale_crater",
        "name": "Gale Crater (Curiosity / MSL)",
        "mission": "msl_curiosity",
        "lat": -4.5895,
        "lon": 137.4417,
        "deg_span": 2.4,
        "resolution_m_px": "100m/px L6 Composite + CTX Inset",
        "features": ["Mount Sharp (Aeolis Mons)", "Bradbury Landing", "Vera Rubin Ridge", "Gediz Vallis"]
    },
    {
        "id": "meridiani_planum",
        "name": "Meridiani Planum (Opportunity / MER-B)",
        "mission": "mer_opportunity",
        "lat": -1.9462,
        "lon": -5.5266,
        "deg_span": 2.6,
        "resolution_m_px": "100m/px L6 Composite + MOC Inset",
        "features": ["Challenger Memorial Station", "Eagle Crater", "Victoria Crater", "Endeavour Crater"]
    },
    {
        "id": "gusev_crater",
        "name": "Gusev Crater (Spirit / MER-A)",
        "mission": "mer_spirit",
        "lat": -14.5684,
        "lon": 175.4726,
        "deg_span": 2.2,
        "resolution_m_px": "100m/px L6 Composite",
        "features": ["Columbia Memorial Station", "Bonneville Crater", "Husband Hill", "Home Plate"]
    },
    {
        "id": "utopia_planitia",
        "name": "Southern Utopia Planitia (Zhurong / Tianwen-1)",
        "mission": "cnsa_zhurong",
        "lat": 25.0833,
        "lon": 109.9084,
        "deg_span": 2.2,
        "resolution_m_px": "100m/px L6 Composite",
        "features": ["Zhurong Landing Site", "Dune Corridor", "Southern Utopia Hibernation Site"]
    }
]

def find_level6_tiff():
    for p in TIFF_CANDIDATE_PATHS:
        abs_p = os.path.abspath(p)
        if os.path.exists(abs_p) and os.path.getsize(abs_p) > 1000000:
            return abs_p
    return None

def latlon_to_tile(lat, lon):
    col = int(((lon + 180.0) / 360.0) * L6_COLS)
    row = int(((90.0 - lat) / 180.0) * L6_ROWS)
    col = max(0, min(L6_COLS - 1, col))
    row = max(0, min(L6_ROWS - 1, row))
    return col, row

def tile_bounds(col, row):
    lon_min = -180.0 + col * DEG_PER_COL
    lon_max = lon_min + DEG_PER_COL
    lat_max = 90.0 - row * DEG_PER_ROW
    lat_min = lat_max - DEG_PER_ROW
    return {
        "lon_min": lon_min,
        "lon_max": lon_max,
        "lat_min": lat_min,
        "lat_max": lat_max,
        "col": col,
        "row": row
    }

def generate_landing_insets(output_dir=None):
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "insets")
    os.makedirs(output_dir, exist_ok=True)
    
    tif_file = find_level6_tiff()
    metadata_list = []
    
    Image.MAX_IMAGE_PIXELS = None
    im = None
    if tif_file:
        try:
            im = Image.open(tif_file)
        except Exception as e:
            print(f"[!] Warning opening TIFF: {e}")
            
    for t in LANDING_INSET_TARGETS:
        lat = t["lat"]
        lon = t["lon"]
        span = t["deg_span"]
        lat_min = lat - span / 2.0
        lat_max = lat + span / 2.0
        lon_min = lon - span / 2.0
        lon_max = lon + span / 2.0
        
        col, row = latlon_to_tile(lat, lon)
        filename = f"{t['id']}_hires.jpg"
        out_path = os.path.join(output_dir, filename)
        
        # If image does not exist and TIFF is available, crop it
        if not os.path.exists(out_path) and im is not None:
            w, h = im.size
            x0 = max(0, min(w - 1, int(((lon_min + 180.0) / 360.0) * w)))
            x1 = max(0, min(w, int(((lon_max + 180.0) / 360.0) * w)))
            y0 = max(0, min(h - 1, int(((90.0 - lat_max) / 180.0) * h)))
            y1 = max(0, min(h, int(((90.0 - lat_min) / 180.0) * h)))
            
            crop = im.crop((x0, y0, x1, y1))
            resized = crop.resize((1024, 1024), Image.Resampling.LANCZOS)
            resized.save(out_path, "JPEG", quality=90)
            
        file_size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
        metadata_list.append({
            "id": t["id"],
            "name": t["name"],
            "mission": t["mission"],
            "lat": lat,
            "lon": lon,
            "deg_span": span,
            "lat_min": lat_min,
            "lat_max": lat_max,
            "lon_min": lon_min,
            "lon_max": lon_max,
            "tile_l6": {"col": col, "row": row},
            "texture_url": f"/insets/{filename}",
            "file_size_bytes": file_size,
            "resolution": t["resolution_m_px"],
            "features": t["features"]
        })
        
    meta_path = os.path.join(output_dir, "insets_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "status": "success",
            "layer": "Level 6 (32K / 100m/px) Targeted Inset Patches",
            "count": len(metadata_list),
            "insets": metadata_list
        }, f, indent=2)
    print(f"[*] Saved inset metadata to {meta_path}")
    return metadata_list

if __name__ == "__main__":
    generate_landing_insets()
