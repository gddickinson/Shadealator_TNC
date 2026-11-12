// Demo reach: a synthetic stream in a valley; TTools Steps 1-6 recompute in the browser on every change.
// Parameters (defaults, ranges) come from /api/scene_spec (Python shadealator.synthetic). "Check against Python" runs
// the same reach through the original Step-script functions on the local server and compares every number.
import { $, api, app, download, esc, isStatic, list, needsServer, route } from './core.js';
import { COLORS, legend, lineChart } from './charts.js';
import { drawPlan, drawSection } from './demo_draw.js';
import { lines, rasters } from './scene.js';
import { run } from './pipeline.js';

const f = (v, d = 2) => (Number.isFinite(v) ? Number(v).toFixed(d) : '-');
const CHECKS = new Set(['veg_left', 'veg_right', 'smooth']);

function controls(spec, p) {
  const groups = [...new Set(spec.params.map(q => q.group))];
  return list(groups, gname => `<fieldset class="ctlgroup"><legend>${esc(gname)}</legend>${list(spec.params.filter(q => q.group === gname), q =>
    CHECKS.has(q.name)
      ? `<div class="ctl check"><label><input type="checkbox" data-p="${q.name}" ${p[q.name] ? 'checked' : ''}>${esc(q.label)}</label></div>`
      : `<div class="ctl"><label for="p-${q.name}">${esc(q.label)} <b data-v="${q.name}">${p[q.name]}${q.unit && q.unit !== 'cells' ? ' ' + q.unit : ''}</b></label>
         <input type="range" id="p-${q.name}" data-p="${q.name}" min="${q.min}" max="${q.max}" step="${q.step}" value="${p[q.name]}"></div>`)}</fieldset>`);
}

function rowTable(r) {
  const z = r.lc_left.map((_, i) => i + 1);
  return `<div class="scroll"><table class="tbl">
    <tr><th>Zone</th>${list(z, i => `<th class="num">${i}</th>`)}</tr>
    <tr><td>LC left (T1)</td>${list(r.lc_left, v => `<td class="num">${f(v, 0)}</td>`)}</tr>
    <tr><td>LC right (T2)</td>${list(r.lc_right, v => `<td class="num">${f(v, 0)}</td>`)}</tr>
    <tr><td>Ground left (m)</td>${list(r.ele_left, v => `<td class="num">${f(v, 2)}</td>`)}</tr>
    <tr><td>Ground right (m)</td>${list(r.ele_right, v => `<td class="num">${f(v, 2)}</td>`)}</tr></table></div>`;
}

function step6Csv(res) {
  const z = [1, 2, 3, 4, 5, 6, 7, 8, 9];
  const head = ['node', 'distance_m', 'elevation_m', 'aspect_deg', 'wetted_width_m', 'nsdz_width_m', 'incision_m',
    'topo_w', 'topo_s', 'topo_e', ...z.map(i => 'lc_left_' + i), ...z.map(i => 'lc_right_' + i),
    ...z.map(i => 'ele_left_' + i), ...z.map(i => 'ele_right_' + i), 'nodata'];
  const rows = res.step6.map(r => [r.node, r.distance, r.elevation, r.aspect, r.wetted_width, r.nsdz_width, r.incision,
    r.topo_w, r.topo_s, r.topo_e, ...r.lc_left, ...r.lc_right, ...r.ele_left, ...r.ele_right, r.nodata].map(v => v ?? '').join(','));
  return [head.join(','), ...rows].join('\n') + '\n';
}

// Largest relative difference between two result objects, over every number they share.
function maxDiff(a, b, path = '') {
  let worst = { d: 0, at: '' };
  const walk = (x, y, p) => {
    if (typeof y === 'number' && typeof x === 'number') {
      const d = Math.abs(x - y) / Math.max(1, Math.abs(y));
      if (d > worst.d) worst = { d, at: p };
    } else if (y && typeof y === 'object') for (const k of Object.keys(y)) if (x && k in x) walk(x[k], y[k], p + '.' + k);
  };
  walk(a, b, path);
  return worst;
}

route('demo', async () => {
  const spec = await api('/scene_spec');
  const p = { ...spec.defaults };
  let res = null, scene = null, sel = null, pick = null;
  app().innerHTML = `
  <p class="kicker">Synthetic reach · Steps 1-6 in your browser</p>
  <h1>Demo reach</h1>
  <p class="lead">A made-up stream meandering south through a valley, with a band of riparian trees. Move the valley
    walls and the vegetation and TTools recomputes: nodes and azimuths (Step 1), channel width (2), elevation and
    gradient (3), topographic angles to the west, south and east (4), and land-cover and ground samples on transects
    at right angles to the stream (5), then the Shade-a-lator columns Step 6 would write. Not real terrain.</p>
  <div class="side">
    <div id="ctls">
      <fieldset class="ctlgroup"><legend>Step 6 script</legend>
        <label for="variant">Land-cover adjustment</label>
        <select id="variant">${list(Object.entries(spec.step6_variants), ([k, v]) => `<option value="${k}">${esc(v)}</option>`)}</select>
      </fieldset>
      ${controls(spec, p)}
      <button class="alt" id="reset">Reset</button>
    </div>
    <div>
      <div class="row"><div><label for="node">Selected node <b id="nodeLabel"></b></label><input type="range" id="node" min="0" max="1" step="1" value="0"></div></div>
      <h3>Plan view</h3>
      <canvas id="plan" role="img" aria-label="Plan view of the synthetic reach: terrain, vegetation, stream, nodes and the selected node's samples" style="width:100%;cursor:pointer;border:1px solid var(--line);border-radius:6px"></canvas>
      ${legend([[COLORS.a, 'nodes', true], [COLORS.b, 'Step 4 rays to the steepest W/S/E angle'], [COLORS.ink, 'Step 5 samples', true], ['rgb(40,180,100)', 'vegetation ≥ 1 m', true], ['rgb(40,110,170)', 'water', true]])}
      <h3>West-east section through the node</h3>
      <canvas id="section" role="img" aria-label="Cross-section through the selected node with topographic angles" style="width:100%;border:1px solid var(--line);border-radius:6px"></canvas>
      <div id="nodeInfo"></div>
    </div>
  </div>
  <h2>Along the reach</h2>
  <div class="two"><div><h3>Stream elevation (Step 3)</h3><div id="elev"></div></div><div><h3>Gradient (Step 3)</h3><div id="grad"></div></div></div>
  <h3>Topographic angles (Step 4)</h3>${legend([[COLORS.a, 'TOPO_W'], [COLORS.b, 'TOPO_S'], [COLORS.c, 'TOPO_E']])}<div id="topo"></div>
  <h2>Step 6 output</h2>
  <p>The columns Step 6 writes into the Shade-a-lator "Main Menu" sheet (one row per node, upstream first). In ArcMap
    these then go to shade_GD.xlsm, which computes the shade; that workbook is not in the repository.</p>
  <button id="csv">Download CSV</button> <button class="alt" id="pycheck">Check against Python</button>
  <div id="pyout" class="check-out"></div>
  <div class="scroll" id="table"></div>`;

  const setHeights = () => (innerWidth < 760 ? [420, 230] : [560, 260]);

  function render(keepSel = true, recompute = true) {
    if (recompute || !res) { scene = { lines: lines(p), rasters: rasters(p) }; res = run(p, scene); }
    const ids = res.nodes.map(n => n.NODE_ID);
    if (!keepSel || !ids.includes(sel)) sel = ids[Math.floor(ids.length / 2)];
    const slider = $('#node'); slider.max = res.nodes.length - 1; slider.value = res.nodes.findIndex(n => n.NODE_ID === sel);
    drawNode();
    const km = res.nodes.map(n => n.STREAM_KM * 1000), mark = res.nodes.findIndex(n => n.NODE_ID === sel);
    const tip = i => `node ${res.nodes[i].NODE_ID} · ${f(km[i], 0)} m from the downstream end`;
    lineChart($('#elev'), [{ label: 'ELEVATION (m)', color: COLORS.c, xs: km, ys: res.nodes.map(n => n.ELEVATION), dots: true }],
      { xlabel: 'distance from downstream end (m)', ylabel: 'm', mark, tip: i => `${tip(i)}<br>ELEVATION ${f(res.nodes[i].ELEVATION, 3)} m`, onPick: i => select(res.nodes[i].NODE_ID) });
    lineChart($('#grad'), [{ label: 'GRADIENT', color: COLORS.a, xs: km, ys: res.nodes.map(n => n.GRADIENT), dots: true }],
      { xlabel: 'distance from downstream end (m)', ylabel: 'm/m', mark, tip: i => `${tip(i)}<br>GRADIENT ${f(res.nodes[i].GRADIENT, 5)}`, onPick: i => select(res.nodes[i].NODE_ID) });
    lineChart($('#topo'), ['W', 'S', 'E'].map((d, k) => ({ label: 'TOPO_' + d, color: [COLORS.a, COLORS.b, COLORS.c][k], xs: km, ys: res.nodes.map(n => n['TOPO_' + d]), dots: true })),
      { xlabel: 'distance from downstream end (m)', ylabel: 'degrees', mark, height: 220, tip: i => `${tip(i)}<br>W ${f(res.nodes[i].TOPO_W, 2)}° · S ${f(res.nodes[i].TOPO_S, 2)}° · E ${f(res.nodes[i].TOPO_E, 2)}°`, onPick: i => select(res.nodes[i].NODE_ID) });
    $('#table').innerHTML = `<table class="tbl"><tr><th>Row</th><th class="num">Distance</th><th class="num">Elev.</th><th class="num">Aspect</th><th class="num">Width</th><th class="num">Topo W</th><th class="num">S</th><th class="num">E</th><th class="num">LC L1</th><th class="num">LC R1</th></tr>
      ${list(res.step6, (r, i) => `<tr class="click" data-i="${i}"><td>${i + 1}${res.nodes[i].NODE_ID === sel ? ' ◀' : ''}</td><td class="num">${r.distance}</td><td class="num">${f(r.elevation)}</td><td class="num">${f(r.aspect, 1)}</td><td class="num">${f(r.wetted_width)}</td><td class="num">${f(r.topo_w)}</td><td class="num">${f(r.topo_s)}</td><td class="num">${f(r.topo_e)}</td><td class="num">${f(r.lc_left[0], 0)}</td><td class="num">${f(r.lc_right[0], 0)}</td></tr>`)}</table>`;
    if (recompute) $('#pyout').innerHTML = res.warnings.length ? `<span class="static-note">Step 6 warnings: ${esc(res.warnings.join('; '))}</span>` : '';
  }

  function drawNode() {
    const [ph, sh] = setHeights();
    pick = drawPlan($('#plan'), scene, res, sel, ph);
    drawSection($('#section'), scene, res, sel, sh);
    const i = res.nodes.findIndex(n => n.NODE_ID === sel), n = res.nodes[i], r = res.step6[i];
    $('#nodeLabel').textContent = `NODE_ID ${sel} (row ${i + 1} of ${res.nodes.length})`;
    $('#nodeInfo').innerHTML = `<dl class="kv">
      <dt>Stream km / azimuth</dt><dd>${f(n.STREAM_KM, 3)} km · ${f(n.STRM_AZMTH, 1)}°</dd>
      <dt>Channel width (left + right)</dt><dd>${f(n.CHANWIDTH)} m (${f(n.LEFT)} + ${f(n.RIGHT)})</dd>
      <dt>ELEVATION / Z_NODE / GRADIENT</dt><dd>${f(n.ELEVATION, 3)} m / ${f(n.Z_NODE, 3)} m / ${f(n.GRADIENT, 5)}</dd>
      <dt>TOPO W / S / E</dt><dd>${f(n.TOPO_W)}° at ${f(n.TOPO_W_DIST, 0)} m / ${f(n.TOPO_S)}° at ${f(n.TOPO_S_DIST, 0)} m / ${f(n.TOPO_E)}° at ${f(n.TOPO_E_DIST, 0)} m</dd></dl>
      <h3>Step 6 zones for this node (land cover = height in cm, + 1)</h3>${rowTable(r)}`;
  }

  function select(id) { sel = id; render(true, false); }

  let pending = 0;
  const schedule = () => { cancelAnimationFrame(pending); pending = requestAnimationFrame(() => render(true)); };
  $('#ctls').addEventListener('input', e => {
    const el = e.target, k = el.dataset.p;
    if (el.id === 'variant') { p.step6_variant = el.value; schedule(); return; }
    if (!k) return;
    p[k] = el.type === 'checkbox' ? (el.checked ? 1 : 0) : Number(el.value);
    const q = spec.params.find(x => x.name === k), b = document.querySelector(`[data-v="${k}"]`);
    if (b) b.textContent = `${p[k]}${q.unit && q.unit !== 'cells' ? ' ' + q.unit : ''}`;
    schedule();
  });
  $('#reset').addEventListener('click', () => { Object.assign(p, spec.defaults); $('#ctls').querySelector('#variant').value = p.step6_variant;
    $('#ctls').querySelectorAll('[data-p]').forEach(el => { if (el.type === 'checkbox') el.checked = !!p[el.dataset.p]; else el.value = p[el.dataset.p]; el.dispatchEvent(new Event('input', { bubbles: true })); }); });
  $('#node').addEventListener('input', e => { sel = res.nodes[+e.target.value].NODE_ID; drawNode(); });
  $('#plan').addEventListener('click', e => {
    const rect = e.target.getBoundingClientRect(), w = pick(e.clientX - rect.left, e.clientY - rect.top);
    let best = res.nodes[0]; for (const n of res.nodes) if (Math.hypot(n.X - w.x, n.Y - w.y) < Math.hypot(best.X - w.x, best.Y - w.y)) best = n;
    select(best.NODE_ID);
  });
  $('#table').addEventListener('click', e => { const tr = e.target.closest('tr[data-i]'); if (tr) select(res.nodes[+tr.dataset.i].NODE_ID); });
  $('#csv').addEventListener('click', () => download('step6_demo_reach.csv', step6Csv(res), 'text/csv'));
  $('#pycheck').addEventListener('click', async () => {
    const out = $('#pyout');
    if (isStatic()) { out.innerHTML = needsServer('Running the same reach in Python'); return; }
    out.textContent = 'Running the original Step-script functions in Python...';
    try {
      const py = await api('/run', { body: p });
      const d = maxDiff({ nodes: res.nodes, step6: res.step6 }, { nodes: py.nodes, step6: py.step6 });
      out.innerHTML = `<span class="${d.d < 1e-9 ? 'ok' : 'err'}">Python and browser ${d.d < 1e-9 ? 'agree' : 'differ'}:</span> largest relative difference ${d.d.toExponential(2)}${d.at ? ` (at ${esc(d.at)})` : ''} over ${py.nodes.length} nodes.`;
    } catch (err) { out.innerHTML = `<span class="err">${esc(err.message)}</span>`; }
  });
  addEventListener('resize', () => { if (location.hash.startsWith('#/demo') && res) drawNode(); });
  render(false);
});
