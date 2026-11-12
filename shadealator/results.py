"""The committed Silver Creek run: Shade-a-lator inputs (output.xlsx) and its shade output (output2.xlsx).

output.xlsx is the "Main Menu" sheet Step 6 filled in (run settings in D2-D11 / I3-I9, one row per node from row 17:
node id, distance, elevation, aspect, widths, incision, topographic angles W/S/E, land-cover codes and ground elevations
for 9 zones on each bank). output2.xlsx is Sheet1 after the Shade-a-lator macros ran: STREAM_ID, FID, ELEVATION,
LATITUDE, LONGITUDE and SHADE (fraction, 0-1). Rows of the two files are the same nodes in the same order.

A node is flagged `missing` when its elevation is 0 (Step 6's setToZero applied to a -9999 off-DEM sample) or a riparian
ground elevation is -1 or -9999; the "complete" summary values leave those nodes out.
"""
import math
import statistics
from functools import lru_cache
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "output.xlsx"
OUTPUT = ROOT / "output2.xlsx"
FIRST_ROW = 17  # Step 6 writes node rows from row 17 of "Main Menu"

SETTINGS = [  # (label, cell) as laid out on the Main Menu sheet
    ("Run name", "D2"), ("Start date", "D4"), ("Number of days", "D5"), ("Time zone", "D6"),
    ("Daylight savings", "D7"), ("Latitude", "D8"), ("Longitude", "D9"), ("Global riparian zone width (m)", "D10"),
    ("Shade calculation method", "D11"), ("Veg codes", "I3"), ("Solar radiation model", "I4"), ("Cloud cover", "I5"),
    ("Bras visibility factor", "I6"), ("Ryan-Stolzenbach factor", "I7"), ("Reach elevation or zone width", "I8"),
    ("Riparian extinction", "I9"), ("Shade.xls version date", "A3"),
]
# column (0-based, A = 0) -> field
COLS = {0: "node", 1: "distance", 2: "elevation", 4: "aspect", 7: "wetted_width", 8: "nsdz_width", 10: "incision",
        11: "topo_w", 12: "topo_s", 13: "topo_e"}
LC_LEFT, LC_RIGHT, ELE_LEFT, ELE_RIGHT = range(15, 24), range(24, 33), range(33, 42), range(42, 51)


def _r(v, nd=6):
    return round(v, nd) if isinstance(v, float) else v


def _haversine_m(lat1, lon1, lat2, lon2):
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@lru_cache(maxsize=1)
def load() -> dict:
    wb = openpyxl.load_workbook(INPUTS, read_only=True, data_only=True)
    ws = wb["Main Menu"]
    settings = [{"label": lab, "value": ws[cell].value} for lab, cell in SETTINGS]
    rows = [r for r in ws.iter_rows(min_row=FIRST_ROW, max_col=51, values_only=True) if r[0] is not None]
    wb.close()
    wb2 = openpyxl.load_workbook(OUTPUT, read_only=True, data_only=True)
    out = [r for r in wb2["Sheet1"].iter_rows(min_row=2, max_col=6, values_only=True) if r[0] is not None]
    wb2.close()
    if len(out) != len(rows):
        raise ValueError(f"{INPUTS.name} has {len(rows)} node rows but {OUTPUT.name} has {len(out)}")
    nodes, along, agree = [], 0.0, True
    for i, (r, o) in enumerate(zip(rows, out)):
        stream_id, fid, elev, lat, lon, shade = o
        if i:
            along += _haversine_m(nodes[-1]["lat"], nodes[-1]["lon"], lat, lon)
        n = {k: _r(r[c]) for c, k in COLS.items()}
        n.update(fid=fid, lat=_r(lat, 8), lon=_r(lon, 8), shade=_r(shade), along_m=_r(along, 2),
                 lc_left=[r[c] for c in LC_LEFT], lc_right=[r[c] for c in LC_RIGHT],
                 ele_left=[_r(r[c]) for c in ELE_LEFT], ele_right=[_r(r[c]) for c in ELE_RIGHT])
        agree = agree and elev == r[2]
        n["missing"] = n["elevation"] == 0 or any(v is None or v <= -1 for v in n["ele_left"] + n["ele_right"])
        nodes.append(n)
    shades = [o[5] for o in out]
    steps = [b["along_m"] - a["along_m"] for a, b in zip(nodes, nodes[1:])]
    summary = {
        "nodes": len(nodes), "stream_ids": sorted({n["node"] for n in nodes}),
        "shade_mean": statistics.fmean(shades), "shade_median": statistics.median(shades),
        "shade_min": min(shades), "shade_max": max(shades),
        "nodes_missing_data": sum(n["missing"] for n in nodes),
        "nodes_zero_elevation": sum(n["elevation"] == 0 for n in nodes),
        "shade_mean_complete": statistics.fmean(c) if (c := [o[5] for o, n in zip(out, nodes) if not n["missing"]]) else None,
        "shade_max_complete": max(c) if c else None,
        "path_length_m": nodes[-1]["along_m"], "median_node_spacing_m": statistics.median(steps) if steps else None,
        "elevation_columns_agree": agree,
    }
    return {"settings": settings, "summary": summary, "nodes": nodes,
            "source": {"inputs": INPUTS.name, "output": OUTPUT.name}}
