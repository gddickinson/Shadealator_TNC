"""Run TTools Steps 1-6 on the synthetic reach, using the original Step-script functions wherever they are pure.

Step 1/2: geometry.py (arcpy geometry calls written out). Step 3: Step3 sample_raster() and calculate_gradient().
Step 4: Step4 get_topo_angles(). Step 5: Step5 create_lc_point_list() and sample_raster(). Step 6: the chosen Step6
script's setToZero/offsetBy1/addLC and its column layout. The raster calls go to fake_arcpy. Block tiling (the scripts'
memory management for large rasters) is skipped: the whole synthetic raster is one block.

What it cannot do: the shade itself. Step 6 hands these columns to an Excel workbook (shade_GD.xlsm, the Shade-a-lator
VBA model) that is not in this repository, so effective shade is not computed here.
"""
import itertools

from . import geometry, synthetic, ttools_source as ts
from .fake_arcpy import FakeRaster

AZIMUTHS = {270: "W", 180: "S", 90: "E"}  # Step 4 with topo_directions = 1, the directions Step 6 uses
ZONES = list(range(1, synthetic.TRANS_SAMPLES + 1))


def _scene(p):
    centre, left, right = synthetic.lines(p)
    dem, cov, x_min, y_min, c = synthetic.rasters(p)
    return centre, left, right, FakeRaster(dem, x_min, y_min, c, "dem"), FakeRaster(cov, x_min, y_min, c, "cover")


def run(params: dict | None = None) -> dict:
    p = synthetic.params_with_defaults(params)
    centre, left, right, dem, cov = _scene(p)
    full = [dem.x_min, dem.y_min, dem.x_max, dem.y_max]

    # Step 1 + 2
    rows = geometry.create_nodes(centre, p["node_dx_m"], synthetic.STREAM_ID)
    nodes = []
    for node_id, sid, km, length, x, y, az in rows:
        w, lb, rb = geometry.channel_width(x, y, left, right)
        nodes.append({"NODE_ID": node_id, "STREAM_ID": sid, "STREAM_KM": km, "LENGTH": length, "X": x, "Y": y,
                      "STRM_AZMTH": az, "CHANWIDTH": w, "LEFT": lb, "RIGHT": rb})
    by_id = {n["NODE_ID"]: n for n in nodes}

    # Step 3: lowest elevation within search_cells of the node, then the gradient (upstream first)
    s3 = ts.load("step3", ("sample_raster", "coord_to_array", "calculate_gradient"))
    moves = list(range(-p["search_cells"], p["search_cells"] + 1))
    cellcoords = list(itertools.product(moves, moves))
    pts = [[n["NODE_ID"], n["X"], n["Y"]] for n in sorted(nodes, key=lambda n: n["NODE_ID"])]
    for node_id, _x, _y, elev, z_node in s3["sample_raster"](full, pts, dem, cellcoords, 1.0):
        by_id[node_id]["ELEVATION"] = float(elev)
        by_id[node_id]["Z_NODE"] = float(z_node)
    order = sorted(nodes, key=lambda n: n["STREAM_KM"], reverse=True)
    grads = s3["calculate_gradient"]([n["ELEVATION"] for n in order], [n["LENGTH"] for n in order],
                                     bool(p["smooth"]))
    for n, g in zip(order, grads):
        n["GRADIENT"] = float(g)

    # Step 4: maximum topographic angle to the west, south and east
    s4 = ts.load("step4", ("get_topo_angles", "build_search_array", "coord_to_array"))
    ts.set_globals(s4, con_to_m=1.0)
    search = int(p["topo_search_m"])
    samples = sorted([n["NODE_ID"], n["STREAM_ID"], a, n["Z_NODE"], n["X"], n["Y"], 0, 0, 0, search]
                     for n in nodes for a in AZIMUTHS)
    cell = dem.cellsize
    for t in s4["get_topo_angles"](by_id, full, samples, dem, {a: cell for a in AZIMUTHS}, search, 1.0):
        n, d = by_id[t[5]], AZIMUTHS[t[6]]
        n["TOPO_" + d] = float(t[7])
        n["TOPO_%s_DIST" % d] = float(t[11])
        n["TOPO_%s_X" % d], n["TOPO_%s_Y" % d] = float(t[0]), float(t[1])

    # Step 5: two transects perpendicular to the stream (perp = True), 9 samples each, land cover + elevation
    s5 = ts.load("step5", ("create_lc_point_list", "sample_raster", "coord_to_array"))
    ts.set_globals(s5, perp=True, con_from_m=1.0, z_raster=dem)
    node_dict = {n["NODE_ID"]: {"POINT_X": n["X"], "POINT_Y": n["Y"], "STREAM_ID": n["STREAM_ID"],
                                "STRM_AZMTH": n["STRM_AZMTH"]} for n in nodes}
    lc_points = s5["create_lc_point_list"](node_dict, sorted(by_id), [0, 90], ZONES, p["sample_dist_m"])
    lc_points = s5["sample_raster"](full, lc_points, cov, None)
    lc_points = s5["sample_raster"](full, lc_points, dem, 1.0)
    for pt in lc_points:
        n = by_id[pt[5]]
        n["LC_" + pt[10]] = float(pt[11])
        n["ELE_" + pt[10]] = float(pt[12])
    samples_out = [[pt[0], pt[1], pt[5], pt[10], float(pt[11]), float(pt[12])] for pt in lc_points]

    return {"params": p, "nodes": nodes, "step6": step6_rows(nodes, p["step6_variant"]), "lc_points": samples_out,
            "raster": {"x_min": dem.x_min, "y_min": dem.y_min, "cellsize": cell, "ncols": dem.ncols,
                       "nrows": dem.nrows}}


STEP6_LC = {  # which transform each Step 6 script applies to the LC zone columns (T1 = left bank, T2 = right)
    "step6": {},
    "step6_addveg": {"LC_T1_S1": "addLC", "LC_T2_S1": "addLC"},
    "step6_addveg_left": {"LC_T1_S1": "addLC"},
    "step6_addveg_right": {"LC_T2_S1": "addLC"},
}


def step6_rows(nodes: list, variant: str = "step6") -> list:
    """The Shade-a-lator 'Main Menu' inputs Step 6 writes, one dict per node in feature-class order.

    As the scripts do: NoData (-9999) values become None (blank cells) and set the row's `nodata` flag; the other
    values go through the chosen script's setToZero / offsetBy1 / addLC.
    """
    names = ("setToZero", "offsetBy1") + (("addLC",) if variant != "step6" else ())
    f = ts.load(variant, names)
    h = ts.step6_helpers()
    nodata = h.NodataTracker()
    col = lambda k: nodata.blank([n[k] for n in nodes])  # noqa: E731 - nodata.blank(extractData(nodes_fc, k))
    out = {"ELEVATION": h.keep_blank(f["setToZero"], col("ELEVATION"))}
    for d in "WSE":
        out["TOPO_" + d] = h.keep_blank(f["setToZero"], col("TOPO_" + d))
    for t in (1, 2):
        for z in ZONES:
            k = "LC_T%d_S%d" % (t, z)
            out[k] = h.keep_blank(f[STEP6_LC[variant].get(k, "offsetBy1")], col(k))
    for t in (1, 2):
        for z in ZONES:
            k = "ELE_T%d_S%d" % (t, z)
            out[k] = col(k)
    flags = nodata.flag_column()
    rows, dist = [], 0
    for i, n in enumerate(nodes):
        rows.append({
            "node": n["STREAM_ID"], "distance": dist, "elevation": out["ELEVATION"][i], "aspect": n["STRM_AZMTH"],
            "wetted_width": n["CHANWIDTH"], "nsdz_width": n["CHANWIDTH"], "incision": 1.0,
            "topo_w": out["TOPO_W"][i], "topo_s": out["TOPO_S"][i], "topo_e": out["TOPO_E"][i],
            "lc_left": [out["LC_T1_S%d" % z][i] for z in ZONES], "lc_right": [out["LC_T2_S%d" % z][i] for z in ZONES],
            "ele_left": [out["ELE_T1_S%d" % z][i] for z in ZONES],
            "ele_right": [out["ELE_T2_S%d" % z][i] for z in ZONES], "nodata": flags[i],
        })
        dist += 50  # Step 6 hard-codes 50 m between nodes, whatever spacing Step 1 used
    return rows
