import arcpy
from arcpy import env
from arcpy.sa import *
import os
import csv
import collections

#arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False

rootdir = 'C:/Mathis/ICSL/stormwater/'
datadir = os.path.join(rootdir, 'data')
resdir  = os.path.join(rootdir,'results')
LU_gdb = os.path.join(resdir, 'LU.gdb')
arcpy.env.workspace = LU_gdb
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

NLCD = os.path.join(datadir, 'nlcd_2011_landcover_2011_edition_2014_10_10\\nlcd_2011_landcover_2011_edition_2014_10_10.img')
WAroads = os.path.join(datadir, 'OSM_WA_20180601/gis_osm_roads_free_1.shp')
ORroads = os.path.join(datadir, 'OSM_OR_20180927/gis_osm_roads_free_1.shp')
CAroads = os.path.join(datadir, 'OSM_CA_20180927/gis_osm_roads_free_1.shp')
bufwidthtab = os.path.join(datadir, 'roadbufwidth.csv')
NLCD_reclass = os.path.join(LU_gdb, 'NLCD_reclass')


#Output variables
WCroads = os.path.join(LU_gdb, 'WestCoastroads')
WCroads_sub = WCroads + '_sub'
WCroads_subproj = WCroads + '_subproj'
WCroadbuff = WCroads + '_buf'
WCroadras = WCroads + 'ras'
WCroadrasag = WCroads + 'ras_ag'
NLCD_reclass_sub = os.path.join(LU_gdb, 'NLCD_reclass_sub')
road_LUinters = 'road_LUurb_inters'
road_LUdiss = road_LUinters + '_diss'
crs= arcpy.Describe(NLCD).SpatialReference

#----------------------------------------------- Analysis --------------------------------------------------------------
#Merge OSM roads along the West Coast
arcpy.Merge_management([WAroads, ORroads, CAroads], WCroads)
#Subset roads to only include
arcpy.MakeFeatureLayer_management(WCroads, 'WCroads_lyr')
#Excludes pedestrian streets, tracks as mainly used for forestry and agricultural and often unpaved, bus_guideway, escape
sel = "{} IN ('motorway','motorway_link','living_street','primary','primary_link','residential','secondary','secondary_link'," \
      "'tertiary','tertiary_link','trunk','trunk_link','service','unclassified','unknown', 'raceway','road')".format('"fclass"')
arcpy.SelectLayerByAttribute_management('WCroads_lyr', 'NEW_SELECTION', sel)
arcpy.CopyFeatures_management('WCroads_lyr', WCroads_sub)

#Project
arcpy.Project_management(WCroads_sub, WCroads_subproj, out_coor_system= crs)

#Assume lanes of 12ft, the most common width standard
#From https://safety.fhwa.dot.gov/geometric/pubs/mitigationstrategies/chapter3/3_lanewidth.cfm
#For all roads but motorways and trunks, assume two 12-ft lanes (to account for two ways) and no shoulder adding to lane width
#For motorway (e.g. interstate), assume three lanes each way + 1-sided 10 ft outside shoulder and inside 4ft shoulder
#For trunk, assume same thing as motorway but two lanes each way
arcpy.MakeFeatureLayer_management(WCroads_subproj, 'WCroads_lyr')
arcpy.AddJoin_management('WCroads_lyr', 'fclass', bufwidthtab, 'fclass')
arcpy.CopyFeatures_management('WCroads_lyr', WCroads_subproj+'_rwidth')

arcpy.Buffer_analysis(WCroads_subproj+'_rwidth', WCroadbuff, 'bufwidth', dissolve_option='NONE')

#Rasterize road buffers to 6 m resolution snapped to NLCD_reclass
arcpy.env.snapRaster = NLCD_reclass
arcpy.AddField_management(WCroadbuff, 'PIX', 'SHORT')
arcpy.CalculateField_management(WCroadbuff, 'PIX', 1, 'PYTHON')
arcpy.PolygonToRaster_conversion(WCroadbuff, 'PIX', WCroadras, cell_assignment= 'MAXIMUM_AREA', cellsize = 6)

#Convert developed land use to road pixels when road pixel covers more than half of developed area
#21	Developed, Open Space - < 20% total cover
#22	Developed, Low Intensity - 20-49% total cover
#23	Developed, Medium Intensity - 50-79% total cover
#24 Developed, high Intensity - 80-100% total cover
roadrasag = arcpy.sa.Aggregate(WCroadras, 5, aggregation_type= 'SUM', extent_handling='EXPAND', ignore_nodata='DATA')
roadrasag.save(WCroadrasag)

OutCon1 = Con(IsNull(Raster(WCroadrasag)), NLCD_reclass,
              Con((Raster(NLCD)==21) & ((Raster(WCroadrasag)/25)>0.15), 96,
                  Con((Raster(NLCD)==22) & ((Raster(WCroadrasag)/25)>0.20), 96,
                      Con((Raster(NLCD)==23) & ((Raster(WCroadrasag)/25)>0.25), 96,
                        Con((Raster(NLCD)==23) & ((Raster(WCroadrasag)/25)>0.40), 96, NLCD_reclass
                            )))))
OutCon1.save("NLCD_reclass_final")

# Out = Con(IsNull("WestCoastroadsras"), "NLCD_reclass_final",
#           Con(("nlcd_2011_landcover_2011_edition_2014_10_10.img"==21) & ((Float("WestCoastroadsras")/25)>=0.20), 96,
#               Con(("nlcd_2011_landcover_2011_edition_2014_10_10.img"==22) & ((Float("WestCoastroadsras")/25)>=0.25), 96,
#                   Con(("nlcd_2011_landcover_2011_edition_2014_10_10.img"==23) & ((Float("WestCoastroadsras")/25)>=0.40), 96,
#                       Con(("nlcd_2011_landcover_2011_edition_2014_10_10.img"==23) & ((Float("WestCoastroadsras")/25)>=0.50), 96,
#                       "NLCD_reclass_final")))))

#Subset raster to just urban pixels
arcpy.env.extent = WCroadbuff
urblu = Con(Raster(NLCD_reclass)>95, 1)
urblu.save(NLCD_reclass_sub)

#Create fishnet to intersect with roads - too bulky, leads to 280 million polygons just for Washington State and took 36h to generate
# orig = str(arcpy.GetRasterProperties_management(NLCD_reclass_sub, 'LEFT').getOutput(0)) + ' ' + \
#        str(arcpy.GetRasterProperties_management(NLCD_reclass_sub, 'BOTTOM').getOutput(0))
# Yaxis = str(arcpy.GetRasterProperties_management(NLCD_reclass_sub, 'LEFT').getOutput(0)) + ' ' + \
#        str(arcpy.GetRasterProperties_management(NLCD_reclass_sub, 'TOP').getOutput(0))
# arcpy.CreateFishnet_management('WCfishnet',
#                                origin_coord= orig, y_axis_coord= Yaxis,labels='NO_LABELS', template=NLCD_reclass,
#                                cell_width = arcpy.GetRasterProperties_management(NLCD_reclass_sub, 'CELLSIZEX').getOutput(0),
#                                cell_height = arcpy.GetRasterProperties_management(NLCD_reclass_sub, 'CELLSIZEY').getOutput(0),
#                                geometry_type= 'POLYGON')
# arcpy.AddGeometryAttributes_management('WCfishnet', 'AREA', Area_Unit='SQUARE_METERS')
# arcpy.AlterField_management('WCfishnet', 'POLY_AREA', 'CELLAREA', 'CELLAREA')

#Intersect fishnet and roads
# arcpy.Intersect_analysis([WCroadbuff_diss, 'WCfishnet'], road_LUinters)
# arcpy.Dissolve_management(road_LUinters, road_LUdiss, dissolve_field=) #Use fishnet identifier
# arcpy.AddGeometryAttributes_management(road_LUdiss, 'AREA', Area_Unit='SQUARE_METERS')
# arcpy.AddField_management(road_LUdiss, 'ROADPER', 'FLOAT')
# arcpy.CalculateField_management(road_LUdiss, 'ROADPER', '!POLY_AREA!/!CELL_AREA!', expression_type='PYTHON')

#Then compete 'ROADPER' to NLCD land use, if road > 0.5, then make it road LU