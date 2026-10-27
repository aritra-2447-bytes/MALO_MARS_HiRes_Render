"""
NASA PDS ODE & GDS REST API Proxies
Proxies NASA PDS ODE REST API (/live2) for products, browse images & footprints
Proxies NASA PDS GDS REST API (/livegds) for MOLA PEDR granular altimetry
In-Memory TTL Caching for rate limit mitigation.
"""

import json
import time
import urllib.request
import urllib.parse


CACHE = {}
CACHE_TTL = 3600  # 1 hour


def handle_ode_proxy(query):
    """Handle NASA ODE REST API proxy request."""
    try:
        center_lat = float(query.get("lat", [18.38])[0])
        center_lon = float(query.get("lon", [77.58])[0])
        radius = float(query.get("radius", [0.4])[0])
        instrument = query.get("instrument", ["CTX"])[0].upper()

        lon_360 = (center_lon + 360.0) % 360.0
        min_lat = max(-90.0, center_lat - radius)
        max_lat = min(90.0, center_lat + radius)
        west_lon = max(0.0, lon_360 - radius)
        east_lon = min(360.0, lon_360 + radius)

        if instrument == "HIRISE":
            ihid, iid, pt = "MRO", "HiRISE", "RDR"
        elif instrument == "CRISM":
            ihid, iid, pt = "MRO", "CRISM", "TRDR"
        else:
            ihid, iid, pt = "MRO", "CTX", "EDR"

        cache_key = f"ode_{ihid}_{iid}_{pt}_{min_lat:.2f}_{max_lat:.2f}_{west_lon:.2f}_{east_lon:.2f}"
        now = time.time()
        if cache_key in CACHE and (now - CACHE[cache_key][0]) < CACHE_TTL:
            return CACHE[cache_key][1]

        ode_url = (
            f"https://oderest.rsl.wustl.edu/live2/?target=mars&query=product&results=compf"
            f"&ihid={ihid}&iid={iid}&pt={pt}"
            f"&minlat={min_lat:.3f}&maxlat={max_lat:.3f}"
            f"&westernlon={west_lon:.3f}&easternlon={east_lon:.3f}"
            f"&limit=15&output=json"
        )

        req = urllib.request.Request(ode_url, headers={"User-Agent": "NASA-MarsExplorer/2.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            ode_data = json.loads(resp.read().decode("utf-8"))

        products = ode_data.get("ODEResults", {}).get("Products", {}).get("Product", [])
        if isinstance(products, dict):
            products = [products]
        elif isinstance(products, str):
            products = []

        results = []
        for p in products:
            geom = p.get("Footprint_geometry", "")
            pdsid = p.get("pdsid", "")
            results.append({
                "pdsid": pdsid,
                "instrument": iid,
                "host": ihid,
                "pt": pt,
                "geometry_wkt": geom,
                "browse_url": f"/api/nasa/browse?pdsid={pdsid}",
                "nasa_ode_url": f"https://ode.rsl.wustl.edu/mars/product/?pdsid={pdsid}"
            })

        response_payload = {
            "status": "success",
            "instrument": instrument,
            "center": {"lat": center_lat, "lon": center_lon},
            "bounds": {"minlat": min_lat, "maxlat": max_lat, "westlon": west_lon, "eastlon": east_lon},
            "count": len(results),
            "products": results
        }

        CACHE[cache_key] = (now, response_payload)
        return response_payload
    except Exception as e:
        return {"status": "error", "message": str(e)}


def handle_browse_proxy(query):
    """Handle NASA ODE browse image streaming."""
    pdsid = query.get("pdsid", [""])[0]
    if not pdsid:
        return {"status": "error", "message": "Missing pdsid", "status_code": 400}

    cache_key = f"browse_{pdsid}"
    now = time.time()
    if cache_key in CACHE:
        ts, raw_bytes, mime = CACHE[cache_key]
        return {"status": "success", "data": raw_bytes, "mime": mime, "cached": True}

    ode_browse_url = f"https://oderest.rsl.wustl.edu/live2/?target=mars&query=browse&pdsid={pdsid}"
    try:
        req = urllib.request.Request(ode_browse_url, headers={"User-Agent": "NASA-MarsExplorer/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "image/jpeg")
            raw_bytes = resp.read()

        CACHE[cache_key] = (now, raw_bytes, content_type)
        return {"status": "success", "data": raw_bytes, "mime": content_type, "cached": False}
    except Exception as e:
        return {"status": "error", "message": f"Failed streaming ODE browse image: {e}", "status_code": 502}


def handle_mola_proxy(query):
    """Handle NASA GDS MOLA elevation proxy request."""
    try:
        lat = float(query.get("lat", [18.38])[0])
        lon = float(query.get("lon", [77.58])[0])
        box = float(query.get("box", [0.15])[0])

        lon_360 = (lon + 360.0) % 360.0
        minlat = lat - box
        maxlat = lat + box
        westlon = lon_360 - box
        eastlon = lon_360 + box

        cache_key = f"mola_{minlat:.3f}_{maxlat:.3f}_{westlon:.3f}_{eastlon:.3f}"
        now = time.time()
        if cache_key in CACHE and (now - CACHE[cache_key][0]) < CACHE_TTL:
            return CACHE[cache_key][1]

        gds_url = (
            f"https://oderest.rsl.wustl.edu/livegds?query=molapedr&results=v&output=json"
            f"&minlat={minlat:.3f}&maxlat={maxlat:.3f}&westernlon={westlon:.3f}&easternlon={eastlon:.3f}"
        )

        req = urllib.request.Request(gds_url, headers={"User-Agent": "NASA-MarsExplorer/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        gds_results = data.get("GDSResults", {})
        files = gds_results.get("ResultFiles", {}).get("ResultFile", [])
        if isinstance(files, dict):
            files = [files]

        elevation_points = []
        if files and len(files) > 0:
            csv_url = files[0].get("URL")
            if csv_url:
                with urllib.request.urlopen(csv_url, timeout=10) as csv_resp:
                    lines = csv_resp.read().decode("utf-8", errors="ignore").splitlines()
                    for line in lines[1:]:
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 3:
                            try:
                                p_lon = float(parts[0])
                                p_lat = float(parts[1])
                                p_topo = float(parts[2])
                                lon_180 = p_lon if p_lon <= 180 else p_lon - 360.0
                                elevation_points.append({
                                    "lon": round(lon_180, 4),
                                    "lat": round(p_lat, 4),
                                    "elevation_m": round(p_topo, 1)
                                })
                            except ValueError:
                                continue

        response_payload = {
            "status": "success",
            "center": {"lat": lat, "lon": lon},
            "count": len(elevation_points),
            "points": elevation_points[:200]
        }

        CACHE[cache_key] = (now, response_payload)
        return response_payload
    except Exception as e:
        return {"status": "error", "message": str(e)}


def handle_sim3292_data(data_dir):
    """Handle USGS SIM 3292 data request."""
    import os
    candidates = [
        os.path.join(data_dir, "sim3292_full_analysis.json"),
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            except Exception as e:
                return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "SIM3292 dataset not found"}


def handle_sim3292_tiles_manifest(tiles_dir):
    """Handle USGS SIM 3292 tiles manifest request."""
    import os
    candidates = [
        os.path.join(tiles_dir, "manifest.json"),
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            except Exception as e:
                return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "SIM3292 tiles manifest not found"}