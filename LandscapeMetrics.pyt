import arcpy

class Toolbox(object):
    def __init__(self):
        self.label =  "LandscapeMetrics toolbox"
        self.alias  = "landscapemetrics"

        # List of tool classes associated with this toolbox
        self.tools = [LandscapeMetrics]

class LandscapeMetrics (object):
    def __init__(self):
        self.label       = "Calculate Proximity Index"
        self.description = "The Proximity Index is measured by deviding " + \
                           "the Distance to neighboring, features inside a pre defined area,  " + \
                           "trough the area of the feature itself."

    def getParameterInfo(self):
        #Define parameter definitions

        # Input Features parameter
        inputFeatureClass = arcpy.Parameter(
            displayName="Input Features",
            name="inputFeatureClass",
            datatype="Layer",
            parameterType="Required",
            direction="Input")

        # Index Name parameter
        # With Multivalue set to True, which allows for more indices to be selected at once
        proximityIndex = arcpy.Parameter(
            displayName="Proximity Index Algorithm",
            name="proximityIndex",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue = True)

        proximityIndex.filter.type = 'ValueList'
        proximityIndex.value = "PXfg"
        proximityIndex.filter.list = ["PX92","PXpt","PXfg","PX94"]

        # Buffer Distance parameter
        bufferDistance = arcpy.Parameter(
            displayName="Buffer Distance",
            name="bufferDistance",
            datatype="String",
            parameterType="Required",
            direction="Input")

        # Class Field parameter
        inputClassField = arcpy.Parameter(
            displayName="Class Field",
            name="inputClassField",
            datatype="Field",
            parameterType="Required",
            direction="Input")

        # Declare the dependencies to the InputFeature class
        # To get a Dropdown of the available Fields
        inputClassField.parameterDependencies = [inputFeatureClass.name]

        # Class Value parameter
        inputClassValue = arcpy.Parameter(
            displayName="Class Value",
            name="inputClassValue",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        # Derived Output Features parameter
        out_features = arcpy.Parameter(
            displayName="Output Features",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Derived",
            direction="Output")

        out_features.parameterDependencies = [inputFeatureClass.name]
        out_features.schema.clone = True

        # All parameters which are declared
        parameters = [inputFeatureClass, proximityIndex, bufferDistance, inputClassField, inputClassValue, out_features]

        return parameters

    def isLicensed(self): #optional
        return True

    def updateParameters(self, parameters): #optional
        # If else clause to enable or disable the Class Value parameter
        if parameters[3].value:
            parameters[4].enabled = True
            arcpy.AddMessage("Update for value in param 3")
        else:
            parameters[4].enabled = False
        return

    def updateMessages(self, parameters): #optional
        return

    def execute(self, parameters, messages):

        # Get all Input Parameters and store them in variables.
        inputFeatureClass   = parameters[0].valueAsText
        fieldName           = parameters[1].valueAsText
        bufferDistance      = parameters[2].valueAsText
        inputClassField     = parameters[3].valueAsText
        inputClassValue     = parameters[4].valueAsText

        # Deselect any previous selected features, since this might interfer with the following tools
        arcpy.SelectLayerByAttribute_management(inputFeatureClass,'CLEAR_SELECTION')

        # Split the fieldName input at a ; (for multivalue input)
        fieldNames = fieldName.split(";")
        arcpy.AddMessage("Indices to calculate :")
        # For loop to create as many fields in the attribute table as indices selected
        for x in range(len(fieldNames)):
            # The name of the newly created field is a string, combined of the Index Field and the buffer distance
            fieldnameClean = fieldNames[x]+ "_" + str(bufferDistance)
            arcpy.AddMessage(fieldnameClean)
            arcpy.AddField_management(inputFeatureClass, fieldnameClean, 'DOUBLE')

        # Some message output for clarity
        arcpy.AddMessage("Input Feature Class : " + inputFeatureClass)
        arcpy.AddMessage("Buffer Distance : " + bufferDistance)
        arcpy.AddMessage("Class Field : " + inputClassField)
        arcpy.AddMessage("Class Value : " + inputClassValue)
        # Creation of more fields which will be filled later on
        arcpy.AddField_management(inputFeatureClass, 'NNDistance', 'DOUBLE')
        arcpy.AddField_management(inputFeatureClass, 'NNArea', 'DOUBLE')
        arcpy.AddField_management(inputFeatureClass, 'NNFID', 'DOUBLE')
        # SQL expression which is used in the Cursors (To only select Features of the same type)
        expression1 = arcpy.AddFieldDelimiters(inputFeatureClass, inputClassField) + ' = ' + '\''+inputClassValue+'\''

        #Create a search cursor using an SQL expression
        with arcpy.da.SearchCursor(inputFeatureClass, ['SHAPE@' ,inputClassField,'OID@','SHAPE@area'], where_clause=expression1) as cursor:
            for row in cursor:
                # Instantiation of variables
                keyFields = []
                indexPXfg = 0
                areaT = 0
                dist = 0
                indexPXpt = 0
                indexPX92 = 0
                indexPX94 = 0
                indexFG = 0
                # Print the ID of the current Row(Feature)
                arcpy.AddMessage("Id of the current Feature : " + str(row[2]))

                # Create a buffer around the feature, represented by the row[0]
                # Use the bufferDistance Parameter as the distance value
                featureSelectForBuffer = arcpy.Buffer_analysis(row[0], "C:/Temp/WaldBuffered", int(bufferDistance))

                # Select all features from the input feature class which itersect the buffer
                featureInsideBuffer = arcpy.SelectLayerByLocation_management(inputFeatureClass, 'INTERSECT',featureSelectForBuffer )
                # Do a subselection of the selected Features, which have the Class field set to the wanted value
                featureInsideBufferOfCorrectType = arcpy.SelectLayerByAttribute_management(inputFeatureClass, "SUBSET_SELECTION", inputClassField + " = " + '\'' + inputClassValue + '\'' )

                # Use the Near function to calulate the closest distaces to each feature of the correct class, inside the buffer
                featureNear = arcpy.Near_analysis(featureInsideBufferOfCorrectType, row[0],'Meters','NO_LOCATION','NO_ANGLE','GEODESIC')
                arcpy.AddMessage(featureNear)

                # Create another Search Cursor
                # This one now got the NEAR_DIST as a field, as well as the area of the row
                with arcpy.da.SearchCursor(featureNear, ['SHAPE@area',inputClassField, 'NEAR_DIST' ,'OID@','NEAR_FID' ], where_clause=expression1) as cursor1:
                    for rows in cursor1:
                        # If the currect Row isnt the Row of the current Feature which we are looking at, then proceed :
                        if rows[3] != row[2]:
                            # If the Distance to the next Feature isnt 0, then proceed:
                            # This is only the case in which the feature and its nearest feature, are sharing a border or are inside of eachother or there is no feature of the same class inside the buffer.
                            if rows[2] != 0:
                                indexPXfg = indexPXfg + rows[0] / (rows[2] * rows[2])
                            listOfNearFeature = [rows[3], rows[0], rows[2]]
                            # Append this list to another list. (A list inside a list)
                            keyFields.append(listOfNearFeature)
                            # Create a Sorted list in which the first entry is allways a list describing the needed parameters of the nearest features field. Sorted by Distance to nearest Neighbor
                            sortedList = sorted(keyFields, key=lambda item: item[2])
                            # Get the needed Values of areaT and Distance

                            nnFID = sortedList[0][0]
                            areaT = sortedList[0][1]
                            dist =  sortedList[0][2]
                            areaF = row[3]

                            # Caluclate the PX92 Index by areaT(of the target patch) / distance (between the target and focal patch)

                            for x in range(len(fieldNames)):
                                fieldnameClean = fieldNames[x]+ "_" + str(bufferDistance)
                                if dist != 0 and fieldnameClean == "PX92_" + str(bufferDistance):
                                    indexPX92 = areaT/dist
                            # Caluclate the PX92 Index by areaF(of the fokal patch) / distance (between the target and focal patch)
                            for x in range(len(fieldNames)):
                                fieldnameClean = fieldNames[x]+ "_" + str(bufferDistance)
                                if dist != 0 and fieldnameClean == "PXpt_" + str(bufferDistance):
                                    indexPXpt  = areaF / dist
                # Use an update Cursor to update the attribute table with the NNDistance NN Area and NNID
                with arcpy.da.UpdateCursor(inputFeatureClass, ['OID@', 'NNDistance','NNArea', 'NNFID'], where_clause=expression1) as cursor3:
                    for row3 in cursor3:
                        if row3[0] == row[2]:
                            row3[1] = dist
                            row3[2] = areaT
                            row3[3] = nnFID
                            cursor3.updateRow(row3)
                for x in range(len(fieldNames)):
                    fieldnameClean = fieldNames[x]+ "_" + str(bufferDistance)
                    if fieldnameClean == "PX94_" + str(bufferDistance):
                        # Use a search Cursor to calculate the PX94
                        with arcpy.da.SearchCursor(inputFeatureClass, ['SHAPE@Area' ,inputClassField,'OID@','NNDistance','NNArea', 'NNFID'], where_clause=expression1) as cursor4:
                            for row4 in cursor4:
                                # If the Distance isnt 0 proceed
                                if row4[3] != 0:
                                    # The index is calculated by Sum of Area / NNDistance of every object in the cursor4
                                    dist92 = row4[3]
                                    area92 = row4[0]
                                    indexPX94 = indexPX94 + area92/dist92

                # For loop, to loop through all fieldNames which got created and update each with its value
                for x in range(len(fieldNames)):
                    fieldnameClean = fieldNames[x]+ "_" + str(bufferDistance)
                    # Use an update Cursor to update the index Field (fieldName) with the newly calculated index
                    with arcpy.da.UpdateCursor(inputFeatureClass, [fieldnameClean,'OID@'], where_clause=expression1) as cursor5:
                        for row5 in cursor5:
                            if row5[1] == row[2]:
                                arcpy.AddMessage(fieldnameClean)
                                # If clause to see which index is currently beeing updated
                                if fieldnameClean == "PXpt_" + str(bufferDistance):
                                    row5[0] = float(indexPXpt)
                                elif fieldnameClean == "PXfg_" + str(bufferDistance):
                                    row5[0] = float(indexPXfg)
                                elif fieldnameClean == "PX92_" + str(bufferDistance):
                                    row5[0] = float(indexPX92)
                                elif fieldnameClean == "PX94_" + str(bufferDistance):
                                    row5[0] = float(indexPX94)
                                cursor5.updateRow(row5)
                # Write the calculated indices into the ArcGis message box
                for x in range(len(fieldNames)):
                    fieldnameClean = fieldNames[x]+ "_" + str(bufferDistance)
                    if fieldnameClean == "PXpt_" + str(bufferDistance):
                        arcpy.AddMessage("Index PXpt from feature ID " + str(row[2]) + " : " + str(indexPXpt))
                    elif fieldnameClean == "PXfg_" + str(bufferDistance):
                        arcpy.AddMessage("Index PXfg from feature ID " + str(row[2]) + " : " + str(indexPXfg))
                    elif fieldnameClean == "PX92_" + str(bufferDistance):
                        arcpy.AddMessage("Index PX92 from feature ID " + str(row[2]) + " : " + str(indexPX92))
                    elif fieldnameClean == "PX94_" + str(bufferDistance):
                        arcpy.AddMessage("Index PX94 from feature ID " + str(row[2]) + " : " + str(indexPX94))
                arcpy.AddMessage("*------------------------*")
        # Deleting the fields NEAR_DIST and NEAR_FID since they only have values for the last calculated row
        arcpy.DeleteField_management(inputFeatureClass, ["NEAR_DIST", "NEAR_FID"])
