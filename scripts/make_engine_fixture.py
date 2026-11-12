"""Write tests/fixtures/engine_cases.json: the Python pipeline's results for the JS engine test.

shadealator/web/static/pipeline.test.mjs runs the browser engine on the same parameters and checks it reproduces every
number; tests/test_pipeline.py checks this fixture still matches what the Python code (the original Step-script
functions) computes now.

Run: python scripts/make_engine_fixture.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shadealator import pipeline, ttools_source as ts  # noqa: E402

OUT = ROOT / "tests" / "fixtures" / "engine_cases.json"

CASES = {
    "defaults": {},
    "addveg_short_trees": {"step6_variant": "step6_addveg", "veg_height_m": 3, "veg_gap_m": 6, "veg_band_m": 20},
    "hollow_smoothed": {"dip_m": 2.0, "node_dx_m": 30, "sample_dist_m": 5, "cellsize_m": 1, "meander_amp_m": 5,
                        "step6_variant": "step6_addveg_left"},
    "hollow_unsmoothed": {"dip_m": 2.0, "smooth": 0, "cellsize_m": 3, "wall_west_m": 60, "topo_search_m": 250,
                          "length_m": 450, "node_dx_m": 40, "search_cells": 0},
    "right_bank_bare": {"veg_right": 0, "low_cover_m": 1.2, "step6_variant": "step6_addveg_right",
                        "meander_amp_m": 35, "meander_wavelength_m": 90, "channel_width_m": 20, "incision_m": 2.5},
}

GRADIENT_CASES = [  # (z, lengths, smooth) straight into Step 3's calculate_gradient
    ([10.0, 9.0, 8.5, 8.0], [50, 50, 50, 50], True),
    ([10.0, 9.0, 9.2, 8.0], [50, 50, 50, 50], True),
    ([10.0, 9.0, 9.2, 9.4, 8.0, 7.9], [12.5, 50, 50, 50, 50, 50], True),
    ([10.0, 9.0, 9.2, 8.0], [50, 50, 50, 50], False),
]
TRANSFORM_INPUT = [-9999, -1, 0, 0.4, 7, 120.6, 499, 500, 2500, 5000, 5000.5, 9000]


def _clean(v):
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    return v


def build() -> dict:
    cases = {}
    for name, params in CASES.items():
        r = pipeline.run(params)
        cases[name] = _clean({"params": r["params"], "nodes": r["nodes"], "step6": r["step6"],
                              "lc_points": r["lc_points"], "raster": r["raster"]})
    grad = ts.fn("step3", "calculate_gradient")
    transforms = {}
    for variant in ("step6", "step6_addveg"):
        names = ("setToZero", "offsetBy1") + (("addLC",) if variant != "step6" else ())
        f = ts.load(variant, names)
        transforms[variant] = {n: f[n](TRANSFORM_INPUT) for n in names}
    # Step 6 with NoData (-9999) injected into a few inputs, for every Step 6 script
    base = pipeline.run({"length_m": 300})["nodes"]
    holes = [dict(n) for n in base]
    holes[1]["ELEVATION"] = -9999.0
    holes[2]["TOPO_S"] = -9999.0
    holes[3]["LC_T1_S1"] = -9999.0
    holes[3]["ELE_T2_S4"] = -9999.0
    holes[4]["TOPO_W"] = -2.5
    step6_nodata = {"nodes": _clean(holes),
                    "rows": {v: _clean(pipeline.step6_rows(holes, v)) for v in pipeline.STEP6_LC}}
    return {
        "cases": cases,
        "step6_nodata": step6_nodata,
        "gradient": [{"z": z, "lengths": L, "smooth": s, "out": grad(z, L, s)} for z, L, s in GRADIENT_CASES],
        "transforms": {"input": TRANSFORM_INPUT, "out": transforms},
    }


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build(), indent=None, separators=(",", ":")) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
