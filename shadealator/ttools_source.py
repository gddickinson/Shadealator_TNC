"""Load the pure functions of the original Step*.py ArcGIS scripts without running them.

The Step scripts read their parameters with arcpy at import time, so they cannot be imported outside ArcMap. Here each
script is parsed with `ast`, only the requested `def` blocks are compiled (wherever they sit: module level or inside the
script's `try:` body, as Step 6's helpers do), and they are executed in a namespace holding numpy, the math functions
the scripts import, and a stand-in `arcpy` (fake_arcpy.py) for the raster calls. The script files themselves are not
modified or executed, so the web app and the tests run exactly the code ArcMap runs.
"""
import ast
import itertools
import math
import sys
import traceback
from functools import lru_cache
from pathlib import Path

import numpy as np

from . import fake_arcpy

ROOT = Path(__file__).resolve().parent.parent

SCRIPTS = {
    "step1": "Step1_SegmentStream.py",
    "step2": "Step2_MeasureChannelWidth.py",
    "step3": "Step3_SampleElevationGradient_Array.py",
    "step4": "Step4_MeasureTopographicAngles.py",
    "step5": "Step5_Sample_Landcover_PointMethod_Array.py",
    "step6": "Step6_Interact_with_Shade.py",
    "step6_addveg": "Step6_Interact_with_Shade_addVeg.py",
    "step6_addveg_left": "Step6_Interact_with_Shade_addVegLeftBank.py",
    "step6_addveg_right": "Step6_Interact_with_Shade_addVegRightBank.py",
}


def base_namespace() -> dict:
    """Globals the extracted functions expect (what the scripts import at the top, plus a fake arcpy)."""
    ns = {"__name__": "ttools_extract", "np": np, "numpy": np, "itertools": itertools, "sys": sys,
          "traceback": traceback, "arcpy": fake_arcpy}
    for name in ("sin", "cos", "radians", "degrees", "atan2", "hypot", "ceil", "sqrt"):
        ns[name] = getattr(math, name)
    return ns


def _defs(tree: ast.AST) -> dict:
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name not in found:
            found[node.name] = node
    return found


@lru_cache(maxsize=None)
def load(script: str, names: tuple) -> dict:
    """Return {name: function} for the given function names in a Step script (key of SCRIPTS or a file name).

    The functions share one namespace dict per call (their __globals__), so script-level globals they read (`perp`,
    `con_from_m`, `con_to_m`, `z_raster`) can be set with set_globals() before calling them.
    """
    path = ROOT / SCRIPTS.get(script, script)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    defs = _defs(tree)
    missing = [n for n in names if n not in defs]
    if missing:
        raise KeyError(f"{path.name} has no function(s) {missing}")
    module = ast.Module(body=[defs[n] for n in names], type_ignores=[])
    ns = base_namespace()
    exec(compile(module, str(path), "exec"), ns)  # noqa: S102 - the repo's own source, functions only
    return {n: ns[n] for n in names}


def set_globals(funcs: dict, **values) -> None:
    """Set script-level globals read by extracted functions (e.g. perp=True, con_from_m=1.0)."""
    for f in funcs.values():
        f.__globals__.update(values)
        break


def fn(script: str, name: str):
    """One function from a Step script."""
    return load(script, (name,))[name]
