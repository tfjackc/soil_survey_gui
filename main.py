# import the necessary modules
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QCompleter,
    QFileDialog,
    QMessageBox,
    QPushButton,
    QTabBar
)
from func_file import *
from configparser import ConfigParser

# start main event loop
app = QApplication(sys.argv)
window = QMainWindow()
ui = gui.Ui_MainWindow()
ui.setupUi(window)


# create a ConfigParser object
config = ConfigParser()

# read the configuration file from disk
current_dir = os.path.dirname(sys.argv[0])
config.read(os.path.join(current_dir, 'config.ini'))


def config_inputs(Qobject, input): # create a function that write and save inputs in the GUI to a config file

    config.set('Paths', Qobject, input)  # write the selected file to a .ini config file to save values

    with open(os.path.join(current_dir, 'config.ini'), 'w') as configfile:
        config.write(configfile)

def selectTaxlotData():

    try:
        # select taxlot data to be uploaded
        filename, _ = QFileDialog.getOpenFileName(window, "Select Taxlot Layer", "", "(*.*)")
        if filename:
            print("selected file is " + filename)
            ui.importTaxlotLE.setText(filename) # set line edit value
            populateLotValues()
            config_inputs('importtaxlotle', filename)

            QMessageBox.information(window, "Information", f"{os.path.basename(filename)} Selected.")

            cb_list = [] #create an empty list to append taxlot values
            fields = arcpy.ListFields(filename)  # get fields from the selected shapefile and populate inputFieldsCB (comboBox)
            for listfields in fields:
                fieldList = listfields.name
                ui.taxlotIDCB.addItems([fieldList])
                cb_list.append(fieldList)
        else:
            print("File dialog got canceled.")

    except Exception as e:
        QMessageBox.information(window, 'operation failed', 'function failed with ' + str(e.__str__()) + ': ' + str(e),
                                QMessageBox.Ok)
        ui.statusbar.clearMessage()

# when the taxlot data is uploaded, the next section of code will populate the search bar with autocomplete of taxlot id's
# start typing "1515.." and the search bar will find the rest


def populateLotValues():

    try:
        lotList = []
        with arcpy.da.SearchCursor(ui.importTaxlotLE.text(), [ui.taxlotIDCB.currentText()]) as cursor:
            for r in cursor:
                lotList.append((r[0]))

        #set completeter to taxlot list
        completer = QCompleter(lotList)
        ui.taxlotSearchLE.setCompleter(completer)

    except Exception as e:
        QMessageBox.information(window, 'operation failed', 'function failed with ' + str(e.__str__()) + ': ' + str(e),
                                QMessageBox.Ok)
        ui.statusbar.clearMessage()


def projDir(): # choose a folder to store all the created outputs from the tool, the directory will begin by storing a new folder named by the taxlot id

    try:
        workspace = QFileDialog.getExistingDirectory(window, "Select Directory", "")
        if workspace:
            print("Selected directory is " + workspace)
            ui.workspaceLE.setText(workspace)

            config_inputs('workspacele', workspace)  # write the selected file to a .ini config file to save values

            QMessageBox.information(window, "Information", f"Folder '{os.path.basename(workspace)}' Selected.")
        else:
            print("File dialog got canceled.")
    except Exception as e:
        QMessageBox.information(window, 'operation failed', 'function failed with ' + str(e.__str__()) + ': ' + str(e),
                                QMessageBox.Ok)
        ui.statusbar.clearMessage()


def createFolder(): # create a folder to store two new shapefiles and arcpro project

    try:
        joinPath = os.path.join(ui.workspaceLE.text(), ui.taxlotSearchLE.text())
        folderPath = os.path.normpath(joinPath)
        # create new folder in the project directory for the new soil survey
        # if-else statement checks if the folder already exists in the directory
        if os.path.exists(folderPath):
            print('Folder already exists, please select another taxlot.') # print info to console
            QMessageBox.information(window, "Information", f"Project folder {os.path.basename(folderPath)} already exists.") # print info to message box
        else:
            os.mkdir(folderPath)
            print(f"New folder {folderPath} has been created.") # print info to console

            config_inputs('taxlotsearchle', str(os.path.basename(folderPath)))

            QMessageBox.information(window, "Information", f"New folder --> {os.path.basename(folderPath)} created.")  # print info to message box

    except Exception as e:
        QMessageBox.information(window, 'operation failed', 'function failed with ' + str(e.__str__()) + ': ' + str(e),
                                QMessageBox.Ok)
        ui.statusbar.clearMessage()


def createTarget(): # create the target shapefile, this will is the taxlot with the soils we are interested in, the shapefile will be used to intersect the soils data.

    try:
        print("...processing...")
        taxlot_id = ui.taxlotSearchLE.text() # grab taxlot id from the search bar, and use to query for its value in the taxlot data
        taxlots = ui.importTaxlotLE.text() # taxlot data containing the target taxlot
        output_file = os.path.join(ui.workspaceLE.text(), ui.taxlotSearchLE.text() + "\Target.shp") # name output file
        taxlot_field = ui.taxlotIDCB.currentText()

        createShpfile(taxlot_id, taxlots, output_file, taxlot_field) # call createShpfile function from func_file & create output file

        QMessageBox.information(window, "Information", f"{os.path.basename(output_file)} has been created in your new folder {os.path.join(ui.workspaceLE.text(), ui.taxlotSearchLE.text())}")
        print("...createShpfile function ran successfully...")
        print(f"{os.path.basename(output_file)} is stored in {os.path.normpath(os.path.dirname(output_file))}")

    except Exception as e:
        QMessageBox.information(window, 'operation failed', 'function failed with ' + str(e.__str__()) + ': ' + str(e),
                                QMessageBox.Ok)
        ui.statusbar.clearMessage()


def selectRhino(): # select the boundary used to determine which soils layer to pull data from

    rhino, _ = QFileDialog.getOpenFileName(window, "Select the Rhino Boundary Layer", "", "(*.*)")
    if rhino:
        print("selected file is " + os.path.basename(rhino))

        QMessageBox.information(window, "Information", f"{os.path.basename(rhino)} Selected.")
        ui.rhinoLE.setText(rhino)

        config_inputs('rhinole', rhino)  # write the selected file to a .ini config file to save values
    else:
        print("File dialog got canceled.")



def selectSoilLayer1(): # select soils layer "soilmumn_a_OR654.shp" --> inside the rhino data
    soils1, _ = QFileDialog.getOpenFileName(window, "Select Soils Layer", "", "(*.*)")
    if soils1:
        print("selected file is " + os.path.basename(soils1))

        QMessageBox.information(window, "Information", f"{os.path.basename(soils1)} Selected.")
        ui.SoilLayer1LE.setText(soils1)

        config_inputs('soillayer1le', soils1)  # write the selected file to a .ini config file to save values
    else:
        print("File dialog got canceled.")


def selectSoilLayer2(): # select soils layer "soilmumn_a_OR618_no654_DRAFT_01_2012.shp" --> outside the rhino data

    soils2, _ = QFileDialog.getOpenFileName(window, "Select Soils Layer", "", "(*.*)")
    if soils2:
        print("selected file is " + os.path.basename(soils2))

        QMessageBox.information(window, "Information", f"{os.path.basename(soils2)} Selected.")
        ui.SoilLayer2LE.setText(soils2)

        config_inputs('soillayer2le', soils2)  # write the selected file to a .ini config file to save values
    else:
        print("File dialog got canceled.")


def selectArcProj(): # select the arc project that contains the soilsLayout file --> pre made layout that will populate with new values provided by the script

    arcProject, _ = QFileDialog.getOpenFileName(window, "Select ArcGIS Pro Project with SoilsLayout", "", "(*.aprx)")
    if arcProject:
        print("selected file is " + os.path.basename(arcProject))
        print(str(arcProject))

        QMessageBox.information(window, "Information", f"{os.path.basename(arcProject)} Selected.")
        ui.arcprojLE.setText(arcProject)

        config_inputs('arcprojle', arcProject)  # write the selected file to a .ini config file to save values
        print(ui.arcprojLE.text())
    else:
        print("File dialog got canceled.")


def runSurvey(): # run the survey, call the selected and created shapefiles to complete the neccessary geoprocessing

    print('...processing...')
    targetShpfile = os.path.join(ui.workspaceLE.text(), ui.taxlotSearchLE.text() + "\Target.shp")
    clippedSoils = os.path.join(ui.workspaceLE.text(), ui.taxlotSearchLE.text())

    soils1 = ui.SoilLayer1LE.text()
    soils2 = ui.SoilLayer2LE.text()
    rhino = ui.rhinoLE.text()
    arcproj = ui.arcprojLE.text()

    try:
        surveyGP(soils1, soils2, targetShpfile, clippedSoils, rhino, arcproj) # call surveyGP function from func_file
        print("...tool has run successfully...")
        QMessageBox.information(window, "Information", f"Survey complete! \n \n New shapefile created and stored in "
                                                       f"{os.path.normpath(clippedSoils)} \n \n SoilMap & SoilReport exported to pdf & csv \n \n {arcproj} saved to directory")

    except Exception as e:
        QMessageBox.information(window, 'operation failed',
                                'surveyGP function failed with ' + str(e.__class__) + ': ' + str(e), QMessageBox.Ok)
        ui.statusbar.clearMessage()

# populate entry values from config file that saves the previously chosen inputs
#-------------------------------------------------------------
ui.importTaxlotLE.setText(config['Paths']['importtaxlotle'])
ui.taxlotIDCB.addItem(config['Paths']['taxlotidcb'])
ui.workspaceLE.setText(config['Paths']['workspacele'])
ui.rhinoLE.setText(config['Paths']['rhinole'])
ui.SoilLayer1LE.setText(config['Paths']['soillayer1le'])
ui.SoilLayer2LE.setText(config['Paths']['soillayer2le'])
ui.arcprojLE.setText(config['Paths']['arcprojle'])
#-------------------------------------------------------------

# connect buttons and selections in the GUI to the functions in the script
#-------------------------------------------------------------
ui.importTaxlotTB.clicked.connect(selectTaxlotData)
ui.workspaceTB.clicked.connect(projDir)
ui.createFolderPB.clicked.connect(createFolder)
ui.createTargetPB.clicked.connect(createTarget)
ui.SoilLayer1TB.clicked.connect(selectSoilLayer1)
ui.SoilLayer2TB.clicked.connect(selectSoilLayer2)
ui.RunSoilSurveyPB.clicked.connect(runSurvey)
ui.rhinoTB.clicked.connect(selectRhino)
ui.arcprojTB.clicked.connect(selectArcProj)
ui.taxlotIDCB.currentTextChanged.connect(populateLotValues)
#-------------------------------------------------------------

# show window, call populateLotValues() - only if the taxlot shapefile line edit has an input, and close the main event loop when exiting the GUI
window.show()
if ui.importTaxlotLE.text() != '':
    populateLotValues()
else:
    pass
sys.exit(app.exec_())



