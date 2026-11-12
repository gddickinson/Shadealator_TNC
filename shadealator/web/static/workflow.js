// Workflow: the seven toolbox steps from /api/steps, with what each needs and what the web reproduces.
import { api, app, esc, isStatic, list, route } from './core.js';

const REPO = 'https://github.com/gddickinson/Shadealator_TNC/blob/main/';

function needBadges(needs) {
  return list(needs, n => `<span class="badge ${/not in this repository/.test(n) ? 'no' : 'need'}">needs ${esc(n)}</span>`);
}

route('workflow', async () => {
  const [{ steps }, info] = await Promise.all([api('/steps'), api('/info')]);
  const arcpyNote = isStatic()
    ? 'This is the static site: nothing here can open ArcGIS data. The ArcGIS steps run only inside ArcMap.'
    : (info.arcpy_available
      ? 'arcpy is importable on this computer, but this app still only runs the pure maths: run the toolbox from ArcMap for real data.'
      : 'arcpy is not installed on this computer, so the ArcGIS parts of each step (reading and writing feature classes and rasters) cannot run here. This app runs their pure maths on a synthetic reach instead.');
  app().innerHTML = `
  <p class="kicker">Georges_Tools.tbx · Script1-Script7</p>
  <h1>Workflow</h1>
  <p class="lead">Each step is one Python script run from the ArcMap toolbox, in order. Steps 1-5 are TTools (ODEQ) with
    George's fixes; Steps 6 and 7 are George's bridge to the Shade-a-lator Excel model and back.</p>
  <div class="notice"><b>ArcGIS and Excel.</b> ${esc(arcpyNote)}
    ${info.excel_model_in_repo ? '' : ' The Shade-a-lator workbook (shade_GD.xlsm) that computes the shade is not in the repository, so Step 6\'s shade calculation cannot be reproduced anywhere outside George\'s setup.'}</div>
  ${list(steps, s => `
  <section class="panel step" id="step${s.n}">
    <div class="num">${s.n}</div>
    <div>
      <h2 style="margin-top:0">${esc(s.title)}</h2>
      <p class="small mute"><a href="${REPO}${encodeURIComponent(s.file)}" target="_blank" rel="noopener">${esc(s.file)}</a> · ${esc(s.author)}</p>
      <p>${esc(s.does)}</p>
      ${s.formula ? `<div class="eq">${esc(s.formula)}</div>` : ''}
      <div class="two">
        <div><h3>Inputs</h3><ul>${list(s.inputs, i => `<li>${esc(i)}</li>`)}</ul></div>
        <div><h3>Outputs</h3><ul>${list(s.outputs, o => `<li>${esc(o)}</li>`)}</ul></div>
      </div>
      <p>${needBadges(s.needs)}<span class="badge web">on the web</span> ${esc(s.reproduced)}</p>
    </div>
  </section>`)}
  <h2>Order of the data</h2>
  <p>Step 1 writes nodes with the upstream end first. Step 3 computes gradients in that order (upstream first) and
    Step 6 writes rows in it too, with Distance measured from the first row along STREAM_KM. Before the November 2026
    fixes Step 6 wrote Distance as row x 50 m, a fixed 1.0 m incision and -9999 (off-DEM) values as 0; the committed
    Silver Creek run was made that way.</p>
  <p><a class="btn" href="#/demo">See it on the demo reach</a></p>`;
});
