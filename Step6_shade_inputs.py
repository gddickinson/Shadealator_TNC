#-------------------------------------------------------------------------------
# Name:        Step6_shade_inputs
# Purpose:     Pure helpers shared by the four Step6_Interact_with_Shade*.py scripts
#              (no arcpy, Python 2.7 and 3). Keep this file in the same folder as
#              the Step 6 scripts.
#
# - NoData: TTools writes -9999 where a sample fell off a raster. Those values
#   are passed to Shade-a-lator as blank cells (None) and the node is flagged,
#   instead of being turned into 0 m / 0 degrees / code 1.
# - Distance: from the nodes' STREAM_KM (Step 1 chainage), not rows x 50 m.
# - Incision: from an INCISION field on the nodes if there is one.
# The fall-backs (rows x node spacing, a constant incision) are only used when
# the data are missing, and the caller is told so it can warn.
#-------------------------------------------------------------------------------
from __future__ import division

NODATA_BELOW = -9998          # TTools writes -9999 for off-raster samples
DEFAULT_NODE_SPACING_M = 50.0  # the spacing Step 6 used to assume
DEFAULT_INCISION_M = 1.0       # the incision Step 6 used to write for every node


def is_nodata(v):
    return v is None or (v != v) or v < NODATA_BELOW  # None, NaN or -9999


class NodataTracker(object):
    """Blanks NoData values column by column and remembers which rows had any."""

    def __init__(self):
        self.flags = []

    def blank(self, values):
        out = []
        if not self.flags:
            self.flags = [False] * len(values)
        for i, v in enumerate(values):
            if is_nodata(v):
                out.append(None)
                self.flags[i] = True
            else:
                out.append(v)
        return out

    def flag_column(self):
        return [1 if f else 0 for f in self.flags]


def keep_blank(transform, values):
    """Apply a list transform (setToZero, offsetBy1, addLC) to the non-blank values only."""
    present = [v for v in values if v is not None]
    done = iter(transform(present))
    return [None if v is None else next(done) for v in values]


def node_distances(stream_km, fallback_spacing=DEFAULT_NODE_SPACING_M):
    """Distance (m) of each node from the first row, from STREAM_KM chainage.

    Steps along the list add |km difference| x 1000, so separate streams with their own
    km also give increasing distances. Returns (distances, used_fallback); the fallback
    (row x fallback_spacing) is used when any STREAM_KM is missing.
    """
    if not stream_km or any(is_nodata(k) for k in stream_km):
        return [i * fallback_spacing for i in range(len(stream_km))], True
    out = [0.0]
    for a, b in zip(stream_km, stream_km[1:]):
        out.append(out[-1] + abs(float(a) - float(b)) * 1000.0)
    return out, False


def incisions(values, n, default=DEFAULT_INCISION_M):
    """Channel incision (m) per node from an INCISION field (values may be None when there
    is no such field). Missing values take the default. Returns (list, used_default)."""
    if values is None:
        return [default] * n, True
    out, used = [], False
    for v in values:
        if is_nodata(v) or v < 0:
            out.append(default)
            used = True
        else:
            out.append(float(v))
    return out, used
