"""The seven toolbox steps, as documented in the README, the script headers and Shade-a-lator_Instructions.docx.

For each step: what it does, its inputs/outputs (from the script header comments), what it needs to run (arcpy,
Excel), which of its calculations this package reproduces without ArcGIS, and the formula, where there is one.
"""

STEPS = [
    {
        "n": 1, "title": "Segment stream", "file": "Step1_SegmentStream.py", "author": "Ryan Michie (TTools 0.953)",
        "does": "Places nodes at a fixed spacing along each stream centreline, measured from the downstream end, and "
                "records the stream azimuth (flow direction) at each node.",
        "inputs": ["Stream centreline polylines", "Node spacing (m)", "Continuous stream km flag",
                   "Optional: check digitised direction against an elevation raster"],
        "outputs": ["Point feature class: NODE_ID, STREAM_ID, STREAM_KM, LENGTH, LONGITUDE, LATITUDE, STRM_AZMTH"],
        "needs": ["arcpy"],
        "reproduced": "Node placement and azimuth (geometry.py / geometry.js, arcpy positionAlongLine written out).",
        "formula": "azimuth = degrees(atan2(x_down - x_up, y_down - y_up)), +360 if negative; "
                   "x/y_up and x/y_down are half a node spacing up- and downstream",
    },
    {
        "n": 2, "title": "Measure channel width", "file": "Step2_MeasureChannelWidth.py",
        "author": "Ryan Michie (TTools 0.911)",
        "does": "Measures the distance from each node to the left and right bank lines; their sum is the channel width.",
        "inputs": ["Nodes (Step 1)", "Right bank polyline", "Left bank polyline"],
        "outputs": ["CHANWIDTH, LEFT, RIGHT (m) on the nodes"],
        "needs": ["arcpy"],
        "reproduced": "Point-to-polyline distances (arcpy distanceTo written out).",
        "formula": "CHANWIDTH = distance(node, left bank) + distance(node, right bank)",
    },
    {
        "n": 3, "title": "Sample elevation and gradient", "file": "Step3_SampleElevationGradient_Array.py",
        "author": "Ryan Michie (TTools 0.97)",
        "does": "Takes the lowest DEM value within a few cells of each node as the stream elevation, then the gradient "
                "between consecutive nodes. With smoothing on, a node higher than the one upstream is skipped and the "
                "drop is spread over the longer distance. End effect (as in upstream TTools): the smoothing distance is "
                "summed over the nodes downstream of the current one, so near the downstream end it runs short, and "
                "nodes after a hollow that never drains keep a gradient of 0.",
        "inputs": ["Nodes", "Search cells around each node", "Smoothing flag", "Elevation raster and its z units"],
        "outputs": ["ELEVATION, Z_NODE (the node's own cell), GRADIENT on the nodes"],
        "needs": ["arcpy (raster reading)"],
        "reproduced": "The script's own sample_raster() and calculate_gradient(), run on a raster through a stand-in "
                      "for arcpy.RasterToNumPyArray.",
        "formula": "GRADIENT = (z_upstream - z) / distance",
    },
    {
        "n": 4, "title": "Measure topographic angles", "file": "Step4_MeasureTopographicAngles.py",
        "author": "Ryan Michie (TTools 0.97)",
        "does": "Walks out from each node along fixed azimuths (west, south, east, or all eight directions) one cell "
                "at a time, and keeps the steepest angle up to the terrain: the topographic shade angle.",
        "inputs": ["Nodes", "Directions: [W, S, E] or [NE, E, SE, S, SW, W, NW, N]", "Maximum search distance (km)",
                   "Elevation raster and z units"],
        "outputs": ["TOPO_W, TOPO_S, TOPO_E (deg) on the nodes", "Point feature class at each maximum"],
        "needs": ["arcpy (raster reading)"],
        "reproduced": "The script's own get_topo_angles() and build_search_array(), with the stand-in arcpy.",
        "formula": "angle = max over d of degrees(atan((z(d) - z_node) / d)), d = cell, 2 cells, ... < search distance",
    },
    {
        "n": 5, "title": "Sample land cover", "file": "Step5_Sample_Landcover_PointMethod_Array.py",
        "author": "Ryan Michie (TTools 0.997, star pattern / point method)",
        "does": "Samples the land-cover (vegetation height or code) and elevation rasters at points along transects "
                "from each node. This copy adds a 'perp' option: two transects at right angles to the stream "
                "(left bank = azimuth - 90, right bank = azimuth + 90), for shade_ver40b04a06.xlsm.",
        "inputs": ["Nodes", "Transects per node, samples per transect, sample spacing (m)",
                   "Land-cover raster (code or height)", "Optional canopy / LAI / k / overhang rasters",
                   "Elevation raster"],
        "outputs": ["LC_T*_S*, ELE_T*_S* on the nodes", "Point feature class of every sample"],
        "needs": ["arcpy (raster reading)"],
        "reproduced": "The script's own create_lc_point_list() and sample_raster() (perp = True), with the stand-in "
                      "arcpy.",
        "formula": "sample = node + zone x spacing x (sin(dir), cos(dir)), zone = 1..9",
    },
    {
        "n": 6, "title": "Export to Shade-a-lator and run it", "file": "Step6_Interact_with_Shade.py",
        "author": "George (2017), with three variants: _addVeg, _addVegLeftBank, _addVegRightBank",
        "does": "Copies the node fields into the Shade-a-lator 'Main Menu' template (blankMainMenu.xlsx -> "
                "output.xlsx) with the run settings, then opens shade_GD.xlsm in Excel and runs its macros, which "
                "compute shade and write it to output2.xlsx. Off-raster samples (-9999) are written as blank cells "
                "and the node is flagged in a NODATA column; other negative elevations and topographic angles are "
                "set to 0; land-cover values get +1 (Shade-a-lator has no riparian code 0). Distance comes from "
                "STREAM_KM and channel incision from an INCISION field if present (else row x 50 m and 1.0 m, with "
                "a warning). Shared helpers: Step6_shade_inputs.py, kept next to the Step 6 scripts. The addVeg variants set zone 1 "
                "to 1000 wherever it is under 500 (10 m and 5 m when the land cover is height in cm, as in the "
                "maxheight_cm_int raster named in Step 5's settings) on both, the left or the right bank, and cap "
                "codes at 5000.",
        "inputs": ["Nodes with Steps 1-5 fields", "Run name, start date, days, latitude, longitude, time zone, "
                   "daylight savings, riparian zone width, shade method, veg codes, cloud cover, Bras visibility, "
                   "Ryan-Stolzenbach factor, elevation or zone width, riparian extinction"],
        "outputs": ["output.xlsx (Shade-a-lator inputs)", "output2.xlsx (SHADE per node)"],
        "needs": ["arcpy", "Windows + Excel (win32com)", "shade_GD.xlsm (not in this repository)"],
        "reproduced": "The column layout, the scripts' own setToZero / offsetBy1 / addLC and Step6_shade_inputs.py. The shade calculation "
                      "itself is VBA inside shade_GD.xlsm, which is not in the repository, so it is not reproduced.",
        "formula": "",
    },
    {
        "n": 7, "title": "Import shade data", "file": "Step7_Import_shadeData.py", "author": "George (ModelBuilder export)",
        "does": "Converts output2.xlsx to a dBASE table (data/outdbf.dbf), makes an XY event layer from its "
                "longitude/latitude (NAD83), saves it as a shapefile and adds it to the open map.",
        "inputs": ["Excel data sheet (output2.xlsx)", "Shade feature class name", "Output folder"],
        "outputs": ["shade_fc shapefile: STREAM_ID, FID, ELEVATION, LATITUDE, LONGITUDE, SHADE"],
        "needs": ["arcpy", "ArcMap (arcpy.mapping)"],
        "reproduced": "Not needed on the web: the Silver Creek page reads output2.xlsx directly.",
        "formula": "",
    },
]
