// Home: hero, real counts, cards to the pages, and a plain statement of what runs where.
import { api, app, route } from './core.js';

route('home', async () => {
  const info = await api('/info');
  app().innerHTML = `
  <section class="hero">
    <p class="kicker">Riparian shade · stream temperature · ArcGIS</p>
    <h1 class="glow">Shade-a-lator for ArcMap</h1>
    <p class="lead">A seven-step ArcGIS toolbox (Georges_Tools.tbx) that turns a stream centreline, its banks, a DEM and a
      vegetation-height raster into inputs for Shade-a-lator, the riparian shade model by Y. D. Chen and the Oregon
      Department of Environmental Quality (Heat Source 6), then brings the shade back into the map. Built for The Nature
      Conservancy's Silver Creek work in Idaho, using TTools by Ryan Michie (ODEQ).</p>
    <a class="btn" href="#/demo">Try the demo reach</a><a class="btn alt" href="#/workflow">How it works</a>
  </section>
  <div class="tiles">
    <div class="tile"><b>${info.steps}</b><span>toolbox steps</span></div>
    <div class="tile"><b>${info.silver_creek_nodes}</b><span>Silver Creek nodes with modelled shade</span></div>
    <div class="tile"><b>${(info.silver_creek_mean_shade * 100).toFixed(1)}%</b><span>mean shade on that run (1 Aug 2016)</span></div>
    <div class="tile"><b>${info.demo_parameters}</b><span>demo parameters you can move</span></div>
  </div>
  <div class="grid">
    <a class="card" href="#/workflow"><b>Workflow</b><small>Steps 1-7</small><span>What each script does, its inputs and outputs, the formula behind it, and what it needs to run.</span></a>
    <a class="card" href="#/demo"><b>Demo reach</b><small>runs in your browser</small><span>A synthetic meandering stream in a valley: move the walls and the trees and watch TTools recompute nodes, gradients, topographic angles and land-cover samples.</span></a>
    <a class="card" href="#/results"><b>Silver Creek</b><small>the committed run</small><span>Shade for ${info.silver_creek_nodes} nodes from output2.xlsx, with the inputs Shade-a-lator was given (output.xlsx).</span></a>
    <a class="card" href="#/about"><b>About</b><small>run it, credits</small><span>Running the toolbox in ArcMap, running this web app, and who wrote what.</span></a>
  </div>
  <div class="callout">
    <b>What runs here, and what cannot.</b> The geometry and raster maths of Steps 1-5 and the data preparation of
    Step 6 run in your browser (a JavaScript port checked number-for-number against the scripts' own Python functions).
    Reading ArcGIS feature classes and rasters needs <code>arcpy</code>, and the shade calculation itself is VBA inside
    the Excel workbook <code>shade_GD.xlsm</code>, which is not in this repository: those parts are explained, and the
    Silver Creek page shows the shade that workbook produced.
  </div>`;
});
