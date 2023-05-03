# ----------------------------------------------------------------------
# Copyright (c) 2023 University of Helsinki SDA group
# @file    fcdDataExtractionV8.py
# @author  Anton Taleiko
# @date    Wed May 3 2023
# ----------------------------------------------------------------------
# For creating a reduced simulation with randomness for edges in Helsinki from
# fcd output from an instance of the large simulation.
# Version has the same performance improvements as version 7, but parses the xml file
# line by line and extracts information with regular expressions instead of parsing it
# using the ElementTree module.

import sys
import xml.etree.ElementTree as ET
import numpy as np
import re
import helsinkiTazs as rt
import sumolib
import pandas as pd
from datetime import datetime

# NOTE This variable should be set to false when the file is run normally,
# otherwise things will not work as they should
TESTING = False

FCD_FILE = "sumo_files/simulation_output/fcdresults.xml"
HELSINKI_ZONES_FILE = "data/sijoittelualueet2019.dbf"
HELSINKI_BEG_INDEX = 1013
HELSINKI_END_INDEX = 1394
ROU_FILE = "sumo_files/verified_trips.rou.xml"
NET_FILE = "sumo_files/whole_area.net.xml"
try:
    DEPARTURE_OUTPUT_FILE = sys.argv[1]
except:
    DEPARTURE_OUTPUT_FILE = "data/fcd_analysis/departure_times_V8.xlsx"
OUTPUT_COLUMNS = ["fromX", "fromY", "toX", "toY", "depart"]
MOCK_ROU_FILE = "tests/test_files/tripsV8.rou.xml"
REDUCED_AREA_MIN_LAT = 60.12944609762057
REDUCED_AREA_MAX_LAT = 60.304555035913104
REDUCED_AREA_MIN_LON = 24.83855347458583
REDUCED_AREA_MAX_LON = 25.257191247107986
SECOND_LAST_TIME_STEP = "3598.00" # 1 hour
# SECOND_LAST_TIME_STEP = "7198.00" # 2 hours
EMPTY = "----------------------------------------"
PERFORMANCE_TEST = True

if PERFORMANCE_TEST:
    startTime = datetime.now()
    print("Start time:\n", startTime.strftime("%H:%M:%S"))

print("Reading the network (whole Helmet area)")
NET = sumolib.net.readNet(NET_FILE)

def createIdToCoordMaps(file=ROU_FILE):
    tree = ET.parse(file)
    originArray = createVehToAttributeArray(tree, "from")
    destinationArray = createVehToAttributeArray(tree, "to")
    return originArray, destinationArray

def createVehToAttributeArray(tree, attribute):
    trips = tree.getroot()
    idToAttributeCoordinates = np.full(len(trips), "00.000000 00.000000")
    for trip in trips:
        attributes = trip.attrib
        coordinates = edgeToLonLat(attributes[attribute])
        coordinatesString = " ".join([str(coordinates[0])[0:9], str(coordinates[1])[0:9]])
        idToAttributeCoordinates[int(attributes["id"])] = coordinatesString
    return idToAttributeCoordinates

def edgeToLonLat(edge):
    edge = NET.getEdge(edge)
    node = edge.getToNode()
    coords = node.getCoord()
    lonLat = NET.convertXY2LonLat(coords[0], coords[1])
    return lonLat

def createVehToAttributeTazMap(attribute):
    if TESTING:
        tree = ET.parse(MOCK_ROU_FILE)
    else:
        tree = ET.parse(ROU_FILE)
    trips = tree.getroot()
    idToTazArray = np.full(len(trips), "po_xxxxx")
    for trip in trips:
        attributes = trip.attrib
        idToTazArray[int(attributes["id"])] = attributes[attribute]
    return idToTazArray

if TESTING:
    ORIGINS, DESTINATIONS = createIdToCoordMaps(MOCK_ROU_FILE)
else:
    ORIGINS, DESTINATIONS = createIdToCoordMaps()

VEH_TO_ORIGIN_TAZ = createVehToAttributeTazMap("fromTaz")
VEH_TO_DESTINATION_TAZ = createVehToAttributeTazMap("toTaz")

def main():
    extracter = fcdInformationExtracter()
    extracter.extractInformationFromFcdFile()

class fcdInformationExtracter:
    def __init__(self):
        self.reducedAreaVehicles = np.full(len(ORIGINS), False)
        self.processedVehicles = np.full(len(ORIGINS), False)
        self.originMemory = np.full(len(ORIGINS), EMPTY)
        self.departureMemory = np.full(len(ORIGINS), EMPTY)
        self.extVehicleGeoDepartures = pd.DataFrame(np.nan, index=range(len(ORIGINS)), columns=OUTPUT_COLUMNS)
        self.addedDepartures = 0
        self.destinationMemory = np.full(len(ORIGINS), EMPTY)
        self.vehicleMemoryMisses = 0


    def extractInformationFromFcdFile(self, fcdFile=FCD_FILE, departureOutputFile=DEPARTURE_OUTPUT_FILE):
        print("Getting the time steps...")
        lastTimeStep = False
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
                        timeStep = self.getTimeFromElement(line)
                        if timeStep == SECOND_LAST_TIME_STEP:
                            lastTimeStep = True
                        print(timeStep, end="\r")
                    elif elementTag == "vehicle":
                        if lastTimeStep:
                            self.finalTimeStepProcedure(line)
                        else:
                            self.regularVehicleProcedure(line, timeStep)
                line = f.readline()

        self.postProcess()
        self.outputResults(departureOutputFile)
        self.performanceResults()

    def outputResults(self, departureOutputFile=DEPARTURE_OUTPUT_FILE):
        print("Saving vehicle information...")
        self.extVehicleGeoDepartures.to_excel(departureOutputFile)

    def regularVehicleProcedure(self, vehicleLine, timeStep, originTazs=VEH_TO_ORIGIN_TAZ, destinationTazs=VEH_TO_DESTINATION_TAZ):
        id = self.getVehicleId(vehicleLine)
        if self.vehicleIsInReducedArea(vehicleLine):
            if not self.vehicleInVehicleSet(id, self.processedVehicles):
                if not self.vehicleInVehicleSet(id, self.reducedAreaVehicles):
                    self.newVehicleProcedure(id, vehicleLine, timeStep, originTazs, destinationTazs)
        elif self.vehicleInVehicleSet(id, self.reducedAreaVehicles):#has exited the reduced area
            self.vehicleProcedure(id, vehicleLine, originTazs, destinationTazs)

    def finalTimeStepProcedure(self, vehicleLine):
        id = self.getVehicleId(vehicleLine)
        if self.vehicleInVehicleSet(id, self.reducedAreaVehicles):
            if not self.vehicleInVehicleSet(id, self.processedVehicles):
                self.destinationMemory[id] = self.createVehicleCoordinates(vehicleLine)

    def newVehicleProcedure(self, id, vehicleLine, timeStep, originTazs, destinationTazs):
        if self.vehicleIsInInVehicle(id, originTazs, destinationTazs):#in-in
            self.addVehicleToVehicleSet(id, self.processedVehicles)
        elif self.vehicleIsInOutVehicle(id, originTazs, destinationTazs):#in-out
            self.addVehicleToVehicleSet(id, self.reducedAreaVehicles)
            self.departureMemory[id] = timeStep
            self.originMemory[id] = originTazs[id]
        elif self.vehicleIsOutInVehicle(id, originTazs, destinationTazs):#out-in
            self.addGeoDeparture(self.createVehicleCoordinates(vehicleLine), destinationTazs[id], timeStep)
            self.addVehicleToVehicleSet(id, self.processedVehicles)
        elif self.vehicleIsOutOutVehicle(id, originTazs, destinationTazs):#out-out, if clause could be removed
            self.addVehicleToVehicleSet(id, self.reducedAreaVehicles)
            self.departureMemory[id] = timeStep
            self.originMemory[id] = self.createVehicleCoordinates(vehicleLine)

    def vehicleProcedure(self, id, vehicleLine, originTazs, destinationTazs):
        if self.vehicleIsOutOutVehicle(id, originTazs, destinationTazs):# out-out vehicle
            self.addGeoDeparture(self.originMemory[id], self.createVehicleCoordinates(vehicleLine), self.departureMemory[id])
        else:#in-out
            originTaz = originTazs[id]
            if self.originInHelsinki(originTaz):# in-out vehicle
                self.addGeoDeparture(originTaz, self.createVehicleCoordinates(vehicleLine), self.departureMemory[id])
            # The other case would be that the vehicle actually started outside Helsinki,
            # but was classified as having started indside, because it was on an edge
            # that stretches within the area
        self.removeVehicleFromVehicleSet(id, self.reducedAreaVehicles)
        self.addVehicleToVehicleSet(id, self.processedVehicles)

    def postProcess(self):
        self.saveRemainingVehicles()

    def performanceResults(self):
        if PERFORMANCE_TEST:
            finishTime = datetime.now()
            print("Finish time:\n", finishTime.strftime("%H:%M:%S"))
            print("Execution time:\n", finishTime - startTime)

    def saveRemainingVehicles(self):
        for id in range(len(self.destinationMemory)):#self.destinationMemory.keys():
            if self.destinationMemory[id] != EMPTY:
                try:
                    self.addGeoDeparture(self.originMemory[id], self.destinationMemory[int(id)], self.departureMemory[int(id)])
                except:
                    self.vehicleMemoryMisses += 1
                    if self.originMemory[id] == EMPTY:
                        print("ID {} not found in origin memory".format(id))
                    if self.destinationMemory[id] == EMPTY:
                        print("ID {} not found in destination memory".format(id))
                    if self.departureMemory[id] == EMPTY:
                        print("ID {} not found in departure memory".format(id))
        if not TESTING:
            print("Out out vehicle save fail rate:", self.vehicleMemoryMisses / len(self.destinationMemory))

    def vehicleIsInInVehicle(self, id, originTazs, destinationTazs):
        originInHelsinki = originTazs[id] in rt.REDUCED_AREA_TAZS
        destinationInHelsinki = destinationTazs[id] in rt.REDUCED_AREA_TAZS
        if originInHelsinki and destinationInHelsinki:
            return True
        return False

    def vehicleIsInOutVehicle(self, id, originTazs, destinationTazs):
        originInHelsinki = originTazs[id] in rt.REDUCED_AREA_TAZS
        destinationOutsideHelsinki = destinationTazs[id] not in rt.REDUCED_AREA_TAZS
        if originInHelsinki and destinationOutsideHelsinki:
            return True
        return False
    
    def vehicleIsOutInVehicle(self, id, originTazs, destinationTazs):
        originOutsideHelsinki = originTazs[id] not in rt.REDUCED_AREA_TAZS
        destinationInHelsinki = destinationTazs[id] in rt.REDUCED_AREA_TAZS
        if originOutsideHelsinki and destinationInHelsinki:
            return True
        return False

    def vehicleIsOutOutVehicle(self, id, originTazs, destinationTazs):
        originOutsideHelsinki = originTazs[id] not in rt.REDUCED_AREA_TAZS
        destinationOutsideHelsinki = destinationTazs[id] not in rt.REDUCED_AREA_TAZS
        if originOutsideHelsinki and destinationOutsideHelsinki:
            return True
        return False

    def vehicleIsInReducedArea(self, vehicleLine):
        lon = self.getVehicleLon(vehicleLine)
        lat = self.getVehicleLat(vehicleLine)
        vehicleIsWithinLon = lon > REDUCED_AREA_MIN_LON and lon < REDUCED_AREA_MAX_LON
        vehicleIsWithinLat = lat > REDUCED_AREA_MIN_LAT and lat < REDUCED_AREA_MAX_LAT
        return vehicleIsWithinLon and vehicleIsWithinLat

    def originInHelsinki(self, origin):
        return origin in rt.REDUCED_AREA_TAZS

    def destinationInHelsinki(self, destination):
        return destination in rt.REDUCED_AREA_TAZS


    def addGeoDeparture(self, origin, destination, time):
        originCoords = origin.split(" ")
        destinationCoords = destination.split(" ")
        if len(originCoords) == 2:
            if len(destinationCoords) == 2:# out-out
                newEntry = {"fromX": float(originCoords[0]), "fromY": float(originCoords[1]), "toX": float(destinationCoords[0]), "toY": float(destinationCoords[1]), "depart": time}
            else:# out-in
                newEntry = {"fromX": float(originCoords[0]), "fromY": float(originCoords[1]), "toX": destinationCoords[0], "toY": np.nan, "depart": time}
        else:# in-out
            newEntry = {"fromX": originCoords[0], "fromY": np.nan, "toX": float(destinationCoords[0]), "toY": float(destinationCoords[1]), "depart": time}
        self.extVehicleGeoDepartures.iloc[self.addedDepartures] = newEntry
        self.addedDepartures += 1

    def addVehicleToVehicleSet(self, id, vehicleSet):
        vehicleSet[id] = True

    def removeVehicleFromVehicleSet(self, id, vehicleSet):
        vehicleSet[id] = False

    def vehicleInVehicleSet(self, id, vehicleSet):
        return vehicleSet[id] == True

    def createVehicleCoordinates(self, vehicleLine):
        return " ".join([str(self.getVehicleLon(vehicleLine)), str(self.getVehicleLat(vehicleLine))])

    def calculateDistance(self, x1, y1, x2, y2):
        return np.sqrt(np.square(x2 - x1) + np.square(y2 - y1))

    def getTimeFromElement(self, timeStepLine):
        return re.findall(r"time=\"(\d+.\d+)\"", timeStepLine)[0]

    def getVehicleLon(self, vehicleLine):
        return float(re.findall(r"x=\"(\d+.\d+)\"", vehicleLine)[0])

    def getVehicleLat(self, vehicleLine):
        return float(re.findall(r"y=\"(\d+.\d+)\"", vehicleLine)[0])

    def getVehicleEdge(self, vehicleLine):
        return re.findall(r"lane=\"([\w#-:]+)_\d+\"", vehicleLine)[0]

    def getVehicleId(self, vehicleLine):
        return int(re.findall(r"id=\"(\d+)\"", vehicleLine)[0])


if __name__ == '__main__':
    sys.exit(main())
