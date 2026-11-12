# INTERFACE.md: navigation map

## ArcGIS toolbox (ArcMap, Python 2.7; needs arcpy)
| File | Purpose |
|---|---|
| `Georges_Tools.tbx` | ArcMap toolbox wiring Script1-Script7 to the files below |
| `Step1_SegmentStream.py` | TTools: nodes along the centreline, stream azimuth |
| `Step2_MeasureChannelWidth.py` | TTools: CHANWIDTH / LEFT / RIGHT from bank lines |
| `Step3_SampleElevationGradient_Array.py` | TTools: ELEVATION (window minimum), Z_NODE, GRADIENT (`calculate_gradient`) |
| `Step4_MeasureTopographicAngles.py` | TTools: TOPO_W/S/E (`get_topo_angles`, `build_search_array`) |
| `Step5_Sample_Landcover_PointMethod_Array.py` | TTools: LC_/ELE_ samples on transects (`create_lc_point_list`, `sample_raster`; `perp` option) |
| `Step6_Interact_with_Shade*.py` | Write Shade-a-lator Main Menu (output.xlsx), run shade_GD.xlsm macros (Excel, win32com); variants addVeg / LeftBank / RightBank |
| `Step6_shade_inputs.py` | Pure helpers for Step 6 (no arcpy): `NodataTracker`, `keep_blank`, `node_distances`, `incisions`; keep next to the Step 6 scripts |
| `Step7_Import_shadeData.py` | output2.xlsx -> dbf -> XY layer -> shapefile in the map |
| `ExcelToTable.py` | Esri Excel-to-table tool |
| `blank*.xlsx`, `output.xlsx`, `output2.xlsx` | Templates and the committed Silver Creek run (inputs / shade) |
| `data/` | outdbf.dbf (output2.xlsx as dBASE) and its metadata |

## `shadealator/` (Python 3, no arcpy)
| Module | Contents |
|---|---|
| `ttools_source.py` | `load(script, names)`, `fn`, `set_globals`: compile chosen functions from a Step script via `ast` |
| `fake_arcpy.py` | `FakeRaster`, `Point`, `GetRasterProperties_management`, `RasterToNumPyArray` stand-ins |
| `synthetic.py` | `PARAMS`/`DEFAULTS` (demo parameters, single source), `lines`, `extent`, `ground`, `cover_cm`, `rasters` |
| `geometry.py` | Step 1 `create_nodes`, `position_along_line`; Step 2 `channel_width`, `distance_to_polyline` |
| `pipeline.py` | `run(params)`: Steps 1-6 on the synthetic reach using the original functions; `step6_rows` |
| `results.py` | `load()`: Silver Creek settings, per-node inputs + shade, summary |
| `workflow.py` | `STEPS`: per-step description, inputs/outputs, needs, what the web reproduces |
| `web/app.py` | FastAPI: `/api/info`, `/steps`, `/scene_spec`, `/results` (exported statically), POST `/run` (local only) |
| `web/static/` | `core.js` (router, kit), `main.js`, pages `home.js` `workflow.js` `demo.js` (+`demo_draw.js`) `results.js` `about.js`, `charts.js`; engine `scene.js` `geometry.js` `ttools_engine.js` `pipeline.js` (ports of the Python above), `pipeline.test.mjs`, `static_api.js` |

Connections: `pipeline` -> `ttools_source` (+`fake_arcpy`) -> Step scripts; `pipeline` -> `synthetic`, `geometry`.
`web/app` -> `pipeline`, `results`, `synthetic`, `workflow`. JS `pipeline.js` -> `scene.js`, `geometry.js`, `ttools_engine.js`.

## Scripts and tests
| File | Purpose |
|---|---|
| `run_web.py` | uvicorn on 127.0.0.1:8120 |
| `scripts/build_static.py` | export the static site (site/) |
| `scripts/screenshots.py` | Playwright smoke test / README images (docs/img) |
| `scripts/make_engine_fixture.py` | writes `tests/fixtures/engine_cases.json` (Python results for the JS test) |
| `tests/test_ttools_source.py` | extracted original functions, regression tests for the fixes |
| `tests/test_step6_inputs.py` | Step 6 NoData / distance / incision (module, scripts, web pipeline) |
| `tests/test_web.py` | API, static build, fixture currency, node engine test |
