"""Step 1 (segment stream) and Step 2 (channel width) without arcpy geometry objects.

These steps call arcpy Polyline.positionAlongLine and PointGeometry.distanceTo, which cannot be loaded from the scripts,
so the same calculations are written out here, following Step1_SegmentStream.py create_node_list() and the
cont_stream_km ordering in its main block, and Step2_MeasureChannelWidth.py calc_channel_width(). Units are metres
(a projected coordinate system in metres, so con_to_m = con_from_m = 1).
"""
import math


def _cumulative(pts):
    d = [0.0]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d.append(d[-1] + math.hypot(x1 - x0, y1 - y0))
    return d


def polyline_length(pts) -> float:
    return _cumulative(pts)[-1]


def position_along_line(pts, fraction: float, cum=None):
    """Point at `fraction` (0-1) of the polyline length, like arcpy positionAlongLine(fraction, True)."""
    cum = cum or _cumulative(pts)
    target = min(max(fraction, 0.0), 1.0) * cum[-1]
    for i in range(1, len(pts)):
        if cum[i] >= target:
            seg = cum[i] - cum[i - 1]
            t = 0.0 if seg == 0 else (target - cum[i - 1]) / seg
            (x0, y0), (x1, y1) = pts[i - 1], pts[i]
            return x0 + t * (x1 - x0), y0 + t * (y1 - y0)
    return pts[-1]


def create_nodes(centre, node_dx: float, stream_id=1, flip: int = 0):
    """Step 1: nodes every node_dx metres from the downstream end, with the stream azimuth (flow direction).

    Returns rows [NODE_ID, STREAM_ID, STREAM_KM, LENGTH, X, Y, STRM_AZMTH] in the feature-class order Step 1 writes
    with cont_stream_km = True (stream km recounted from the downstream end, then sorted upstream first).
    """
    cum = _cumulative(centre)
    line_length = cum[-1]
    num_nodes = int(line_length / node_dx)
    positions = [n * node_dx / line_length for n in range(num_nodes + 1)]
    segment_length = [node_dx] * num_nodes + [line_length % node_dx]
    mid_distance = min(node_dx / line_length, 1)
    at = lambda f: position_along_line(centre, abs(flip - f), cum)  # noqa: E731
    rows = []
    for i, position in enumerate(positions):
        node = at(position)
        if position == 0.0:
            mid_up, mid_down = at(position + mid_distance), node
        elif 0.0 < position + mid_distance < 1:
            mid_up, mid_down = at(position + mid_distance), at(position - mid_distance)
        else:
            mid_up, mid_down = node, at(position - mid_distance)
        az = math.degrees(math.atan2(mid_down[0] - mid_up[0], mid_down[1] - mid_up[1]))
        if az < 0:
            az += 360
        rows.append([i, stream_id, position * line_length / 1000, segment_length[i], node[0], node[1], az])
    # cont_stream_km: sort by (stream, km), renumber km by node_dx, then sort with the largest km first
    rows.sort(key=lambda r: (r[1], r[2]))
    skm = 0.0
    for r in rows:
        r[2] = skm
        skm = skm + node_dx * 0.001
    rows.sort(key=lambda r: r[2], reverse=True)
    return rows


def distance_to_polyline(x: float, y: float, pts) -> float:
    """Shortest distance from a point to a polyline (arcpy PointGeometry.distanceTo)."""
    best = math.inf
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        vx, vy = x1 - x0, y1 - y0
        L2 = vx * vx + vy * vy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x0) * vx + (y - y0) * vy) / L2))
        best = min(best, math.hypot(x - (x0 + t * vx), y - (y0 + t * vy)))
    return best


def channel_width(x: float, y: float, left, right):
    """Step 2: (CHANWIDTH, LEFT, RIGHT) = distances from the node to the left and right bank lines."""
    lb = distance_to_polyline(x, y, left)
    rb = distance_to_polyline(x, y, right)
    return lb + rb, lb, rb
