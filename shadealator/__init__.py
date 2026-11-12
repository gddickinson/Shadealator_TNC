"""Shade-a-lator TNC: arcpy-free helpers around the TTools / Shade-a-lator ArcGIS scripts (for the web interface).

ttools_source  load pure functions from the original Step*.py scripts (ast; scripts not executed)
fake_arcpy     minimal stand-in for the arcpy raster calls those functions make
synthetic      synthetic stream reach (centreline, banks, DEM, vegetation raster) and demo parameters
geometry       Step 1 node/azimuth and Step 2 channel width without arcpy geometry
pipeline       Steps 1-6 on the synthetic reach, using the original functions
results        the committed Silver Creek run (output.xlsx inputs, output2.xlsx shade)
web/           FastAPI app and static front end
"""
