"""A synthetic stream reach for the demo: centreline, banks, elevation (DEM) and vegetation-height rasters.

Nothing here is measured data. The scene is built from simple formulas so the Python pipeline (pipeline.py, running
the original TTools functions) and the browser engine (web/static/scene.js) can build exactly the same rasters.
Coordinates are metres, x east, y north. The stream flows south: the downstream end is at y = 0 and the upstream end
at y = length. Facing downstream (south), the left bank is the east side (x > centreline).

PARAMS is the single source of the demo's parameters (defaults, ranges, labels); the web page reads it from the API.
"""
import math

import numpy as np

Z0 = 1480.0  # base elevation of the downstream end of the bed (m); arbitrary, close to the Silver Creek run's elevations

# name, label, min, max, step, default, unit, group
PARAMS = [
    ("length_m", "Reach length", 200, 1000, 50, 600, "m", "Stream"),
    ("meander_amp_m", "Meander amplitude", 0, 40, 1, 15, "m", "Stream"),
    ("meander_wavelength_m", "Meander wavelength", 80, 400, 10, 200, "m", "Stream"),
    ("channel_width_m", "Channel width", 2, 30, 1, 8, "m", "Stream"),
    ("incision_m", "Channel incision", 0, 3, 0.1, 0.5, "m", "Stream"),
    ("bed_slope", "Bed slope", 0, 0.02, 0.001, 0.004, "m/m", "Stream"),
    ("dip_m", "Bed hollow at mid-reach", 0, 3, 0.1, 0.0, "m", "Stream"),
    ("floodplain_half_m", "Floodplain half-width", 5, 150, 5, 40, "m", "Valley"),
    ("wall_width_m", "Valley wall run", 10, 200, 5, 60, "m", "Valley"),
    ("wall_west_m", "West wall height", 0, 80, 1, 25, "m", "Valley"),
    ("wall_east_m", "East wall height", 0, 80, 1, 15, "m", "Valley"),
    ("veg_height_m", "Riparian vegetation height", 0, 40, 0.5, 12, "m", "Vegetation"),
    ("veg_band_m", "Vegetation band width", 0, 90, 5, 30, "m", "Vegetation"),
    ("veg_gap_m", "Cleared strip at the bank", 0, 40, 1, 0, "m", "Vegetation"),
    ("veg_left", "Vegetation on the left (east) bank", 0, 1, 1, 1, "", "Vegetation"),
    ("veg_right", "Vegetation on the right (west) bank", 0, 1, 1, 1, "", "Vegetation"),
    ("low_cover_m", "Other ground cover height", 0, 2, 0.1, 0.3, "m", "Vegetation"),
    ("cellsize_m", "Raster cell size", 1, 5, 1, 2, "m", "TTools"),
    ("node_dx_m", "Node spacing (Step 1)", 10, 200, 10, 50, "m", "TTools"),
    ("search_cells", "Elevation search cells (Step 3)", 0, 5, 1, 2, "cells", "TTools"),
    ("smooth", "Smooth non-positive gradients (Step 3)", 0, 1, 1, 1, "", "TTools"),
    ("topo_search_m", "Topographic search distance (Step 4)", 20, 300, 10, 100, "m", "TTools"),
    ("sample_dist_m", "Transect sample spacing (Step 5)", 2, 30, 1, 10, "m", "TTools"),
]
DEFAULTS = {p[0]: p[5] for p in PARAMS}
STEP6_VARIANTS = {
    "step6": "Step6_Interact_with_Shade.py: land cover + 1",
    "step6_addveg": "Step6 ..._addVeg.py: zone 1 on both banks set to 10 m where under 5 m",
    "step6_addveg_left": "Step6 ..._addVegLeftBank.py: zone 1 on the left bank only",
    "step6_addveg_right": "Step6 ..._addVegRightBank.py: zone 1 on the right bank only",
}
TRANS_SAMPLES = 9  # Step 6 writes zones 1-9 for each bank, so Step 5 samples 9 points per transect
STREAM_ID = 1


def params_with_defaults(p: dict | None) -> dict:
    """Merge user parameters over DEFAULTS, clamped to each parameter's range."""
    out = dict(DEFAULTS)
    for name, _label, lo, hi, _step, _d, _u, _g in PARAMS:
        if p and name in p and p[name] is not None:
            out[name] = min(max(float(p[name]), lo), hi)
    for k in ("search_cells", "veg_left", "veg_right", "smooth"):
        out[k] = int(round(out[k]))
    out["step6_variant"] = (p or {}).get("step6_variant", "step6")
    if out["step6_variant"] not in STEP6_VARIANTS:
        raise ValueError(f"unknown step6_variant {out['step6_variant']!r}")
    return out


def centre_x(p: dict, y: float) -> float:
    return p["meander_amp_m"] * math.sin(2 * math.pi * y / p["meander_wavelength_m"])


def lines(p: dict):
    """Centreline and bank polylines, digitised from the downstream end (y = 0) upstream, one vertex per metre."""
    n = int(p["length_m"])
    half = p["channel_width_m"] / 2
    centre, left, right = [], [], []
    for i in range(n + 1):
        y = float(i)
        xc = centre_x(p, y)
        centre.append((xc, y))
        left.append((xc + half, y))
        right.append((xc - half, y))
    return centre, left, right


def extent(p: dict):
    """Raster lower-left corner and size: wide enough that every Step 3/4/5 sample stays on the raster."""
    c = p["cellsize_m"]
    margin = p["topo_search_m"] + 10 * c + 20
    half_w = p["meander_amp_m"] + max(p["floodplain_half_m"] + p["wall_width_m"],
                                      p["channel_width_m"] / 2 + 9 * p["sample_dist_m"]) + margin
    ncols = 2 * int(math.ceil(half_w / c))
    nrows = int(math.ceil((p["length_m"] + 2 * margin) / c))
    x_min = -ncols / 2 * c
    y_min = -math.ceil(margin / c) * c
    return x_min, y_min, ncols, nrows


def ground(p: dict, x: float, y: float) -> float:
    """Synthetic DEM elevation (m)."""
    dx = x - centre_x(p, y)
    ad = abs(dx)
    z = Z0 + p["bed_slope"] * y
    z -= p["dip_m"] * max(0.0, 1 - abs(y - p["length_m"] / 2) / 30)
    if ad <= p["channel_width_m"] / 2:
        z -= p["incision_m"]
    t = min(max((ad - p["floodplain_half_m"]) / p["wall_width_m"], 0.0), 1.0)
    h = p["wall_west_m"] if dx < 0 else p["wall_east_m"]
    return z + h * t * t * (3 - 2 * t)


def cover_cm(p: dict, x: float, y: float) -> int:
    """Synthetic land-cover raster: vegetation height in whole centimetres (like the run's maxheight_cm_int)."""
    dx = x - centre_x(p, y)
    bank = abs(dx) - p["channel_width_m"] / 2
    if bank < 0:
        return 0
    side_on = p["veg_left"] if dx > 0 else p["veg_right"]
    in_band = p["veg_gap_m"] <= bank < p["veg_gap_m"] + p["veg_band_m"]
    h = p["veg_height_m"] if (side_on and in_band) else p["low_cover_m"]
    return int(round(h * 100))


def rasters(p: dict):
    """(dem, cover) as FakeRaster-ready (array, x_min, y_min, cellsize); row 0 is the north edge."""
    x_min, y_min, ncols, nrows = extent(p)
    c = p["cellsize_m"]
    y_max = y_min + nrows * c
    dem = np.empty((nrows, ncols))
    cov = np.empty((nrows, ncols))
    for r in range(nrows):
        y = y_max - (r + 0.5) * c
        for col in range(ncols):
            x = x_min + (col + 0.5) * c
            dem[r, col] = ground(p, x, y)
            cov[r, col] = cover_cm(p, x, y)
    return dem, cov, x_min, y_min, c
