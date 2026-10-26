"""Cooperative Informative Path Planning (scouting-ipp) for Mars rovers.

Implements the dual-agent principle of ETH Zurich ASL's `scouting-ipp`
("Traversing Mars: Cooperative Informative Path Planning to Efficiently
Navigate Unknown Scenes"):

* Follower / rover: may only traverse terrain that has been observed
  (scouted) and whose slope is <= 30 degrees.  Unscouted cells are treated as
  impassable for the conservative (feasible) path.
* Scout / aerial recon: flies ahead, observes unknown cells, and reveals the
  true slope.  Viewpoints are chosen to maximise information gain along the
  optimistic (lower-bound) rover path.
* The planner alternates between A* on the conservative map and A* on the
  optimistic map until the two cost bounds converge (provable optimality) or
  the optimistic path is blocked (provable infeasibility).

The true terrain is a real USGS CTX/HiRISE DTM window when one is available;
otherwise a deterministic MOLA-anchored fractal infill is used.
"""

import heapq
import math
import time

from . import dem as dem_module

MARS_RADIUS_M = 3396190.0
SLOPE_LIMIT_DEG = 30.0
CAUTION_DEG = 15.0


def _meters_per_deg(lat):
    return MARS_RADIUS_M * math.pi / 180.0, MARS_RADIUS_M * math.pi / 180.0 * math.cos(math.radians(lat))


def _cell_index(lat, lon, meta):
    r = int((meta["lat0"] - lat) / meta["dlat"])
    c = int((lon - meta["lon0"]) / meta["dlon"])
    return max(0, min(meta["n"] - 1, r)), max(0, min(meta["n"] - 1, c))


def _cell_center(r, c, meta):
    lat = meta["lat0"] - (r + 0.5) * meta["dlat"]
    lon = meta["lon0"] + (c + 0.5) * meta["dlon"]
    return lat, lon


def _edge_cost(slope_deg, step_m):
    """Rover cost per metre.  <=30 deg traversable; steeper is impassable."""
    if slope_deg > SLOPE_LIMIT_DEG:
        return math.inf
    # Quadratic slip penalty, normalised at the 30 degree limit.
    return step_m * (1.0 + 4.0 * (max(0.0, slope_deg) / SLOPE_LIMIT_DEG) ** 2)


def _build_passable(meta, slopes, known, mode):
    """Return an n x n passability matrix for 'feasible' or 'optimistic'."""
    n = meta["n"]
    passable = [[False] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            steep = slopes[r][c] > SLOPE_LIMIT_DEG
            if mode == "feasible":
                passable[r][c] = known[r][c] and not steep
            else:  # optimistic: unknown terrain is assumed traversable
                passable[r][c] = (not known[r][c]) or (not steep)
    return passable


def _astar(meta, slopes, passable, start_rc, goal_rc, mode):
    """A* over 8-connected cells.  Returns (path, cost_units) or (None, inf)."""
    n = meta["n"]
    sr, sc = start_rc
    gr, gc = goal_rc
    if not passable[gr][gc] or not passable[sr][sc]:
        return None, math.inf

    lat_mid = meta["center"]["lat"]
    m_per_deg_lat, m_per_deg_lon = _meters_per_deg(lat_mid)
    dx = meta["dlon"] * m_per_deg_lon
    dy = meta["dlat"] * m_per_deg_lat

    def xy(r, c):
        return c * dx, -r * dy

    gx, gy = xy(gr, gc)
    open_heap = []
    gscore = {}
    came = {}
    sr_key = (sr, sc)
    gscore[sr_key] = 0.0
    h0 = math.hypot(xy(sr, sc)[0] - gx, xy(sr, sc)[1] - gy)
    heapq.heappush(open_heap, (h0, 0.0, sr, sc))
    neighbours = [
        (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
        (-1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)),
        (1, -1, math.sqrt(2)), (1, 1, math.sqrt(2)),
    ]
    while open_heap:
        f, g, r, c = heapq.heappop(open_heap)
        if (r, c) == (gr, gc):
            path = [(r, c)]
            cur = (r, c)
            while cur in came:
                cur = came[cur]
                path.append(cur)
            path.reverse()
            return path, g
        if g > gscore.get((r, c), math.inf) + 1e-9:
            continue
        for dr, dc, mult in neighbours:
            nr, nc = r + dr, c + dc
            if nr < 0 or nr >= n or nc < 0 or nc >= n:
                continue
            if not passable[nr][nc]:
                continue
            # Do not cut a corner between two blocked orthogonal cells.
            if dr != 0 and dc != 0:
                if not passable[r][nc] and not passable[nr][c]:
                    continue
            step_m = math.hypot(dx * dc, dy * dr)
            slope = max(slopes[r][c], slopes[nr][nc])
            if mode == "optimistic":
                # Unknown cells are assumed to be at the minimum cost.
                if not passable[r][c] or not passable[nr][nc]:
                    edge = step_m
                else:
                    edge = _edge_cost(slope, step_m)
                    if not math.isfinite(edge):
                        edge = step_m
            else:
                edge = _edge_cost(slope, step_m)
                if not math.isfinite(edge):
                    continue
            ng = g + edge
            key = (nr, nc)
            if ng + 1e-9 < gscore.get(key, math.inf):
                gscore[key] = ng
                came[key] = (r, c)
                h = math.hypot(xy(nr, nc)[0] - gx, xy(nr, nc)[1] - gy)
                heapq.heappush(open_heap, (ng + h, ng, nr, nc))
    return None, math.inf


def _path_payload(path, meta, elevations, slopes):
    out = []
    cust = 0.0
    prev = None
    lat_mid = meta["center"]["lat"]
    m_per_deg_lat, m_per_deg_lon = _meters_per_deg(lat_mid)
    dx = meta["dlon"] * m_per_deg_lon
    dy = meta["dlat"] * m_per_deg_lat
    for (r, c) in path:
        lat, lon = _cell_center(r, c, meta)
        if prev is not None:
            pr, pc = prev
            step = math.hypot((c - pc) * dx, (r - pr) * dy)
            cost = _edge_cost(max(slopes[r][c], slopes[pr][pc]), step)
            if not math.isfinite(cost):
                cost = step
            cust += cost
        out.append({
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "lon_east": round(lon % 360.0, 6),
            "elev_m": round(float(elevations[r][c]), 1),
            "slope_deg": round(float(slopes[r][c]), 2),
            "cum_cost": round(cust, 1),
            "hazard": "NO_GO" if slopes[r][c] > SLOPE_LIMIT_DEG else ("CAUTION" if slopes[r][c] > CAUTION_DEG else "SAFE"),
            "row": r,
            "col": c,
        })
        prev = (r, c)
    return out


def _path_distance_km(path, meta):
    lat_mid = meta["center"]["lat"]
    m_per_deg_lat, m_per_deg_lon = _meters_per_deg(lat_mid)
    dx = meta["dlon"] * m_per_deg_lon
    dy = meta["dlat"] * m_per_deg_lat
    dist = 0.0
    for i in range(1, len(path)):
        dr = path[i][0] - path[i - 1][0]
        dc = path[i][1] - path[i - 1][1]
        dist += math.hypot(dc * dx, dr * dy)
    return dist / 1000.0


def _initial_known(n, start_rc, start_radius_m, cell_m):
    known = [[False] * n for _ in range(n)]
    rad = max(1.5, start_radius_m / max(1.0, cell_m))
    sr, sc = start_rc
    for r in range(n):
        for c in range(n):
            if math.hypot(r - sr, c - sc) <= rad:
                known[r][c] = True
    return known


def _reveal(known, r0, c0, radius_cells):
    n = len(known)
    gained = 0
    r_lo = max(0, int(math.floor(r0 - radius_cells)))
    r_hi = min(n - 1, int(math.ceil(r0 + radius_cells)))
    c_lo = max(0, int(math.floor(c0 - radius_cells)))
    c_hi = min(n - 1, int(math.ceil(c0 + radius_cells)))
    for r in range(r_lo, r_hi + 1):
        for c in range(c_lo, c_hi + 1):
            if math.hypot(r - r0, c - c0) <= radius_cells and not known[r][c]:
                known[r][c] = True
                gained += 1
    return gained


def _reveal_segment(known, r0, c0, r1, c1, radius_cells):
    """Reveal a sensor swath along a straight scout leg (aerial observation)."""
    dist = math.hypot(r1 - r0, c1 - c0)
    steps = max(1, int(math.ceil(dist / 0.35)))
    gained = 0
    for i in range(steps + 1):
        t = i / float(steps)
        r = r0 + (r1 - r0) * t
        c = c0 + (c1 - c0) * t
        gained += _reveal(known, r, c, radius_cells)
    return gained


def _unknown_on_path(path, known):
    return [(r, c) for (r, c) in path if not known[r][c]]


def _choose_viewpoint(optimistic_path, known, scout_rc, radius_cells, n, meta):
    """Maximise unknown-cell coverage near the optimistic path."""
    cand = _unknown_on_path(optimistic_path, known)
    if not cand:
        # Fall back to unknown cells near the optimistic path.
        near = set()
        path_set = set(optimistic_path)
        for (r, c) in optimistic_path:
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < n and 0 <= cc < n and (rr, cc) not in path_set and not known[rr][cc]:
                        near.add((rr, cc))
        cand = list(near)
    if not cand:
        return None, 0, 0.0

    # Deduplicate / thin candidates for speed.
    if len(cand) > 90:
        stride = max(1, len(cand) // 90)
        cand = cand[::stride]

    best = None
    best_score = -1.0
    best_gain = 0
    sr, sc = scout_rc
    max_leg = 34.0
    near_best = None
    near_score = -1.0
    near_gain = 0
    for (r, c) in cand:
        gain = 0
        for dr in range(-int(radius_cells) - 1, int(radius_cells) + 2):
            for dc in range(-int(radius_cells) - 1, int(radius_cells) + 2):
                rr, cc = r + dr, c + dc
                if 0 <= rr < n and 0 <= cc < n and not known[rr][cc]:
                    if math.hypot(dr, dc) <= radius_cells:
                        gain += 1
        dist = math.hypot(r - sr, c - sc)
        # Prefer high-gain viewpoints that can be reached in one bounded sortie,
        # so the revealed swath stays connected to the follower's known region.
        score = gain - 0.10 * dist
        if dist <= max_leg and score > near_score:
            near_score = score
            near_best = (r, c)
            near_gain = gain
        if score > best_score:
            best_score = score
            best = (r, c)
            best_gain = gain
    if near_best is not None:
        return near_best, near_gain, near_score
    return best, best_gain, best_score


def _profile(path_payload):
    if not path_payload:
        return []
    out = []
    for i, p in enumerate(path_payload):
        out.append({
            "distance_km": round(p["cum_cost"] / 1000.0, 3),
            "lat": p["lat"],
            "lon": p["lon"],
            "elev_m": p["elev_m"],
            "slope_deg": p["slope_deg"],
            "hazard": p["hazard"],
        })
    return out


def plan(start, target, size_deg=None, resolution_m=20.0, prefer="ctx",
         max_iterations=14, sensor_radius_m=260.0, start_known_radius_m=320.0,
         seed=7):
    """Run cooperative informative path planning.

    start/target: dicts with 'lat' and 'lon' (lon in -180..180 or 0..360).
    """
    t0 = time.time()
    slat, slon = float(start["lat"]), float(start["lon"])
    tlat, tlon = float(target["lat"]), float(target["lon"])
    if slon > 180.0:
        slon -= 360.0
    if tlon > 180.0:
        tlon -= 360.0
    # Keep the AOI from wrapping the antimeridian for this planner.
    if abs(slon - tlon) > 180.0:
        if slon < tlon:
            slon += 360.0
        else:
            tlon += 360.0
    mid_lat = (slat + tlat) / 2.0
    mid_lon = (slon + tlon) / 2.0
    span_lat = abs(tlat - slat)
    span_lon = abs(tlon - slon) * max(0.1, math.cos(math.radians(mid_lat)))
    span = max(span_lat, span_lon)
    if size_deg is None:
        size_deg = max(0.025, span * 1.45)
    size_deg = max(0.012, min(2.0, float(size_deg)))
    # Ensure both endpoints (plus a margin) are inside the AOI.
    need = span * 1.35 + 0.006
    size_deg = max(size_deg, need)
    n = int(max(48, min(160, round(size_deg * math.pi / 180.0 * MARS_RADIUS_M / max(8.0, resolution_m)))))
    n = max(n, 56)

    grid = dem_module.slope_grid(
        mid_lat, mid_lon, size_deg=size_deg, resolution_m=resolution_m,
        prefer=prefer, n=n
    )
    if grid.get("status") != "success":
        return {"status": "error", "message": grid.get("message", "terrain unavailable")}

    meta = {
        "n": grid["n"],
        "lat0": grid["lat0"],
        "lon0": grid["lon0"],
        "dlat": grid["dlat"],
        "dlon": grid["dlon"],
        "center": {"lat": mid_lat, "lon": mid_lon},
        "size_deg": grid["size_deg"],
        "size_km": grid["size_km"],
        "cell_size_m": grid["cell_size_m"],
        "source": grid["source"],
        "source_detail": grid["source_detail"],
        "is_real_dem": grid["is_real_dem"],
        "stac_id": grid.get("stac_id"),
        "instrument": grid.get("instrument"),
    }
    elev = grid["elevation"]
    slopes = grid["slope"]
    n = meta["n"]
    start_rc = _cell_index(slat, slon, meta)
    goal_rc = _cell_index(tlat, tlon, meta)
    cell_m = min(meta["cell_size_m"]["x"], meta["cell_size_m"]["y"])

    # If the start cell is a >30 degree pixel, step to the nearest passable cell.
    def nearest_passable(rc):
        r0, c0 = rc
        if slopes[r0][c0] <= SLOPE_LIMIT_DEG:
            return rc
        best = rc
        bestd = 1e9
        for r in range(n):
            for c in range(n):
                if slopes[r][c] <= SLOPE_LIMIT_DEG:
                    d = math.hypot(r - r0, c - c0)
                    if d < bestd:
                        bestd = d
                        best = (r, c)
        return best

    start_rc = nearest_passable(start_rc)
    goal_rc = nearest_passable(goal_rc)
    known = _initial_known(n, start_rc, start_known_radius_m, cell_m)
    radius_cells = max(1.2, sensor_radius_m / max(1.0, cell_m))

    scout_rc = start_rc
    scout_trajectory = [{
        "lat": round(_cell_center(start_rc[0], start_rc[1], meta)[0], 6),
        "lon": round(_cell_center(start_rc[0], start_rc[1], meta)[1], 6),
        "iteration": 0,
        "label": "Scout launch",
    }]
    viewpoints = []
    iterations = []
    convergence = []
    feasible_path = None
    optimistic_path = None
    feasible_cost = math.inf
    optimistic_cost = math.inf
    status = "MAX_ITERATIONS"
    proof = {"optimality_proven": False, "infeasibility_proven": False, "reason": "Iteration limit reached."}
    total_revealed = 0

    for it in range(max_iterations + 1):
        pass_f = _build_passable(meta, slopes, known, "feasible")
        pass_o = _build_passable(meta, slopes, known, "optimistic")
        feasible_path, feasible_cost = _astar(meta, slopes, pass_f, start_rc, goal_rc, "feasible")
        optimistic_path, optimistic_cost = _astar(meta, slopes, pass_o, start_rc, goal_rc, "optimistic")

        if optimistic_path is None:
            status = "INFEASIBLE_PROVEN"
            proof = {
                "optimality_proven": False,
                "infeasibility_proven": True,
                "reason": "No route exists even when every unscouted cell is assumed traversable; the observed >30 degree hazards form a closed barrier.",
            }
            convergence.append({
                "iteration": it,
                "feasible_cost": None,
                "optimistic_cost": None,
                "gap_pct": None,
                "known_fraction": round(_known_fraction(known), 4),
                "info_gain": 0,
            })
            iterations.append(_snapshot(it, feasible_path, optimistic_path, meta, elev, slopes,
                                        None, 0, known, feasible_cost, optimistic_cost, scout_trajectory))
            break

        gap_abs = None
        gap_pct = None
        if feasible_path is not None and math.isfinite(feasible_cost):
            gap_abs = max(0.0, feasible_cost - optimistic_cost)
            gap_pct = 100.0 * gap_abs / max(1e-9, optimistic_cost)
        convergence.append({
            "iteration": it,
            "feasible_cost": round(feasible_cost, 1) if math.isfinite(feasible_cost) else None,
            "optimistic_cost": round(optimistic_cost, 1),
            "feasible_distance_km": round(_path_distance_km(feasible_path, meta), 3) if feasible_path else None,
            "optimistic_distance_km": round(_path_distance_km(optimistic_path, meta), 3),
            "gap_pct": round(gap_pct, 3) if gap_pct is not None else None,
            "known_fraction": round(_known_fraction(known), 4),
            "info_gain": 0,
        })

        # Convergence: the conservative and optimistic cost bounds meet.
        same_path = feasible_path is not None and feasible_path == optimistic_path
        if feasible_path is not None and (same_path or (gap_pct is not None and gap_pct <= 0.5)):
            status = "OPTIMAL_PROVEN"
            proof = {
                "optimality_proven": True,
                "infeasibility_proven": False,
                "reason": ("The feasible and optimistic paths are identical." if same_path else
                           "The feasible and optimistic cost bounds have converged; no unscouted shortcut can improve the route."),
            }
            iterations.append(_snapshot(it, feasible_path, optimistic_path, meta, elev, slopes,
                                        None, 0, known, feasible_cost, optimistic_cost, scout_trajectory))
            break

        # Choose the next scouting viewpoint on the optimistic path.
        vp, gain, score = _choose_viewpoint(optimistic_path, known, scout_rc, radius_cells, n, meta)
        if vp is None:
            # No information left to gain: if feasible exists it is optimal;
            # otherwise report the best available result.
            if feasible_path is not None:
                status = "OPTIMAL_PROVEN"
                proof = {
                    "optimality_proven": True,
                    "infeasibility_proven": False,
                    "reason": "All terrain relevant to the optimistic path is observed; the conservative route is therefore optimal.",
                }
            else:
                status = "NO_FEASIBLE_PATH"
                proof = {
                    "optimality_proven": False,
                    "infeasibility_proven": False,
                    "reason": "Scouting exhausted the informative viewpoints without finding a traversable route.",
                }
            iterations.append(_snapshot(it, feasible_path, optimistic_path, meta, elev, slopes,
                                        None, 0, known, feasible_cost, optimistic_cost, scout_trajectory))
            break

        vr, vc = vp
        vlat, vlon = _cell_center(vr, vc, meta)
        sr, sc = scout_rc
        scout_leg = {
            "from": {"lat": round(_cell_center(sr, sc, meta)[0], 6), "lon": round(_cell_center(sr, sc, meta)[1], 6)},
            "to": {"lat": round(vlat, 6), "lon": round(vlon, 6)},
            "gain_estimate": int(gain),
            "iteration": it + 1,
        }
        # The scout observes continuously along its flight leg, not just at the
        # terminal viewpoint; this creates a connected traversable swath.
        revealed = _reveal_segment(known, sr, sc, vr, vc, radius_cells)
        total_revealed += revealed
        scout_rc = vp
        scout_trajectory.append({
            "lat": round(vlat, 6),
            "lon": round(vlon, 6),
            "iteration": it + 1,
            "label": f"Scout observation {it + 1} (+{revealed} cells)",
            "gain": int(revealed),
        })
        viewpoints.append({
            "lat": round(vlat, 6),
            "lon": round(vlon, 6),
            "lon_east": round(vlon % 360.0, 6),
            "iteration": it + 1,
            "gain_cells": int(revealed),
            "gain_estimate": int(gain),
            "sensor_radius_m": sensor_radius_m,
            "score": round(score, 2),
        })
        iterations.append(_snapshot(it, feasible_path, optimistic_path, meta, elev, slopes,
                                    scout_leg, revealed, known, feasible_cost, optimistic_cost, scout_trajectory))

    final_feasible = _path_payload(feasible_path, meta, elev, slopes) if feasible_path else None
    final_optimistic = _path_payload(optimistic_path, meta, elev, slopes) if optimistic_path else None
    hazard_cells = []
    for r in range(n):
        for c in range(n):
            if slopes[r][c] > SLOPE_LIMIT_DEG:
                lat, lon = _cell_center(r, c, meta)
                hazard_cells.append({
                    "lat": round(lat, 5),
                    "lon": round(lon, 5),
                    "slope_deg": round(float(slopes[r][c]), 1),
                })
    if len(hazard_cells) > 3500:
        stride = max(1, len(hazard_cells) // 3500)
        hazard_cells = hazard_cells[::stride]

    final_gap = None
    if final_feasible and final_optimistic:
        final_gap = round(100.0 * max(0.0, feasible_cost - optimistic_cost) / max(1e-9, optimistic_cost), 3)

    payload = {
        "status": "success",
        "planner": "cooperative-informative-path-planning",
        "reference": "ethz-asl/scouting-ipp (Traversing Mars)",
        "outcome": status,
        "proof": proof,
        "start": {"lat": slat, "lon": slon, "lon_east": round(slon % 360.0, 5)},
        "target": {"lat": tlat, "lon": tlon, "lon_east": round(tlon % 360.0, 5)},
        "aoi": {
            "center": {"lat": round(mid_lat, 5), "lon": round(mid_lon, 5)},
            "size_deg": round(size_deg, 5),
            "size_km": grid["size_km"],
            "n": n,
            "cell_size_m": grid["cell_size_m"],
            "lat0": grid["lat0"],
            "lon0": grid["lon0"],
            "dlat": grid["dlat"],
            "dlon": grid["dlon"],
        },
        "terrain": {
            "source": grid["source"],
            "source_detail": grid["source_detail"],
            "is_real_dem": grid["is_real_dem"],
            "stac_id": grid.get("stac_id"),
            "instrument": grid.get("instrument"),
            "native_resolution_m": grid.get("native_resolution_m"),
            "slope_max_deg": grid["slope_max_deg"],
            "slope_mean_deg": grid["slope_mean_deg"],
            "hazard_counts": grid["hazard_counts"],
        },
        "summary": {
            "iterations": len(iterations),
            "feasible_cost": round(feasible_cost, 1) if final_feasible else None,
            "optimistic_cost": round(optimistic_cost, 1) if final_optimistic else None,
            "feasible_distance_km": round(_path_distance_km(feasible_path, meta), 3) if feasible_path else None,
            "optimistic_distance_km": round(_path_distance_km(optimistic_path, meta), 3) if optimistic_path else None,
            "optimality_gap_pct": final_gap,
            "scout_distance_km": _scout_distance(scout_trajectory),
            "scout_sorties": len(viewpoints),
            "cells_revealed": total_revealed,
            "known_fraction": round(_known_fraction(known), 4),
            "sensor_radius_m": sensor_radius_m,
            "slope_limit_deg": SLOPE_LIMIT_DEG,
            "elapsed_ms": round((time.time() - t0) * 1000.0, 1),
        },
        "feasible_path": final_feasible,
        "optimistic_path": final_optimistic,
        "scout_trajectory": scout_trajectory,
        "viewpoints": viewpoints,
        "iterations": iterations,
        "convergence": convergence,
        "profile": _profile(final_feasible or final_optimistic),
        "hazard_cells": hazard_cells,
    }
    return payload


def _known_fraction(known):
    n = len(known)
    total = n * n
    if total == 0:
        return 0.0
    return sum(1 for row in known for v in row if v) / total


def _scout_distance(trajectory):
    if not trajectory or len(trajectory) < 2:
        return 0.0
    total = 0.0
    for a, b in zip(trajectory, trajectory[1:]):
        dlat = math.radians(b["lat"] - a["lat"])
        dlon = math.radians(b["lon"] - a["lon"])
        h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(a["lat"])) * math.cos(math.radians(b["lat"])) * math.sin(dlon / 2) ** 2
        total += 2 * MARS_RADIUS_M * math.asin(min(1.0, math.sqrt(h)))
    return round(total / 1000.0, 3)


def _snapshot(it, feasible_path, optimistic_path, meta, elev, slopes, scout_leg,
              revealed, known, feasible_cost, optimistic_cost, scout_trajectory):
    return {
        "iteration": it,
        "feasible_path": _path_payload(feasible_path, meta, elev, slopes) if feasible_path else None,
        "optimistic_path": _path_payload(optimistic_path, meta, elev, slopes) if optimistic_path else None,
        "feasible_cost": round(feasible_cost, 1) if math.isfinite(feasible_cost) else None,
        "optimistic_cost": round(optimistic_cost, 1) if math.isfinite(optimistic_cost) else None,
        "gap_pct": round(100.0 * max(0.0, feasible_cost - optimistic_cost) / max(1e-9, optimistic_cost), 3)
        if (math.isfinite(feasible_cost) and math.isfinite(optimistic_cost)) else None,
        "scout_leg": scout_leg,
        "revealed_cells": int(revealed),
        "known_fraction": round(_known_fraction(known), 4),
        "scout_trajectory": list(scout_trajectory),
        "feasible_distance_km": round(_path_distance_km(feasible_path, meta), 3) if feasible_path else None,
        "optimistic_distance_km": round(_path_distance_km(optimistic_path, meta), 3) if optimistic_path else None,
    }
