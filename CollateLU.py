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
SanDiegozoning = os.path.join(CAdir, 'SanDiego\LANDUSE_CURRENT\LANDUSE_CURRENT.shp')
SanBerzoning = os.path.join(CAdir, 'SanBernardino\SBCo_Parcel_Polygons\SBCo_Parcel_Polygons.shp')
ContraCostazoning = os.path.join(CAdir, 'ContraCosta/PLA_DCD_Zoning/PLA_DCD_Zoning.shp')
Kernzoning = os.path.join(CAdir, 'Kern/Zoning/Zoning.shp')
Montereyzoning = os.path.join(CAdir, 'Monterey/Zoning/Zoning.shp')
SantaCruzzoning = os.path.join(CAdir, 'SantaCruz/Zoning/Zoning.shp')
SCAGzoning = os.path.join(CAdir, 'SCAG/landuse_poly_SCAG_2012.shp')

arcpy.env.workspace = resdir

#Output variables
CDWR_merge = os.path.join(resdir, 'CDWR_merge.shp')
CDWR_merge_noZ = os.path.join(resdir, 'CDWR_merge_noZ.shp')
LAreclass = LAzoning[:-4]+'_reclass.shp'
SanDiegoreclass = SanDiegozoning[:-4]+'_reclass.shp'
SanBerreclass = SanBerzoning[:-4]+'_reclass.shp'
ContraCostareclass = ContraCostazoning[:-4]+'_reclass.shp'
Kernreclass = Kernzoning[:-4]+'_reclass.shp'
Montereyreclass = Montereyzoning[:-4]+'_reclass.shp'
SantaCruzreclass = SantaCruzzoning[:-4]+'_reclass.shp'
SCAGreclass = SCAGzoning[:-4]+'_reclass.shp'

#Define functions
def listunique(feature, field) :
    '''Function to write out a csv table listing unique values of a field'''
    ulist = [field]
    [ulist.append(row[0]) for row in arcpy.da.SearchCursor(feature, [field]) if row[0] not in ulist]
    with open(os.path.join(resdir,feature+'reclass.csv'), 'wb') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr.writerow(ulist)

# ----------------------------------- FORMAT INDIVIDUAL DATASETS -------------------------------------------------------

#Reclassify Oregon zoning dataset
listunique(ORzoning, 'orZDesc') #Then manually format and classify into Agriculture, Residential, Commercial, Industrial, Miscellaneous in Excel
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
arcpy.CopyFeatures_management('LAzoninglyr', LAreclass)
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
#Add 'SURVEYYEAR'

# ----------------------------------- MERGE DATASETS -------------------------------------------------------



#Still missing: Tehama (missing in database, should be a 2012 layer),
#Normal to be missing (don't drain to west coast): Nevada, Sierra, Mono, Inyo, Alpine