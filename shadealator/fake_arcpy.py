"""A minimal stand-in for the three arcpy raster calls the TTools sampling functions make.

Only what Step 3/4/5's sample_raster/get_topo_angles use: GetRasterProperties_management(raster, prop).getOutput(0),
RasterToNumPyArray(raster, lower_left_point, ncols, nrows, nodata) and Point(x, y). Rasters are FakeRaster objects:
a numpy array (row 0 = north edge) plus the lower-left corner and a square cell size, like an ESRI grid.
"""
import math

import numpy as np


class FakeRaster:
    def __init__(self, array, x_min: float, y_min: float, cellsize: float, name: str = "raster"):
        self.array = np.asarray(array, dtype=float)
        self.x_min, self.y_min, self.cellsize, self.name = float(x_min), float(y_min), float(cellsize), name

    @property
    def nrows(self) -> int:
        return self.array.shape[0]

    @property
    def ncols(self) -> int:
        return self.array.shape[1]

    @property
    def x_max(self) -> float:
        return self.x_min + self.ncols * self.cellsize

    @property
    def y_max(self) -> float:
        return self.y_min + self.nrows * self.cellsize

    def __repr__(self):
        return f"FakeRaster({self.name}, {self.nrows}x{self.ncols}, cell {self.cellsize})"


class Point:
    def __init__(self, X=0.0, Y=0.0):
        self.X, self.Y = float(X), float(Y)


class _Result:
    def __init__(self, value):
        self.value = value

    def getOutput(self, i):  # noqa: N802 - arcpy API name
        return self.value


def GetRasterProperties_management(raster, prop):  # noqa: N802 - arcpy API name
    values = {"CELLSIZEX": raster.cellsize, "CELLSIZEY": raster.cellsize, "LEFT": raster.x_min,
              "BOTTOM": raster.y_min, "RIGHT": raster.x_max, "TOP": raster.y_max}
    return _Result(repr(values[prop]))


def RasterToNumPyArray(raster, lower_left=None, ncols=None, nrows=None, nodata_to_value=None):  # noqa: N802
    """Cells from the one containing `lower_left` (a cell centre) going ncols east and nrows north, as (row, col)
    with row 0 at the north; cells outside the raster get nodata_to_value, as arcpy does."""
    c0 = int(math.floor((lower_left.X - raster.x_min) / raster.cellsize))
    r_bottom = int(math.floor((raster.y_max - lower_left.Y) / raster.cellsize))  # row index counted from the north
    out = np.full((nrows, ncols), float(nodata_to_value), dtype=float)
    for i in range(nrows):
        r = r_bottom - (nrows - 1 - i)
        if 0 <= r < raster.nrows:
            lo, hi = max(c0, 0), min(c0 + ncols, raster.ncols)
            if lo < hi:
                out[i, lo - c0:hi - c0] = raster.array[r, lo:hi]
    return out
