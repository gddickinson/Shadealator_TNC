"""The original Step-script functions load without arcpy and behave as the scripts intend.

Run: python -m pytest -q tests/test_ttools_source.py
"""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shadealator import ttools_source as ts  # noqa: E402
from shadealator.fake_arcpy import FakeRaster, Point, RasterToNumPyArray  # noqa: E402


def test_every_step_script_parses_and_named_functions_load():
    for key in ts.SCRIPTS:
        assert (ROOT / ts.SCRIPTS[key]).exists()
    f = ts.load("step3", ("calculate_gradient", "coord_to_array", "sample_raster", "from_z_units_to_meters_con"))
    assert set(f) == {"calculate_gradient", "coord_to_array", "sample_raster", "from_z_units_to_meters_con"}
    with pytest.raises(KeyError):
        ts.load("step3", ("no_such_function",))


def test_calculate_gradient_plain_and_smoothed():
    grad = ts.fn("step3", "calculate_gradient")
    z, lengths = [10.0, 9.0, 8.5, 8.0], [50, 50, 50, 50]
    assert grad(z, lengths, True) == [0, 0.02, 0.01, 0.01]
    # node 2 is higher than node 1: smoothing gives nodes 2 and 3 the drop from node 1 to node 3. The distance is
    # sum(len_list[i:i + skips + 1]), which at the downstream end of the list runs out of nodes and uses 50 m, not
    # 100 m. Upstream TTools (OR-Dept-Environmental-Quality/TTools, ttools/step3.py) does the same; kept as is and
    # listed for George's decision rather than changed here.
    z2 = [10.0, 9.0, 9.2, 8.0]
    assert grad(z2, lengths, True) == [0, 0.02, 0.02, 0.02]
    assert grad(z2 + [7.5], lengths + [50], True)[2:4] == [0.01, 0.01]  # mid-list: 1 m over 100 m
    assert grad(z2, lengths, False)[2] == pytest.approx(-0.2 / 50)


def test_coord_to_array_rows_count_from_the_north():
    c2a = ts.fn("step4", "coord_to_array")
    assert c2a(5.0, 95.0, 0.0, 100.0, 2.0, 2.0) == [2, 2]
    assert c2a(0.1, 99.9, 0.0, 100.0, 2.0, 2.0) == [0, 0]


def test_build_search_array_starts_one_cell_out():
    bsa = ts.fn("step4", "build_search_array")
    assert list(bsa(0, 10, 2.0, False)) == [2.0, 4.0, 6.0, 8.0]
    assert list(bsa(5, 6, 2.0, False)) == [5]


def test_find_intersection_crossing_and_parallel():
    fi = ts.fn("step4", "find_intersection")
    hit = fi((0, 0), (2, 2), (0, 2), (2, 0), True)
    assert hit[0] and hit[1] == pytest.approx(1) and hit[2] == pytest.approx(1)
    assert fi((0, 0), (1, 0), (0, 1), (1, 1), True)[0] is False


def test_fake_raster_matches_arcpy_layout():
    r = FakeRaster(np.arange(12).reshape(3, 4), 0, 0, 1)
    a = RasterToNumPyArray(r, Point(0.5, 0.5), 4, 3, -9999)
    assert (a == r.array).all()
    pad = RasterToNumPyArray(r, Point(-0.5, 0.5), 2, 1, -9999)
    assert pad.tolist() == [[-9999, 8]]


def test_step6_transforms():
    plain = ts.load("step6", ("setToZero", "offsetBy1"))
    assert plain["setToZero"]([-3, 0.5, 2]) == [0, 0.5, 2.0]
    assert plain["offsetBy1"]([-5, 0, 12.7]) == [1, 1, 13]
    veg = ts.load("step6_addveg", ("offsetBy1", "addLC"))
    assert veg["addLC"]([0, 499, 500, 6000]) == [1001, 1001, 501, 5001]
    assert veg["offsetBy1"]([-5, 12.5, 9000]) == [1, 13.5, 5001]
