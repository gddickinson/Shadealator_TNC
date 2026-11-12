// About: what the project is, how to run the toolbox and the web app, credits and references (from the README and
// Shade-a-lator_Instructions.docx).
import { app, route } from './core.js';

route('about', () => {
  app().innerHTML = `
  <p class="kicker">About</p>
  <h1>Shade-a-lator TNC</h1>
  <p class="lead">ArcGIS Python scripts that run the Shade-a-lator riparian shade model from within ArcMap, using TTools
    to estimate its inputs from GIS data. Written for stream temperature work on Silver Creek (Idaho) for The Nature
    Conservancy in 2017.</p>
  <h2>Run the toolbox (ArcMap)</h2>
  <ol>
    <li>ArcMap 10.3.1 or later with its Python 2.7, Microsoft Excel with macros enabled, and the
      <code>openpyxl</code> and <code>pypiwin32</code> packages (<code>pip.exe install openpyxl pypiwin32</code> in
      ArcGIS's Python Scripts folder).</li>
    <li>The scripts folder with the Step scripts, <code>Step6_shade_inputs.py</code> (helpers the Step 6 scripts import), the Excel templates and <code>shade_GD.xlsm</code> (the Shade-a-lator
      workbook with George's data-transfer macros; not in this repository). Step 6 and 7 look for them under
      <code>C:\\Google Drive\\SiCr_Digitization\\scripts</code> (Step 6 addVeg variants: <code>C:\\arcgis\\shade_a_lator\\scripts</code>).</li>
    <li>Add <code>Georges_Tools.tbx</code> to ArcMap and run Script1 to Script7 in order, pointing them at the centreline,
      the left and right banks, the DEM and the vegetation-height raster. The result is the <code>shade_fc</code>
      shapefile with FID, STREAM_ID, ELEVATION, LATITUDE, LONGITUDE and SHADE.</li>
  </ol>
  <h2>Run this web app</h2>
<pre>pip install -r requirements-web.txt
python run_web.py            # http://127.0.0.1:8120</pre>
  <p>The local app adds one thing to the static site: <b>Check against Python</b> on the demo page runs the same reach
    through the original Step-script functions in Python and compares every number with the browser's.</p>
  <h2>Credits</h2>
  <ul>
    <li>Shade-a-lator: Y. D. Chen and the Oregon Department of Environmental Quality (Heat Source model version 6).
      For Shade.xls: Greg Pelletier, Washington State Department of Ecology.</li>
    <li>TTools (Steps 1-5): Ryan Michie, ODEQ, GPL v3 (<a href="https://github.com/rmichie/TTools" target="_blank" rel="noopener">github.com/rmichie/TTools</a>).
      The Shade-a-lator and TTools scripts were supplied by Luke Spaete at Boise State University.</li>
    <li>ArcMap integration, Steps 6-7 and fixes to the TTools scripts: George (gddickinson). ExcelToTable.py: Esri.</li>
  </ul>
  <h2>References</h2>
  <ul class="small">
    <li>Chen, Y.D. (1996). Hydrologic and water quality modeling for aquatic ecosystem protection and restoration in forest watersheds: a case study of stream temperature in the Upper Grande Ronde River, Oregon. PhD dissertation, University of Georgia.</li>
    <li>Chen, Y.D., Carsel, R.F., McCutcheon, S.C. and Nutter, W.L. (1998). Stream temperature simulation of forested riparian areas: I. watershed-scale model development. Journal of Environmental Engineering, April 1998, 304-315.</li>
    <li>Chen, Y.D., Carsel, R.F., McCutcheon, S.C. and Nutter, W.L. (1998). Stream temperature simulation of forested riparian areas: II. model application. Journal of Environmental Engineering, April 1998, 316-328.</li>
    <li>Boyd, M. and Kasper, B. (2003). Analytical methods for dynamic open channel heat and mass transfer: methodology for Heat Source model version 7.0.</li>
  </ul>
  <p class="small mute">Licence: GNU GPL v3 (see LICENSE and THIRD_PARTY.md).</p>`;
});
