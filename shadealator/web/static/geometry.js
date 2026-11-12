// Step 1 (segment stream: nodes + stream azimuth) and Step 2 (channel width): port of shadealator/geometry.py, which
// writes out Step1_SegmentStream.py create_node_list() and Step2_MeasureChannelWidth.py without arcpy geometry.

function cumulative(pts) {
  const d = [0];
  for (let i = 1; i < pts.length; i++) d.push(d[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  return d;
}

export function positionAlongLine(pts, fraction, cum = cumulative(pts)) {
  const target = Math.min(Math.max(fraction, 0), 1) * cum[cum.length - 1];
  for (let i = 1; i < pts.length; i++) {
    if (cum[i] >= target) {
      const seg = cum[i] - cum[i - 1];
      const t = seg === 0 ? 0 : (target - cum[i - 1]) / seg;
      const [x0, y0] = pts[i - 1], [x1, y1] = pts[i];
      return [x0 + t * (x1 - x0), y0 + t * (y1 - y0)];
    }
  }
  return pts[pts.length - 1];
}

const degrees = r => r * (180 / Math.PI);

// Rows [NODE_ID, STREAM_ID, STREAM_KM, LENGTH, X, Y, STRM_AZMTH] in Step 1's output order (cont_stream_km = True).
export function createNodes(centre, nodeDx, streamId = 1, flip = 0) {
  const cum = cumulative(centre), lineLength = cum[cum.length - 1];
  const numNodes = Math.trunc(lineLength / nodeDx);
  const positions = [], segmentLength = [];
  for (let n = 0; n <= numNodes; n++) positions.push(n * nodeDx / lineLength);
  for (let n = 0; n < numNodes; n++) segmentLength.push(nodeDx);
  segmentLength.push(lineLength % nodeDx);
  const midDistance = Math.min(nodeDx / lineLength, 1);
  const at = f => positionAlongLine(centre, Math.abs(flip - f), cum);
  const rows = positions.map((position, i) => {
    const node = at(position);
    let up, down;
    if (position === 0) { up = at(position + midDistance); down = node; }
    else if (0 < position + midDistance && position + midDistance < 1) { up = at(position + midDistance); down = at(position - midDistance); }
    else { up = node; down = at(position - midDistance); }
    let az = degrees(Math.atan2(down[0] - up[0], down[1] - up[1]));
    if (az < 0) az += 360;
    return [i, streamId, position * lineLength / 1000, segmentLength[i], node[0], node[1], az];
  });
  rows.sort((a, b) => a[1] - b[1] || a[2] - b[2]);
  let skm = 0;
  for (const r of rows) { r[2] = skm; skm = skm + nodeDx * 0.001; }
  rows.sort((a, b) => b[2] - a[2]);
  return rows;
}

export function distanceToPolyline(x, y, pts) {
  let best = Infinity;
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1], vx = pts[i][0] - x0, vy = pts[i][1] - y0;
    const L2 = vx * vx + vy * vy;
    const t = L2 === 0 ? 0 : Math.max(0, Math.min(1, ((x - x0) * vx + (y - y0) * vy) / L2));
    best = Math.min(best, Math.hypot(x - (x0 + t * vx), y - (y0 + t * vy)));
  }
  return best;
}

// Step 2: [CHANWIDTH, LEFT, RIGHT]
export function channelWidth(x, y, left, right) {
  const lb = distanceToPolyline(x, y, left), rb = distanceToPolyline(x, y, right);
  return [lb + rb, lb, rb];
}
