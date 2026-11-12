// TTools Steps 3-6 in the browser: ports of the original Step-script functions, checked against them by
// ttools_engine.test.mjs (fixture written by scripts/make_engine_fixture.py running the Python scripts' own code).
// Rasters are { data, ncols, nrows, x_min, y_max, cellsize } with row 0 at the north (see scene.js); the whole raster
// is one block, so the scripts' block offsets are all zero.
import { at } from './scene.js';

const NODATA = -9999;
const radians = d => d * (Math.PI / 180);
const degrees = r => r * (180 / Math.PI);

// Step3/4/5 coord_to_array: [col, row] with int() truncation toward zero, as Python int() does.
export function coordToArray(easting, northing, xMin, yMax, cx, cy) {
  return [Math.trunc((easting - xMin) / cx), Math.trunc((northing - yMax) / cy * -1)];
}

const cell = (ras, x, y) => {
  const [c, r] = coordToArray(x, y, ras.x_min, ras.y_max, ras.cellsize, ras.cellsize);
  return [r, c];
};

// Step 3 sample_raster: ELEVATION = lowest value in the (2n+1)^2 window around the node; Z_NODE = the node's cell.
export function sampleElevation(dem, x, y, searchCells) {
  const [r, c] = cell(dem, x, y), vals = [];
  for (let dx = -searchCells; dx <= searchCells; dx++)
    for (let dy = -searchCells; dy <= searchCells; dy++) vals.push(at(dem, r + dy, c + dx));
  const ok = Math.max(...vals) < -9998 ? vals : vals.filter(z => z > -9999);
  return { elevation: Math.min(...ok), z_node: at(dem, r, c) };
}

// Step 3 calculate_gradient (z and lengths ordered upstream first).
export function calculateGradient(zList, lenList, smooth) {
  let skip = [0];
  const out = zList.map(() => 0);
  for (let i = 1; i < zList.length; i++) {
    const z = zList[i], maxSkip = Math.max(...skip), zUp = zList[i - 1 - maxSkip];
    if (z > zUp && smooth) { skip.push(maxSkip + 1); continue; }
    let dx = 0;
    for (const L of lenList.slice(i, i + maxSkip + 1)) dx += L;
    const g = (zUp - z) / dx;
    for (const s of skip) out[i - s] = g;
    skip = [0];
  }
  return out;
}

// Step 4 build_search_array (use_skippy = False).
export function buildSearchArray(min, max, cellsize) {
  if (min <= 0) min = cellsize;
  if (max - min >= cellsize) {
    const n = Math.ceil((max - min) / cellsize), out = [];
    for (let i = 0; i < n; i++) out.push(min + i * cellsize);
    return out;
  }
  return [min];
}

// Step 4 get_topo_angles for one node and azimuth: the steepest angle (deg) from the node to the terrain.
export function topoAngle(dem, zNode, x, y, a, searchMax) {
  const d = buildSearchArray(0, searchMax, dem.cellsize);
  const s = Math.sin(radians(a)), co = Math.cos(radians(a));
  const z = d.map(dist => { const [r, c] = cell(dem, dist * s + x, dist * co + y); return at(dem, r, c); });
  const ang = z.map((zt, i) => (zt < -9998 ? NODATA : degrees(Math.atan((zt - zNode) / d[i]))));
  const best = Math.max(...ang), i = ang.indexOf(best);
  return { angle: best, z_topo: z[i], distance: d[i], x: d[i] * s + x, y: d[i] * co + y,
    off_raster: z.filter(v => v < -9998).length };
}

// Step 5 create_lc_point_list with perp = True: the stream sample plus two transects at azimuth -/+ 90 deg.
export function lcPoints(nodeId, x, y, azimuth, zones, sampleDist) {
  const pts = [{ x, y, node: nodeId, key: 'T0_S0', dir: 0 }];
  const d1 = azimuth - 90, d2 = azimuth + 90;
  const dirs = [d1 < 0 ? d1 + 360 : d1, d2 > 360 ? d2 - 360 : d2];
  dirs.forEach((dir, d) => {
    for (const zone of zones) {
      pts.push({ x: (zone * sampleDist * 1.0 * Math.sin(radians(dir))) + x,
        y: (zone * sampleDist * 1.0 * Math.cos(radians(dir))) + y, node: nodeId, key: `T${d + 1}_S${zone}`, dir });
    }
  });
  return pts;
}

// Step 5 sample_raster: the cell value under each point.
export function sampleAt(ras, x, y) {
  const [r, c] = cell(ras, x, y);
  return at(ras, r, c);
}

// Step 6 transforms, per script (they differ: the addVeg scripts cap codes at 5000 and keep fractions).
export const setToZero = v => { v = Number(v); return v < 0 ? 0 : v; };
const offsetPlain = v => { v = Math.trunc(Number(v)); if (v < 0) v = 0; return v + 1; };
const offsetVeg = v => { v = Number(v); if (v < 0) v = 0; if (v > 5000) v = 5000; return v + 1; };
export const addLC = v => { v = Number(v); if (v < 500) v = 1000; if (v > 5000) v = 5000; return v + 1; };
export const STEP6 = {
  step6: { offset: offsetPlain, add: [] },
  step6_addveg: { offset: offsetVeg, add: ['LC_T1_S1', 'LC_T2_S1'] },
  step6_addveg_left: { offset: offsetVeg, add: ['LC_T1_S1'] },
  step6_addveg_right: { offset: offsetVeg, add: ['LC_T2_S1'] },
};

// Step6_shade_inputs.py: off-raster samples (-9999), None or NaN are NoData; they are written as blank cells (null)
// and flag the node, instead of passing through setToZero / offsetBy1 as 0 m / code 1.
export const isNodata = v => v == null || Number.isNaN(v) || v < -9998;

// The Shade-a-lator "Main Menu" columns Step 6 writes, one object per node in feature-class order.
export function step6Rows(nodes, variant, zones) {
  const v = STEP6[variant];
  if (!v) throw new Error(`unknown Step 6 variant ${variant}`);
  const flags = nodes.map(() => 0);
  const val = (i, k, fn = x => x) => { const x = nodes[i][k]; if (isNodata(x)) { flags[i] = 1; return null; } return fn(x); };
  const lcFn = k => (v.add.includes(k) ? addLC : v.offset);
  const rows = nodes.map((n, i) => ({
    node: n.STREAM_ID, distance: i * 50, elevation: val(i, 'ELEVATION', setToZero), aspect: n.STRM_AZMTH,
    wetted_width: n.CHANWIDTH, nsdz_width: n.CHANWIDTH, incision: 1.0,
    topo_w: val(i, 'TOPO_W', setToZero), topo_s: val(i, 'TOPO_S', setToZero), topo_e: val(i, 'TOPO_E', setToZero),
    lc_left: zones.map(z => val(i, `LC_T1_S${z}`, lcFn(`LC_T1_S${z}`))),
    lc_right: zones.map(z => val(i, `LC_T2_S${z}`, lcFn(`LC_T2_S${z}`))),
    ele_left: zones.map(z => val(i, `ELE_T1_S${z}`)), ele_right: zones.map(z => val(i, `ELE_T2_S${z}`)),
  }));
  rows.forEach((r, i) => { r.nodata = flags[i]; });
  return rows;
}
