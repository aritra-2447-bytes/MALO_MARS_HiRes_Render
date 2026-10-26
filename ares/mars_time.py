"""Mars24 / Allison & McEwen (2000) timekeeping and solar ephemeris.

Implements Coordinated Mars Time (MTC), Mars Sol Date (MSD), areocentric
solar longitude (Ls), equation of time, subsolar coordinates, local mean and
true solar time, solar elevation, seasons, and mission-sol clocks.

Reference: Allison, M., & McEwen, M. (2000), "A post-Pathfinder evaluation of
areocentric solar coordinates with improved timing recipes for Mars seasonal/
diurnal climate studies", Planetary and Space Science 48, 215-235.
NASA Mars24 Technical Notes.
"""

import datetime
import math

RAD = math.pi / 180.0
DEG = 180.0 / math.pi
MARS_OBLIQUITY_DEG = 25.19
MARS_SOL_SECONDS = 88775.244
EARTH_SECONDS_PER_SOL = 88775.244

# Landing epochs (UTC) and east longitudes for mission clocks.
ROVER_EPOCHS = {
    "perseverance": {
        "name": "Perseverance",
        "mission": "Mars 2020",
        "landing_utc": datetime.datetime(2021, 2, 18, 20, 55, 0, tzinfo=datetime.timezone.utc),
        "lon_east": 77.4508,
        "lat": 18.4446,
        "site": "Jezero Crater",
    },
    "curiosity": {
        "name": "Curiosity",
        "mission": "Mars Science Laboratory",
        "landing_utc": datetime.datetime(2012, 8, 6, 5, 17, 0, tzinfo=datetime.timezone.utc),
        "lon_east": 137.4417,
        "lat": -4.5895,
        "site": "Gale Crater",
    },
    "insight": {
        "name": "InSight",
        "mission": "InSight",
        "landing_utc": datetime.datetime(2018, 11, 26, 19, 52, 0, tzinfo=datetime.timezone.utc),
        "lon_east": 135.623,
        "lat": 4.502,
        "site": "Elysium Planitia",
    },
    "zhurong": {
        "name": "Zhurong",
        "mission": "Tianwen-1",
        "landing_utc": datetime.datetime(2021, 5, 14, 23, 18, 0, tzinfo=datetime.timezone.utc),
        "lon_east": 109.9084,
        "lat": 25.0833,
        "site": "Utopia Planitia",
    },
}


def jd_ut(dt):
    return 2440587.5 + dt.timestamp() / 86400.0


def jd_tt(dt):
    return jd_ut(dt) + 69.184 / 86400.0


def _norm360(x):
    return x % 360.0


def _norm24(x):
    return x % 24.0


def msd(dt):
    """Mars Sol Date (MSD) from a UTC datetime."""
    jd = jd_tt(dt)
    return ((jd - 2451549.5) / 1.027491252) + 44796.0 - 0.00096


def mtc_hours(dt):
    return _norm24(24.0 * msd(dt))


def mars_solar_longitude(dt):
    """Areocentric solar longitude Ls in degrees (0-360)."""
    jd = jd_tt(dt)
    d = jd - 2451545.0
    M = _norm360(19.3870 + 0.52402075 * d)
    alpha_fms = _norm360(270.3863 + 0.52403840 * d)
    Mr = M * RAD
    # Equation of centre (principal orbital eccentricity terms)
    eoc = (
        10.691 * math.sin(Mr)
        + 0.623 * math.sin(2 * Mr)
        + 0.050 * math.sin(3 * Mr)
        + 0.005 * math.sin(4 * Mr)
        + 0.0005 * math.sin(5 * Mr)
    )
    # Small planetary perturbations (Mars24 table, leading terms)
    pbs = (
        0.014 * math.cos(d * 0.9856 * RAD)
        + 0.008 * math.cos(d * 1.9712 * RAD)
        + 0.004 * math.cos(d * 2.6291 * RAD)
    )
    return _norm360(alpha_fms + eoc + pbs)


def equation_of_time_deg(dt):
    """Mars equation of time in degrees (LTST - LMST, expressed as angle)."""
    Ls = mars_solar_longitude(dt)
    Lr = Ls * RAD
    jd = jd_tt(dt)
    d = jd - 2451545.0
    M = _norm360(19.3870 + 0.52402075 * d) * RAD
    eoc = (
        10.691 * math.sin(M)
        + 0.623 * math.sin(2 * M)
        + 0.050 * math.sin(3 * M)
        + 0.005 * math.sin(4 * M)
        + 0.0005 * math.sin(5 * M)
    )
    return (
        2.861 * math.sin(2 * Lr)
        - 0.071 * math.sin(4 * Lr)
        + 0.002 * math.sin(6 * Lr)
        - eoc
    )


def subsolar_point(dt):
    hs = mtc_hours(dt)
    Ls = mars_solar_longitude(dt)
    eot = equation_of_time_deg(dt)
    lat = math.asin(math.sin(MARS_OBLIQUITY_DEG * RAD) * math.sin(Ls * RAD)) * DEG
    lon = (12.0 - hs) * 15.0 - eot
    while lon > 180.0:
        lon -= 360.0
    while lon < -180.0:
        lon += 360.0
    return lat, lon


def lmst_hours(dt, lon_east):
    """Local Mean Solar Time in hours (0-24) at east longitude."""
    return _norm24(mtc_hours(dt) + lon_east / 15.0)


def ltst_hours(dt, lon_east):
    """Local True Solar Time in hours (0-24) at east longitude."""
    return _norm24(lmst_hours(dt, lon_east) + equation_of_time_deg(dt) / 15.0)


def solar_elevation_deg(dt, lat, lon_east):
    dec, _ = subsolar_point(dt)
    ha = (ltst_hours(dt, lon_east) - 12.0) * 15.0
    s = (
        math.sin(lat * RAD) * math.sin(dec * RAD)
        + math.cos(lat * RAD) * math.cos(dec * RAD) * math.cos(ha * RAD)
    )
    return math.asin(max(-1.0, min(1.0, s))) * DEG


def solar_azimuth_deg(dt, lat, lon_east):
    dec, _ = subsolar_point(dt)
    ha = (ltst_hours(dt, lon_east) - 12.0) * 15.0
    y = math.sin(ha * RAD)
    x = math.cos(ha * RAD) * math.sin(lat * RAD) - math.tan(dec * RAD) * math.cos(lat * RAD)
    return _norm360(math.atan2(y, x) * DEG + 180.0)


def season_from_ls(Ls):
    """Return northern and southern hemisphere seasons for Ls."""
    if Ls < 90:
        return "Northern Spring", "Southern Autumn"
    if Ls < 180:
        return "Northern Summer", "Southern Winter"
    if Ls < 270:
        return "Northern Autumn", "Southern Spring"
    return "Northern Winter", "Southern Summer"


def _fmt_hms(hours):
    h = int(hours) % 24
    m = int((hours * 60) % 60)
    s = int((hours * 3600) % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _fmt_hms_precise(hours):
    total = (hours % 24.0) * 3600.0
    h = int(total // 3600)
    m = int((total % 3600) // 60)
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"


def mission_clock(key, dt):
    cfg = ROVER_EPOCHS[key]
    landing_msd = msd(cfg["landing_utc"])
    now_msd = msd(dt)
    sol = max(0, int(math.floor(now_msd - landing_msd)))
    lon = cfg["lon_east"]
    lmst = lmst_hours(dt, lon)
    ltst = ltst_hours(dt, lon)
    elev = solar_elevation_deg(dt, cfg["lat"], lon)
    return {
        "id": key,
        "name": cfg["name"],
        "mission": cfg["mission"],
        "site": cfg["site"],
        "lat": cfg["lat"],
        "lon_east": round(lon, 4),
        "sol": sol,
        "landing_msd": round(landing_msd, 6),
        "sol_fraction": round(now_msd - landing_msd - sol, 6),
        "lmst": _fmt_hms(lmst),
        "ltst": _fmt_hms(ltst),
        "ltst_hours": round(ltst, 5),
        "solar_elevation_deg": round(elev, 2),
        "daylight": elev > 0.0,
        "phase": "DAY" if elev > 10 else ("TWILIGHT" if elev > 0 else "NIGHT"),
        "local_time_zone": f"MTC{('+' if lon >= 0 else '-')}{abs(lon) / 15.0:.2f}",
    }


def ephemeris(dt=None, cursor_lon=None):
    if dt is None:
        dt = datetime.datetime.now(datetime.timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    Ls = mars_solar_longitude(dt)
    nseason, sseason = season_from_ls(Ls)
    hs = mtc_hours(dt)
    sublat, sublon = subsolar_point(dt)
    eot = equation_of_time_deg(dt)
    r_sun_au = 1.5236 * (1.0 - 0.0934 ** 2) / (1.0 + 0.0934 * math.cos(
        _norm360(19.3870 + 0.52402075 * (jd_tt(dt) - 2451545.0)) * RAD
    ))
    payload = {
        "status": "success",
        "earth_utc": dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "earth_utc_iso": dt.isoformat().replace("+00:00", "Z"),
        "mars_sol_date": round(msd(dt), 5),
        "mars_sol_date_display": f"{msd(dt):,.3f}",
        "sol_number": int(msd(dt)),
        "mtc_time": _fmt_hms(hs),
        "mtc_time_precise": _fmt_hms_precise(hs),
        "mtc_hours": round(hs, 6),
        "solar_longitude_Ls": round(Ls, 3),
        "season": f"{nseason} / {sseason}",
        "northern_season": nseason,
        "southern_season": sseason,
        "equation_of_time_deg": round(eot, 4),
        "solar_irradiance_wm2": round(1361.0 / (r_sun_au ** 2), 1),
        "subsolar_point": {"lat": round(sublat, 3), "lon": round(sublon, 3)},
        "rover_clocks": {k: mission_clock(k, dt) for k in ("perseverance", "curiosity")},
        "all_mission_clocks": {k: mission_clock(k, dt) for k in ROVER_EPOCHS},
    }
    if cursor_lon is not None:
        lon = ((float(cursor_lon) + 180.0) % 360.0) - 180.0
        lst = ltst_hours(dt, lon)
        lmst = lmst_hours(dt, lon)
        payload["cursor"] = {
            "lon": round(lon, 3),
            "lmst": _fmt_hms(lmst),
            "ltst": _fmt_hms(lst),
            "ltst_hours": round(lst, 5),
            "solar_elevation_deg": round(
                solar_elevation_deg(dt, 0.0, lon), 2
            ),
        }
    return payload


def time_at_longitude(dt, lon):
    if dt is None:
        dt = datetime.datetime.now(datetime.timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    lon = ((float(lon) + 180.0) % 360.0) - 180.0
    lst = ltst_hours(dt, lon)
    lmst = lmst_hours(dt, lon)
    return {
        "status": "success",
        "earth_utc": dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "lon": round(lon, 3),
        "lon_east": round(lon % 360.0, 3),
        "mtc_time": _fmt_hms(mtc_hours(dt)),
        "lmst": _fmt_hms(lmst),
        "ltst": _fmt_hms(lst),
        "ltst_hours": round(lst, 5),
        "solar_elevation_deg": round(solar_elevation_deg(dt, 0.0, lon), 2),
    }
