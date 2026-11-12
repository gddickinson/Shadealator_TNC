"""Step 6 data preparation: NoData handling, distance and incision (Step6_shade_inputs.py and its use in the scripts).

Run: python -m pytest -q tests/test_step6_inputs.py
"""
import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import Step6_shade_inputs as s6  # noqa: E402
from shadealator import pipeline  # noqa: E402

STEP6 = ["Step6_Interact_with_Shade.py", "Step6_Interact_with_Shade_addVeg.py",
         "Step6_Interact_with_Shade_addVegLeftBank.py", "Step6_Interact_with_Shade_addVegRightBank.py"]


def test_nodata_values_become_blank_and_flag_the_node():
    t = s6.NodataTracker()
    assert t.blank([1480.2, -9999, -3.0, None]) == [1480.2, None, -3.0, None]
    assert t.blank([0.5, 0.2, -9999.0, 1.0]) == [0.5, 0.2, None, 1.0]
    assert t.flag_column() == [0, 1, 1, 1]


def test_keep_blank_applies_the_scripts_transforms_to_values_only():
    set_to_zero = lambda xs: [0 if float(x) < 0 else float(x) for x in xs]  # noqa: E731 - as in Step 6
    assert s6.keep_blank(set_to_zero, [None, -2.0, 3.0]) == [None, 0, 3.0]


@pytest.mark.parametrize("script", STEP6)
def test_step6_scripts_blank_nodata_instead_of_zero(script):
    """Regression: Step 6 fed -9999 (off-DEM) elevations and angles through setToZero, so Shade-a-lator got 0 m
    (about 1480 m below the banks at Silver Creek) and returned near-total shade for those nodes."""
    src = (ROOT / script).read_text()
    assert "from Step6_shade_inputs import" in src
    assert "ELEVATION = keep_blank(setToZero, nodata.blank(extractData(nodes_fc, 'ELEVATION')))" in src
    for d in "WSE":
        assert f"TOPO_{d} = keep_blank(setToZero, nodata.blank(extractData(nodes_fc, 'TOPO_{d}')))" in src
    assert "ELE_T2_S9 = nodata.blank(extractData(nodes_fc, 'ELE_T2_S9'))" in src
    assert 'writeColumn(NODATA_FLAG,excel_output,"Sheet1",2,\'G\')' in src
    ast.parse(src)


def test_pipeline_step6_rows_blank_and_flag_nodata():
    r = pipeline.run({"length_m": 300})
    nodes = [dict(n) for n in r["nodes"]]
    nodes[1]["ELEVATION"] = -9999.0
    nodes[2]["TOPO_S"] = -9999.0
    nodes[2]["ELE_T1_S9"] = -9999.0
    rows = pipeline.step6_rows(nodes, "step6")
    assert rows[1]["elevation"] is None and rows[1]["nodata"] == 1
    assert rows[2]["topo_s"] is None and rows[2]["ele_left"][8] is None and rows[2]["nodata"] == 1
    assert rows[0]["nodata"] == 0 and rows[0]["elevation"] > 1000
