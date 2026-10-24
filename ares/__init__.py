"""ARES-OS science services for the Mars Mission Control application.

The package is intentionally dependency-light.  Every module works with the
Python standard library; optional scientific acceleration is used when
`numpy` / `rasterio` are available (real USGS COG DEM windows).
"""

__version__ = "1.0.0"
