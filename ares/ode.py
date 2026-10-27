"""Thin, defensive helpers for the NASA PDS ODE REST V2 API."""

import json
import math
import time
import urllib.parse
import urllib.request

ODE_BASE = "https://oderest.rsl.wustl.edu/live2/"
CACHE = {}
CACHE_TTL = 1800.0

INSTRUMENTS = {
    "CTX": {"host": "MRO", "iid": "CTX", "products": ["EDR", "RDR", "DTM"], "default": "EDR"},
    "HIRISE": {"host": "MRO", "iid": "HiRISE", "products": ["RDR", "EDR", "DTM", "COLOR"], "default": "RDR"},
    "CRISM": {"host": "MRO", "iid": "CRISM", "products": ["TRDR", "DDR", "MRDR", "EDR"], "default": "TRDR"},
    "OMEGA": {"host": "MEX", "iid": "OMEGA", "products": ["EDR", "DDR"], "default": "DDR"},
}


def _get_json(url, timeout=20):
    req = urllib.request.Request(url, headers={
        "User-Agent": "ARES-OS/1.0 (Mars Mission Control; NASA PDS ODE client)",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _wrap_lon(lon):
    x = float(lon)
    while x > 180.0:
        x -= 360.0
    while x < -180.0:
        x += 360.0
    return x


def products(lat, lon, radius=0.4, instrument="CTX", product_type=None, limit=15):
    lat = float(lat)
    lon = _wrap_lon(lon)
    radius = max(0.005, min(30.0, float(radius)))
    key = (round(lat, 3), round(lon, 3), round(radius, 3), instrument.upper(), product_type, limit)
    now = time.time()
    if key in CACHE and now - CACHE[key][0] < CACHE_TTL:
        return CACHE[key][1]

    inst = INSTRUMENTS.get(instrument.upper(), INSTRUMENTS["CTX"])
    pt = (product_type or inst["default"]).upper()
    if pt not in inst["products"]:
        pt = inst["default"]
    lon_360 = lon % 360.0
    minlat = max(-90.0, lat - radius)
    maxlat = min(90.0, lat + radius)
    west = (lon_360 - radius)
    east = (lon_360 + radius)
    # ODE expects 0..360; clamp / split at the seam by using a full-longitude
    # query only for polar or seam-crossing cases.
    if west < 0.0:
        west, east = 0.0, min(360.0, east)
    if east > 360.0:
        east = 360.0
    q = {
        "target": "mars",
        "query": "product",
        "results": "compf",
        "ihid": inst["host"],
        "iid": inst["iid"],
        "pt": pt,
        "minlat": f"{minlat:.3f}",
        "maxlat": f"{maxlat:.3f}",
        "westernlon": f"{west:.3f}",
        "easternlon": f"{east:.3f}",
        "limit": str(max(1, min(100, int(limit)))),
        "output": "json",
    }
    url = ODE_BASE + "?" + urllib.parse.urlencode(q)
    try:
        data = _get_json(url, timeout=18)
    except Exception as exc:
        return {"status": "error", "message": str(exc), "instrument": instrument.upper(), "products": []}
    ode = data.get("ODEResults", {})
    prods = ode.get("Products", {}).get("Product", [])
    if isinstance(prods, dict):
        prods = [prods]
    if not isinstance(prods, list):
        prods = []
    out = []
    for p in prods:
        pdsid = p.get("pdsid") or p.get("PDSID") or ""
        center_lat = p.get("Center_latitude") or p.get("center_latitude")
        center_lon = p.get("Center_longitude") or p.get("center_longitude")
        out.append({
            "pdsid": pdsid,
            "instrument": inst["iid"],
            "host": inst["host"],
            "pt": pt,
            "center_lat": _f(center_lat),
            "center_lon": _f(center_lon),
            "geometry_wkt": p.get("Footprint_geometry", ""),
            "solar_longitude": _f(p.get("Solar_longitude")),
            "phase_angle": _f(p.get("Phase_angle")),
            "emission_angle": _f(p.get("Emission_angle")),
            "incidence_angle": _f(p.get("Incidence_angle")),
            "comment": p.get("Comment", ""),
            "browse_url": f"/api/nasa/browse?pdsid={urllib.parse.quote(pdsid)}",
            "nasa_ode_url": f"https://ode.rsl.wustl.edu/mars/product/?pdsid={urllib.parse.quote(pdsid)}",
        })
    payload = {
        "status": "success",
        "instrument": instrument.upper(),
        "host": inst["host"],
        "product_type": pt,
        "center": {"lat": lat, "lon": lon},
        "bounds": {"minlat": minlat, "maxlat": maxlat, "westlon": west, "eastlon": east},
        "count": len(out),
        "products": out,
        "source": "NASA PDS ODE REST V2 (/live2)",
    }
    CACHE[key] = (now, payload)
    return payload


def _f(v):
    try:
        return float(v)
    except Exception:
        return None


def feature_classes():
    key = "featureclasses"
    now = time.time()
    if key in CACHE and now - CACHE[key][0] < 86400:
        return CACHE[key][1]
    url = ODE_BASE + "?" + urllib.parse.urlencode({"target": "mars", "query": "featureclasses", "output": "json"})
    try:
        data = _get_json(url)
        raw = data.get("ODEResults", {}).get("FeatureClasses", {}).get("FeatureClass", [])
        if isinstance(raw, str):
            raw = [raw]
        # De-duplicate while preserving order.
        seen = set()
        classes = []
        for c in raw:
            if c not in seen:
                seen.add(c)
                classes.append(c)
        payload = {"status": "success", "count": len(classes), "classes": classes}
    except Exception as exc:
        payload = {"status": "error", "message": str(exc), "classes": []}
    CACHE[key] = (now, payload)
    return payload


def feature_names(feature_class=None, limit=500):
    key = f"featurenames_{feature_class}_{limit}"
    now = time.time()
    if key in CACHE and now - CACHE[key][0] < 86400:
        return CACHE[key][1]
    q = {"target": "mars", "query": "featurenames", "output": "json"}
    if feature_class:
        q["featureclass"] = feature_class
    try:
        data = _get_json(ODE_BASE + "?" + urllib.parse.urlencode(q))
        raw = data.get("ODEResults", {}).get("FeatureNames", {}).get("FeatureName", [])
        if isinstance(raw, str):
            raw = [raw]
        payload = {"status": "success", "count": len(raw), "names": raw[:max(1, int(limit))]}
    except Exception as exc:
        payload = {"status": "error", "message": str(exc), "names": []}
    CACHE[key] = (now, payload)
    return payload


def feature_data(name):
    key = f"featuredata_{name}"
    now = time.time()
    if key in CACHE and now - CACHE[key][0] < 86400:
        return CACHE[key][1]
    url = ODE_BASE + "?" + urllib.parse.urlencode({
        "target": "mars", "query": "featuredata", "featurename": name, "output": "json"
    })
    try:
        data = _get_json(url)
        raw = data.get("ODEResults", {}).get("Features", {}).get("Feature", [])
        if isinstance(raw, dict):
            raw = [raw]
        feats = []
        for f in raw:
            try:
                minlat = float(f.get("MinLat"))
                maxlat = float(f.get("MaxLat"))
                west = float(f.get("WestLon"))
                east = float(f.get("EastLon"))
                feats.append({
                    "name": f.get("FeatureName", name),
                    "feature_class": f.get("FeatureClass"),
                    "min_lat": minlat,
                    "max_lat": maxlat,
                    "west_lon": west,
                    "east_lon": east,
                    "center_lat": (minlat + maxlat) / 2.0,
                    "center_lon": (west + east) / 2.0,
                })
            except Exception:
                continue
        payload = {"status": "success", "count": len(feats), "features": feats}
    except Exception as exc:
        payload = {"status": "error", "message": str(exc), "features": []}
    CACHE[key] = (now, payload)
    return payload
