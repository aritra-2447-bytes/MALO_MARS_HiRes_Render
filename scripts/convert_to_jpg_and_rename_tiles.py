#!/usr/bin/env python3
"""
Convert PNG tiles from WebCrawlerBot to RGB JPEG and rename them for staging.
Supports converting and staging zoom level tiles (e.g. from {z}/{r}/{c}.png to {z}_{r}_{c}.jpg).
"""

import os
import sys
from pathlib import Path
from PIL import Image

def convert_and_rename(src_base_dir: str, dst_staging_dir: str, target_zoom: int = 2):
    os.makedirs(dst_staging_dir, exist_ok=True)
    zoom_dir = os.path.join(src_base_dir, str(target_zoom))
    
    if not os.path.exists(zoom_dir):
        print(f"[Error] Zoom directory {zoom_dir} not found.")
        return 0
        
    converted = 0
    for r_entry in sorted(os.listdir(zoom_dir)):
        r_path = os.path.join(zoom_dir, r_entry)
        if not os.path.isdir(r_path):
            continue
        row = int(r_entry)
        for c_file in sorted(os.listdir(r_path)):
            if not c_file.endswith(".png"):
                continue
            col = int(c_file.split(".")[0])
            src_file = os.path.join(r_path, c_file)
            
            # Destination naming: e.g. 5_{row}_{col}.jpg or {target_zoom}_{row}_{col}.jpg
            dst_name = f"5_{row}_{col}.jpg"
            dst_file = os.path.join(dst_staging_dir, dst_name)
            
            with Image.open(src_file) as img:
                rgb_img = img.convert("RGB")
                rgb_img.save(dst_file, format="JPEG", quality=95)
                converted += 1
                
    print(f"[+] Converted and staged {converted} tiles into: {dst_staging_dir}")
    return converted

if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    default_src = os.path.abspath(os.path.join(current_dir, "..", "..", "WebCrawlerBot", "GeologyData", "Geological_Map_tiles", "SIM3292_Global_Geology"))
    default_dst = os.path.abspath(os.path.join(current_dir, "..", "staging_geology_tiles"))
    
    src = sys.argv[1] if len(sys.argv) > 1 else default_src
    dst = sys.argv[2] if len(sys.argv) > 2 else default_dst
    
    convert_and_rename(src, dst)
