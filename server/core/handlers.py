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
        return {
            "status": "success",
            "count": len(HISTORICAL_ROVER_MISSIONS),
            "missions": HISTORICAL_ROVER_MISSIONS
        }

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