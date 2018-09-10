import arcpy
import os
import collections
import csv
import re

#arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False


#Input data
rootdir = 'C:\Mathis\ICSL\stormwater'
datadir = os.path.join(rootdir,'data')
resdir = os.path.join(rootdir,'results')
CAdir = os.path.join(datadir,'CA_LULC')
ORzoning = os.path.join(datadir,'Oregon_Zoning_2017/Oregon_Zoning_2017.shp')
LAzoning = os.path.join(CAdir, 'LosAngeles/General_Plan_Land_Use__Los_Angeles/Los_Angeles_PL_SCAG.shp')
Orangezoning = os.path.join(CAdir, 'Orange\Zoning\Zoning_2018_08_01.shp')
SanDiegozoning = os.path.join(CAdir, 'SanDiego\LANDUSE_CURRENT\LANDUSE_CURRENT.shp')
SanBerzoning = os.path.join(CAdir, 'SanBernardino\SBCo_Parcel_Polygons\SBCo_Parcel_Polygons.shp')

arcpy.env.workspace = resdir

#Output variables
CDWR_merge = os.path.join(resdir, 'CDWR_merge.shp')
CDWR_merge_noZ = os.path.join(resdir, 'CDWR_merge_noZ.shp')

#Define functions
def listunique(feature, field) :
    '''Function to write out a csv table listing unique values of a field'''
    ulist = [field]
    [ulist.append(row[0]) for row in arcpy.da.SearchCursor(feature, [field]) if row[0] not in ulist]
    with open(os.path.join(resdir,feature+'reclass.csv'), 'wb') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr.writerow(ulist)

# ----------------------------------- ANALYSIS ------------------------------------------------------------------------#

#Reclassify Oregon zoning dataset
listunique(ORzoning, 'orZDesc')
arcpy.MakeFeatureLayer_management(ORzoning, 'ORzoning_lyr')
arcpy.AddJoin_management('ORzoning_lyr', 'orZDesc',
                         os.path.join(datadir,'Oregon_Zoning_2017/ORzoningreclass_edit.csv'), 'orZDesc')

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
arcpy.AddJoin_management('CDWR_mergelyr','CLASS1',os.path.join(CAdir,'CDWR_reclass_edit.csv'),'CLASS1')
arcpy.CopyFeatures_management('CDWR_mergelyr', CDWR_merge_noZ)

#Los Angeles
listunique(LAzoning, 'SCAG_GP_CO')
arcpy.MakeFeatureLayer_management(LAzoning, 'LAzoninglyr')
arcpy.AddJoin_management('LAzoninglyr','SCAG_GP_CO',
                         os.path.join(CAdir,'LosAngeles/General_Plan_Land_Use__Los_Angeles/Los_Angeles_PL_SCAGreclass_edit.csv'),'SCAG_GP_CO')
arcpy.CopyFeatures_management('LAzoninglyr', 'LAzoning_reclass.shp')

#San Diego
listunique(SanDiegozoning, 'Landuse')
arcpy.MakeFeatureLayer_management(SanDiegozoning, 'SanDiegozoninglyr')
arcpy.AddJoin_management('SanDiegozoninglyr','Landuse',os.path.join(CAdir,'LANDUSE_CURRENTreclass_edit.csv'),'Landuse')
arcpy.CopyFeatures_management('SanDiegozoninglyr', 'SanDiegozoning_reclass.shp')

#San Bernardino
listunique(SanBerzoning, 'AssessClas')
arcpy.MakeFeatureLayer_management(SanBerzoning, 'SanBerzoninglyr')
arcpy.AddJoin_management('SanBerzoninglyr','AssessClas',os.path.join(CAdir,'SBCo_Parcel_Polygonsreclass_edit.csv'),'AssessClas')
arcpy.CopyFeatures_management('SanBerzoninglyr', 'SanBerzoning_reclass.shp')


#######To do:
#Add other counties
#Add Kern zoning
#For Kern: still missing Ridgecrest and California City zoning data
#Follow up on SCAG data (for Orange and Imperial counties)
#Still missing: Tehama (missing in database, should be a 2012 layer),

#Normal to be missing (don't drain to west coast): Nevada, Sierra, Mono, Inyo, Alpine

#Add common field that includes year