// Drawing for the demo reach: the plan view (DEM shading, vegetation, stream, nodes, the selected node's Step 4 rays
// and Step 5 samples) and the west-east cross-section through the selected node with its topographic angles.
import { COLORS, fit } from './charts.js';
import { at } from './scene.js';

// Plan view. Returns a function mapping a click (canvas px) to world x/y, for picking the nearest node.
export function drawPlan(canvas, scene, res, sel, height) {
  const { dem, cover } = scene.rasters;
  const { g, w, h } = fit(canvas, height);
  // crop to the stream corridor: the node area plus the Step 4 search distance
  const p = res.params, padX = Math.min(p.topo_search_m + 10, 200);
  const xs = res.nodes.map(n => n.X);
  const wx0 = Math.max(dem.x_min, Math.min(...xs) - padX), wx1 = Math.min(dem.x_max, Math.max(...xs) + padX);
  const wy0 = Math.max(dem.y_min, -20), wy1 = Math.min(dem.y_max, p.length_m + 20);
  const s = Math.min(w / (wx1 - wx0), h / (wy1 - wy0));
  const ox = (w - (wx1 - wx0) * s) / 2, oy = (h - (wy1 - wy0) * s) / 2;
  const X = x => ox + (x - wx0) * s, Y = y => oy + (wy1 - y) * s;
  // raster image
  let zmin = Infinity, zmax = -Infinity;
  for (const z of dem.data) { if (z < zmin) zmin = z; if (z > zmax) zmax = z; }
  const img = new ImageData(dem.ncols, dem.nrows);
  for (let r = 0; r < dem.nrows; r++) for (let c = 0; c < dem.ncols; c++) {
    const i = r * dem.ncols + c, t = (dem.data[i] - zmin) / ((zmax - zmin) || 1), veg = cover.data[i];
    let col = [18 + 70 * t, 26 + 80 * t, 46 + 90 * t];
    if (veg >= 100) { const k = Math.min(veg / 2500, 1); col = [20 + 20 * k, 90 + 90 * k, 60 + 40 * k]; }
    if (veg === 0) col = [40, 110, 170];
    img.data.set([col[0], col[1], col[2], 255], i * 4);
  }
  const off = new OffscreenCanvas(dem.ncols, dem.nrows);
  off.getContext('2d').putImageData(img, 0, 0);
  g.imageSmoothingEnabled = false;
  g.save(); g.beginPath(); g.rect(X(wx0), Y(wy1), (wx1 - wx0) * s, (wy1 - wy0) * s); g.clip();
  g.drawImage(off, X(dem.x_min), Y(dem.y_max), dem.ncols * dem.cellsize * s, dem.nrows * dem.cellsize * s);
  // banks and centreline
  const line = (pts, color, lw, dash = []) => { g.strokeStyle = color; g.lineWidth = lw; g.setLineDash(dash); g.beginPath();
    pts.forEach(([x, y], i) => (i ? g.lineTo(X(x), Y(y)) : g.moveTo(X(x), Y(y)))); g.stroke(); g.setLineDash([]); };
  line(scene.lines.left, 'rgba(232,241,255,.55)', 1); line(scene.lines.right, 'rgba(232,241,255,.55)', 1);
  line(scene.lines.centre, COLORS.c, 1.5, [5, 4]);
  // selected node: Step 4 rays to the maximum angle and Step 5 samples
  const n = res.nodes.find(q => q.NODE_ID === sel);
  if (n) {
    g.strokeStyle = COLORS.b; g.lineWidth = 2;
    for (const d of 'WSE') { g.beginPath(); g.moveTo(X(n.X), Y(n.Y)); g.lineTo(X(n[`TOPO_${d}_X`]), Y(n[`TOPO_${d}_Y`])); g.stroke();
      g.fillStyle = COLORS.b; g.beginPath(); g.arc(X(n[`TOPO_${d}_X`]), Y(n[`TOPO_${d}_Y`]), 4, 0, 7); g.fill(); }
    g.fillStyle = COLORS.ink;
    for (const [x, y, id, key] of res.lc_points) if (id === sel && key !== 'T0_S0') { g.beginPath(); g.arc(X(x), Y(y), 2.6, 0, 7); g.fill(); }
  }
  for (const q of res.nodes) {
    g.fillStyle = q.NODE_ID === sel ? COLORS.b : COLORS.a; g.strokeStyle = '#05060c'; g.lineWidth = 2;
    g.beginPath(); g.arc(X(q.X), Y(q.Y), q.NODE_ID === sel ? 7 : 5, 0, 7); g.fill(); g.stroke();
  }
  g.restore();
  // scale bar + north arrow + flow label
  const bar = [10, 20, 50, 100, 200].find(b => b * s > 50) || 200;
  g.fillStyle = COLORS.ink; g.fillRect(12, h - 18, bar * s, 3);
  g.font = '11px ui-monospace, Menlo, monospace'; g.fillText(`${bar} m`, 12, h - 24);
  g.fillText('N ↑   flow ↓', w - 92, 16);
  return (px, py) => ({ x: wx0 + (px - ox) / s, y: wy1 - (py - oy) / s });
}

// West-east section through the node: ground, vegetation (cover raster), water, the node, and the W/E topo angles.
export function drawSection(canvas, scene, res, sel, height) {
  const { dem, cover } = scene.rasters;
  const n = res.nodes.find(q => q.NODE_ID === sel);
  const { g, w, h } = fit(canvas, height);
  if (!n) return;
  const reach = res.params.topo_search_m, c = dem.cellsize;
  const cellOf = (x, y) => [Math.trunc((dem.y_max - y) / c), Math.trunc((x - dem.x_min) / c)];
  const prof = [];
  for (let x = n.X - reach; x <= n.X + reach; x += c / 2) {
    const [r, col] = cellOf(x, n.Y);
    if (r >= 0 && r < dem.nrows && col >= 0 && col < dem.ncols) prof.push([x, at(dem, r, col), at(cover, r, col) / 100]);
  }
  const top = Math.max(...prof.map(q => q[1] + q[2]), n.Z_NODE + 2), bot = Math.min(...prof.map(q => q[1])) - 1;
  const M = { l: 52, r: 12, t: 14, b: 30 };
  const X = x => M.l + (x - (n.X - reach)) / (2 * reach) * (w - M.l - M.r);
  const Y = z => h - M.b - (z - bot) / (top - bot) * (h - M.t - M.b);
  g.font = '11px ui-monospace, Menlo, monospace'; g.fillStyle = COLORS.mute; g.textAlign = 'right';
  for (let k = 0; k <= 4; k++) { const z = bot + (top - bot) * k / 4; g.fillText(z.toFixed(1), M.l - 6, Y(z) + 4);
    g.strokeStyle = COLORS.grid; g.beginPath(); g.moveTo(M.l, Y(z)); g.lineTo(w - M.r, Y(z)); g.stroke(); }
  g.textAlign = 'center';
  g.fillText(`west  ←  ${reach} m  ·  node  ·  ${reach} m  →  east   (elevation m, vertical exaggeration ${((2 * reach) / (w - 64) / ((top - bot) / (h - 44))).toFixed(1)}x)`, w / 2, h - 8);
  // vegetation (from the ground up), then ground
  for (const [x, z, v] of prof) if (v >= 1) { g.fillStyle = 'rgba(89,240,160,.55)'; g.fillRect(X(x) - 1, Y(z + v), Math.max(2, X(x + c / 2) - X(x)), Y(z) - Y(z + v)); }
  g.fillStyle = 'rgba(79,195,255,.18)'; g.strokeStyle = '#c6d4ee'; g.lineWidth = 2; g.beginPath();
  prof.forEach(([x, z], i) => (i ? g.lineTo(X(x), Y(z)) : g.moveTo(X(x), Y(z)))); g.stroke();
  // topographic angle rays (to W and E maxima) from the node
  g.strokeStyle = COLORS.b; g.lineWidth = 2; g.setLineDash([6, 4]);
  for (const d of ['W', 'E']) {
    const dist = n[`TOPO_${d}_DIST`], sign = d === 'W' ? -1 : 1, ang = n['TOPO_' + d] * Math.PI / 180;
    g.beginPath(); g.moveTo(X(n.X), Y(n.Z_NODE)); g.lineTo(X(n.X + sign * dist), Y(n.Z_NODE + Math.tan(ang) * dist)); g.stroke();
    g.fillStyle = COLORS.b; g.textAlign = sign < 0 ? 'left' : 'right';
    g.fillText(`TOPO_${d} ${n['TOPO_' + d].toFixed(1)}°`, sign < 0 ? M.l + 6 : w - M.r - 6, M.t + 12);
  }
  g.setLineDash([]);
  g.fillStyle = COLORS.c; g.strokeStyle = '#05060c'; g.beginPath(); g.arc(X(n.X), Y(n.Z_NODE), 5, 0, 7); g.fill(); g.stroke();
}
