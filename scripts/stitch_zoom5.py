#!/usr/bin/env python3
"""
Stitch NASA Mars Trek Zoom 5 Grayscale Tiles into High-Resolution Texture Mosaics.
Grid: 64 columns x 32 rows = 2,048 tiles of 256x256 pixels.
Source: MALO_MARS_HiRes_Render/zoom_5/{row}_{col}.jpg
Outputs:
  - public/textures/mars_zoom5_grayscale_4k.jpg (4096 x 2048)
  - public/textures/mars_zoom5_grayscale_8k.jpg (8192 x 4096)
"""

import os
import sys
import time
from pathlib import Path
import numpy as np
from PIL import Image

def stitch_zoom5(src_dir: str, out_dir: str):
    ROWS = 32
    COLS = 64
    TILE_SIZE = 256
    full_w = COLS * TILE_SIZE
    full_h = ROWS * TILE_SIZE

    os.makedirs(out_dir, exist_ok=True)
    mosaic = np.zeros((full_h, full_w), dtype=np.uint8)

    t0 = time.time()
    loaded = 0
    missing = []

    for r in range(ROWS):
        for c in range(COLS):
            fname = f"{r}_{c}.jpg"
            fpath = os.path.join(src_dir, fname)
            if os.path.exists(fpath):
                try:
                    with Image.open(fpath) as img:
                        arr = np.array(img)
                        mosaic[r * TILE_SIZE:(r + 1) * TILE_SIZE, c * TILE_SIZE:(c + 1) * TILE_SIZE] = arr
                        loaded += 1
                except Exception:
                    missing.append((r, c))
            else:
                missing.append((r, c))

    print(f"[+] Loaded {loaded} tiles in {time.time() - t0:.2f}s. Missing: {len(missing)}")

    # Fill polar row 0 if missing
    if all(r == 0 for r, c in missing if r == 0):
        row1 = mosaic[TILE_SIZE:2 * TILE_SIZE, :]
        mosaic[0:TILE_SIZE, :] = row1

    # Fill sparse missing tiles with adjacent columns
    for r, c in missing:
        if r == 0:
            continue
        prev_c = (c - 1) % COLS
        next_c = (c + 1) % COLS
        prev_fpath = os.path.join(src_dir, f"{r}_{prev_c}.jpg")
        next_fpath = os.path.join(src_dir, f"{r}_{next_c}.jpg")
        if os.path.exists(prev_fpath):
            mosaic[r * TILE_SIZE:(r + 1) * TILE_SIZE, c * TILE_SIZE:(c + 1) * TILE_SIZE] = mosaic[r * TILE_SIZE:(r + 1) * TILE_SIZE, prev_c * TILE_SIZE:(prev_c + 1) * TILE_SIZE]
        elif os.path.exists(next_fpath):
            mosaic[r * TILE_SIZE:(r + 1) * TILE_SIZE, c * TILE_SIZE:(c + 1) * TILE_SIZE] = mosaic[r * TILE_SIZE:(r + 1) * TILE_SIZE, next_c * TILE_SIZE:(next_c + 1) * TILE_SIZE]

    # Save 4K composite
    out_4k = os.path.join(out_dir, "mars_zoom5_grayscale_4k.jpg")
    img_full = Image.fromarray(mosaic, mode="L")
    img_4k = img_full.resize((4096, 2048), Image.Resampling.LANCZOS)
    img_4k.save(out_4k, format="JPEG", quality=92)
    print(f"[+] 4K mosaic saved: {out_4k} ({os.path.getsize(out_4k):,} bytes)")

    # Save 8K composite
    out_8k = os.path.join(out_dir, "mars_zoom5_grayscale_8k.jpg")
    img_8k = img_full.resize((8192, 4096), Image.Resampling.LANCZOS)
    img_8k.save(out_8k, format="JPEG", quality=90)
    print(f"[+] 8K mosaic saved: {out_8k} ({os.path.getsize(out_8k):,} bytes)")

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    default_src = os.path.abspath(os.path.join(script_dir, "..", "zoom_5"))
    default_out = os.path.abspath(os.path.join(script_dir, "..", "public", "textures"))
    src = sys.argv[1] if len(sys.argv) > 1 else default_src
    out = sys.argv[2] if len(sys.argv) > 2 else default_out
    stitch_zoom5(src, out)
