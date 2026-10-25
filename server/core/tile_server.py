"""
Tile Server Path Translation
Handles path resolution for Level 5 tiles, SIM 3292 tiles, textures, and static assets.
"""

import os
import urllib.parse


def get_project_dirs(current_file_dir):
    """Get all project directory paths based on server location."""
    # current_file_dir is .../MALO_MARS_HiRes_Render/server
    # Project root is one level up from server/
    root_dir = os.path.abspath(os.path.join(current_file_dir, ".."))
    public_dir = os.path.join(root_dir, "public")
    data_dir = os.path.join(root_dir, "data")
    tiles_dir = os.path.join(root_dir, "tiles")
    sim3292_tiles_dir = os.path.join(public_dir, "sim3292_tiles")
    textures_dir = os.path.join(public_dir, "textures")
    lib_dir = os.path.join(public_dir, "lib")
    panos_dir = os.path.join(public_dir, "panos")
    web_app_2d_dir = os.path.join(root_dir, "web_app_2d")

    zoom5_dir = os.path.join(root_dir, "zoom_5")

    return {
        "ROOT_DIR": root_dir,
        "PUBLIC_DIR": public_dir,
        "DATA_DIR": data_dir,
        "TILES_DIR": tiles_dir,
        "ZOOM5_DIR": zoom5_dir,
        "SIM3292_TILES_DIR": sim3292_tiles_dir,
        "TEXTURES_DIR": textures_dir,
        "LIB_DIR": lib_dir,
        "PANOS_DIR": panos_dir,
        "WEB_APP_2D_DIR": web_app_2d_dir,
    }


def translate_path(path, dirs):
    """
    Translate request path to filesystem path.
    """
    parsed = urllib.parse.urlsplit(path).path
    clean_path = os.path.normpath(urllib.parse.unquote(parsed))

    public_dir = dirs["PUBLIC_DIR"]
    data_dir = dirs["DATA_DIR"]
    tiles_dir = dirs["TILES_DIR"]
    sim3292_tiles_dir = dirs["SIM3292_TILES_DIR"]
    textures_dir = dirs["TEXTURES_DIR"]
    lib_dir = dirs["LIB_DIR"]
    panos_dir = dirs["PANOS_DIR"]
    web_app_2d_dir = dirs["WEB_APP_2D_DIR"]
    zoom5_dir = dirs.get("ZOOM5_DIR", os.path.join(dirs["ROOT_DIR"], "zoom_5"))

    # Root -> index.html
    if clean_path in ("/", "\\"):
        return os.path.join(public_dir, "index.html")

    # Favicon
    if clean_path in ("/favicon.ico", "/favicon.svg", "\\favicon.ico", "\\favicon.svg"):
        return os.path.join(public_dir, "favicon.svg")

    # Static HTML pages in public/
    if clean_path in ("/index.html", "/index_2d_backup.html", "/geology_atlas.html",
                      "\\index.html", "\\index_2d_backup.html", "\\geology_atlas.html"):
        basename = os.path.basename(clean_path)
        return os.path.join(public_dir, basename)

    # Aliases for geology atlas
    if clean_path in ("/atlas", "/geology", "/usgs", "\\atlas", "\\geology", "\\usgs"):
        return os.path.join(public_dir, "geology_atlas.html")

    # Aliases for 2D WebGL viewer
    if clean_path in ("/2d", "/flat", "\\2d", "\\flat"):
        return os.path.join(public_dir, "index_2d_backup.html")

    # Aliases for Leaflet 2D viewer
    if clean_path in ("/leaflet", "/web_app_2d", "/web_app_2d/", "\\leaflet", "\\web_app_2d"):
        return os.path.join(web_app_2d_dir, "index.html")

    # Library files (Three.js, OrbitControls, Leaflet)
    if clean_path.startswith("/lib/") or clean_path.startswith("\\lib\\"):
        rel = clean_path[len("/lib/"):].lstrip("/\\")
        return os.path.join(lib_dir, rel)

    # Textures (LOD)
    if clean_path.startswith("/textures/") or clean_path.startswith("\\textures\\"):
        rel = clean_path[len("/textures/"):].lstrip("/\\")
        return os.path.join(textures_dir, rel)

    # Panoramas
    if clean_path.startswith("/panos/") or clean_path.startswith("\\panos\\"):
        rel = clean_path[len("/panos/"):].lstrip("/\\")
        return os.path.join(panos_dir, rel)

    # SIM 3292 tiles
    if clean_path.startswith("/sim3292_tiles/") or clean_path.startswith("\\sim3292_tiles\\"):
        rel = clean_path[len("/sim3292_tiles/"):].lstrip("/\\")
        return os.path.join(sim3292_tiles_dir, rel)

    # Level 5 tiles (5_row_col.jpg)
    if clean_path.startswith("/tiles/") or clean_path.startswith("\\tiles\\"):
        rel = clean_path[len("/tiles/"):].lstrip("/\\")
        return os.path.join(tiles_dir, rel)

    # Zoom 5 grayscale tiles (row_col.jpg)
    if clean_path.startswith("/zoom_5/") or clean_path.startswith("\\zoom_5\\"):
        rel = clean_path[len("/zoom_5/"):].lstrip("/\\")
        target = os.path.join(zoom5_dir, rel)
        if os.path.exists(target):
            return target
        return None

    # Direct tile filename access (5_0_0.jpg etc.)
    basename = os.path.basename(clean_path)
    if basename.startswith("5_") and basename.endswith(".jpg"):
        return os.path.join(tiles_dir, basename)

    # Texture files by name
    texture_files = (
        "mars_mola_base_2k.jpg", "mars_mola_4k.jpg", "mars_mola_8k.jpg",
        "mars_sim3292_geology_2k.jpg", "mars_sim3292_geology_4k.jpg",
        "mars_sim3292_geology_fast.jpg", "mars_mola_level5_mosaic.jpg",
        "mars_zoom5_grayscale_4k.jpg", "mars_zoom5_grayscale_8k.jpg"
    )
    if basename in texture_files:
        target = os.path.join(textures_dir, basename)
        if not os.path.exists(target) and basename == "mars_mola_level5_mosaic.jpg":
            return os.path.join(textures_dir, "mars_mola_8k.jpg")
        return target

    # Data files (GeoJSON, etc.)
    if clean_path.startswith("/data/") or clean_path.startswith("\\data\\"):
        rel = clean_path[len("/data/"):].lstrip("/\\")
        return os.path.join(data_dir, rel)

    # web_app_2d static files
    if clean_path.startswith("/web_app_2d/") or clean_path.startswith("\\web_app_2d\\"):
        rel = clean_path[len("/web_app_2d/"):].lstrip("/\\")
        target = os.path.join(web_app_2d_dir, rel)
        if os.path.isdir(target):
            index_target = os.path.join(target, "index.html")
            if os.path.exists(index_target):
                return index_target
        return target

    # Fallback to public directory
    candidate = os.path.join(public_dir, clean_path.lstrip("/\\"))
    if os.path.exists(candidate):
        if os.path.isdir(candidate):
            index_target = os.path.join(candidate, "index.html")
            if os.path.exists(index_target):
                return index_target
        return candidate

    return None