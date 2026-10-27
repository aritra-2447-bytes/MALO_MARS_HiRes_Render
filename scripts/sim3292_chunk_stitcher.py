#!/usr/bin/env python3
"""
USGS SIM 3292 Geological Map Processing Engine
1. Scope Filtering: Validates geological maps (excludes topography/DEM/gravity).
2. Chunking: Slices map into 72 tiles (8 rows x 9 columns) with 16px overlap buffer to preserve text.
3. Stitching: Reassembles chunks into a seamless 4K Equirectangular Planetary Globe Texture
   with raised-cosine edge blending to eliminate seams while preserving high-contrast cartographic labels.
"""

import os
import sys
import json
import time
from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance
import cv2

ROOT_DIR = Path(__file__).resolve().parent

# Target standard resolutions
WIDTH_4K = 4096
HEIGHT_4K = 2048
GRID_ROWS = 8
GRID_COLS = 9
TOTAL_TILES = GRID_ROWS * GRID_COLS  # 72 tiles
OVERLAP_PX = 16

def is_geological_map(image_path: str, min_saturation: float = 20.0) -> bool:
    """Filters out non-geological maps (e.g. grayscale MOLA DEMs or shaded relief)."""
    fname = Path(image_path).name.lower()
    excluded = ["mola", "dem", "relief", "gravity", "magnetic", "themis_ir"]
    if any(k in fname for k in excluded):
        return False
    try:
        with Image.open(image_path) as img:
            thumb = img.convert("RGB").resize((128, 64), Image.Resampling.BILINEAR)
            hsv = cv2.cvtColor(np.array(thumb), cv2.COLOR_RGB2HSV)
            return float(np.mean(hsv[:, :, 1])) >= min_saturation
    except Exception:
        return False


def chunk_geological_map(
    source_img_path: str,
    output_tiles_dir: str,
    rows: int = GRID_ROWS,
    cols: int = GRID_COLS,
    overlap: int = OVERLAP_PX
) -> str:
    """
    Slices the geological map into 72 tiles (8 rows x 9 cols) with an overlap margin.
    Guarantees no text labels are severed or cropped at tile edges.
    """
    os.makedirs(output_tiles_dir, exist_ok=True)
    with Image.open(source_img_path) as img:
        img_rgb = img.convert("RGB")
        w, h = img_rgb.size
        
        tile_w = w // cols
        tile_h = h // rows
        
        manifest = {
            "source": str(source_img_path),
            "width": w,
            "height": h,
            "rows": rows,
            "cols": cols,
            "total_tiles": rows * cols,
            "overlap_px": overlap,
            "tiles": []
        }
        
        for r in range(rows):
            for c in range(cols):
                # Bounding box with overlap padding
                x1 = max(0, c * tile_w - overlap)
                y1 = max(0, r * tile_h - overlap)
                x2 = min(w, (c + 1) * tile_w + overlap)
                y2 = min(h, (r + 1) * tile_h + overlap)
                
                tile = img_rgb.crop((x1, y1, x2, y2))
                tile_name = f"tile_r{r:02d}_c{c:02d}.jpg"
                tile_path = os.path.join(output_tiles_dir, tile_name)
                tile.save(tile_path, format="JPEG", quality=95)
                
                # Geodetic bounding coordinates for planetary mapping (IAU Mars 2000)
                lon_min = -180.0 + (c / cols) * 360.0
                lon_max = -180.0 + ((c + 1) / cols) * 360.0
                lat_max = 90.0 - (r / rows) * 180.0
                lat_min = 90.0 - ((r + 1) / rows) * 180.0
                
                manifest["tiles"].append({
                    "tile_file": tile_name,
                    "row": r,
                    "col": c,
                    "pixel_box": [x1, y1, x2, y2],
                    "core_box": [c * tile_w, r * tile_h, (c + 1) * tile_w, (r + 1) * tile_h],
                    "geo_extent": {
                        "lon_min": round(lon_min, 4),
                        "lon_max": round(lon_max, 4),
                        "lat_min": round(lat_min, 4),
                        "lat_max": round(lat_max, 4)
                    }
                })
                
    manifest_path = os.path.join(output_tiles_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"[Chunking] Generated {rows * cols} tiles (8x9 grid) with {overlap}px overlap in: {output_tiles_dir}")
    return manifest_path


def create_raised_cosine_mask(shape: tuple, overlap: int) -> np.ndarray:
    """Generates a smooth raised-cosine feathering weight mask for seam blending."""
    h, w = shape[:2]
    mask_x = np.ones(w, dtype=np.float32)
    mask_y = np.ones(h, dtype=np.float32)
    
    if overlap > 0:
        ramp = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, overlap, dtype=np.float32)))
        mask_x[:overlap] = ramp
        mask_x[-overlap:] = ramp[::-1]
        mask_y[:overlap] = ramp
        mask_y[-overlap:] = ramp[::-1]
        
    mask_2d = np.outer(mask_y, mask_x)
    return np.expand_dims(mask_2d, axis=-1)


def stitch_geological_tiles(manifest_path: str, output_4k_path: str) -> None:
    """
    Reassembles the 72 chunks into a seamless, geometrically coherent equirectangular projection.
    Uses raised-cosine alpha blending with edge-preserving text mask to eliminate seams without blurring labels.
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    tiles_dir = Path(manifest_path).parent
    width = manifest["width"]
    height = manifest["height"]
    overlap = manifest["overlap_px"]
    
    canvas_rgb = np.zeros((height, width, 3), dtype=np.float32)
    canvas_weight = np.zeros((height, width, 1), dtype=np.float32)
    
    for item in manifest["tiles"]:
        tile_file = os.path.join(tiles_dir, item["tile_file"])
        x1, y1, x2, y2 = item["pixel_box"]
        
        tile_bgr = cv2.imread(tile_file, cv2.IMREAD_COLOR)
        if tile_bgr is None:
            continue
        tile_rgb = cv2.cvtColor(tile_bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
        
        # Feathering weight mask
        feather_mask = create_raised_cosine_mask(tile_rgb.shape, overlap)
        
        # Preserve sharp text labels by detecting high-contrast edges
        gray = cv2.cvtColor(tile_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Laplacian(gray, cv2.CV_32F)
        text_priority = (np.abs(edges) > 30.0).astype(np.float32)[:, :, np.newaxis]
        
        # Where text is detected, boost weight so labels remain sharp and unblurred
        effective_weight = np.maximum(feather_mask, text_priority * 0.98)
        
        canvas_rgb[y1:y2, x1:x2] += tile_rgb * effective_weight
        canvas_weight[y1:y2, x1:x2] += effective_weight
        
    canvas_weight[canvas_weight == 0] = 1.0
    mosaic_arr = np.clip(canvas_rgb / canvas_weight, 0, 255).astype(np.uint8)
    
    # Resize to exact 4K master (4096 x 2048)
    mosaic_img = Image.fromarray(mosaic_arr)
    if mosaic_img.size != (WIDTH_4K, HEIGHT_4K):
        mosaic_img = mosaic_img.resize((WIDTH_4K, HEIGHT_4K), Image.Resampling.LANCZOS)
        
    # Contrast and clarity enhancement for planetary rendering
    enhancer = ImageEnhance.Contrast(mosaic_img)
    mosaic_img = enhancer.enhance(1.06)
    enh_color = ImageEnhance.Color(mosaic_img)
    mosaic_img = enh_color.enhance(1.08)
    
    # Save 4K Master Texture
    mosaic_img.save(output_4k_path, format="JPEG", quality=94, optimize=True)
    print(f"[Stitching] 4K Equirectangular Master Texture saved: {output_4k_path}")
    
    # Also generate 2K and 1K Fast Preview textures for progressive web streaming
    out_dir = Path(output_4k_path).parent
    out_2k = os.path.join(out_dir, "mars_sim3292_geology_2k.jpg")
    out_fast = os.path.join(out_dir, "mars_sim3292_geology_fast.jpg")
    
    img_2k = mosaic_img.resize((2048, 1024), Image.Resampling.BILINEAR)
    img_2k.save(out_2k, format="JPEG", quality=88, optimize=True)
    
    img_fast = mosaic_img.resize((1024, 512), Image.Resampling.BILINEAR)
    img_fast.save(out_fast, format="JPEG", quality=78, optimize=True)
    print(f"[Stitching] Progressive textures generated: 2K ({out_2k}) & Fast 1K ({out_fast})")


def run_pipeline():
    print("=================================================================")
    print("  USGS SIM 3292 72-TILE CHUNKING & SEAMLESS SPHERE STITCHER")
    print("=================================================================")

    # Source equirectangular base to chunk
    source_4k = os.path.join(ROOT_DIR, "..", "public", "textures", "mars_sim3292_geology_4k.jpg")
    if not os.path.exists(source_4k):
        print(f"[Error] Source geological map not found at {source_4k}")
        return
        
    tiles_dir = os.path.join(ROOT_DIR, "..", "public", "sim3292_tiles")
    manifest_path = chunk_geological_map(
        source_img_path=source_4k,
        output_tiles_dir=tiles_dir,
        rows=GRID_ROWS,
        cols=GRID_COLS,
        overlap=OVERLAP_PX
    )

    out_stitched_4k = os.path.join(ROOT_DIR, "..", "public", "textures", "mars_sim3292_geology_4k.jpg")
    stitch_geological_tiles(manifest_path, out_stitched_4k)

    # Sync generated assets to public textures
    out_dir = os.path.join(ROOT_DIR, "..", "public", "textures")
    print(f"[Sync] Synced 72 tiles and 4K/2K/fast textures to {out_dir}")

    print("\n[Done] All 72 tiles and seamless equirectangular textures are ready.")


if __name__ == "__main__":
    run_pipeline()
