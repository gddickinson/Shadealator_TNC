# TTools & Shade-a-lator

A collection of ArcGIS Python scripts for stream temperature modeling and riparian shade analysis using the Shade-a-lator model.

## Overview

This repository contains Python scripts and tools for running the Shade-a-lator model from within ArcGIS. The Shade-a-lator model was originally developed by Y.D. Chen and the Oregon Department of Environmental Quality (ODEQ) as part of their HeatSource model version 6. This implementation interfaces with ArcGIS using TTools (also developed by ODEQ) to estimate input values for shade calculations from GIS data.

The workflow consists of several sequential steps that:
1. Process stream centerlines and banks
2. Create observation points (nodes) along streams
3. Sample topographic and vegetation characteristics
4. Calculate shade conditions using the Shade-a-lator model
5. Export results back to ArcGIS

## System Requirements

- ArcGIS 10.3.1 or higher (tested on ArcGIS 10.3.1)
- Python 2.7 (specifically the version installed with ArcGIS)
- Microsoft Excel (with macros enabled)
- Required Python packages:
  - openpyxl
  - pypiwin32 (for Excel automation)
  - xlrd
  - Other standard libraries (numpy, math, etc.)

## Installation

1. Clone or download this repository
2. Ensure you have the required Python packages installed in ArcGIS's Python environment:

```bash
cd C:\Python27\ArcGIS10.x\Scripts
pip.exe install openpyxl pypiwin32
```

3. Add Georges_Tools.tbx to your ArcMap toolbox

## Required Input Data

- Stream centerline feature class (with fields: OBJECTID, Shape, Shape_Length, Id)
- Right bank feature class (with fields: OBJECTID, Shape, Shape_Length, LEFT_FID, RIGHT_FID)
- Left bank feature class (with fields: OBJECTID, Shape, Shape_Length, LEFT_FID, RIGHT_FID)
- Elevation raster (e.g., LiDAR DEM)
- Land cover/vegetation height raster

## Workflow Steps

### Step 1: Segment Stream (Step1_SegmentStream.py)
Creates evenly spaced nodes along the stream centerline with unique IDs.

### Step 2: Measure Channel Width (Step2_MeasureChannelWidth.py)
Calculates channel width at each node by measuring the distance between left and right bank features.

### Step 3: Sample Elevation & Gradient (Step3_SampleElevationGradient_Array.py)
Samples elevation at each node and calculates stream gradient between nodes.

### Step 4: Measure Topographic Angles (Step4_MeasureTopographicAngles.py)
Calculates the maximum topographic elevation and slope angle from each node in different directions.

### Step 5: Sample Land Cover (Step5_Sample_Landcover_PointMethod_Array.py)
Samples land cover/vegetation height in multiple directions at different distances from each node.

### Step 6: Interact with Shade-a-lator (Step6_Interact_with_Shade.py)
Exports data to Excel and runs the Shade-a-lator model using Excel macros. Several variations of this script exist to handle different vegetation configurations.

### Step 7: Import Shade Data (Step7_Import_shadeData.py)
Imports the Shade-a-lator results back into ArcGIS as a feature class.

## File Descriptions

- **Georges_Tools.tbx**: ArcGIS toolbox containing the tools for each step
- **ExcelToTable.py/pyc**: Utility to convert Excel files to ArcGIS tables
- **Step*.py**: Python scripts for each step in the workflow
- **blank.xlsx**, **blankMainMenu.xlsx**: Template Excel files for data transfer
- **output.xlsx**, **output2.xlsx**: Output Excel files containing intermediate results
- **Shade-a-lator_Instructions.docx**: Detailed instructions for setup and usage
- **get-pip.py**: Utility for installing pip in Python environments

## Running the Tools

1. Open ArcMap and add the Georges_Tools.tbx toolbox
2. Run each tool in sequence (Step 1, Step 2, etc.)
3. Follow the prompts for each tool to specify input data and parameters

The tools will create several output feature classes during processing:
- nodes_fc: Points along the stream centerline
- topo_fc: Points with topographic measurement information
- lc_point_fc: Points with land cover sample information
- shade_fc: Final output with calculated shade values

## Credits

- The Shade-a-lator model was developed by Y.D. Chen and the Oregon Department of Environmental Quality
- TTools was developed by the Oregon Department of Environmental Quality
- These scripts were modified by "George" for ArcGIS integration

## References

- Chen, Y.D. (1996). Hydrologic and water quality modeling for aquatic ecosystem protection and restoration in forest watersheds: a case study of stream temperature in the Upper Grande Ronde River, Oregon. PhD dissertation. University of Georgia. Athens, GA.
- Chen, Y.D., Carsel, R.F., McCutcheon, S.C., and Nutter, W.L. (1998). Stream temperature simulation of forested riparian areas: I. watershed-scale model development. Journal of Environmental Engineering. April 1998. pp 304-315.
- Chen, Y.D., Carsel, R.F., McCutcheon, S.C., and Nutter, W.L. (1998). Stream temperature simulation of forested riparian areas: II. model application. Journal of Environmental Engineering. April 1998. pp 316-328.
- Boyd, M., and Kasper, B. 2003. Analytical methods for dynamic open channel heat and mass transfer: Methodology for heat source model Version 7.0.

## GitHub Repository
TTools original repository: https://github.com/rmichie/TTools

# ArcGIS TTools - Georges_Tools.tbx README

This toolbox (`Georges_Tools.tbx`) contains a collection of ArcGIS tools designed for stream temperature modeling. The toolbox appears to be based on or adapted from the "TTools" (Temperature Tools) framework, which is commonly used for preparing spatial data for stream temperature modeling, particularly for Heat Source models.

## Overview

The toolbox contains a sequential workflow of scripts (Script1 through Script7) designed to generate and process stream network data for temperature modeling. Each script builds upon the outputs of previous scripts, creating a comprehensive dataset that characterizes stream channels, riparian vegetation, and topography.

## Scripts in the Toolbox

### Script1: Segment Stream
Creates evenly spaced points along stream centerlines.
- **Inputs**: Stream centerline polyline, spacing between nodes in meters, options for continuous stream kilometers
- **Outputs**: Point feature class with fields including NODE_ID, STREAM_ID, STREAM_KM, LONGITUDE, LATITUDE, and STREAM_AZMTH (azimuth in flow direction)

### Script2: Measure Channel Widths
Calculates channel width measurements at each node.
- **Inputs**: Nodes feature class (from Script1), right bank feature class, left bank feature class
- **Outputs**: Updated nodes feature class with CHANWIDTH, LEFT, and RIGHT fields added

### Script3: Sample Stream Elevations/Gradient
Samples elevation and calculates stream gradient.
- **Inputs**: Nodes feature class, search cell parameters, elevation raster
- **Outputs**: Updated nodes feature class with ELEVATION and GRADIENT fields

### Script4: Measure Topographic Angles
Calculates topographic shading angles from different directions.
- **Inputs**: Nodes feature class, direction parameters, elevation raster
- **Outputs**: Updated nodes feature class with topographic shade angles, plus a new point feature class showing maximum elevation locations

### Script5: Sample Landcover - Star Pattern, Point Method
Samples land cover in transects extending from each stream node.
- **Inputs**: Nodes feature class, transect parameters, land cover and elevation rasters
- **Outputs**: Updated nodes feature class with land cover data, plus sample points feature class

### Script6: Export Data to Shadelator
Exports processed node data to "shadelator" format for shade analysis.
- **Inputs**: Node feature class and various shade analysis parameters
- **Outputs**: Data formatted for shade analysis

### Script7: Import Shade Data
Imports shade calculation results.
- **Inputs**: Excel data sheet, shade data filename, and output path
- **Outputs**: Shapefile with shade calculation results

### excelToShapefile
A model that converts tabular Excel data to shapefile format.

## Typical Workflow

1. Create evenly spaced nodes along stream centerlines
2. Measure channel widths at each node
3. Sample stream elevations and calculate gradients
4. Calculate topographic shading angles
5. Sample land cover along transects from each node
6. Export data for shade analysis
7. Import shade calculation results

## Required Data

- Stream centerline polylines
- Stream bank (left and right) polylines
- Digital elevation model (DEM) raster
- Land cover/vegetation height raster
- Optional: canopy cover, LAI (Leaf Area Index), overhang rasters

## Technical Notes

- The tools were designed for the Silver Creek watershed, as indicated by file paths
- Coordinate systems used include NAD_1983_UTM_Zone_11N
- The sample data appears to include streams in Idaho
- Many parameters are configurable (e.g., transect spacing, number of directions)
- The tools can handle processing data in blocks for large datasets

This toolbox represents a comprehensive workflow for preparing spatial data for stream temperature and shade modeling, particularly useful for understanding thermal dynamics in river systems and riparian restoration planning.
