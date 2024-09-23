import os
import matplotlib.pyplot as plt
import arcpy
import pandas as pd
from pandas.plotting import table
arcpy.env.overwriteOutput = True


def createShpfile(taxlot_id, taxlots, output_file, taxlot_field): # create new shapefile based on a taxlot id value from the taxlot.shp file

    where_clause = f"{taxlot_field} = '{taxlot_id}'"

    arcpy.conversion.ExportFeatures(taxlots, output_file, where_clause)


def surveyGP(soils1, soils2, targetShpfile, clippedSoils, rhino, arcproj):

    # use list comprehensions to find the geometry of each shapefile
    target_geom = [r[0] for r in arcpy.da.SearchCursor(targetShpfile, ['SHAPE@'])][0]
    rhino_geom = [r[0] for r in arcpy.da.SearchCursor(rhino, ['SHAPE@'])][0]

    # find if the target is inside or outside the rhino, and name the clipped soils layer appropriately
    if target_geom.within(rhino_geom):
        soilsShpfile = os.path.join(clippedSoils, "Clip_approved.shp")
        arcpy.analysis.Intersect([targetShpfile, soils1], soilsShpfile)

    else:
        soilsShpfile = os.path.join(clippedSoils, "Clip_interim.shp")
        arcpy.analysis.Intersect([targetShpfile, soils2], soilsShpfile)

    # add an acres field for calculating soil % within target feature
    arcpy.management.AddField(soilsShpfile, "Clip_Acres", "FLOAT")

    arcpy.management.CalculateGeometryAttributes(soilsShpfile, "Clip_Acres AREA_GEODESIC", '', "ACRES_US", None,
                                                 "SAME_AS_INPUT")

    # use pandas and matplotlib to create a dataframe from soilsShpfile, export a table, chart, and csv with map unit descriptions and percentages
    #--------------------------------------------------------------------------------------------

    soils_df = pd.DataFrame([row for row in arcpy.da.SearchCursor(soilsShpfile,
                                                             ['musym', 'muname', 'TaxlotAcre', 'Clip_Acres'])])

    soils_df.columns = ['Musym', 'Soil Type', 'TaxlotAcre', 'Acreage']
    soils_df['Soil %'] = (soils_df['Acreage'] / soils_df['TaxlotAcre']) * 100 # create a column with soil %
    soils_df['Soil %'] = round(soils_df['Soil %'], 2) # round off values to 2 decimals
    df = soils_df.copy()
    #df.drop(['TaxlotAcre'], axis=1, inplace=True)
    df['Map Unit Description'] = df['Musym'] + ' - ' + df['Soil Type'] # create a column titles 'map unit description'

    fig, ax = plt.subplots(1, 1) # use tuple unpacking to assign the fig, ax variables
    table(ax, df['Map Unit Description'], bbox=[1.2, 0, 1.2, 1]); # create a table
    # plot bar graph values
    df.plot.bar(ax=ax, x='Musym', y='Soil %', title=f"Soil % for taxlot {os.path.basename(clippedSoils)}", color="brown", legend=None)
    ax.bar_label(ax.containers[0])
    plt.subplots_adjust(bottom=0.2) # organize the appearance for the pdf

    df.drop(['TaxlotAcre', 'Musym', 'Soil Type'], axis=1, inplace=True) # drop unwanted values for the csv
    df.to_csv(os.path.join(clippedSoils, "SoilsReport.csv")) #export to csv
    plt.savefig(os.path.join(clippedSoils, "SoilsReport.pdf"), bbox_inches='tight') # export table and chart combined on one pdf
    plt.close()

    # use arcpy.mp module to populate a layout and export a pdf map
    #--------------------------------------------------------------------------------------------

    aprx = arcpy.mp.ArcGISProject(arcproj) # assign project variable
    soilLayer = soilsShpfile # assign new variable for organizational purposes

    map = aprx.listMaps()[0]
    map.addDataFromPath(soilLayer) # add shapefile to the map
    print(f"{os.path.basename(soilLayer)} added to the map")

    soilsClip = map.listLayers()[0]
    sym = soilsClip.symbology

    attrList = [] # assign the unique value symbology
    if sym.renderer.type == 'SimpleRenderer':
        sym.updateRenderer('UniqueValueRenderer')
        sym.renderer.colorRamp = aprx.listColorRamps("Yellow-Orange-Brown (Continuous)")[0]
        with arcpy.da.SearchCursor(soilLayer, ['muname']) as cursor:
            for row in cursor:
                attrList.append(row[0])

    sym.renderer.addValues({"muname": [attrList]}) # add values to the symbology classes
    sym.renderer.fields = ['muname']
    soilsClip.symbology = sym

    print(f"Symbology set to --> {soilsClip.symbology.renderer.type}")

    lyts = aprx.listLayouts()[0]

    text6 = lyts.listElements()[0]
    text6.text = os.path.basename(os.path.dirname(soilsShpfile)) # assign tax lot ID to the title of the layout

    # create buffer to the increase the size of the map frame without adding it to the map
    arcpy.analysis.Buffer(soilsShpfile, r"memory\soilsBuffer", "100 Meters")
    desc_buffer = arcpy.Describe(r"memory\soilsBuffer")
    buff_ext = desc_buffer.extent
    print(f"Map frame extent set to --> {buff_ext}")

    mapElem = lyts.listElements("MAPFRAME_ELEMENT")[0]
    mapElem.camera.setExtent(buff_ext) # set map frame extent

    lyts.exportToPDF(os.path.join(os.path.dirname(soilsShpfile), "SoilMap.pdf")) # export map to pdf
    print("Map & report exported to pdf")
    aprx.saveACopy(os.path.join(os.path.dirname(soilsShpfile), "Soils.aprx")) # save a copy of the project to the new directory
    print("Project saved to directory")
    print(' ')
    del aprx

















