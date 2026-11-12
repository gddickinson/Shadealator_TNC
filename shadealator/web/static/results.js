// Silver Creek: the committed Shade-a-lator run (inputs output.xlsx, shade output2.xlsx), node by node.
import { $, api, app, esc, list, route } from './core.js';
import { COLORS, fit, legend, lineChart, ramp } from './charts.js';

const f = (v, d = 2) => (Number.isFinite(v) ? Number(v).toFixed(d) : '-');
const pct = v => (v * 100).toFixed(1) + '%';

function drawMap(canvas, nodes, sel, height) {
  const { g, w, h } = fit(canvas, height);
  const lat0 = nodes.reduce((a, n) => a + n.lat, 0) / nodes.length, kx = Math.cos(lat0 * Math.PI / 180);
  const xs = nodes.map(n => n.lon * kx), ys = nodes.map(n => n.lat);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const pad = 16, s = Math.min((w - 2 * pad) / (x1 - x0), (h - 2 * pad) / (y1 - y0));
  const ox = (w - (x1 - x0) * s) / 2, oy = (h - (y1 - y0) * s) / 2;
  const X = i => ox + (xs[i] - x0) * s, Y = i => h - oy - (ys[i] - y0) * s;
  g.strokeStyle = 'rgba(79,195,255,.35)'; g.lineWidth = 1.5; g.beginPath();
  nodes.forEach((_, i) => (i ? g.lineTo(X(i), Y(i)) : g.moveTo(X(i), Y(i)))); g.stroke();
  nodes.forEach((n, i) => { g.fillStyle = ramp(n.shade); g.beginPath(); g.arc(X(i), Y(i), 3.2, 0, 7); g.fill();
    if (n.missing) { g.strokeStyle = COLORS.ink; g.lineWidth = 1.5; g.beginPath(); g.arc(X(i), Y(i), 6, 0, 7); g.stroke(); } });
  if (sel != null) { g.strokeStyle = COLORS.b; g.lineWidth = 2.5; g.beginPath(); g.arc(X(sel), Y(sel), 9, 0, 7); g.stroke(); }
  // scale bar (metres per degree of latitude ~ 111 km)
  const mPerPx = 111195 / s, bar = [100, 200, 500, 1000, 2000].find(b => b / mPerPx > 50) || 2000;
  g.fillStyle = COLORS.ink; g.fillRect(12, h - 16, bar / mPerPx, 3);
  g.font = '11px ui-monospace, Menlo, monospace'; g.fillText(bar >= 1000 ? `${bar / 1000} km` : `${bar} m`, 12, h - 22);
  g.fillText('N ↑', w - 34, 16);
  return (px, py) => { let b = 0, bd = Infinity; nodes.forEach((_, i) => { const d = Math.hypot(X(i) - px, Y(i) - py); if (d < bd) { bd = d; b = i; } }); return b; };
}

function nodeCard(n) {
  const zones = n.lc_left.map((_, i) => i + 1);
  return `<h3>Node FID ${n.fid} · ${f(n.along_m / 1000, 2)} km along the node path</h3>
  <dl class="kv">
    <dt>Shade (output2.xlsx)</dt><dd>${pct(n.shade)}</dd>
    <dt>Elevation / aspect</dt><dd>${f(n.elevation)} m / ${f(n.aspect, 1)}°</dd>
    <dt>Wetted width</dt><dd>${f(n.wetted_width)} m</dd>
    <dt>Topographic angles W / S / E</dt><dd>${f(n.topo_w)}° / ${f(n.topo_s)}° / ${f(n.topo_e)}°</dd>
    <dt>Position</dt><dd>${f(n.lat, 5)}, ${f(n.lon, 5)}</dd></dl>
  ${n.missing ? '<p class="static-note">Some inputs for this node are missing in the sheet (elevation 0 or ground elevation -1 / -9999: samples off the DEM).</p>' : ''}
  <div class="scroll"><table class="tbl"><tr><th>Zone</th>${list(zones, z => `<th class="num">${z}</th>`)}</tr>
    <tr><td>Riparian code, left</td>${list(n.lc_left, v => `<td class="num">${v}</td>`)}</tr>
    <tr><td>Riparian code, right</td>${list(n.lc_right, v => `<td class="num">${v}</td>`)}</tr>
    <tr><td>Ground elev. left (m)</td>${list(n.ele_left, v => `<td class="num">${f(v)}</td>`)}</tr>
    <tr><td>Ground elev. right (m)</td>${list(n.ele_right, v => `<td class="num">${f(v)}</td>`)}</tr></table></div>`;
}

route('results', async () => {
  const d = await api('/results');
  const { summary: s, nodes } = d;
  let sel = nodes.reduce((b, n, i) => (!n.missing && (nodes[b].missing || n.shade > nodes[b].shade) ? i : b), 0), pick = null;
  app().innerHTML = `
  <p class="kicker">Silver Creek, Idaho · run start date 1 August 2016</p>
  <h1>Silver Creek results</h1>
  <p class="lead">The run committed with the scripts: ${s.nodes} nodes on stream ${esc(s.stream_ids.join(', '))}, the
    inputs Step 6 wrote into Shade-a-lator (<code>${esc(d.source.inputs)}</code>) and the shade it returned
    (<code>${esc(d.source.output)}</code>, the fraction of the stream surface shaded, shown as %). Read directly from
    the two workbooks, nothing recomputed.</p>
  <div class="tiles">
    <div class="tile"><b>${s.nodes}</b><span>nodes</span></div>
    <div class="tile"><b>${pct(s.shade_mean)}</b><span>mean shade</span></div>
    <div class="tile"><b>${pct(s.shade_median)}</b><span>median shade</span></div>
    <div class="tile"><b>${pct(s.shade_max_complete)}</b><span>most shaded node with complete inputs</span></div>
    <div class="tile"><b>${f(s.path_length_m / 1000, 1)} km</b><span>path through the nodes (median spacing ${f(s.median_node_spacing_m, 0)} m)</span></div>
    <div class="tile"><b>${s.nodes_missing_data}</b><span>nodes with some inputs off the DEM</span></div>
  </div>
  <div class="notice"><b>Committed output from the earlier code.</b> These workbooks were produced in 2017 by the Step 6
    scripts as they were then, before the fixes on this site's branch: Distance written as row x 50 m, incision fixed at
    1.0 m, and off-raster (-9999) values passed through as 0 m / 0° / code 1. They cannot be regenerated here because
    the Shade-a-lator workbook (shade_GD.xlsm) is not in the repository; re-running Step 6 in ArcMap would now write
    those inputs as blanks with a NODATA flag.</div>
  <div class="notice"><b>Read the highest values with care.</b> ${s.nodes_zero_elevation} nodes have an elevation of 0 m in
    the sheet: their DEM sample was off the raster (-9999) and the old Step 6's setToZero turned it into 0, about 1480 m below
    their banks. Their shade (up to ${pct(s.shade_max)}) and some of their topographic angles (up to about 90°) are
    artefacts of that. Leaving out all ${s.nodes_missing_data} nodes with missing inputs, mean shade is
    ${pct(s.shade_mean_complete)} and the maximum ${pct(s.shade_max_complete)}. Missing nodes are drawn with a white ring.</div>
  <div class="two">
    <div><h3>Shade along the stream (map)</h3>
      <canvas id="map" role="img" aria-label="Map of the Silver Creek nodes coloured by shade" style="width:100%;cursor:pointer;border:1px solid var(--line);border-radius:6px"></canvas>
      <div class="row" style="align-items:center;margin-top:6px"><span class="small mute" style="flex:0">0%</span><div class="ramp" id="ramp"></div><span class="small mute" style="flex:0">100%</span></div>
      <p class="small mute">Positions are the nodes' latitude/longitude from output2.xlsx; click a node to inspect it.</p>
    </div>
    <div id="card" class="panel"></div>
  </div>
  <h3>Shade by node</h3><div id="prof"></div>
  <h3>Topographic angles given to Shade-a-lator</h3>${legend([[COLORS.a, 'West'], [COLORS.b, 'South'], [COLORS.c, 'East']])}<div id="topo"></div>
  <h2>Run settings</h2>
  <div class="scroll"><table class="tbl">${list(d.settings, r => `<tr><td>${esc(r.label)}</td><td class="mono">${esc(r.value ?? '')}</td></tr>`)}</table></div>
  <p class="small mute">Riparian codes are the Step 5 land-cover values + 1 (Step 6's offsetBy1), as written to the
    sheet's "Left/Right Bank Riparian Codes" columns. ${s.elevation_columns_agree ? 'The ELEVATION columns of the two workbooks agree for every node.' : 'Note: the ELEVATION columns of the two workbooks do not agree everywhere.'}</p>`;
  $('#ramp').style.background = `linear-gradient(90deg, ${[0, .1, .25, .5, .75, 1].map(ramp).join(',')})`;
  const xs = nodes.map(n => n.along_m / 1000);
  const tip = i => `FID ${nodes[i].fid} · ${f(xs[i], 2)} km<br>shade ${pct(nodes[i].shade)}`;
  let prof, topo;
  const draw = () => {
    pick = drawMap($('#map'), nodes, sel, innerWidth < 760 ? 360 : 440);
    $('#card').innerHTML = nodeCard(nodes[sel]);
  };
  const choose = i => { sel = i; draw(); prof = make(); };
  const make = () => {
    prof = lineChart($('#prof'), [{ label: 'shade', color: COLORS.a, xs, ys: nodes.map(n => n.shade * 100) }],
      { xlabel: 'km along the node path from the first row', ylabel: 'shade %', ylim: [0, 100], mark: sel, tip, onPick: choose });
    topo = lineChart($('#topo'), ['topo_w', 'topo_s', 'topo_e'].map((k, j) => ({ label: k, color: [COLORS.a, COLORS.b, COLORS.c][j], xs, ys: nodes.map(n => n[k]) })),
      { xlabel: 'km along the node path', ylabel: 'degrees', mark: sel, height: 200, onPick: choose,
        tip: i => `FID ${nodes[i].fid}<br>W ${f(nodes[i].topo_w)}° · S ${f(nodes[i].topo_s)}° · E ${f(nodes[i].topo_e)}°` });
    return prof;
  };
  draw(); make();
  $('#map').addEventListener('click', e => { const r = e.target.getBoundingClientRect(); choose(pick(e.clientX - r.left, e.clientY - r.top)); });
  addEventListener('resize', () => { if (location.hash.startsWith('#/results')) { draw(); make(); } });
});
