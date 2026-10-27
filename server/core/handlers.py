"""
API Route Handlers
Handles all /api/* endpoints for the Mars Unified Server.
Provides ARES-OS science layer, historical atlas, mission control, and NASA PDS proxy endpoints.
"""

import json
import os
import urllib.parse
import datetime

from .mars_data import MARS_LANDMARKS, HISTORICAL_ROVER_MISSIONS
from .ephemeris import calculate_mars_ephemeris
from .eva_engine import plan_eva_route, get_eva_presets
from .nasa_proxy import (
    handle_ode_proxy, handle_browse_proxy, handle_mola_proxy,
    handle_sim3292_data, handle_sim3292_tiles_manifest
)
from .tile_server import get_project_dirs

try:
    from ares import catalog as ares_catalog
    from ares import mars_time as ares_time
    from ares import dem as ares_dem
    from ares import scouting as ares_scouting
    from ares import ode as ares_ode
    from ares import gds_jobs as ares_gds
    ARES_AVAILABLE = True
except Exception:
    ARES_AVAILABLE = False
    ares_catalog = None
    ares_time = None
    ares_dem = None
    ares_scouting = None
    ares_ode = None
    ares_gds = None


class APIHandler:
    """Handles all API route requests."""

    def __init__(self, current_file_dir):
        self.dirs = get_project_dirs(current_file_dir)

    def handle_landmarks(self):
        """GET /api/landmarks - Returns IAU Martian landmarks enriched with biographies & gazetteer data."""
        if not ARES_AVAILABLE:
            return {"status": "success", "landmarks": MARS_LANDMARKS}
        try:
            merged = []
            seen = set()
            for lm in MARS_LANDMARKS:
                item = dict(lm)
                item["lon_east"] = round(item["lon"] % 360.0, 4)
                item.setdefault("significance", item.get("description", ""))
                item["source"] = "NASA Mars Trek / IAU"
                merged.append(item)
                seen.add(item["id"])
                seen.add(item["name"].lower())
            figures = ares_catalog.FIGURES
            for lm in ares_catalog.landmark_payload():
                if lm["id"] in seen or lm["name"].lower() in seen:
                    continue
                item = {
                    "id": lm["id"],
                    "name": lm["name"],
                    "lat": lm["lat"],
                    "lon": lm["lon"],
                    "lon_east": lm["lon_east"],
                    "elevation_m": lm.get("elevation_m", 0),
                    "category": lm.get("category", "landmark"),
                    "description": lm.get("significance", ""),
                    "significance": lm.get("significance", ""),
                    "namesake": lm.get("namesake") or figures.get(lm.get("figure")),
                    "diameter_km": lm.get("diameter_km"),
                    "source": "IAU Gazetteer / NASA PDS",
                }
                merged.append(item)
                seen.add(item["id"])
                seen.add(item["name"].lower())
            return {
                "status": "success",
                "count": len(merged),
                "landmarks": merged,
                "source": "NASA Mars Trek, IAU Gazetteer, NASA PDS ODE",
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc), "status_code": 500}

    def handle_atlas_missions(self):
        """GET /api/atlas/missions & /api/rover/registry - Historical mission atlas & biographies."""
        if not ARES_AVAILABLE:
            return {"status": "error", "message": "ares package unavailable", "status_code": 500}
        try:
            return {
                "status": "success",
                "count": len(ares_catalog.HISTORICAL_MISSIONS),
                "missions": ares_catalog.mission_payload(),
                "figures": ares_catalog.FIGURES,
                "source": "NASA PDS / IAU Gazetteer / mission archives",
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc), "status_code": 500}

    def handle_atlas_landmarks(self):
        """GET /api/atlas/landmarks - 48 IAU landmarks with biographies and geology notes."""
        if not ARES_AVAILABLE:
            return {"status": "error", "message": "ares package unavailable", "status_code": 500}
        try:
            return {
                "status": "success",
                "count": len(ares_catalog.LANDMARKS),
                "landmarks": ares_catalog.landmark_payload(),
                "source": "IAU Gazetteer / NASA PDS ODE feature catalogue",
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc), "status_code": 500}

    def handle_atlas_figures(self):
        """GET /api/atlas/figures - Historical figures dictionary."""
        if not ARES_AVAILABLE:
            return {"status": "error", "message": "ares package unavailable", "status_code": 500}
        try:
            return {"status": "success", "figures": ares_catalog.FIGURES}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "status_code": 500}

    def handle_minerals(self, query):
        """GET /api/minerals - Aqueous mineral distribution & live ODE spectral queries."""
        if not ARES_AVAILABLE:
            return {"status": "error", "message": "ares package unavailable", "status_code": 500}
        try:
            payload = ares_catalog.mineral_payload()
            lat = query.get("lat", [None])[0]
            lon = query.get("lon", [None])[0]
            instrument = (query.get("instrument", ["CRISM"])[0] or "CRISM").upper()
            radius = float(query.get("radius", [0.6])[0])
            if lat is not None and lon is not None:
                ode = ares_ode.products(
                    float(lat), float(lon), radius=radius, instrument=instrument,
                    product_type=query.get("pt", [None])[0], limit=int(query.get("limit", [12])[0])
                )
                payload["ode_query"] = ode
                payload["query_center"] = {"lat": float(lat), "lon": float(lon)}
            payload["status"] = "success"
            return payload
        except Exception as exc:
            return {"status": "error", "message": str(exc), "status_code": 500}

    def handle_slope(self, query):
        """GET /api/terrain/slope - DEM windowing & >30 degree slope-hazard classification."""
        if not ARES_AVAILABLE:
            return {"status": "error", "message": "ares package unavailable", "status_code": 500}
        try:
            lat = float(query.get("lat", [18.4446])[0])
            lon = float(query.get("lon", [77.4508])[0])
            size_deg = float(query.get("size", [0.06])[0])
            resolution = float(query.get("resolution", [20.0])[0])
            prefer = (query.get("prefer", ["ctx"])[0] or "ctx").lower()
            n = query.get("n", [None])[0]
            n = int(n) if n is not None else None
            result = ares_dem.slope_grid(lat, lon, size_deg=size_deg,
                                         resolution_m=resolution, prefer=prefer, n=n)
            return result
        except Exception as exc:
            return {"status": "error", "message": str(exc), "status_code": 500}

    def handle_stac(self, query):
        """GET /api/terrain/stac - USGS Astrogeology STAC item footprints."""
        if not ARES_AVAILABLE:
            return {"status": "error", "message": "ares package unavailable", "status_code": 500}
        try:
            lat = float(query.get("lat", [18.4446])[0])
            lon = float(query.get("lon", [77.4508])[0])
            size_deg = float(query.get("size", [0.2])[0])
            return ares_dem.stac_catalog(lat, lon, size_deg)
        except Exception as exc:
            return {"status": "error", "message": str(exc), "status_code": 500}

    def handle_scouting(self, query):
        """GET /api/scouting/plan - ETH ASL cooperative follower/scout informative path planning."""
        if not ARES_AVAILABLE:
            return {"status": "error", "message": "ares package unavailable", "status_code": 500}
        try:
            start = {
                "lat": float(query.get("start_lat", [18.4446])[0]),
                "lon": float(query.get("start_lon", [77.4508])[0]),
            }
            target = {
                "lat": float(query.get("target_lat", [18.51])[0]),
                "lon": float(query.get("target_lon", [77.35])[0]),
            }
            result = ares_scouting.plan(
                start, target,
                size_deg=float(query.get("size", [0])[0]) or None,
                resolution_m=float(query.get("resolution", [20.0])[0]),
                prefer=(query.get("prefer", ["ctx"])[0] or "ctx").lower(),
                max_iterations=int(query.get("max_iterations", [14])[0]),
                sensor_radius_m=float(query.get("sensor_radius", [260.0])[0]),
                start_known_radius_m=float(query.get("start_known_radius", [320.0])[0]),
            )
            return result
        except Exception as exc:
            return {"status": "error", "message": str(exc), "status_code": 500}

    def handle_scouting_post(self, body):
        """POST /api/scouting/plan - ETH ASL cooperative follower/scout informative path planning."""
        if not ARES_AVAILABLE:
            return {"status": "error", "message": "ares package unavailable", "status_code": 500}
        try:
            start = body.get("start") or {"lat": body.get("start_lat", 18.4446), "lon": body.get("start_lon", 77.4508)}
            target = body.get("target") or {"lat": body.get("target_lat", 18.51), "lon": body.get("target_lon", 77.35)}
            result = ares_scouting.plan(
                start, target,
                size_deg=body.get("size_deg"),
                resolution_m=float(body.get("resolution_m", 20.0)),
                prefer=body.get("prefer", "ctx"),
                max_iterations=int(body.get("max_iterations", 14)),
                sensor_radius_m=float(body.get("sensor_radius_m", 260.0)),
                start_known_radius_m=float(body.get("start_known_radius_m", 320.0)),
            )
            return result
        except Exception as exc:
            return {"status": "error", "message": str(exc), "status_code": 500}

    def handle_gds_jobs(self, query):
        """GET /api/nasa/gds/jobs - Async NASA PDS GDS job status / list."""
        if not ARES_AVAILABLE:
            return {"status": "error", "message": "ares package unavailable", "status_code": 500}
        try:
            action = (query.get("action", ["list"])[0] or "list").lower()
            if action == "submit":
                params = {k: v[0] for k, v in query.items() if k != "action"}
                job = ares_gds.MANAGER.submit(params)
                return {"status": "success", "job": job}
            elif action == "status":
                job_id = query.get("jobid", [""])[0]
                job = ares_gds.MANAGER.get(job_id)
                if not job:
                    return {"status": "error", "message": "Unknown job id", "status_code": 404}
                return {"status": "success", "job": job}
            elif action == "abort":
                job_id = query.get("jobid", [""])[0]
                job = ares_gds.MANAGER.abort(job_id)
                if not job:
                    return {"status": "error", "message": "Unknown job id", "status_code": 404}
                return {"status": "success", "job": job}
            else:
                return {"status": "success", "jobs": ares_gds.MANAGER.list()}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "status_code": 500}

    def handle_gds_jobs_post(self, body):
        """POST /api/nasa/gds/jobs - Async NASA PDS GDS job submission."""
        if not ARES_AVAILABLE:
            return {"status": "error", "message": "ares package unavailable", "status_code": 500}
        try:
            params = dict(body)
            params["action"] = "submit"
            job = ares_gds.MANAGER.submit(params)
            return {"status": "success", "job": job}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "status_code": 500}

    def handle_ode_features(self, query):
        """GET /api/nasa/features - NASA PDS ODE feature catalogue."""
        if not ARES_AVAILABLE:
            return {"status": "error", "message": "ares package unavailable", "status_code": 500}
        try:
            kind = (query.get("query", ["featureclasses"])[0] or "featureclasses").lower()
            if kind == "featureclasses":
                return ares_ode.feature_classes()
            elif kind == "featurenames":
                fc = query.get("featureclass", [None])[0]
                limit = int(query.get("limit", [500])[0])
                return ares_ode.feature_names(fc, limit)
            elif kind == "featuredata":
                name = query.get("featurename", [""])[0]
                return ares_ode.feature_data(name)
            else:
                return {"status": "error", "message": "Unsupported feature query", "status_code": 400}
        except Exception as exc:
            return {"status": "error", "message": str(exc), "status_code": 500}

    def handle_mars_time(self, query):
        """GET /api/mars/time - Mars local solar time at arbitrary longitude."""
        if not ARES_AVAILABLE:
            return {"status": "error", "message": "ares package unavailable", "status_code": 500}
        try:
            lon = float(query.get("lon", [0.0])[0])
            dt = None
            if query.get("utc"):
                dt = datetime.datetime.fromisoformat(query["utc"][0].replace("Z", "+00:00"))
            return ares_time.time_at_longitude(dt, lon)
        except Exception as exc:
            return {"status": "error", "message": str(exc), "status_code": 500}

    def handle_mars_ephemeris(self, query=None):
        """GET /api/mars/ephemeris - Allison & McEwen (2000) Mars24 ephemeris and rover clocks."""
        try:
            query = query or {}
            dt_utc = datetime.datetime.now(datetime.timezone.utc)
            if query.get("utc"):
                dt_utc = datetime.datetime.fromisoformat(query["utc"][0].replace("Z", "+00:00"))
            cursor_lon = None
            if query.get("lon"):
                cursor_lon = float(query["lon"][0])
            if ARES_AVAILABLE:
                return ares_time.ephemeris(dt_utc, cursor_lon=cursor_lon)
            else:
                return calculate_mars_ephemeris()
        except Exception as e:
            return {"status": "error", "message": str(e), "status_code": 500}

    def handle_eva_presets(self):
        """GET /api/eva/presets - Returns preset EVA routes."""
        return get_eva_presets()

    def handle_rover_missions(self):
        """GET /api/rover/missions - Returns historical rover traverse data."""
        missions = [dict(m) for m in HISTORICAL_ROVER_MISSIONS]
        try:
            rt_file = os.path.join(self.dirs["DATA_DIR"], "rover_traverses.json")
            if os.path.exists(rt_file):
                with open(rt_file, "r", encoding="utf-8") as f_rt:
                    rt_data = json.load(f_rt)
                for m in missions:
                    mid = m.get("id")
                    if mid in rt_data and "track" in rt_data[mid] and not m.get("actual_path"):
                        m["actual_path"] = rt_data[mid]["track"]
        except Exception:
            pass
        return {
            "status": "success",
            "count": len(missions),
            "missions": missions
        }

    def handle_rover_traverses(self, query):
        """GET /api/rover/traverses - Returns continuous high-density rover tracks."""
        rover_id = query.get("rover", [None])[0]
        json_path = os.path.join(self.dirs["DATA_DIR"], "rover_traverses.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if rover_id and rover_id in data:
                return {"status": "success", "mission": data[rover_id]}
            else:
                return {"status": "success", "missions": data}
        except Exception as e:
            return {"status": "error", "message": str(e), "status_code": 500}

    def handle_eva_plan(self, query):
        """GET /api/eva/plan - Plans EVA route with hazard and metabolic analysis."""
        waypoints_json = query.get("waypoints", [""])[0]
        return plan_eva_route(waypoints_json if waypoints_json else None)

    def handle_nasa_ode(self, query):
        """GET /api/nasa/ode - Proxies NASA PDS ODE REST API."""
        return handle_ode_proxy(query)

    def handle_nasa_browse(self, query):
        """GET /api/nasa/browse - Streams NASA PDS browse images."""
        return handle_browse_proxy(query)

    def handle_nasa_mola(self, query):
        """GET /api/nasa/mola-elevation - Proxies NASA GDS MOLA altimetry."""
        return handle_mola_proxy(query)

    def handle_sim3292_data(self):
        """GET /api/sim3292/data - Returns USGS SIM 3292 geological data."""
        return handle_sim3292_data(self.dirs["DATA_DIR"])

    def handle_sim3292_tiles_manifest(self):
        """GET /api/sim3292/tiles - Returns SIM 3292 tile manifest."""
        return handle_sim3292_tiles_manifest(self.dirs["SIM3292_TILES_DIR"])

    def route_request(self, path, query):
        """Route API request to appropriate handler."""
        if path == "/api/landmarks":
            return self.handle_landmarks()
        elif path == "/api/eva/presets":
            return self.handle_eva_presets()
        elif path == "/api/rover/missions":
            return self.handle_rover_missions()
        elif path == "/api/rover/traverses":
            return self.handle_rover_traverses(query)
        elif path in ("/api/atlas/missions", "/api/rover/registry"):
            return self.handle_atlas_missions()
        elif path == "/api/atlas/landmarks":
            return self.handle_atlas_landmarks()
        elif path == "/api/atlas/figures":
            return self.handle_atlas_figures()
        elif path == "/api/minerals":
            return self.handle_minerals(query)
        elif path == "/api/terrain/slope":
            return self.handle_slope(query)
        elif path == "/api/terrain/stac":
            return self.handle_stac(query)
        elif path == "/api/scouting/plan":
            return self.handle_scouting(query)
        elif path == "/api/nasa/gds/jobs":
            return self.handle_gds_jobs(query)
        elif path == "/api/nasa/features":
            return self.handle_ode_features(query)
        elif path == "/api/mars/time":
            return self.handle_mars_time(query)
        elif path == "/api/eva/plan":
            return self.handle_eva_plan(query)
        elif path == "/api/mars/ephemeris":
            return self.handle_mars_ephemeris(query)
        elif path == "/api/nasa/ode":
            return self.handle_nasa_ode(query)
        elif path == "/api/nasa/browse":
            return self.handle_nasa_browse(query)
        elif path == "/api/nasa/mola-elevation":
            return self.handle_nasa_mola(query)
        elif path in ("/api/sim3292/data", "/api/geology", "/api/sim3292"):
            return self.handle_sim3292_data()
        elif path in ("/api/sim3292/tiles", "/api/sim3292/manifest"):
            return self.handle_sim3292_tiles_manifest()
        return None
