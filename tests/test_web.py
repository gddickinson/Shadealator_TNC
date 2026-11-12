"""Web interface tests: every exported endpoint answers, the static build is complete, and the JS engine tests pass.

Run: python -m pytest -q tests/test_web.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shadealator.web.app import STATIC, STATIC_ENDPOINTS, app  # noqa: E402

client = TestClient(app)


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200 and "static/main.js" in r.text


@pytest.mark.parametrize("path", STATIC_ENDPOINTS)
def test_endpoint(path):
    r = client.get("/api" + path)
    assert r.status_code == 200, r.text
    assert r.json() is not None


def test_static_build(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_static
    build_static.build(tmp_path / "site")
    assert (tmp_path / "site" / "index.html").read_text().count("APP_STATIC") == 1
    for path in STATIC_ENDPOINTS:
        assert (tmp_path / "site" / "api" / (path.strip("/") + ".json")).exists()


def test_static_assets_referenced_exist():
    html = (STATIC / "index.html").read_text()
    for name in ("style.css", "main.js"):
        assert f"static/{name}" in html and (STATIC / name).exists()


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_js_engine():
    tests = sorted(STATIC.glob("*.test.mjs"))
    for t in tests:
        r = subprocess.run(["node", str(t)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr


# --- project-specific API tests -------------------------------------------------------------------------------


def test_info_counts():
    d = client.get("/api/info").json()
    assert d["steps"] == 7 and d["silver_creek_nodes"] == 674
    assert 0 < d["silver_creek_mean_shade"] < 1
    assert d["arcpy_available"] in (True, False)


def test_scene_spec_defaults_are_within_ranges():
    d = client.get("/api/scene_spec").json()
    for p in d["params"]:
        assert p["min"] <= d["defaults"][p["name"]] <= p["max"], p["name"]
    assert set(d["step6_variants"]) == {"step6", "step6_addveg", "step6_addveg_left", "step6_addveg_right"}


def test_results_match_the_workbooks():
    d = client.get("/api/results").json()
    s = d["summary"]
    assert s["nodes"] == len(d["nodes"]) == 674
    assert s["elevation_columns_agree"]
    assert abs(s["shade_mean"] - 0.11115715142946142) < 1e-12
    assert d["nodes"][0]["shade"] == round(0.04000383659534429, 6)
    assert {r["label"]: r["value"] for r in d["settings"]}["Start date"] == "8/1/2016"


def test_run_endpoint_runs_the_python_pipeline():
    r = client.post("/api/run", json={"length_m": 300, "step6_variant": "step6_addveg"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["computed_by"] == "python" and len(d["nodes"]) == 7 and len(d["step6"]) == 7
    assert client.post("/api/run", json={"step6_variant": "nope"}).status_code == 400


def test_engine_fixture_matches_python():
    """tests/fixtures/engine_cases.json (used by pipeline.test.mjs) still matches the Python pipeline."""
    import json
    import math
    sys.path.insert(0, str(ROOT / "scripts"))
    import make_engine_fixture
    fresh = make_engine_fixture.build()
    stored = json.loads((ROOT / "tests" / "fixtures" / "engine_cases.json").read_text())

    def same(a, b, where):
        if isinstance(b, dict):
            assert set(a) == set(b), where
            for k in b:
                same(a[k], b[k], f"{where}.{k}")
        elif isinstance(b, list):
            assert len(a) == len(b), where
            for i, (x, y) in enumerate(zip(a, b)):
                same(x, y, f"{where}[{i}]")
        elif isinstance(b, float) or isinstance(a, float):
            assert math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9), f"{where}: {a} vs {b}"
        else:
            assert a == b, where
    same(json.loads(json.dumps(fresh)), stored, "fixture")
