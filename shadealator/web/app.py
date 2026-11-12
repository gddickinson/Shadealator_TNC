"""FastAPI web app for Shade-a-lator TNC: serves the front end in static/ and the JSON API under /api.

Run with `python run_web.py` (http://127.0.0.1:8120, local only). `scripts/build_static.py` exports every path in
STATIC_ENDPOINTS to JSON for the GitHub Pages site, so keep that list in step with the GET routes below.

What runs here: the pure parts of the TTools Step scripts (their own functions, loaded by shadealator.ttools_source)
on a synthetic reach, and the committed Silver Creek results. What cannot run here: anything needing arcpy (ArcGIS
feature classes and rasters) or Excel (the Shade-a-lator workbook); /api/info reports whether arcpy is importable.
"""
import importlib.util
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .. import pipeline, results, synthetic, workflow

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Shade-a-lator TNC")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/info")
def info():
    """Project summary and counts for the home page."""
    s = results.load()["summary"]
    return {
        "title": "Shade-a-lator TNC",
        "steps": len(workflow.STEPS),
        "silver_creek_nodes": s["nodes"],
        "silver_creek_mean_shade": s["shade_mean"],
        "demo_parameters": len(synthetic.PARAMS),
        "arcpy_available": importlib.util.find_spec("arcpy") is not None,
        "excel_model_in_repo": (Path(__file__).resolve().parents[2] / "shade_GD.xlsm").exists(),
    }


@app.get("/api/steps")
def steps():
    """The seven toolbox steps: what each does, what it needs, what the web reproduces."""
    return {"steps": workflow.STEPS}


@app.get("/api/scene_spec")
def scene_spec():
    """Demo parameters (single source: shadealator.synthetic) and the Step 6 variants."""
    return {
        "params": [dict(zip(("name", "label", "min", "max", "step", "default", "unit", "group"), p))
                   for p in synthetic.PARAMS],
        "defaults": synthetic.params_with_defaults({}),
        "step6_variants": synthetic.STEP6_VARIANTS,
        "zones": pipeline.ZONES,
        "z0": synthetic.Z0,
    }


@app.get("/api/results")
def silver_creek():
    """The committed Silver Creek run: settings, per-node inputs (output.xlsx) and shade (output2.xlsx)."""
    return results.load()


@app.post("/api/run")
def run(params: dict = Body(default={})):
    """Run Steps 1-6 on the synthetic reach in Python with the original Step-script functions."""
    try:
        r = pipeline.run(params)
    except (ValueError, TypeError) as e:
        raise HTTPException(400, str(e)) from e
    r["computed_by"] = "python"
    return r


# GET paths (without the /api prefix) written to the static site as api/<path>.json.
STATIC_ENDPOINTS = ["/info", "/steps", "/scene_spec", "/results"]
