########################################################################
# TTools
# Step 5: Sample Landcover - Star Pattern, Point Method v 0.997
# Ryan Michie

# Sample_Landcover_PointMethod will take an input point
# feature (from Step 1) and sample input landcover rasters in a user
# specificed number of cardinal directions with point samples spaced
# at a user defined distance moving away from the stream.

# General scripts steps include:
# 1. open nodes fc. iterate and read info from node fc into a dict

# 2. create a list with the x/y and related info for each lc sample
#    calculate the extent bounding box for the entire dataset

# 3. create a list holding the bounding box coords for each block itteration

# 4. loop through each block
    #- sample the raster for all samples in the block
    #- update the node dict
    #- update the node fc
    #- update the lc sample fc
    #- continue to the next block

# INPUTS
# 0: TTools point feature class (nodes_fc)
# 1: Number of transects per node (trans_count)
# 2: Number of samples per transect (transsample_count)
# 3: The distance between transect samples (transsample_distance)
# 4: True/False flag if using heatsource 8 methods (heatsource8)
# 5: Land cover code or height raster (lc_raster)
# 6: input (optional) landcover height z units
#     1. "Feet", 2. "Meters" 3. "None" Float (lc_units)
# 7: OPTIONAL - landcover data type:
#     1."CanopyCover", or 2."LAI" (canopy_data_type)
# 8: OPTIONAL - canopy cover or LAI raster (canopy_raster)
# 9: OPTIONAL - k coeffcient raster (k_raster)
# 10: OPTIONAL - overhang raster (oh_raster)
# 11: Elevation raster (z_raster)
# 12: Elevation raster z units (z_units)
#      1. "Feet", 2. "Meters" 3. "Other"
# 13: Path/name of output sample point file (lc_point_fc)
# 14: OPTIONAL - km distance to process within each array (block_size)
# 15: True/False flag if existing data can be over written (overwrite_data)

# OUTPUTS
# 0. point feature class (edit nodes_fc) - added fields with
#     Landcover and elevation data for each azimuth direction at each node
# 1. point feature class (new) - point at each x/y sample and
#     the sample raster values

# Future Updates
# -Change the node dict so the node is the primary key
# -Build the block list based on the nodes and then build point list itterativly
# instead of building them into one huge list. The huge list results
# in a memory error for large areas
# -Include stream sample in transect count (True/False)
# -Eliminate arcpy and use gdal for reading/writing feature class data

# This version is for manual starts from within python.
# This script requires Python 2.6 and ArcGIS 10.1 or higher to run.

########################################################################

# Import system modules
from __future__ import division, print_function
import sys
import os
import gc
import time
import traceback
from datetime import timedelta
from math import radians, sin, cos, ceil, sqrt
from collections import defaultdict, OrderedDict
import numpy
import arcpy
from arcpy import env

env.overwriteOutput = True

def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'true':
        return True
    else:
        return False

# ----------------------------------------------------------------------
# Start Fill in Data
##nodes_fc = r"C:\Google Drive\SiCr_Digitization\Shade_a_lator\TNC_2017\GIS\SilverCreek_Shade.gdb\SC_nodes_traced_river_upper_section_branch2_2_100m"
##trans_count =10
##transsample_count = 9 # does not include a sample at the stream node
##transsample_distance = 10
##heatsource8 = False
##perp = True # will create 2 transects perpendicular to each stream node (use with shade_ver40b04a06.xlsm)
##sampleID_for_code = True  # Use the sampleID instead of height for the landcover
##lc_raster = r"C:\Google Drive\SiCr_Digitization\Shade_a_lator\TNC_2017\GIS\SilverCreek_Shade.gdb\maxheight_cm_int"
##lc_units = "Meters"
##canopy_data_type = "#" # OPTIONAL This is either 1. "CanopyCover", or 2."LAI"
##canopy_raster = "#" # OPTIONAL This is either canopy cover or a LAI raster
##k_raster = "#" # OPTIONAL This is the k value for LAI
##oh_raster = "#" # OPTIONAL This is the overhang raster
##z_raster = r"C:\Google Drive\SiCr_Digitization\Shade_a_lator\TNC_2017\GIS\SilverCreek_Shade.gdb\maxheight_cm_int"
##z_units = "Meters"
##lc_point_fc = r"C:\Google Drive\SiCr_Digitization\Shade_a_lator\TNC_2017\GIS\SilverCreek_Shade.gdb\SC_nodes_lc_traced_river_upper_section_branch2_2_100m_new"
##block_size = 1 # OPTIONAL defualt to 5
##overwrite_data = True
# End Fill in Data
# ----------------------------------------------------------------------

nodes_fc = arcpy.GetParameterAsText(0)
trans_count = int(arcpy.GetParameterAsText(1))
transsample_count = int(arcpy.GetParameterAsText(2)) # does not include a sample at the stream node
transsample_distance = float(arcpy.GetParameterAsText(3))
heatsource8 = arcpy.GetParameterAsText(4)
heatsource8 = str_to_bool(heatsource8)

perp = arcpy.GetParameterAsText(5) # will create 2 transects perpendicular to each stream node (use with shade_ver40b04a06.xlsm)
perp = str_to_bool(perp)
sampleID_for_code = arcpy.GetParameterAsText(6)  # Use the sampleID instead of height for the landcover
sampleID_for_code = str_to_bool(sampleID_for_code)

lc_raster = arcpy.GetParameterAsText(7)
lc_units = arcpy.GetParameterAsText(8)
canopy_data_type = arcpy.GetParameterAsText(9) # OPTIONAL This is either 1. "CanopyCover", or 2."LAI"
canopy_raster = arcpy.GetParameterAsText(10) # OPTIONAL This is either canopy cover or a LAI raster
k_raster = arcpy.GetParameterAsText(11) # OPTIONAL This is the k value for LAI
oh_raster = arcpy.GetParameterAsText(12) # OPTIONAL This is the overhang raster
z_raster = arcpy.GetParameterAsText(13)
z_units = arcpy.GetParameterAsText(14)
lc_point_fc = arcpy.GetParameterAsText(15)
block_size = int(arcpy.GetParameterAsText(16)) # OPTIONAL defualt to 5
overwrite_data = arcpy.GetParameterAsText(17)
overwrite_data = str_to_bool(overwrite_data)


def nested_dict():
    """Build a nested dictionary"""
    return defaultdict(nested_dict)

def read_nodes_fc(nodes_fc, overwrite_data, addFields):
    """Reads the input point feature class and returns the STREAM_ID,
    NODE_ID, and X/Y coordinates as a nested dictionary"""
    nodeDict = nested_dict()
    incursorFields = ["NODE_ID", "STREAM_ID", "STREAM_KM", "STRM_AZMTH", "SHAPE@X","SHAPE@Y"]

    # Get a list of existing fields
    existingFields = [f.name for f in arcpy.ListFields(nodes_fc)]

    # Check to see if the last field exists if yes add it.
    # Grabs last field becuase often the first field, emergent, is zero
    if overwrite_data is False and (addFields[len(addFields)-1] in existingFields) is True:
        incursorFields.append(addFields[len(addFields)-1])
    else:
        overwrite_data = True

    # Determine input point spatial units
    proj = arcpy.Describe(nodes_fc).spatialReference

    with arcpy.da.SearchCursor(nodes_fc, incursorFields,"",proj) as Inrows:
        if overwrite_data:
            for row in Inrows:
                nodeDict[row[0]]["STREAM_ID"] = row[1]
                nodeDict[row[0]]["STREAM_KM"] = row[2]
                nodeDict[row[0]]["STRM_AZMTH"] = row[3]
                nodeDict[row[0]]["POINT_X"] = row[4]
                nodeDict[row[0]]["POINT_Y"] = row[5]
        else:
            for row in Inrows:
                # Is the data null or zero, if yes grab it.
                if row[6] is None or row[6] == 0 or row[6] < -9998:
                    nodeDict[row[0]]["STREAM_ID"] = row[1]
                    nodeDict[row[0]]["STREAM_KM"] = row[2]
                    nodeDict[row[0]]["STRM_AZMTH"] = row[3]
                    nodeDict[row[0]]["POINT_X"] = row[4]
                    nodeDict[row[0]]["POINT_Y"] = row[5]

    if len(nodeDict) == 0:
        sys.exit("The fields checked in the input point feature class " +
                 "have existing data. There is nothing to process. Exiting")

    return nodeDict

def update_lc_point_fc(lc_point_list, type, lc_point_fc, nodes_fc,
                       nodes_in_block, overwrite_data, proj):
    """Creates/updates the output landcover sample point feature
    class using the data from the landcover point list"""
    #arcpy.AddMessage("Exporting data to land cover sample feature class")
    #print("Exporting data to land cover sample feature class")

    cursorfields = ["POINT_X","POINT_Y"] +["STREAM_ID","NODE_ID", "SAMPLE_ID",
                                           "TRANS_AZI", "TRANSECT",
                                           "SAMPLE", "KEY"] + type

    # Check if the output exists and create if not
    if not arcpy.Exists(lc_point_fc):
        arcpy.CreateFeatureclass_management(os.path.dirname(lc_point_fc),
                                            os.path.basename(lc_point_fc),
                                            "POINT","","DISABLED","DISABLED",proj)

        # Determine Stream ID field properties
        sid_type = arcpy.ListFields(nodes_fc,"STREAM_ID")[0].type
        sid_precision = arcpy.ListFields(nodes_fc,"STREAM_ID")[0].precision
        sid_scale = arcpy.ListFields(nodes_fc,"STREAM_ID")[0].scale
        sid_length = arcpy.ListFields(nodes_fc,"STREAM_ID")[0].length

        typeDict = {"POINT_X": "DOUBLE",
                    "POINT_Y": "DOUBLE",
                    "NODE_ID": "LONG",
                    "SAMPLE_ID": "LONG",
                    "TRANS_AZI": "DOUBLE",
                    "TRANSECT": "SHORT",
                    "SAMPLE": "SHORT",
                    "KEY": "TEXT",}

        for t in type:
            typeDict[t] = "DOUBLE"

        # Add attribute fields
        for f in cursorfields:
            if f == "STREAM_ID":
                arcpy.AddField_management(lc_point_fc, f, sid_type,
                                          sid_precision, sid_scale, sid_length,
                                          "", "NULLABLE", "NON_REQUIRED")
            else:
                arcpy.AddField_management(lc_point_fc, f, typeDict[f], "",
                                          "", "", "", "NULLABLE", "NON_REQUIRED")

    if not overwrite_data:
        # Build a query to retreive existing rows from the nodes
        # that need updating
        whereclause = """{0} IN ({1})""".format("NODE_ID", ','.join(str(i) for i in nodes_in_block))

        # delete those rows
        with arcpy.da.UpdateCursor(lc_point_fc,["NODE_ID"], whereclause) as cursor:
            for row in cursor:
                cursor.deleteRow()

    with arcpy.da.InsertCursor(lc_point_fc, ["SHAPE@X","SHAPE@Y"] +
                               cursorfields) as cursor:
        for row in lc_point_list:
            cursor.insertRow(row)

def setup_lcdata_headers(transsample_count, trans_count,
                          canopy_data_type, stream_sample):
    """Generates a list of the landcover data file
    column header names and data types"""

    type = ["ELE"]

    #Use LAI methods
    if canopy_data_type == "LAI":
        type = type + ["LAI","k","OH"]

    #Use Canopy Cover methods
    if canopy_data_type == "CanopyCover":
        type = type + ["CAN","OH"]

    lcheaders = []
    otherheaders = []

    dirs = ["T{0}".format(x) for x in range(1, trans_count + 1)]

    zones = range(1,int(transsample_count)+1)

    # Concatenate the type, dir, and zone and order in the correct way

    for d, dir in enumerate(dirs):
        for z, zone in enumerate(zones):
            if stream_sample and d==0 and z==0:
                lcheaders.append("LC_T0_S0") # add emergent
                lcheaders.append("LC_{0}_S{1}".format(dir, zone))
            else:
                lcheaders.append("LC_{0}_S{1}".format(dir, zone))

    for t in type:
        for d, dir in enumerate(dirs):
            for z, zone in enumerate(zones):
                if stream_sample and t !="ELE" and d==0 and z==0:
                    otherheaders.append(t+"_T0_S0") # add emergent
                    otherheaders.append("{0}_{1}_S{2}".format(t, dir, zone))
                else:
                    otherheaders.append("{0}_{1}_S{2}".format(t, dir, zone))

    #type = ["LC"] + type

    return lcheaders, otherheaders

def coord_to_array(easting, northing, block_x_min, block_y_max, x_cellsize, y_cellsize):
    """converts x/y coordinates to col and row of the array"""
    xy = []
    xy.append(int((easting - block_x_min) / x_cellsize))  # col, x
    xy.append(int((northing - block_y_max) / y_cellsize * -1))  # row, y
    return xy

def create_lc_point_list(nodeDict, nodes_in_block, dirs, zones, transsample_distance):
    """This builds a unique long form list of information for all the
    landcover samples in the block. This list is used to
    create/update the output feature class."""

    lc_point_list = []
    numDirs = len(dirs)
    numZones = len(zones)
    zonesPerNode = (numDirs * numZones) + 1

    for nodeID in nodes_in_block:
        origin_x = nodeDict[nodeID]["POINT_X"]
        origin_y = nodeDict[nodeID]["POINT_Y"]
        streamID = nodeDict[nodeID]["STREAM_ID"]
        #sampleID = '{0}{1}{2}'.format(nodeID, '000', '00')
        sampleID = nodeID * zonesPerNode

        # This is the emergent/stream sample
        lc_point_list.append([origin_x, origin_y, origin_x, origin_y,
                              streamID, nodeID, sampleID,
                              0, 0, 0, "T0_S0"])
		#this is adding 2 perp transect directions
        if perp is True:
            streamAZMTH = nodeDict[nodeID]["STRM_AZMTH"]
            direction1 = streamAZMTH - 90
            direction2 = streamAZMTH + 90
            if direction1 < 0:
                direction3 = direction1 + 360
            else: direction3 = direction1

            if direction2 > 360:
                direction4 = direction2 -360
            else:
                direction4 = direction2

            dirs = [direction3, direction4]
            numDirs = len(dirs)

        for d, dir in enumerate(dirs):
            for zone in zones:
                # Calculate the x and y coordinate of the
                # landcover sample location
                pt_x = (zone * transsample_distance * con_from_m *
                        sin(radians(dir))) + origin_x
                pt_y = (zone * transsample_distance * con_from_m *
                        cos(radians(dir))) + origin_y

                key = 'T{0}_S{1}'.format(d+1, zone)
                tran_num = '{:{}{}}'.format(d+1, 0, 3)
                samp_num = '{:{}{}}'.format(zone, 0, 2)
                sampleID = (nodeID * zonesPerNode) + (d * numZones) + zone

                # Add to the list
                lc_point_list.append([pt_x, pt_y, pt_x, pt_y,
                                      streamID, nodeID, sampleID,
                                      dir, d+1, zone, key])

    return lc_point_list

def create_block_list(nodes, block_size):
    """Returns two lists, one containting the coordinate extent
    for each block that will be itterativly extracted to an array
    and the other containing node IDs within each block extent."""

    arcpy.AddMessage("Calculating block extents")
    print("Calculating block extents")
    x_coord_list = [nodeDict[nodeID]["POINT_X"] for nodeID in nodes]
    y_coord_list = [nodeDict[nodeID]["POINT_Y"] for nodeID in nodes]

    # calculate the buffer distance (in raster spatial units) to add to
    # the base bounding box when extracting to an array. The buffer is
    # equal to the sample distance + 1 to make sure the block includes
    # all the landcover samples for each node.
    buffer = int((transsample_count + 1) * transsample_distance * con_from_m)

    # calculate bounding box extent for samples
    x_min = min(x_coord_list)
    x_max = max(x_coord_list)
    y_min = min(y_coord_list)
    y_max = max(y_coord_list)

    x_width = int(x_max - x_min + 1)
    y_width = int(y_max - y_min + 1)

    block_extents = []
    block_nodes = []

    # Build data blocks
    for x in range(0, x_width, block_size):
        for y in range(0, y_width, block_size):

            # Lower left coordinate of block (in map units)
            block0_x_min = min([x_min + x, x_max])
            block0_y_min = min([y_min + y, y_max])
            # Upper right coordinate of block (in map units)
            block0_x_max = min([block0_x_min + block_size, x_max])
            block0_y_max = min([block0_y_min + block_size, y_max])

            block_x_min = block0_x_max
            block_x_max = block0_x_min
            block_y_min = block0_y_max
            block_y_max = block0_y_min

            nodes_in_block = []
            for nodeID in nodes:
                node_x = nodeDict[nodeID]["POINT_X"]
                node_y = nodeDict[nodeID]["POINT_Y"]
                if (block0_x_min <= node_x <= block0_x_max and
                    block0_y_min <= node_y <= block0_y_max):

                    nodes_in_block.append(nodeID)

                    # Minimize the size of the block0 by the true
                    # extent of the nodes in the block
                    if block_x_min > node_x: block_x_min = node_x
                    if block_x_max < node_x: block_x_max = node_x
                    if block_y_min > node_y: block_y_min = node_y
                    if block_y_max < node_y: block_y_max = node_y

            if nodes_in_block:
                # add the block extent for processing
                # order 0 left,      1 bottom,    2 right,     3 top
                block_extents.append((block_x_min - buffer, block_y_min - buffer,
                                      block_x_max + buffer, block_y_max + buffer))
                block_nodes.append(nodes_in_block)

    return block_extents, block_nodes

def sample_raster(block, lc_point_list, raster, con):

    if con is not None:
        nodata_to_value = -9999 / con
    else:
        nodata_to_value = -9999

    # localize the block extent values
    block_x_min = block[0]
    block_y_min = block[1]
    block_x_max = block[2]
    block_y_max = block[3]

    x_cellsize = float(arcpy.GetRasterProperties_management(z_raster, "CELLSIZEX").getOutput(0))
    y_cellsize = float(arcpy.GetRasterProperties_management(z_raster, "CELLSIZEY").getOutput(0))

    # Get the coordinates extent of the input raster
    raster_x_min = float(arcpy.GetRasterProperties_management(raster, "LEFT").getOutput(0))
    raster_y_min = float(arcpy.GetRasterProperties_management(raster, "BOTTOM").getOutput(0))
    raster_x_max = float(arcpy.GetRasterProperties_management(raster, "RIGHT").getOutput(0))
    raster_y_max = float(arcpy.GetRasterProperties_management(raster, "TOP").getOutput(0))

    # Calculate the X and Y offset from the upper left node
    # coordinates bounding box
    x_minoffset = (block_x_min - raster_x_min)%x_cellsize
    y_minoffset = (block_y_min - raster_y_min)%y_cellsize
    x_maxoffset = (raster_x_max - block_x_max)%x_cellsize
    y_maxoffset = (raster_y_max - block_y_max)%y_cellsize

    # adjust so the coordinates are at the raster cell corners
    block_x_min = block_x_min - x_minoffset
    block_y_min = block_y_min - y_minoffset
    block_x_max = block_x_max + x_maxoffset
    block_y_max = block_y_max + y_maxoffset

    # Get the lower left cell center coordinate. This is for ESRI's
    # RastertoNumpyArray function which defaults to the adjacent
    # lower left cell
    block_x_min_center = block_x_min + (x_cellsize / 2)
    block_y_min_center = block_y_min + (y_cellsize / 2)

    # calculate the number or cols/ros from the lower left
    ncols = max([int(ceil((block_x_max - block_x_min)/ x_cellsize)), 1])
    nrows = max([int(ceil((block_y_max - block_y_min)/ y_cellsize)), 1])

    # Construct the array. Note returned array is (row, col) so (y, x)
    try:
        raster_array = arcpy.RasterToNumPyArray(raster, arcpy.Point(block_x_min_center, block_y_min_center),
                                                ncols, nrows, nodata_to_value)
    except:
        tbinfo = traceback.format_exc()
        pymsg = tbinfo + "\nError Info:\n" + "\nNot enough memory. Reduce the block size"
        sys.exit(pymsg)

    # convert array values to meters if needed
    if con is not None:
        raster_array = raster_array * con

    lc_point_list_new = []
    if raster_array.max() > -9999:
        # There is at least one pixel of data
        for point in lc_point_list:
            xy = coord_to_array(point[0], point[1], block_x_min, block_y_max, x_cellsize, y_cellsize)
            point.append(raster_array[xy[1], xy[0]])
            lc_point_list_new.append(point)
    else:
        # No data, add -9999
        for point in lc_point_list:
            point.append(-9999)
            lc_point_list_new.append(point)
    return lc_point_list_new

def update_nodes_fc(nodeDict, nodes_fc, addFields, nodes_to_query):
    """Updates the input point feature class with data from the
    nodes dictionary"""
    #print("Updating input point feature class")

    # Build a query to retreive just the nodes that needs updating
    whereclause = """{0} IN ({1})""".format("NODE_ID", ','.join(str(i) for i in nodes_to_query))

    with arcpy.da.UpdateCursor(nodes_fc,["NODE_ID"] + addFields, whereclause) as cursor:
        for row in cursor:
            for f, field in enumerate(addFields):
                nodeID =row[0]
                row[f+1] = nodeDict[nodeID][field]
                cursor.updateRow(row)

def from_meters_con(inFeature):
    """Returns the conversion factor to get from meters to the
    spatial units of the input feature class"""
    try:
        con_from_m = 1 / arcpy.Describe(inFeature).SpatialReference.metersPerUnit
    except:
        arcpy.AddError("{0} has a coordinate system that".format(inFeature)+
        "is not projected or not recognized. Use a projected"+
        "coordinate system preferably"+
        "in linear units of feet or meters.")
        sys.exit("Coordinate system is not projected or not recognized. "+
                 "Use a projected coordinate system, preferably in linear "+
                 "units of feet or meters.")
    return con_from_m

def from_z_units_to_meters_con(zUnits):
    """Returns the converstion factor to get from
    the input z units to meters"""

    try:
        con_z_to_m = float(zunits)
    except:
        if zUnits == "Meters":
            con_z_to_m = 1.0
        elif zUnits == "Feet":
            con_z_to_m = 0.3048
        else: con_z_to_m = None # The conversion factor will not be used

    return con_z_to_m

#enable garbage collection
gc.enable()

try:
    arcpy.AddMessage("Step 5: Sample Landcover - Star Pattern, Point Method")
    print("Step 5: Sample Landcover - Star Pattern, Point Method")

    #keeping track of time
    startTime= time.time()

    # Check if the node fc exists
    if not arcpy.Exists(nodes_fc):
        arcpy.AddError("\nThis output does not exist: \n" +
                       "{0}\n".format(nodes_fc))
        sys.exit("This output does not exist: \n" +
                 "{0}\n".format(nodes_fc))

    # Check if the lc point fc exists and delete if needed
    if arcpy.Exists(lc_point_fc) and overwrite_data:
        arcpy.Delete_management(lc_point_fc)


    # Determine input spatial units and set unit conversion factors
    proj = arcpy.Describe(nodes_fc).SpatialReference
    proj_ele = arcpy.Describe(z_raster).spatialReference
    proj_lc = arcpy.Describe(lc_raster).spatialReference

    con_from_m = from_meters_con(nodes_fc)
    con_lc_to_m = from_z_units_to_meters_con(lc_units)
    con_z_to_m = from_z_units_to_meters_con(z_units)

    # convert block size from km to meters to units of the node fc
    # in the future block size should be estimated based on availiable memory
    # memorysize = datatypeinbytes*nobands*block_size^2
    # block_size = int(sqrt(memorysize/datatypeinbytes*nobands))
    if block_size in ["#", ""]:
        block_size = int(con_from_m * 5000)
    else:
        block_size = int(con_from_m * block_size * 1000)

    # Check to make sure the raster and input
    # points are in the same projection.
    if proj.name != proj_ele.name:
        arcpy.AddError("{0} and {1} do not ".format(nodes_fc,z_raster)+
                       "have the same projection."+
                       "Please reproject your data.")
        sys.exit("Input points and elevation raster do not have the "+
                 "same projection. Please reproject your data.")

    if proj_lc.name != proj_ele.name:
        arcpy.AddError("{0} and {1} do not ".format(proj_lc,z_raster)+
                       "have the same projection."+
                       "Please reproject your data.")
        sys.exit("The landcover and elevation rasters do not have the "+
                 "same projection. Please reproject your data.")

    # Setup the raster list
    #typeraster = [lc_raster, z_raster]
    #if canopy_data_type == "LAI":  #Use LAI methods
        #if canopy_raster is not "#": typeraster.append(canopy_raster)
        #else: typeraster.append(None)
        #if k_raster is not "#": typeraster.append(k_raster)
        #else: typeraster.append(None)
        #if oh_raster is not "#": typeraster.append(oh_raster)
        #else: typeraster.append(None)

    #if canopy_data_type == "CanopyCover":  #Use Canopy Cover methods
        #if canopy_raster is not "#": typeraster.append(canopy_raster)
        #else: typeraster.append(None)
        #if oh_raster is not "#": typeraster.append(oh_raster)
        #else: typeraster.append(None)

    # Setup the raster dictionary. It is ordered because
    # key list needs to correspond to the order of the attribute fields
    rasterDict = OrderedDict({"LC": lc_raster,
                              "ELE": z_raster})

    if canopy_data_type == "LAI":  #Use LAI methods
        if canopy_raster is not "#":
            rasterDict["LAI"] = canopy_raster
        else:
            rasterDict["LAI"] = None

        if k_raster is not "#":
            rasterDict["k"] = k_raster
        else:
            rasterDict["k"]  = None

        if oh_raster is not "#":
            rasterDict["OH"] = oh_raster
        else:
            rasterDict["OH"] = None


    if canopy_data_type == "CanopyCover":  #Use Canopy Cover methods
        if canopy_raster is not "#":
            rasterDict["CAN"] = canopy_raster
        else:
            rasterDict["CAN"]  = None

        if oh_raster is not "#":
            rasterDict["OH"] = oh_raster
        else:
            rasterDict["OH"] = None




    # flag indicating the model should use the heat source 8 methods
    # (same as 8 directions but no north)
    if heatsource8:
        dirs = [45,90,135,180,225,270,315]
        trans_count = 7
    else:
        dirs = [x * 360.0 / trans_count for x in range(1,trans_count+ 1)]

    if perp:
        dirs = [0,90]
        trans_count = 2
    else:
        dirs = [x * 360.0 / trans_count for x in range(1,trans_count+ 1)]

    zones = range(1,int(transsample_count+1))

    # TODO
    stream_sample = True
    # This is a future function that may replace the emergent methods.
    # If True there is a regular landcover sample at the stream node
    # for each azimuth direction vs a single emergent sample at the
    # stream node.
    #if stream_sample == "TRUE":
        #zone = range(0,int(transsample_count))
    #else:
        #zone = range(1,int(transsample_count+1))

    lcheaders, otherheaders = setup_lcdata_headers(transsample_count, trans_count,
                                            canopy_data_type, stream_sample)

    addFields = lcheaders + otherheaders

    # Get a list of existing fields
    existingFields = [f.name for f in arcpy.ListFields(nodes_fc)]

    # Check to see if the field exists and add it if not
    for f in lcheaders:
        if (f in existingFields) is False:
            arcpy.AddField_management(nodes_fc, f, "TEXT", "", "", "",
                                      "", "NULLABLE", "NON_REQUIRED")

    # Check to see if the field exists and add it if not
    for f in otherheaders:
        if (f in existingFields) is False:
            arcpy.AddField_management(nodes_fc, f, "DOUBLE", "", "", "",
                                      "", "NULLABLE", "NON_REQUIRED")

    # read the node data into the node dictionary
    nodeDict = read_nodes_fc(nodes_fc, overwrite_data, addFields)

    # Get a list of the nodes, sort them
    nodes = nodeDict.keys()
    nodes.sort()

    # Build the block list
    block_extents, block_nodes = create_block_list(nodes, block_size)

    # Itterate through each block, calculate sample coordinates,
    # convert raster to array, sample the raster
    total_samples = 0
    for p, block in enumerate(block_extents):
        nodes_in_block = block_nodes[p]
        nodes_in_block.sort()
        arcpy.AddMessage("Processing block {0} of {1}".format(p + 1, len(block_extents)))
        print("Processing block {0} of {1}".format(p + 1, len(block_extents)))

        # build the landcover sample list
        lc_point_list = create_lc_point_list(nodeDict, nodes_in_block,
                                            dirs, zones, transsample_distance)

        for t, (type, raster) in enumerate(rasterDict.iteritems()):
            if raster is None:
                for i in range(0, len(lc_point_list)):
                    lc_point_list[i].append(-9999)
            else:
                if raster == z_raster:
                    con = con_z_to_m
                elif raster == lc_raster:
                    con = con_lc_to_m
                else:
                    con = None

                lc_point_list = sample_raster(block, lc_point_list, raster, con)

            # Update the node fc
            for row in lc_point_list:
                key = "{0}_{1}".format(type, row[10])
                nodeDict[row[5]][key] = row[11 + t]

        # Write the landcover data to the TTools point feature class
        update_nodes_fc(nodeDict, nodes_fc, addFields, nodes_in_block)

        # Build the output point feature class using the data
        update_lc_point_fc(lc_point_list, rasterDict.keys(), lc_point_fc,
                           nodes_fc, nodes_in_block, overwrite_data, proj)

        total_samples = total_samples + len(lc_point_list)
        del lc_point_list
        gc.collect()

    endTime = time.time()

    elapsedmin= ceil(((endTime - startTime) / 60)* 10)/10
    mspersample = timedelta(seconds=(endTime - startTime) /
                            total_samples).microseconds
    print("Process Complete in {0} minutes. {1} microseconds per sample".format(elapsedmin, mspersample))
    arcpy.AddMessage("Process Complete in %s minutes. %s microseconds per sample" % (elapsedmin, mspersample))

# For arctool errors
except arcpy.ExecuteError:
    msgs = arcpy.GetMessages(2)
    arcpy.AddError(msgs)
    print(msgs)

# For other errors
except:
    tbinfo = traceback.format_exc()

    pymsg = "PYTHON ERRORS:\n" + tbinfo + "\nError Info:\n" +str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"

    arcpy.AddError(pymsg)
    arcpy.AddError(msgs)

    print(pymsg)
    print(msgs)
