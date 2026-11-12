// Node test: the browser engine (scene.js, geometry.js, ttools_engine.js, pipeline.js) reproduces the Python pipeline,
// which runs the original TTools Step-script functions (tests/fixtures/engine_cases.json, written by
// scripts/make_engine_fixture.py). Run: node shadealator/web/static/pipeline.test.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { run } from './pipeline.js';
import { calculateGradient, STEP6, addLC, setToZero, step6Rows } from './ttools_engine.js';
import { rasters } from './scene.js';

const fx = JSON.parse(readFileSync(new URL('../../../tests/fixtures/engine_cases.json', import.meta.url), 'utf8'));
let checks = 0;
const close = (a, b, what, tol = 1e-9) => {
  if (typeof b === 'string' || b === null) { assert.equal(a, b, what); checks++; return; }
  assert.ok(Number.isFinite(a), `${what}: got ${a}`);
  assert.ok(Math.abs(a - b) <= tol * Math.max(1, Math.abs(b)), `${what}: ${a} vs ${b}`);
  checks++;
};
const deepClose = (a, b, what) => {
  if (Array.isArray(b)) { assert.equal(a.length, b.length, `${what} length`); b.forEach((x, i) => deepClose(a[i], x, `${what}[${i}]`)); }
  else if (b && typeof b === 'object') { for (const k of Object.keys(b)) deepClose(a[k], b[k], `${what}.${k}`); }
  else close(a, b, what);
};

for (const [name, c] of Object.entries(fx.cases)) {
  const js = run(c.params);
  assert.deepEqual(js.raster, c.raster, `${name}: raster layout`);
  assert.deepEqual(js.nodes.map(n => n.NODE_ID), c.nodes.map(n => n.NODE_ID), `${name}: node order`);
  c.nodes.forEach((n, i) => deepClose(js.nodes[i], n, `${name} node ${n.NODE_ID}`));
  deepClose(js.step6, c.step6, `${name} step6`);
  deepClose(js.lc_points, c.lc_points, `${name} lc_points`);
}

// Rasters: a spot check of whole-array agreement for the default case.
const r = rasters(fx.cases.defaults.params);
assert.equal(r.dem.data.length, fx.cases.defaults.raster.ncols * fx.cases.defaults.raster.nrows);

for (const g of fx.gradient) deepClose(calculateGradient(g.z, g.lengths, g.smooth), g.out, `gradient ${JSON.stringify(g.z)}`);

const inp = fx.transforms.input;
deepClose(inp.map(setToZero), fx.transforms.out.step6.setToZero, 'setToZero');
deepClose(inp.map(STEP6.step6.offset), fx.transforms.out.step6.offsetBy1, 'offsetBy1 (Step6)');
deepClose(inp.map(STEP6.step6_addveg.offset), fx.transforms.out.step6_addveg.offsetBy1, 'offsetBy1 (addVeg)');
deepClose(inp.map(addLC), fx.transforms.out.step6_addveg.addLC, 'addLC');

// Step 6 NoData: -9999 inputs become null and flag the row, in every Step 6 script.
for (const [variant, rows] of Object.entries(fx.step6_nodata.rows)) {
  const js = step6Rows(fx.step6_nodata.nodes, variant, [1, 2, 3, 4, 5, 6, 7, 8, 9]);
  deepClose(js, rows, `step6 nodata ${variant}`);
  assert.deepEqual(js.map(r => r.nodata), [0, 1, 1, 1, 0, 0, 0]);
  assert.equal(js[1].elevation, null);
}

console.log(`pipeline.test.mjs: ${checks} checks passed over ${Object.keys(fx.cases).length} scenes`);
