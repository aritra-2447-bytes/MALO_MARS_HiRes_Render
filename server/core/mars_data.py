"""
Mars Geodetic Data Constants
Includes landmarks, historical rover missions, and EVA preset routes.
"""

import math


MARS_LANDMARKS = [
    {
        "id": "olympus_mons",
        "name": "Olympus Mons",
        "lat": 18.65,
        "lon": -133.80,
        "elevation_m": 21287,
        "category": "volcano",
        "description": "Largest shield volcano in Solar System (21.3 km high, 600 km wide)."
    },
    {
        "id": "valles_marineris",
        "name": "Valles Marineris (Melas Chasma)",
        "lat": -9.80,
        "lon": -76.50,
        "elevation_m": -8200,
        "category": "canyon",
        "description": "Tectonic chasma system spanning 4,000 km, plunging to depths of 8.2 km."
    },
    {
        "id": "jezero_crater",
        "name": "Jezero Crater (Octavia E. Butler Landing)",
        "lat": 18.4446,
        "lon": 77.4508,
        "elevation_m": -2570,
        "category": "landing_site",
        "station_name": "Octavia E. Butler Landing",
        "description": "Paleolake river delta. Touchdown site: Octavia E. Butler Landing (Mars 2020)."
    },
    {
        "id": "gale_crater",
        "name": "Gale Crater (Bradbury Landing)",
        "lat": -4.5895,
        "lon": 137.4417,
        "elevation_m": -4501,
        "category": "landing_site",
        "station_name": "Bradbury Landing",
        "description": "Bradbury Landing touchdown site in Aeolis Palus, Mount Sharp sedimentary sequence."
    },
    {
        "id": "planum_boreum",
        "name": "Planum Boreum (North Polar Cap)",
        "lat": 84.50,
        "lon": 0.00,
        "elevation_m": -2000,
        "category": "polar_cap",
        "description": "Perennial northern water ice dome carved by spiral chasmata."
    },
    {
        "id": "planum_australe",
        "name": "Planum Australe (South Polar Cap)",
        "lat": -85.00,
        "lon": 0.00,
        "elevation_m": 1500,
        "category": "polar_cap",
        "description": "Southern polar plateau capped by CO2 and underlying water ice sheets."
    },
    {
        "id": "hellas_planitia",
        "name": "Hellas Planitia Basin",
        "lat": -42.70,
        "lon": 70.00,
        "elevation_m": -7152,
        "category": "basin",
        "description": "Enormous impact basin 2,300 km across; lowest elevation on Mars."
    },
    {
        "id": "elysium_mons",
        "name": "Elysium Mons",
        "lat": 25.02,
        "lon": 147.21,
        "elevation_m": 12600,
        "category": "volcano",
        "description": "Volcanic peak rising 12.6 km above surrounding plains."
    },
    {
        "id": "meridiani_planum",
        "name": "Meridiani Planum (Challenger Memorial Station)",
        "lat": -1.9462,
        "lon": -5.5266,
        "elevation_m": -1390,
        "category": "landing_site",
        "station_name": "Challenger Memorial Station",
        "description": "Challenger Memorial Station at Eagle Crater; hematite-rich plain revealing past surface water."
    },
    {
        "id": "gusev_crater",
        "name": "Gusev Crater (Columbia Memorial Station)",
        "lat": -14.5684,
        "lon": 175.4726,
        "elevation_m": -1910,
        "category": "landing_site",
        "station_name": "Columbia Memorial Station",
        "description": "Columbia Memorial Station exploration site connected to ancient Ma'adim Vallis."
    }
]


# Real Historical NASA Rover Exploration Traverse Waypoints (Perseverance, Curiosity, Opportunity, Spirit)
HISTORICAL_ROVER_MISSIONS = [
    {
        "id": "m20_perseverance",
        "rover": "Perseverance (Mars 2020)",
        "landing_site": "Jezero Crater (Octavia E. Butler Landing)",
        "sol_range": "Sol 0 – Sol 1,120+",
        "total_odometry_km": 28.4,
        "hazard_strategy": "AutoNav visual odometry with slope-limiting scarp traversal and sample tube caching.",
        "waypoints": [
            {"lat": 18.4446, "lon": 77.4508, "sol": 0, "elev_m": -2570, "hazard": "SAFE", "label": "Sol 0: Octavia E. Butler Landing"},
            {"lat": 18.405, "lon": 77.545, "sol": 180, "elev_m": -2520, "hazard": "SAFE", "label": "Sol 180: Séítah Dunes Margin (Wheel slip caution)"},
            {"lat": 18.420, "lon": 77.510, "sol": 350, "elev_m": -2480, "hazard": "SAFE", "label": "Sol 350: Kodiak Delta Remnant Butte"},
            {"lat": 18.445, "lon": 77.450, "sol": 510, "elev_m": -2420, "hazard": "CAUTION_STEEP", "label": "Sol 510: Hawksbill Gap (Western Delta Scarp)"},
            {"lat": 18.470, "lon": 77.410, "sol": 740, "elev_m": -2380, "hazard": "SAFE", "label": "Sol 740: Neretva Vallis River Inlet Channel"},
            {"lat": 18.510, "sol": 1050, "lon": 77.350, "elev_m": -2310, "hazard": "CAUTION_STEEP", "label": "Sol 1050: Belva Impact Crater Rim Ascent"}
        ]
    },
    {
        "id": "msl_curiosity",
        "rover": "Curiosity (MSL)",
        "landing_site": "Gale Crater (Bradbury Landing)",
        "sol_range": "Sol 0 – Sol 4,100+",
        "total_odometry_km": 32.8,
        "hazard_strategy": "Wheel puncture mitigation avoidance on wind-carved ventifacts; switchback climbs on Vera Rubin Ridge.",
        "waypoints": [
            {"lat": -4.5895, "lon": 137.4417, "sol": 0, "elev_m": -4501, "hazard": "SAFE", "label": "Sol 0: Bradbury Landing Point"},
            {"lat": -4.640, "lon": 137.400, "sol": 300, "elev_m": -4520, "hazard": "SAFE", "label": "Sol 300: Yellowknife Bay (Lacustrine Mudstone)"},
            {"lat": -4.665, "lon": 137.380, "sol": 750, "elev_m": -4460, "hazard": "CAUTION_STEEP", "label": "Sol 750: Bagnold Dunes Sand Crossing (Slip risk)"},
            {"lat": -4.690, "lon": 137.360, "sol": 1800, "elev_m": -4150, "hazard": "CAUTION_STEEP", "label": "Sol 1800: Vera Rubin Ridge Scarp (Hematite Unit)"},
            {"lat": -4.730, "lon": 137.330, "sol": 2700, "elev_m": -3900, "hazard": "SAFE", "label": "Sol 2700: Sulfate-Bearing Transition Valley"},
            {"lat": -4.780, "lon": 137.300, "sol": 3950, "elev_m": -3680, "hazard": "CRITICAL_SLOPE", "label": "Sol 3950: Gediz Vallis Debris Flow Ridge (Ascent ceiling)"}
        ]
    },
    {
        "id": "mer_opportunity",
        "rover": "Opportunity (MER-B)",
        "landing_site": "Meridiani Planum (Challenger Memorial Station)",
        "sol_range": "Sol 0 – Sol 5,111",
        "total_odometry_km": 45.16,
        "hazard_strategy": "Purgatory Dune extraction lessons; rim traversal avoidance of soft drift sands.",
        "waypoints": [
            {"lat": -1.9462, "lon": -5.5266, "sol": 0, "elev_m": -1390, "hazard": "SAFE", "label": "Sol 0: Challenger Memorial Station (Eagle Crater)"},
            {"lat": -1.950, "lon": -5.510, "sol": 100, "elev_m": -1390, "hazard": "SAFE", "label": "Sol 100: Fram Crater Outcrop"},
            {"lat": -1.960, "lon": -5.480, "sol": 450, "elev_m": -1380, "hazard": "CRITICAL_SLOPE", "label": "Sol 450: Purgatory Dune (High wheel entrapment)"},
            {"lat": -1.980, "lon": -5.440, "sol": 950, "elev_m": -1350, "hazard": "CAUTION_STEEP", "label": "Sol 950: Victoria Crater (Duck Bay Descent)"},
            {"lat": -2.280, "lon": -5.230, "sol": 2800, "elev_m": -1310, "hazard": "SAFE", "label": "Sol 2800: Endeavour Crater Rim (Cape York)"},
            {"lat": -2.330, "lon": -5.190, "sol": 5111, "elev_m": -1280, "hazard": "SAFE", "label": "Sol 5111: Perseverance Valley (Final Location)"}
        ]
    },
    {
        "id": "mer_spirit",
        "rover": "Spirit (MER-A)",
        "landing_site": "Gusev Crater (Columbia Memorial Station)",
        "sol_range": "Sol 0 – Sol 2,210",
        "total_odometry_km": 7.73,
        "hazard_strategy": "Right front wheel failure reverse driving; avoided basaltic boulder fields and soft Troy sand deposits.",
        "waypoints": [
            {"lat": -14.5684, "lon": 175.4726, "sol": 0, "elev_m": -1910, "hazard": "SAFE", "label": "Sol 0: Columbia Memorial Station"},
            {"lat": -14.580, "lon": 175.495, "sol": 85, "elev_m": -1920, "hazard": "SAFE", "label": "Sol 85: Bonneville Crater Rim"},
            {"lat": -14.610, "lon": 175.520, "sol": 300, "elev_m": -1880, "hazard": "CAUTION_STEEP", "label": "Sol 300: West Spur (Columbia Hills Base)"},
            {"lat": -14.630, "lon": 175.540, "sol": 580, "elev_m": -1810, "hazard": "CRITICAL_SLOPE", "label": "Sol 580: Husband Hill Summit (107m Climb)"},
            {"lat": -14.645, "lon": 175.550, "sol": 1300, "elev_m": -1850, "hazard": "SAFE", "label": "Sol 1300: Home Plate Hydrothermal Plateau"},
            {"lat": -14.655, "lon": 175.560, "sol": 2210, "elev_m": -1865, "hazard": "CRITICAL_SLOPE", "label": "Sol 2210: Troy Silica Sands (Entrapment Site)"}
        ]
    }
]


def interpolate_mola_elevation(lat, lon):
    """
    Inverse-Distance Weighting (IDW) interpolation using IAU Geodetic Datum &
    MOLA Laser Altimetry baseline aeroid points.
    """
    weights = []
    elevs = []
    for lm in MARS_LANDMARKS:
        d = math.hypot(lat - lm["lat"], lon - lm["lon"])
        if d < 0.0001:
            return float(lm["elevation_m"])
        w = 1.0 / (d ** 2.2)
        weights.append(w)
        elevs.append(float(lm["elevation_m"]))
    total_w = sum(weights)
    return round(sum(w * e for w, e in zip(weights, elevs)) / total_w, 1)


# Preset astronaut EVA expedition routes for human explorers
EVA_PRESET_ROUTES = [
    {
        "id": "jezero_delta_traverse",
        "name": "Jezero Western Delta & Belva Crater Traverse",
        "description": "Perseverance delta scarp ascent to ancient clay deposits and sample caches.",
        "waypoints": [
            {"lat": 18.4446, "lon": 77.4508, "label": "Octavia E. Butler Landing Site"},
            {"lat": 18.420, "lon": 77.510, "label": "Kodiak Delta Remnant Butte"},
            {"lat": 18.445, "lon": 77.450, "label": "Western Fan Delta Scarp"},
            {"lat": 18.470, "lon": 77.410, "label": "Neretva Vallis River Inlet Channel"},
            {"lat": 18.510, "lon": 77.350, "label": "Belva Crater Rim Observation Point"}
        ]
    },
    {
        "id": "mount_sharp_ascent",
        "name": "Gale Crater: Mount Sharp (Aeolis Mons) Expedition",
        "description": "Curiosity ascent corridor through Vera Rubin Ridge to sulfate-bearing units.",
        "waypoints": [
            {"lat": -4.5895, "lon": 137.4417, "label": "Bradbury Landing Point"},
            {"lat": -4.640, "lon": 137.400, "label": "Yellowknife Bay Mudstone"},
            {"lat": -4.690, "lon": 137.360, "label": "Vera Rubin Ridge (Hematite)"},
            {"lat": -4.730, "lon": 137.330, "label": "Sulfate-Bearing Canyon Entry"},
            {"lat": -4.780, "lon": 137.300, "label": "Gediz Vallis Debris Ridge"}
        ]
    },
    {
        "id": "valles_marineris_rim_descent",
        "name": "Valles Marineris: Melas Chasma Rim to Floor EVA",
        "description": "Deep canyon descent investigating layered sulfate deposits and recurring slope lineae.",
        "waypoints": [
            {"lat": -9.200, "lon": -76.800, "label": "North Plateau Habitat Site"},
            {"lat": -9.500, "lon": -76.650, "label": "Melas Chasma Upper Canyon Terraces"},
            {"lat": -9.800, "lon": -76.400, "label": "Melas Chasma Central Deep Basin (-8,200m)"}
        ]
    }
]