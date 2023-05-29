# ----------------------------------------------------------------------
# Copyright (c) 2023 University of Helsinki SDA group
# @file    odMatrixReduction.py
# @author  Anton Taleiko
# @date    Wed May 29 2023
# ----------------------------------------------------------------------
# For reducing an origin-destination matrix to a subset of origin/destination
# zones. The inputs are the SUMO FCD file from a simulation of the whole area
# and a .taz file containing the wanted subset of zones with their edges.

import sys
import xml.etree.ElementTree as ET
import numpy as np
import re
import helsinkiTazs as rt
from simpledbf import Dbf5
import openmatrix as omx
from datetime import datetime

FCD_FILE = "sumo_files/simulation_output/fcdresults.xml"
REDUCED_AREA_TAZS_FILE = "sumo_files/reduced_cut_districts.taz.xml"
ROU_FILE = "sumo_files/verified_trips.rou.xml"
DBF_FILE = "data/sijoittelualueet2019.dbf"
DBF_INDICES_COLUMN = "FID_1"
DBF_ID_COLUMN = "SIJ2019"
OUTPUT_MATRIX_FILE = "data/od_matrix_reduction/reduced_od_matrix.omx"
OUTPUT_MISS_LOG_FILE = "data/od_matrix_reduction/miss_log.txt"

PERFORMANCE_TEST = True

def main():
    if PERFORMANCE_TEST:
        print(datetime.now())
    mr = odMatrixReducer()
    mr.matrixReduction()
    if PERFORMANCE_TEST:
        print(datetime.now())

class odMatrixReducer:
    def __init__(self, reducedAreaTazsFile=REDUCED_AREA_TAZS_FILE):
        self.vehToOriginTaz = self.createVehToAttributeTazMap("fromTaz")
        self.vehToDestinationTaz = self.createVehToAttributeTazMap("toTaz")
        self.tazToIndex = self.createZoneIdToIndexMap()

        self.reducedOdMatrix = np.zeros((2035,2035), dtype=int)
        self.reducedEdgeSet, self.edgeToTaz = self.createTazSets(reducedAreaTazsFile)
        self.outOutOriginMemory = np.full(len(self.vehToOriginTaz), -1, dtype=int)

        self.processedVehicles = set()
        self.recordedInOutVehicles = np.full(len(self.vehToOriginTaz), False, dtype=bool)
        self.recordedOutInVehicles = np.full(len(self.vehToOriginTaz), False, dtype=bool)
        self.recordedOutOutVehicles = np.full(len(self.vehToOriginTaz), False, dtype=bool)
        self.lastRecordedTazInReducedArea = np.full(len(self.vehToOriginTaz), "po_xxxxx")

        self.inInMisses = 0
        self.inOutMisses = 0
        self.outInMisses = 0
        self.outOutMisses = 0


    def matrixReduction(self, fcdFile=FCD_FILE):
        print("Getting the time steps...")
        # lastTimeStep = False
        timeStep = "0.00"
        with open(fcdFile, "r") as f:
            line = f.readline()
            while len(re.findall(r"<timestep", line)) == 0:
                line = f.readline()
            while line:
                elementTagSearch = re.findall(r"<([a-z]+)\s", line)
                if len(elementTagSearch) > 0:
                    elementTag = elementTagSearch[0]
                    if elementTag == "timestep":
                        timeStep = self.getTimeFromTimeStepElement(line)
                        # if timeStep == SECOND_LAST_TIME_STEP:
                            # lastTimeStep = True
                        print(timeStep, end="\r")
                    elif elementTag == "vehicle":
                        # if lastTimeStep:
                        #     self.finalTimeStepProcedure(line)
                        # else:
                        self.vehicleProcedure(line)
                line = f.readline()
        self.postProcedure()
        self.writeMatrixToFile()
        self.writeMissLog()

    def writeMatrixToFile(self, outputFile=OUTPUT_MATRIX_FILE):
        omxMatrixFile = omx.open_file(outputFile, "w")
        omxMatrixFile["traffic"] = self.reducedOdMatrix
        omxMatrixFile.close()

    def writeMissLog(self, outputFile=OUTPUT_MISS_LOG_FILE):
        with open(outputFile, "w") as f:
            f.writelines("".join(["in-in misses: ", str(self.inInMisses), "\n"]))
            f.writelines("".join(["in-out misses: ",  str(self.inOutMisses), "\n"]))
            f.writelines("".join(["out-in misses: ", str(self.outInMisses), "\n"]))
            f.writelines("".join(["out-out misses: ", str(self.outOutMisses), "\n"]))

    def vehicleProcedure(self, vehicleLine):
        id = int(self.getIdFromVehicleElement(vehicleLine))
        if id in self.processedVehicles:
            return
        originInReducedArea = self.originIsInReducedArea(id)
        destinationInReducedArea = self.destinationIsInReducedArea(id)
        if originInReducedArea:
            if destinationInReducedArea:#in-in
                self.inInVehicleProcedure(id)
            else:#in-out
                self.inOutVehicleProcedure(id, vehicleLine)
        elif destinationInReducedArea:#out-in
            self.outInVehicleProcedure(id, vehicleLine)
        else:#out-out
            self.outOutVehicleProcedure(id, vehicleLine)

    def inInVehicleProcedure(self, id):
        originIndex = self.tazToIndex[self.vehToOriginTaz[id]]
        destinationIndex = self.tazToIndex[self.vehToDestinationTaz[id]]
        self.addOneToOdMatrix(originIndex, destinationIndex, self.inInMisses)
        self.processedVehicles.add(id)

    def inOutVehicleProcedure(self, id, vehicleLine):
        if self.vehicleIsInReducedArea(vehicleLine):
            self.recordedInOutVehicles[id] = True
            vehicleEdge = self.getVehicleEdge(vehicleLine)
            self.lastRecordedTazInReducedArea[id] = self.edgeToTaz[vehicleEdge]

    def outInVehicleProcedure(self, id, vehicleLine):#The same as in-out but with a separate set 
        if self.vehicleIsInReducedArea(vehicleLine):
            self.recordedOutInVehicles[id] = True
            self.lastRecordedTazInReducedArea[id] = self.edgeToTaz[self.getVehicleEdge(vehicleLine)]

    def outOutVehicleProcedure(self, id, vehicleLine):
        if self.outOutOriginMemory[id] == -1:#Has not entered the reduced area before
            if self.vehicleIsInReducedArea(vehicleLine):
                self.recordedOutOutVehicles[id] = True
                entryTaz = self.edgeToTaz[self.getVehicleEdge(vehicleLine)]
                self.outOutOriginMemory[id] = self.tazToIndex[entryTaz]
                self.lastRecordedTazInReducedArea[id] = entryTaz
        else:
            if self.vehicleIsInReducedArea(vehicleLine):
                self.lastRecordedTazInReducedArea[id] = self.edgeToTaz[self.getVehicleEdge(vehicleLine)]

    def postProcedure(self):
        self.saveInOutVehicles()
        self.saveOutInVehicles()
        self.saveOutOutVehicles()

    def saveInOutVehicles(self):
        for id in range(len(self.recordedInOutVehicles)):
            if self.recordedInOutVehicles[id] == True:
                originIndex = self.tazToIndex[self.vehToOriginTaz[id]]
                destinationIndex = self.tazToIndex[self.lastRecordedTazInReducedArea[id]]
                self.addOneToOdMatrix(originIndex, destinationIndex, self.inOutMisses)

    def saveOutInVehicles(self):
        for id in range(len(self.recordedOutInVehicles)):
            if self.recordedOutInVehicles[id] == True:
                originIndex = self.tazToIndex[self.lastRecordedTazInReducedArea[id]]
                destinationIndex = self.tazToIndex[self.vehToDestinationTaz[id]]
                self.addOneToOdMatrix(originIndex, destinationIndex, self.outInMisses)

    def saveOutOutVehicles(self):
        for id in range(len(self.recordedOutOutVehicles)):
            if self.recordedOutOutVehicles[id] == True:
                originIndex = self.outOutOriginMemory[id]
                destinationIndex = self.tazToIndex[self.lastRecordedTazInReducedArea[id]]
                self.addOneToOdMatrix(originIndex, destinationIndex, self.outOutMisses)

    def addOneToOdMatrix(self, originIndex, destinationIndex, missLog):
        try:
            self.reducedOdMatrix[originIndex, destinationIndex] += 1
        except:
            missLog += 1

    def vehicleIsInReducedArea(self, vehicleLine):
        return self.getVehicleEdge(vehicleLine) in self.reducedEdgeSet
    
    def getVehicleEdge(self, vehicleLine):
        return re.findall(r"lane=\"([\w#-:]+)_\d+\"", vehicleLine)[0]

    def extractEdgeFromLane(self, lane):
        edge = re.findall(r"([\-\w#]+)_\d+", lane)[0]
        return edge

    def originIsInReducedArea(self, id):
        return self.vehToOriginTaz[id] in rt.REDUCED_AREA_TAZS
    
    def destinationIsInReducedArea(self, id):
        return self.vehToDestinationTaz[id] in rt.REDUCED_AREA_TAZS

    def getIdFromVehicleElement(self, vehicleLine):
        return int(re.findall(r"id=\"(\d+)\"", vehicleLine)[0])

    def addOneToTimeStep(self, timeStep):
        timeStep = int(re.findall(r"(\d+).\d+", timeStep)[0])
        timeStep += 1
        return str(timeStep) + ".00"

    def getXmlIterator(self, fcdFile=FCD_FILE):
        return ET.iterparse(fcdFile)
    
    def getTimeFromTimeStepElement(self, timeStepLine):
        return re.findall(r"time=\"(\d+.\d+)\"", timeStepLine)[0]

    def createTazSets(self, reducedAreaTazsFile=REDUCED_AREA_TAZS_FILE):
        tree = ET.parse(reducedAreaTazsFile)
        tazs = tree.getroot()
        reducedAreaEdges = self.createReducedAreaEdgesSet(tazs)
        edgeToTaz = self.createEdgeToTazMap(tazs)
        return (reducedAreaEdges, edgeToTaz)
    
    def createReducedAreaEdgesSet(self, tazXmlTreeRoot):
        reducedAreaEdges = set()
        for taz in tazXmlTreeRoot:
            edges = taz.attrib["edges"].split(" ")
            reducedAreaEdges.update(edges)
        return reducedAreaEdges

    def createEdgeToTazMap(self, tazXmlTreeRoot):
        edgeToTaz = {}
        for taz in tazXmlTreeRoot:
            tazId = taz.attrib["id"]
            for edge in taz.attrib["edges"].split(" "):
                edgeToTaz[edge] = tazId
        return edgeToTaz

    def createVehToAttributeTazMap(self, attribute, rouFile=ROU_FILE):
        tree = ET.parse(rouFile)
        trips = tree.getroot()
        idToTazArray = np.full(len(trips), "po_xxxxx")
        for trip in trips:
            attributes = trip.attrib
            idToTazArray[int(attributes["id"])] = attributes[attribute]
        return idToTazArray

    def createZoneIdToIndexMap(self, dbfFile=DBF_FILE):
        zoneIds, zoneIndexes = self.readZonesAndIndexes(dbfFile)
        tazToIndexMap = {}
        for i in range(len(zoneIds)):
            tazToIndexMap[zoneIds[i]] = zoneIndexes[i]
        return tazToIndexMap#, zoneIndexes

    def readZonesAndIndexes(self, dbfFile=DBF_FILE):
        table = Dbf5(dbfFile).to_dataframe()
        numberOfRows = len(table[DBF_INDICES_COLUMN])
        ids = np.full(numberOfRows, "po_xxxxx")
        indexes = np.full(numberOfRows, -1, dtype=int)
        for i in range(len(table[DBF_INDICES_COLUMN])):
            zoneIndexString = self.extractZoneNumberFromDoubleString(str(table[DBF_ID_COLUMN][i]))
            ids[i] = "po_" + zoneIndexString
            indexes[i] = table[DBF_INDICES_COLUMN][i]
        return (ids, indexes)
    
    def extractZoneNumberFromDoubleString(self, doubleStr):
        return re.findall(r"(\d+).\d+", doubleStr)[0]


if __name__ == '__main__':
    sys.exit(main())