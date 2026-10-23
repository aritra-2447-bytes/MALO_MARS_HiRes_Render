"""
Mars Solar Ephemeris - Allison & McEwen (2000) NASA Mars24 Formulation
Calculates Mars Sol Date (MSD), Coordinated Mars Time (MTC),
Areocentric Solar Longitude (Ls), Subsolar Coordinates, and Solar Irradiance.
"""

import math
import datetime


def calculate_mars_ephemeris():
    """
    Calculate Mars ephemeris using Allison & McEwen (2000) formulation.
    Returns a dictionary with all ephemeris data.
    """
    dt_utc = datetime.datetime.now(datetime.timezone.utc)

    # 1. Julian Date
    jd_ut = 2440587.5 + (dt_utc.timestamp() / 86400.0)
    jd_tt = jd_ut + (69.184 / 86400.0)
    d2000 = jd_tt - 2451545.0

    # 2. Mars Mean Anomaly M
    M = (19.3870 + 0.52402075 * d2000) % 360.0
    M_rad = math.radians(M)

    # 3. Angle of Fictitious Mean Sun
    alpha_fms = (270.3863 + 0.52403840 * d2000) % 360.0

    # 4. Planetary Perturbations & Equation of Center
    pbs = (
        (10.691 + 3.0e-7 * d2000) * math.sin(M_rad)
        + 0.623 * math.sin(2 * M_rad)
        + 0.050 * math.sin(3 * M_rad)
        + 0.005 * math.sin(4 * M_rad)
        + 0.0005 * math.sin(5 * M_rad)
    )

    # 5. Areocentric Solar Longitude Ls
    Ls = (alpha_fms + pbs) % 360.0

    # 6. Equation of Time
    eot_deg = (
        (2.861 / 360.0) * math.sin(2 * math.radians(Ls))
        - 0.071 * math.sin(4 * math.radians(Ls))
        + 0.002 * math.sin(6 * math.radians(Ls))
        - pbs
    )

    # 7. Mars Sol Date (MSD)
    msd = ((jd_tt - 2451549.5) / 1.027491252) + 44796.0 - 0.00096

    # 8. Coordinated Mars Time (MTC)
    mtc_hours = (24.0 * msd) % 24.0

    # Subsolar point (Mars obliquity = 25.19 deg)
    subsolar_lat = math.degrees(math.asin(math.sin(math.radians(25.19)) * math.sin(math.radians(Ls))))
    subsolar_lon = (12.0 - mtc_hours) * 15.0 - eot_deg
    while subsolar_lon > 180:
        subsolar_lon -= 360
    while subsolar_lon < -180:
        subsolar_lon += 360

    # Solar Distance (AU) and surface solar irradiance (W/m^2)
    r_sun_au = 1.5236 * (1.0 - 0.0934**2) / (1.0 + 0.0934 * math.cos(M_rad))
    solar_irradiance = round(1361.0 / (r_sun_au ** 2), 1)

    # Martian Season
    if Ls < 90:
        season = "Northern Spring / Southern Autumn"
    elif Ls < 180:
        season = "Northern Summer / Southern Winter"
    elif Ls < 270:
        season = "Northern Autumn / Southern Spring"
    else:
        season = "Northern Winter / Southern Summer"

    mtc_h = int(mtc_hours)
    mtc_m = int((mtc_hours * 60) % 60)
    mtc_s = int((mtc_hours * 3600) % 60)

    return {
        "status": "success",
        "earth_utc": dt_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "mars_sol_date": round(msd, 2),
        "sol_number": int(msd),
        "mtc_time": f"{mtc_h:02d}:{mtc_m:02d}:{mtc_s:02d}",
        "solar_longitude_Ls": round(Ls, 2),
        "season": season,
        "solar_irradiance_wm2": solar_irradiance,
        "subsolar_point": {
            "lat": round(subsolar_lat, 2),
            "lon": round(subsolar_lon, 2)
        }
    }