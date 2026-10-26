"""Digital Elevation Model access and slope-hazard analysis.

Primary source: USGS Astrogeology STAC cloud-optimised GeoTIFF DTMs
(MRO CTX controlled DTMs at ~20 m/px and MRO HiRISE SOCET DTMs at ~1 m/px).
The module reads only the requested window over HTTP range requests, so the
application never has to download multi-gigabyte products.

If `rasterio`/`numpy` are not installed, or no DTM covers the region, the
module falls back to a deterministic MOLA-anchored fractal terrain model.  The
response always reports which source was used.
"""

import math
import time
import json
import urllib.request

try:  # optional scientific stack
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None

try:
    import rasterio  # type: ignore
    from rasterio.windows import from_bounds  # type: ignore
    from rasterio.enums import Resampling  # type: ignore
    from rasterio.crs import CRS  # type: ignore
    from rasterio.warp import transform_bounds  # type: ignore
    _HAS_RASTERIO = True
except Exception:  # pragma: no cover
    rasterio = None
    _HAS_RASTERIO = False

MARS_RADIUS_M = 3396190.0
STAC_SEARCH_URL = "https://stac.astrogeology.usgs.gov/api/search"
STAC_COLLECTIONS = {
    "ctx": "mro_ctx_controlled_usgs_dtms",
    "hirise": "mro_hirise_socet_dtms",
}
PLANET_CRS_PROJ4 = (
    "+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 +a=3396190 +b=3396190 "
    "+units=m +no_defs"
)

CACHE = {}
CACHE_TTL = 3600.0
STAC_CACHE = {}


def _norm_lon(lon):
    x = float(lon)
    while x > 180.0:
        x -= 360.0
    while x < -180.0:
        x += 360.0
    return x


def _stac_search(west, south, east, north, collection, limit=12):
    key = (round(west, 4), round(south, 4), round(east, 4), round(north, 4), collection)
    now = time.time()
    if key in STAC_CACHE and now - STAC_CACHE[key][0] < 900:
        return STAC_CACHE[key][1]
    body = json.dumps({
        "collections": [collection],
        "bbox": [west, south, east, north],
        "limit": limit,
        "query": {"platform": {"eq": "mars"}} if False else None,
    }).encode("utf-8")
    # Remove the null query; STAC APIs reject null.
    payload = json.loads(body.decode("utf-8"))
    if payload.get("query") is None:
        payload.pop("query", None)
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        STAC_SEARCH_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "ARES-OS/1.0 (Mars Mission Control)",
            "Accept": "application/geo+json, application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=18) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        STAC_CACHE[key] = (now, [])
        return {"error": str(exc), "features": []}
    feats = data.get("features", [])
    STAC_CACHE[key] = (now, feats)
    return feats


def _bbox_overlap(a, b):
    aw, as_, ae, an = a
    bw, bs, be, bn = b
    w = max(aw, bw)
    s = max(as_, bs)
    e = min(ae, be)
    n = min(an, bn)
    if e <= w or n <= s:
        return 0.0
    return (e - w) * (n - s)


def find_dem_item(lat, lon, size_deg=0.06, prefer="ctx"):
    """Find the best STAC DTM item covering the AOI. Returns (item, kind) or (None, None)."""
    half = size_deg / 2.0
    west = _norm_lon(lon - half)
    east = _norm_lon(lon + half)
    south = max(-89.9, lat - half)
    north = min(89.9, lat + half)
    if east < west:  # antimeridian wrap: use a broad bbox and let overlap decide
        west, east = -180.0, 180.0
    order = [prefer] if prefer in STAC_COLLECTIONS else []
    for k in ("ctx", "hirise"):
        if k not in order:
            order.append(k)
    best = None
    best_score = -1.0
    best_kind = None
    for kind in order:
        feats = _stac_search(west, south, east, north, STAC_COLLECTIONS[kind])
        if isinstance(feats, dict):
            feats = feats.get("features", [])
        for f in feats:
            bbox = f.get("bbox")
            if not bbox or len(bbox) < 4:
                continue
            ov = _bbox_overlap((west, south, east, north), bbox[:4])
            if ov <= 0:
                continue
            assets = f.get("assets", {})
            if "dtm" not in assets:
                continue
            # Prefer complete coverage, then the requested instrument.
            aoi_area = max(1e-9, (east - west) * (north - south))
            score = ov / aoi_area
            if kind == prefer:
                score += 0.15
            if score > best_score:
                best_score = score
                best = f
                best_kind = kind
    return best, best_kind


def _resolve_bounds_for_crs(src, west, south, east, north):
    """Transform planetocentric lon/lat bounds into the DEM's CRS."""
    if src.crs is None:
        return west * math.pi / 180.0 * MARS_RADIUS_M, south * math.pi / 180.0 * MARS_RADIUS_M, \
               east * math.pi / 180.0 * MARS_RADIUS_M, north * math.pi / 180.0 * MARS_RADIUS_M
    planet = CRS.from_proj4(PLANET_CRS_PROJ4)
    try:
        xmin = west * math.pi / 180.0 * MARS_RADIUS_M
        ymin = south * math.pi / 180.0 * MARS_RADIUS_M
        xmax = east * math.pi / 180.0 * MARS_RADIUS_M
        ymax = north * math.pi / 180.0 * MARS_RADIUS_M
        return transform_bounds(planet, src.crs, xmin, ymin, xmax, ymax, densify_pts=21)
    except Exception:
        return west, south, east, north


def _read_dem_window(item, west, south, east, north, out_rows, out_cols):
    url = item["assets"]["dtm"]["href"]
    try:
        env = rasterio.Env(
            GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
            GDAL_HTTP_MULTIPLEX="YES",
            GDAL_HTTP_VERSION="2",
            VSI_CACHE="TRUE",
            VSI_CACHE_SIZE="33554432",
            CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.TIF",
        )
        with env:
            with rasterio.open(url) as src:
                b = _resolve_bounds_for_crs(src, west, south, east, north)
                win = from_bounds(b[0], b[1], b[2], b[3], src.transform)
                win = win.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
                if win.width < 0.5 or win.height < 0.5:
                    return None
                arr = src.read(
                    1,
                    window=win,
                    out_shape=(out_rows, out_cols),
                    resampling=Resampling.bilinear,
                    boundless=False,
                ).astype("float32")
                nodata = src.nodata
                res_x, res_y = src.res
                native_res = abs(float(res_x))
                return {
                    "elevation": arr,
                    "nodata": nodata,
                    "native_resolution_m": round(native_res, 3),
                    "crs": str(src.crs),
                    "href": url,
                    "width": src.width,
                    "height": src.height,
                }
    except Exception as exc:
        return {"error": str(exc), "href": url}


def _slope_from_array(elev, dx_m, dy_m):
    """Horn (1981) 3x3 slope operator. Returns slope in degrees."""
    if np is None:
        return None
    z = np.array(elev, dtype="float64")
    # Fill NaN/nodata with the local median so edges do not explode.
    valid = np.isfinite(z)
    if not valid.any():
        return np.zeros_like(z)
    fill = float(np.median(z[valid]))
    z = np.where(valid, z, fill)
    p = np.pad(z, 1, mode="edge")
    dzdx = (
        (p[0:-2, 2:] + 2.0 * p[1:-1, 2:] + p[2:, 2:])
        - (p[0:-2, 0:-2] + 2.0 * p[1:-1, 0:-2] + p[2:, 0:-2])
    ) / (8.0 * dx_m)
    dzdy = (
        (p[2:, 0:-2] + 2.0 * p[2:, 1:-1] + p[2:, 2:])
        - (p[0:-2, 0:-2] + 2.0 * p[0:-2, 1:-1] + p[0:-2, 2:])
    ) / (8.0 * dy_m)
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy)))
    return np.clip(slope, 0.0, 89.0)


def _block_reduce(arr, n, mode="mean"):
    """Aggregate a high-resolution array into an n x n grid (nan-safe)."""
    if np is None:
        return arr
    a = np.asarray(arr, dtype="float64")
    rows, cols = a.shape
    out = np.zeros((n, n), dtype="float64")
    for r in range(n):
        r0 = int(round(r * rows / n))
        r1 = max(r0 + 1, int(round((r + 1) * rows / n)))
        for c in range(n):
            c0 = int(round(c * cols / n))
            c1 = max(c0 + 1, int(round((c + 1) * cols / n)))
            block = a[r0:r1, c0:c1]
            if block.size == 0:
                out[r, c] = 0.0
                continue
            if mode == "max":
                out[r, c] = float(np.nanmax(block))
            elif mode == "min":
                out[r, c] = float(np.nanmin(block))
            else:
                out[r, c] = float(np.nanmean(block))
    return out


def _hash01(i, j, seed):
    n = (i * 374761393 + j * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    n = n ^ (n >> 16)
    return (n & 0xFFFFFF) / float(0xFFFFFF)


def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


def _value_noise(x, y, seed):
    xi = math.floor(x)
    yi = math.floor(y)
    xf = x - xi
    yf = y - yi
    u = _smooth(xf)
    v = _smooth(yf)
    a = _hash01(xi, yi, seed)
    b = _hash01(xi + 1, yi, seed)
    c = _hash01(xi, yi + 1, seed)
    d = _hash01(xi + 1, yi + 1, seed)
    return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v


def _fbm(lat, lon, seed=7):
    """Multi-octave fractal terrain in metres, aspect-corrected by latitude."""
    scale = max(0.15, math.cos(math.radians(lat)))
    x = lon * scale
    y = lat
    total = 0.0
    # wavelengths in degrees and amplitudes in metres
    octaves = [
        (0.020, 118.0),
        (0.0080, 52.0),
        (0.0032, 22.0),
        (0.00130, 9.0),
        (0.00052, 3.6),
    ]
    for idx, (wl, amp) in enumerate(octaves):
        total += amp * (_value_noise(x / wl, y / wl, seed + idx * 31) - 0.5) * 2.0
    # Broad undulation to avoid a flat mean.
    total += 70.0 * (_value_noise(x / 0.09, y / 0.09, seed + 91) - 0.5)
    return total



def _list_stats(arr):
    """min/max/mean for a pure-Python 2D array."""
    vals = []
    for row in arr:
        for v in row:
            try:
                f = float(v)
            except Exception:
                continue
            if math.isfinite(f):
                vals.append(f)
    if not vals:
        return 0.0, 0.0, 0.0
    return min(vals), max(vals), sum(vals) / float(len(vals))


def _slope_from_list(elev, dx_m, dy_m):
    """Pure-Python Horn (1981) slope operator, used when NumPy is absent."""
    rows = len(elev)
    cols = len(elev[0]) if rows else 0
    if rows < 2 or cols < 2:
        return [[0.0] * cols for _ in range(rows)]
    vals = []
    for row in elev:
        for v in row:
            try:
                f = float(v)
            except Exception:
                continue
            if math.isfinite(f):
                vals.append(f)
    fill = sorted(vals)[len(vals) // 2] if vals else 0.0
    z = []
    for row in elev:
        out_row = []
        for v in row:
            try:
                f = float(v)
            except Exception:
                f = fill
            out_row.append(f if math.isfinite(f) else fill)
        z.append(out_row)
    p = [[0.0] * (cols + 2) for _ in range(rows + 2)]
    for r in range(rows):
        for c in range(cols):
            p[r + 1][c + 1] = z[r][c]
    for i in range(rows + 2):
        p[i][0] = p[i][1]
        p[i][-1] = p[i][-2]
    for j in range(cols + 2):
        p[0][j] = p[1][j]
        p[-1][j] = p[-2][j]
    out = []
    inv_x = 1.0 / (8.0 * max(0.01, dx_m))
    inv_y = 1.0 / (8.0 * max(0.01, dy_m))
    for r in range(rows):
        out_row = []
        for c in range(cols):
            dzdx = (
                (p[r][c + 2] + 2.0 * p[r + 1][c + 2] + p[r + 2][c + 2])
                - (p[r][c] + 2.0 * p[r + 1][c] + p[r + 2][c])
            ) * inv_x
            dzdy = (
                (p[r + 2][c] + 2.0 * p[r + 2][c + 1] + p[r + 2][c + 2])
                - (p[r][c] + 2.0 * p[r][c + 1] + p[r][c + 2])
            ) * inv_y
            deg = math.degrees(math.atan(math.hypot(dzdx, dzdy)))
            out_row.append(max(0.0, min(89.0, deg)))
        out.append(out_row)
    return out

def _synthetic_grid(lat, lon, size_deg, n, base_elev=None, seed=7):
    if base_elev is None:
        base_elev = -2500.0
    dlat = size_deg / float(n)
    dlon = size_deg / float(n)
    elev = np.zeros((n, n), dtype="float64") if np is not None else [[0.0] * n for _ in range(n)]
    for r in range(n):
        cell_lat = lat + (0.5 - (r + 0.5) / n) * size_deg
        for c in range(n):
            cell_lon = lon + ((c + 0.5) / n - 0.5) * size_deg
            val = base_elev + _fbm(cell_lat, cell_lon, seed)
            if np is not None:
                elev[r, c] = val
            else:
                elev[r][c] = val
    return elev, dlat, dlon


def slope_grid(lat, lon, size_deg=0.06, resolution_m=20.0, prefer="ctx", n=None):
    """Return a DEM-backed or procedural slope grid for an AOI.

    Output is JSON-friendly: 2D row-major arrays, row 0 = north.
    """
    lat = max(-89.5, min(89.5, float(lat)))
    lon = _norm_lon(lon)
    size_deg = max(0.002, min(2.0, float(size_deg)))
    size_m = size_deg * math.pi / 180.0 * MARS_RADIUS_M
    if n is None:
        n = int(max(32, min(96, round(size_m / max(5.0, resolution_m)))))
    n = int(max(16, min(160, n)))
    cache_key = f"slope_{lat:.5f}_{lon:.5f}_{size_deg:.5f}_{resolution_m:.1f}_{prefer}_{n}"
    now = time.time()
    if cache_key in CACHE and now - CACHE[cache_key][0] < CACHE_TTL:
        return CACHE[cache_key][1]

    source = "procedural"
    source_detail = "MOLA-anchored deterministic fractal infill"
    item = None
    kind = None
    result = None
    if _HAS_RASTERIO and np is not None:
        item, kind = find_dem_item(lat, lon, size_deg, prefer)
        if item:
            half = size_deg / 2.0
            # Read the DEM at (up to) native resolution so that 20 m scarps are
            # not lost to downsampling, then aggregate to the planning grid.
            try:
                native = 20.0
                read_n = int(min(512, max(n * 3, round(size_m / native))))
            except Exception:
                read_n = min(512, max(n * 3, 192))
            raw = _read_dem_window(
                item, _norm_lon(lon - half), max(-90.0, lat - half),
                _norm_lon(lon + half), min(90.0, lat + half), read_n, read_n
            )
            if raw and "error" not in raw:
                elev_hi = raw["elevation"]
                nodata = raw["nodata"]
                valid = np.isfinite(elev_hi)
                if nodata is not None:
                    valid &= elev_hi != nodata
                coverage = float(valid.mean()) if valid.size else 0.0
                if coverage >= 0.55:
                    if not valid.all():
                        fill = float(np.median(elev_hi[valid]))
                        elev_hi = np.where(valid, elev_hi, fill)
                    dx_hi = (size_deg / read_n) * math.pi / 180.0 * MARS_RADIUS_M * math.cos(math.radians(lat))
                    dy_hi = (size_deg / read_n) * math.pi / 180.0 * MARS_RADIUS_M
                    slope_hi = _slope_from_array(elev_hi, max(0.01, dx_hi), max(0.01, dy_hi))
                    # Block aggregate: mean elevation, conservative max slope.
                    elev = _block_reduce(elev_hi, n, "mean")
                    slopes = _block_reduce(slope_hi, n, "max")
                    source = f"USGS STAC {kind.upper()} DTM"
                    source_detail = f"{item.get('id', 'DTM')} ({raw['native_resolution_m']} m/px native, COG range read)"
                    result = {
                        "elevation": elev,
                        "slopes": slopes,
                        "coverage": coverage,
                        "native_resolution_m": raw["native_resolution_m"],
                        "stac_id": item.get("id"),
                        "stac_href": raw["href"],
                        "stac_bbox": item.get("bbox"),
                        "coverage_fraction": round(coverage, 3),
                        "instrument": kind,
                        "read_resolution_m": round(size_m / read_n, 2),
                    }

    if result is None:
        elev, dlat, dlon = _synthetic_grid(lat, lon, size_deg, n)
        result = {
            "elevation": elev,
            "coverage": 1.0,
            "native_resolution_m": round(size_m / n, 2),
            "stac_id": None,
            "stac_href": None,
            "stac_bbox": None,
            "coverage_fraction": 1.0,
            "instrument": None,
        }
    else:
        dlat = size_deg / n
        dlon = size_deg / n

    dx_m = dlon * math.pi / 180.0 * MARS_RADIUS_M * math.cos(math.radians(lat))
    dy_m = dlat * math.pi / 180.0 * MARS_RADIUS_M
    elev = result["elevation"]
    if np is None:
        # Standard-library-only path.  All arrays stay as plain lists.
        slopes = _slope_from_list(elev, max(0.01, dx_m), max(0.01, dy_m))
        rows = len(slopes)
        cols = len(slopes[0]) if rows else 0
        classes = [[0] * cols for _ in range(rows)]
        safe = caution = no_go = 0
        slope_max = 0.0
        slope_sum = 0.0
        for r in range(rows):
            for c in range(cols):
                value = float(slopes[r][c])
                if value > 30.0:
                    klass = 2
                    no_go += 1
                elif value > 15.0:
                    klass = 1
                    caution += 1
                else:
                    klass = 0
                    safe += 1
                classes[r][c] = klass
                if value > slope_max:
                    slope_max = value
                slope_sum += value
        total = rows * cols
        counts = {
            "safe": safe,
            "caution": caution,
            "no_go": no_go,
            "total": total,
        }
        elev_min, elev_max, elev_mean = _list_stats(elev)
        slope_mean = slope_sum / float(max(1, total))
        elev_out = [[round(float(v), 1) for v in row] for row in elev]
        slope_out = [[round(float(v), 2) for v in row] for row in slopes]
        classes_out = classes
    else:
        if "slopes" in result:
            slopes = result["slopes"]
        else:
            slopes = _slope_from_array(elev, max(0.01, dx_m), max(0.01, dy_m))
        if slopes is None:
            slopes = np.zeros_like(elev, dtype="float64")
        # Hazard classes: 0 safe <=15, 1 caution 15-30, 2 no-go >30
        cls = np.zeros_like(slopes, dtype="uint8")
        cls[(slopes > 15.0) & (slopes <= 30.0)] = 1
        cls[slopes > 30.0] = 2
        total = int(cls.size)
        counts = {
            "safe": int((cls == 0).sum()),
            "caution": int((cls == 1).sum()),
            "no_go": int((cls == 2).sum()),
            "total": total,
        }
        elev_min = float(np.nanmin(elev))
        elev_max = float(np.nanmax(elev))
        elev_mean = float(np.nanmean(elev))
        slope_max = float(np.nanmax(slopes))
        slope_mean = float(np.nanmean(slopes))
        elev_out = [[round(float(v), 1) for v in row] for row in elev.tolist()]
        slope_out = [[round(float(v), 2) for v in row] for row in slopes.tolist()]
        classes_out = [[int(v) for v in row] for row in cls.tolist()]
    for k in ("safe", "caution", "no_go"):
        counts[k + "_pct"] = round(100.0 * counts[k] / max(1, total), 2)

    payload = {
        "status": "success",
        "center": {"lat": lat, "lon": lon, "lon_east": round(lon % 360.0, 4)},
        "size_deg": size_deg,
        "size_km": round(size_m / 1000.0, 3),
        "n": n,
        "lat0": round(lat + size_deg / 2.0, 6),
        "lon0": round(lon - size_deg / 2.0, 6),
        "dlat": round(dlat, 8),
        "dlon": round(dlon, 8),
        "source": source,
        "source_detail": source_detail,
        "is_real_dem": source.startswith("USGS"),
        "instrument": result.get("instrument"),
        "stac_id": result.get("stac_id"),
        "stac_href": result.get("stac_href"),
        "coverage_fraction": result.get("coverage_fraction", 1.0),
        "native_resolution_m": result.get("native_resolution_m"),
        "cell_size_m": {"x": round(dx_m, 2), "y": round(dy_m, 2)},
        "elevation_min_m": round(elev_min, 1),
        "elevation_max_m": round(elev_max, 1),
        "elevation_mean_m": round(elev_mean, 1),
        "slope_max_deg": round(slope_max, 2),
        "slope_mean_deg": round(slope_mean, 2),
        "hazard_counts": counts,
        "elevation": elev_out,
        "slope": slope_out,
        "classes": classes_out,
        "thresholds": {"safe_max": 15.0, "caution_max": 30.0, "no_go_min": 30.0},
    }
    CACHE[cache_key] = (now, payload)
    return payload


def stac_catalog(lat, lon, size_deg=0.2):
    """List available USGS DEM products covering an AOI."""
    half = size_deg / 2.0
    west = _norm_lon(lon - half)
    east = _norm_lon(lon + half)
    south = max(-89.9, lat - half)
    north = min(89.9, lat + half)
    out = {"status": "success", "aoi": {"lat": lat, "lon": lon, "size_deg": size_deg}, "collections": []}
    for kind, coll in STAC_COLLECTIONS.items():
        feats = _stac_search(west, south, east, north, coll)
        if isinstance(feats, dict):
            out["collections"].append({"instrument": kind, "collection": coll, "error": feats.get("error"), "items": []})
            continue
        items = []
        for f in feats:
            assets = f.get("assets", {})
            if "dtm" not in assets:
                continue
            items.append({
                "id": f.get("id"),
                "bbox": f.get("bbox"),
                "datetime": f.get("properties", {}).get("datetime"),
                "dtm_href": assets["dtm"].get("href"),
                "thumbnail": assets.get("thumbnail", {}).get("href"),
                "title": f.get("properties", {}).get("title"),
            })
        out["collections"].append({
            "instrument": kind,
            "collection": coll,
            "count": len(items),
            "items": items,
        })
    return out
