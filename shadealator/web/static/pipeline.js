// TTools Steps 1-6 on the synthetic reach, in the browser: the same sequence as shadealator/pipeline.py, returning
// the same structure ({ params, nodes, step6, lc_points, raster }). The shade itself is not computed: Step 6 hands these
// columns to the Shade-a-lator Excel workbook (shade_GD.xlsm), which is not in the repository.
import { lines, rasters } from './scene.js';
import { channelWidth, createNodes } from './geometry.js';
import { calculateGradient, lcPoints, sampleAt, sampleElevation, step6Rows, topoAngle } from './ttools_engine.js';

export const AZIMUTHS = { 270: 'W', 180: 'S', 90: 'E' };
export const ZONES = [1, 2, 3, 4, 5, 6, 7, 8, 9];
const STREAM_ID = 1;

export function run(p, scene = null) {
  const { centre, left, right } = scene?.lines || lines(p);
  const { dem, cover } = scene?.rasters || rasters(p);

  // Step 1 + 2
  const nodes = createNodes(centre, p.node_dx_m, STREAM_ID).map(([id, sid, km, len, x, y, az]) => {
    const [w, lb, rb] = channelWidth(x, y, left, right);
    return { NODE_ID: id, STREAM_ID: sid, STREAM_KM: km, LENGTH: len, X: x, Y: y, STRM_AZMTH: az,
      CHANWIDTH: w, LEFT: lb, RIGHT: rb, INCISION: p.incision_m };
  });

  // Step 3
  for (const n of nodes) {
    const s = sampleElevation(dem, n.X, n.Y, p.search_cells);
    n.ELEVATION = s.elevation; n.Z_NODE = s.z_node;
  }
  const order = [...nodes].sort((a, b) => b.STREAM_KM - a.STREAM_KM);
  calculateGradient(order.map(n => n.ELEVATION), order.map(n => n.LENGTH), !!p.smooth)
    .forEach((g, i) => { order[i].GRADIENT = g; });

  // Step 4
  const search = Math.trunc(p.topo_search_m);
  for (const n of nodes) {
    for (const [a, d] of Object.entries(AZIMUTHS)) {
      const t = topoAngle(dem, n.Z_NODE, n.X, n.Y, Number(a), search);
      n['TOPO_' + d] = t.angle; n[`TOPO_${d}_DIST`] = t.distance; n[`TOPO_${d}_X`] = t.x; n[`TOPO_${d}_Y`] = t.y;
    }
  }

  // Step 5
  const lc = [];
  for (const n of [...nodes].sort((a, b) => a.NODE_ID - b.NODE_ID)) {
    for (const pt of lcPoints(n.NODE_ID, n.X, n.Y, n.STRM_AZMTH, ZONES, p.sample_dist_m)) {
      const v = sampleAt(cover, pt.x, pt.y), z = sampleAt(dem, pt.x, pt.y);
      n['LC_' + pt.key] = v; n['ELE_' + pt.key] = z;
      lc.push([pt.x, pt.y, pt.node, pt.key, v, z]);
    }
  }

  const warnings = [];
  return { params: p, nodes, step6: step6Rows(nodes, p.step6_variant, ZONES, warnings), warnings, lc_points: lc,
    raster: { x_min: dem.x_min, y_min: dem.y_min, cellsize: dem.cellsize, ncols: dem.ncols, nrows: dem.nrows } };
}
