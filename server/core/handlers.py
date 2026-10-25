"""
API Route Handlers
Handles all /api/* endpoints for the Mars Unified Server.
"""

import json
import os
import urllib.parse

from .mars_data import MARS_LANDMARKS, HISTORICAL_ROVER_MISSIONS
from .ephemeris import calculate_mars_ephemeris
from .eva_engine import plan_eva_route, get_eva_presets
from .nasa_proxy import (
    handle_ode_proxy, handle_browse_proxy, handle_mola_proxy,
    handle_sim3292_data, handle_sim3292_tiles_manifest
)
from .tile_server import get_project_dirs


class APIHandler:
    """Handles all API route requests."""

    def __init__(self, current_file_dir):
        self.dirs = get_project_dirs(current_file_dir)

    def handle_landmarks(self):
        """GET /api/landmarks - Returns IAU Martian landmarks."""
        return {"status": "success", "landmarks": MARS_LANDMARKS}

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

    def handle_ipp_presets(self):
        """GET /api/ipp/presets - Returns ARES-OS Scouting-IPP presets."""
        try:
            from ipp_engine import IPP_PRESETS
            return {"status": "success", "presets": list(IPP_PRESETS.values())}
        except Exception as e:
            return {"status": "error", "message": str(e), "status_code": 500}

    def handle_ipp_terrain_grid(self, query):
        """GET /api/ipp/terrain-grid - Returns IPP terrain elevation and hazard grids."""
        preset = query.get("preset", ["jezero"])[0]
        try:
            from ipp_engine import AresScoutPlanner
            planner = AresScoutPlanner(preset)
            return planner.get_terrain_payload()
        except Exception as e:
            return {"status": "error", "message": str(e), "status_code": 500}

    def handle_ipp_scout_plan(self, params):
        """GET/POST /api/ipp/scout-plan - Runs ARES-OS scout informative path planning."""
        preset = params.get("preset", ["jezero"])
        if isinstance(preset, list):
            preset = preset[0] if preset else "jezero"
        max_iter = params.get("max_iterations", [10])
        if isinstance(max_iter, list):
            max_iter = int(max_iter[0]) if max_iter else 10
        else:
            max_iter = int(max_iter)
        swath = params.get("swath_radius", [3.5])
        if isinstance(swath, list):
            swath = float(swath[0]) if swath else 3.5
        else:
            swath = float(swath)
        try:
            from ipp_engine import AresScoutPlanner
            planner = AresScoutPlanner(preset)
            return planner.run_scout_ipp(max_iterations=max_iter, swath_radius_cells=swath)
        except Exception as e:
            return {"status": "error", "message": str(e), "status_code": 500}

    def handle_eva_plan(self, query):
        """GET /api/eva/plan - Plans EVA route with hazard and metabolic analysis."""
        waypoints_json = query.get("waypoints", [""])[0]
        return plan_eva_route(waypoints_json if waypoints_json else None)

    def handle_mars_ephemeris(self):
        """GET /api/mars/ephemeris - Returns Mars solar ephemeris data."""
        return calculate_mars_ephemeris()

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
        elif path == "/api/ipp/presets":
            return self.handle_ipp_presets()
        elif path == "/api/ipp/terrain-grid":
            return self.handle_ipp_terrain_grid(query)
        elif path == "/api/ipp/scout-plan":
            return self.handle_ipp_scout_plan(query)
        elif path == "/api/eva/plan":
            return self.handle_eva_plan(query)
        elif path == "/api/mars/ephemeris":
            return self.handle_mars_ephemeris()
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