import arcpy
from arcpy.sa import *
import os
import collections
import csv
import re

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False

#Input data
rootdir = 'C:\Mathis\ICSL\stormwater'
datadir = os.path.join(rootdir,'data')
resdir = os.path.join(rootdir,'results')
NLCD = os.path.join(datadir, 'nlcd_2011_landcover_2011_edition_2014_10_10\\nlcd_2011_landcover_2011_edition_2014_10_10.img')
CAdir = os.path.join(datadir,'CA_LULC')
ORzoning = os.path.join(datadir,'Oregon_Zoning_2017/Oregon_Zoning_2017.shp')
LAzoning = os.path.join(CAdir, 'LosAngeles/General_Plan_Land_Use__Los_Angeles/LA.gdb/Los_Angeles_PL_SCAG.shp')
SanDiegozoning = os.path.join(CAdir, 'SanDiego\LANDUSE_CURRENT\LANDUSE_CURRENT.shp')
SanBerzoning = os.path.join(CAdir, 'SanBernardino\SBCo_Parcel_Polygons\SBCo_Parcel_Polygons.shp')
ContraCostazoning = os.path.join(CAdir, 'ContraCosta/PLA_DCD_Zoning/PLA_DCD_Zoning.shp')
Kernzoning = os.path.join(CAdir, 'Kern/Zoning/Zoning.shp')
Montereyzoning = os.path.join(CAdir, 'Monterey/Zoning/Zoning.shp')
SantaCruzzoning = os.path.join(CAdir, 'SantaCruz/Zoning/Zoning.shp')
SCAGzoning = os.path.join(CAdir, 'SCAG/SCAG.gdb/landuse_poly_SCAG_2012.shp')
LUint_reclass = os.path.join(CAdir, 'LUintensity_reclass.csv')

WAzoning = 'C:/Mathis/ICSL/flood_vulnerability/results/flood_risk.gdb/parcel_o5cleanall_dissolve' #Completely different directory WARNING

arcpy.env.workspace = resdir

#Output variables
LU_gdb = os.path.join(resdir, 'LU.gdb')
if not arcpy.Exists(LU_gdb):
    arcpy.CreateFileGDB_management(resdir, 'LU.gdb')

WAreclass = os.path.join(LU_gdb, 'WAzoning_reclass')
ORreclass = os.path.join(LU_gdb,'ORzoning_reclass')
CDWR_merge = os.path.join(resdir, 'CDWR_merge.shp')
CDWR_merge_noZ = os.path.join(resdir, 'CDWR_merge_noZ.shp')
LAreclass = LAzoning[:-4]+'_reclass'
SanDiegoreclass = SanDiegozoning[:-4]+'_reclass.shp'
SanBerreclass = SanBerzoning[:-4]+'_reclass.shp'
ContraCostareclass = ContraCostazoning[:-4]+'_reclass.shp'
Kernreclass = Kernzoning[:-4]+'_reclass.shp'
Montereyreclass = Montereyzoning[:-4]+'_reclass.shp'
SantaCruzreclass = SantaCruzzoning[:-4]+'_reclass.shp'
SCAGreclass = SCAGzoning[:-4]+'_reclass'

CALUall = os.path.join(LU_gdb, 'CALU_all')
CALUurb = os.path.join(LU_gdb,'CALU_urban')
CALUras = os.path.join(LU_gdb,'CALU_urbanras')
WALUras = os.path.join(LU_gdb, 'WALU_urbanras')
ORLUras = os.path.join(LU_gdb, 'ORLU_urbanras')
WCLU = os.path.join(LU_gdb, 'WestCoastLU')
NLCD_reclass = os.path.join(LU_gdb, 'NLCD_reclass')

#Define functions
def listunique(feature, field) :
    '''Function to write out a csv table listing unique values of a field'''
    ulist = [field]
    [ulist.append(row[0]) for row in arcpy.da.SearchCursor(feature, [field]) if row[0] not in ulist]
    with open(os.path.join(resdir,os.path.basename(feature)+'reclass.csv'), 'wb') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr.writerow(ulist)

crs= arcpy.Describe(NLCD).SpatialReference

# ----------------------------------- FORMAT INDIVIDUAL DATASETS -------------------------------------------------------
#Reclassify Washington parcel dataset
listunique(WAzoning, 'StateLandUseCD') #Then manually format and classify into Agriculture, Residential, Commercial, Industrial, Miscellaneous in Excel
arcpy.Project_management(WAzoning, os.path.join(LU_gdb,'WAzoning_proj'), crs)
arcpy.MakeFeatureLayer_management(os.path.join(LU_gdb,'WAzoning_proj'), 'WAzoning_lyr')
arcpy.AddJoin_management('WAzoning_lyr', 'StateLandUseCD',os.path.join(resdir,'WAzoningreclass_edit.csv'),
                         'StateLandUseCD', 'KEEP_COMMON')
arcpy.CopyFeatures_management('WAzoning_lyr', WAreclass)


#Reclassify Oregon zoning dataset
listunique(ORzoning, 'orZDesc') #Then manually format and classify into Agriculture, Residential, Commercial, Industrial, Miscellaneous in Excel
arcpy.Project_management(ORzoning, os.path.join(LU_gdb,'ORzoning_proj'), crs)
arcpy.MakeFeatureLayer_management(os.path.join(LU_gdb,'ORzoning_proj'), 'ORzoning_lyr')
arcpy.AddJoin_management('ORzoning_lyr', 'orZDesc',os.path.join(datadir,'Oregon_Zoning_2017/ORzoningreclass_edit.csv'),
                         'orZDesc', 'KEEP_COMMON')
arcpy.CopyFeatures_management('ORzoning_lyr', ORreclass)

#Merge all California Department of Water Resources Land Use datasets
regx_dir = '.*\d.*'
CDWRdirlist = [st for st in os.listdir(CAdir) if re.match(regx_dir, st) and st not in ['esrplulc200406b']]
regx_shp = '.*[.]shp$'
CAdatlist = []
for d in CDWRdirlist:
    for root, dirs, files in os.walk(os.path.join(CAdir,d)):
        [CAdatlist.append(os.path.join(root,st)) for st in files if re.search(regx_shp, st)]
arcpy.Merge_management(inputs=CAdatlist, output=CDWR_merge)
#Remove overlapping dummy polygons (marked with 'Z' land use)
arcpy.MakeFeatureLayer_management(CDWR_merge, 'CDWR_mergelyr', where_clause="NOT CLASS1 = 'Z'")
#Get unique zoning values
listunique(CDWR_merge_noZ, 'CLASS1')
arcpy.AddJoin_management('CDWR_mergelyr','CLASS1',os.path.join(CAdir,'CDWR_reclass_edit.csv'),'CLASS1', 'KEEP_COMMON')
arcpy.CopyFeatures_management('CDWR_mergelyr', CDWR_merge_noZ)
#arcpy.MakeFeatureLayer_management(CDWR_merge_noZ, 'CDWR_mergelyr', where_clause="FID = 228570")
#arcpy.DeleteFeatures_management('CDWR_mergelyr')

#Los Angeles
listunique(LAzoning, 'SCAG_GP_CO')
arcpy.MakeFeatureLayer_management(LAzoning, 'LAzoninglyr')
arcpy.AddJoin_management('LAzoninglyr','SCAG_GP_CO',
                         os.path.join(CAdir,'LosAngeles/General_Plan_Land_Use__Los_Angeles/Los_Angeles_PL_SCAGreclass_edit.csv'),
                         'SCAG_GP_CO', 'KEEP_COMMON')
arcpy.CopyFeatures_management('LAzoninglyr', LAreclass) #Can't do that in Python unless in same gdb
arcpy.AddField_management(LAreclass, 'SURVEYYEAR','LONG',10)
arcpy.CalculateField_management(LAreclass, 'SURVEYYEAR', 2012, expression_type='PYTHON')

#San Diego
listunique(SanDiegozoning, 'Landuse')
arcpy.MakeFeatureLayer_management(SanDiegozoning, 'SanDiegozoninglyr')
arcpy.AddJoin_management('SanDiegozoninglyr','Landuse',SanDiegozoning[:-4]+'reclass_edit.csv','Landuse')
arcpy.CopyFeatures_management('SanDiegozoninglyr', SanDiegoreclass)
arcpy.AddField_management(SanDiegoreclass, 'SURVEYYEAR','LONG',10)
arcpy.CalculateField_management(SanDiegoreclass, 'SURVEYYEAR', 2017, expression_type='PYTHON')

#San Bernardino
listunique(SanBerzoning, 'AssessClas')
arcpy.MakeFeatureLayer_management(SanBerzoning, 'SanBerzoninglyr')
arcpy.AddJoin_management('SanBerzoninglyr','AssessClas',SanBerzoning[:-4]+'reclass_edit.csv','AssessClas')
arcpy.CopyFeatures_management('SanBerzoninglyr', SanBerreclass)
arcpy.AddField_management(SanDiegoreclass, 'SURVEYYEAR','LONG',10)
arcpy.CalculateField_management(SanDiegoreclass, 'SURVEYYEAR', 2017, expression_type='PYTHON')

#Contra Costa
listunique(ContraCostazoning, 'Zoning_Tex')
arcpy.MakeFeatureLayer_management(ContraCostazoning, 'ContraCostazoninglyr')
arcpy.AddJoin_management('ContraCostazoninglyr','Zoning_Tex', ContraCostazoning[:-4]+'reclass_edit.csv','Zoning_Tex')
arcpy.CopyFeatures_management('ContraCostazoninglyr', ContraCostareclass)
arcpy.AddField_management(ContraCostareclass, 'SURVEYYEAR','LONG',10)
arcpy.CalculateField_management(ContraCostareclass, 'SURVEYYEAR', 2005, expression_type='PYTHON')

#Kern
listunique(Kernzoning, 'Comb_Zn')
arcpy.MakeFeatureLayer_management(Kernzoning, 'Kernzoninglyr')
arcpy.AddJoin_management('Kernzoninglyr','Comb_Zn', Kernzoning[:-4]+'reclass_edit.csv','Comb_Zn')
arcpy.CopyFeatures_management('Kernzoninglyr', Kernreclass)
arcpy.AddField_management(Kernreclass, 'SURVEYYEAR','LONG',10)
arcpy.CalculateField_management(Kernreclass, 'SURVEYYEAR', 2005, expression_type='PYTHON')
#Still missing Ridgecrest and California City zoning data

#Monterey
listunique(Montereyzoning, 'ZONE_CATEG')
arcpy.MakeFeatureLayer_management(Montereyzoning, 'Montereyzoninglyr')
arcpy.AddJoin_management('Montereyzoninglyr','ZONE_CATEG', Montereyzoning[:-4]+'reclass_edit.csv','ZONE_CATEG')
arcpy.CopyFeatures_management('Montereyzoninglyr', Montereyreclass)
arcpy.AddField_management(Montereyreclass, 'SURVEYYEAR','LONG',10)
arcpy.CalculateField_management(Montereyreclass, 'SURVEYYEAR', 2018, expression_type='PYTHON')

#Santa Cruz
listunique(SantaCruzzoning, 'GENERIC')
arcpy.MakeFeatureLayer_management(SantaCruzzoning, 'SantaCruzzoninglyr')
arcpy.AddJoin_management('SantaCruzzoninglyr','GENERIC', SantaCruzzoning[:-4]+'reclass_edit.csv','GENERIC')
arcpy.CopyFeatures_management('SantaCruzzoninglyr', SantaCruzreclass)
arcpy.AddField_management(SantaCruzreclass, 'SURVEYYEAR','LONG',10)
arcpy.CalculateField_management(SantaCruzreclass, 'SURVEYYEAR', 2017, expression_type='PYTHON')

#SCAG
listunique(SCAGzoning, 'LU12')
arcpy.MakeFeatureLayer_management(SCAGzoning, 'SCAGzoninglyr')
arcpy.AddJoin_management('SCAGzoninglyr','LU12', SCAGzoning[:-4]+'reclass_edit.csv','LU12','KEEP_COMMON')  #Can't do that in Python unless in same gdb
arcpy.CopyFeatures_management('SCAGzoninglyr', SCAGreclass)
arcpy.AddField_management(SCAGreclass, 'SURVEYYEAR','LONG',10) #Corrupts the shapefile (?), do it in Arcmap
arcpy.CalculateField_management(SCAGreclass, 'SURVEYYEAR', 2012, expression_type='PYTHON')

#Still missing: Tehama (only 1999 data for now, update with 2012 layer when get it),
#Normal to be missing (don't drain to west coast): Nevada, Sierra, Mono, Inyo, Alpine

# ----------------------------------- MERGE CALIFORNIA DATASETS -------------------------------------------------------
#Merge all polygons
mergedatlist = [CDWR_merge_noZ,LAreclass,SanDiegoreclass,SanBerreclass,ContraCostareclass,Kernreclass,
                        Montereyreclass,SantaCruzreclass, SCAGreclass]
mergeready = True
for fc in mergedatlist:
    if not arcpy.Exists(fc):
        print('{} does not exist'.format(fc))
        mergeready = False

mergedatlistproj = []
for i in range(0,len(mergedatlist)):
    path = os.path.splitext(mergedatlist[i])
    outpath = path[0] + '_proj' + path[1]
    if arcpy.Describe(mergedatlist[i]).SpatialReference.name != crs.name and \
         not (arcpy.Exists(outpath)):
            print('Project '+ mergedatlist[i])
            arcpy.Project_management(mergedatlist[i], outpath, crs)
            mergedatlistproj.append(outpath)
    else:
        mergedatlistproj.append(mergedatlist[i])

#Errors during merge:
#ExecuteError: ERROR 001156: Failed on input OID 288, could not write value 'The "HR" regulations apply to the following structures in the Tassajara Hot Springs complex: dining room, stonerooms and office. (See historic resources file.)' to output field Notes
# for fc in mergedatlist:
#     if arcpy.Exists(fc):
#         for f in arcpy.ListFields(fc):
#             if f.name=='Notes':
#                 print(fc)
arcpy.DeleteField_management(Kernreclass, 'Notes')
if mergeready == True:
    arcpy.Merge_management(mergedatlistproj, CALUall)
#Only keep urban pixels
#Create table that associates StormClass: residential:1, commercial:2, industrial:3
arcpy.MakeFeatureLayer_management(CALUall, 'CALU_alllyr')
arcpy.AddJoin_management('CALU_alllyr', 'StormClass', LUint_reclass, 'StormClass', 'KEEP_COMMON')
arcpy.CopyFeatures_management('CALU_alllyr', CALUurb)
########################## TO TEST/RUN ############################
#Delete full merged dataset
arcpy.Delete_management('CALU_alllyr')
arcpy.Delete_management(CALUall)

#Rasterize to same extent and resolution as NLCD keeping maximum LU intensity when overlap
arcpy.env.snapRaster = NLCD
arcpy.PolygonToRaster_conversion(CALUurb, 'Luintensity', CALUras, cell_assignment='MAXIMUM_AREA',
                                 priority_field='Luintensity', cellsize=NLCD)
#(assume that most recent LU is always more intense)

#Rasterize Washington and Oregon datasets as well
arcpy.MakeFeatureLayer_management(WAreclass, 'WAreclasslyr')
arcpy.AddJoin_management('WAreclasslyr', 'StormClass', LUint_reclass, 'StormClass', 'KEEP_COMMON')
arcpy.PolygonToRaster_conversion('WAreclasslyr', os.path.split(LUint_reclass)[1]+'.Luintensity', WALUras, cell_assignment='MAXIMUM_AREA',
                                 priority_field=os.path.split(LUint_reclass)[1]+'.Luintensity', cellsize=NLCD)

arcpy.MakeFeatureLayer_management(ORreclass, 'ORreclasslyr')
arcpy.AddJoin_management('ORreclasslyr', 'StormClass', LUint_reclass, 'StormClass', 'KEEP_COMMON')
arcpy.PolygonToRaster_conversion('ORreclasslyr', os.path.split(LUint_reclass)[1]+'.Luintensity', ORLUras, cell_assignment='MAXIMUM_AREA',
                                 priority_field=os.path.split(LUint_reclass)[1]+'.Luintensity', cellsize=NLCD)

#Merge all rasters
arcpy.MosaicToNewRaster_management([CALUras, ORLUras, WALUras], LU_gdb, os.path.split(WCLU)[1],
                                   number_of_bands = 1,mosaic_method='MAXIMUM')

#Create residential, commercial, industrial dataset
NLCD_reclass = os.path.join(LU_gdb, 'NLCD_reclass')
outCon = Con((Raster(NLCD)>=21) & (Raster(NLCD)<=23), 97,
             Con((Raster(NLCD)==24) & (Raster(WCLU)<3), 98,
             Con((Raster(NLCD) == 24) & (Raster(WCLU) == 3), 99, Raster(NLCD))))
outCon.save(NLCD_reclass)