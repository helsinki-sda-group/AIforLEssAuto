# ----------------------------------------------------------------------
# Copyright (c) 2023 University of Helsinki SDA group
# @file    fcdDataExtractionV7.py
# @author  Anton Taleiko
# @date    Wed May 3 2023
# ----------------------------------------------------------------------
# For creating a reduced simulation with randomness for edges in Helsinki from
# fcd output from an instance of the large simulation.
# In version 7 it is assumed that the reduced area is a square. This is to improve
# resource efficiency by not having to store out-out vehicles until the end of the
# program's exection.
# The sets used in the class fcdInformationExtracter have also been replaced by
# NumPy arrays to improve performance.

# NOTE: It has not been checked how well the results of this version correspond to
# those produced by version 5 since version 7 was only an intermediate step towards
# version 8.

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
REDUCED_AREA_TAZ_FILE = "sumo_files/helsinki_box_edges.taz.xml"
ROU_FILE = "sumo_files/verified_trips.rou.xml"
NET_FILE = "sumo_files/whole_area.net.xml"
try:
    DEPARTURE_OUTPUT_FILE = sys.argv[1]
except:
    DEPARTURE_OUTPUT_FILE = "data/fcd_analysis/departure_times_V7.xlsx"
OUTPUT_COLUMNS = ["fromX", "fromY", "toX", "toY", "depart"]
MOCK_ROU_FILE = "tests/test_files/mock_trips.rou.xml"
REDUCED_AREA_MIN_LAT = 60.132311 # y: 64540.64
REDUCED_AREA_MAX_LAT = 60.301523 # y: 83332.12
REDUCED_AREA_MIN_LON = 24.826718 # x: 130522.98
REDUCED_AREA_MAX_LON = 25.260729 # x: 154756.69
SECOND_LAST_TIME_STEP = "3598.00" # 1 hour
# SECOND_LAST_TIME_STEP = "7198.00" # 2 hours
EMPTY = "----------------------------------------"
PERFORMANCE_TEST = True

if PERFORMANCE_TEST:
    startTime = datetime.now()
    print("Start time:\n", startTime.strftime("%H:%M:%S"))

print("Reading the network (whole Helmet area)")
NET = sumolib.net.readNet(NET_FILE)

def readReducedAreaEdges():
    tree = ET.parse(REDUCED_AREA_TAZ_FILE)
    tazs = tree.getroot()
    helsinkiEdges = set()
    for taz in tazs:
        helsinkiEdges.update(taz.attrib["edges"].split(" "))
    return helsinkiEdges

REDUCED_AREA_EDGES = readReducedAreaEdges()

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
        # self.inVehicles = np.full(len(ORIGINS), False) # TODO Remove all instances of this variable and replace it with reducedAreaVehicles
        self.processedVehicles = np.full(len(ORIGINS), False)
        self.originMemory = np.full(len(ORIGINS), EMPTY)
        self.departureMemory = np.full(len(ORIGINS), EMPTY)
        self.extVehicleGeoDepartures = pd.DataFrame(np.nan, index=range(len(ORIGINS)), columns=OUTPUT_COLUMNS)
        self.addedDepartures = 0
        self.destinationMemory = np.full(len(ORIGINS), EMPTY)
        self.vehicleMemoryMisses = 0


    def extractInformationFromFcdFile(self, file=FCD_FILE):
        print("Parsing the trajectory file...")
        treeIterator = ET.iterparse(file)
        print("Getting the time steps...")
        lastTimeStep = False
        timeStep = "0.00"
        for iteratorItem in treeIterator:
            element = iteratorItem[1]
            elementTag = element.tag
            if elementTag == "timestep":
                timeStep = self.addOneToTimeStep(self.getTimeFromElement(element))
                if timeStep == SECOND_LAST_TIME_STEP:
                    lastTimeStep = True
                print(timeStep, end="\r")
            elif elementTag == "vehicle":
                if lastTimeStep:
                    self.finalTimeStepProcedure(element)
                else:
                    self.regularVehicleProcedure(element, timeStep)

        self.postProcess()
        self.outputResults()
        self.performanceResults()

    def outputResults(self, departureOutputFile=DEPARTURE_OUTPUT_FILE):
        print("Saving vehicle information...")
        self.extVehicleGeoDepartures.to_excel(departureOutputFile)

    def regularVehicleProcedure(self, vehicle, timeStep, originTazs=VEH_TO_ORIGIN_TAZ, destinationTazs=VEH_TO_DESTINATION_TAZ):
        id = self.getVehicleId(vehicle)
        edge = self.getVehicleEdge(vehicle)
        if self.vehicleIsInReducedArea(vehicle):
            if not self.vehicleInVehicleSet(id, self.processedVehicles):
                if not self.vehicleInVehicleSet(id, self.reducedAreaVehicles):
                    self.newVehicleProcedure(id, vehicle, timeStep, originTazs, destinationTazs)
                # Not needed when the reduced area is a square
                # elif self.vehicleInVehicleSet(id, self.outVehicles):
                #     self.outVehicleProcedure(id, edge, vehicle, timeStep, destinationTazs)
                elif self.vehicleInVehicleSet(id, self.reducedAreaVehicles):
                    self.vehicleProcedure(id, edge, vehicle, originTazs, destinationTazs)

    def finalTimeStepProcedure(self, vehicle):
        id = self.getVehicleId(vehicle)
        if self.vehicleInVehicleSet(id, self.reducedAreaVehicles):
            if not self.vehicleInVehicleSet(id, self.processedVehicles):
                # if self.vehicleInVehicleSet(id, self.inVehicles):
                self.destinationMemory[id] = self.createVehicleCoordinates(vehicle)

    def newVehicleProcedure(self, id, vehicle, timeStep, originTazs, destinationTazs):
        if self.vehicleIsInInVehicle(id, originTazs, destinationTazs):
            self.addVehicleToVehicleSet(id, self.processedVehicles)
        else:
            self.addVehicleToVehicleSet(id, self.reducedAreaVehicles)
            # self.addVehicleToVehicleSet(id, self.inVehicles)
            self.departureMemory[id] = timeStep
            if self.vehicleIsInOutVehicle(id, originTazs, destinationTazs):
                self.originMemory[id] = originTazs[id]
            else:
                self.originMemory[id] = self.createVehicleCoordinates(vehicle)

    def vehicleProcedure(self, id, edge, vehicle, originTazs, destinationTazs):
        if self.vehicleHasExitedReducedArea(edge):
            if self.vehicleIsOutOutVehicle(id, originTazs, destinationTazs):# out-out vehicle
                self.addGeoDeparture(self.originMemory[id], self.createVehicleCoordinates(vehicle), self.departureMemory[id])
                # self.destinationMemory[int(id)] = self.createVehicleCoordinates(vehicle)
                # self.addVehicleToVehicleSet(id, self.outVehicles)
            else:
                originTaz = originTazs[id]
                if self.originInHelsinki(originTaz):# in-out vehicle
                    # self.originMemory[int(id)] = VEH_TO_ORIGIN_TAZ[id]
                    # self.destinationMemory[int(id)] = self.createVehicleCoordinates(vehicle)
                    self.addGeoDeparture(originTaz, self.createVehicleCoordinates(vehicle), self.departureMemory[id])
                # The other case would be that the vehicle actually started outside Helsinki,
                # but was classified as having started indside, because it was on an edge
                # that stretches within the area
            # self.removeVehicleFromVehicleSet(id, self.inVehicles)
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

    def vehicleIsInOutVehicle(self, id, originTazs, destinationTazs):
        originInHelsinki = originTazs[id] in rt.REDUCED_AREA_TAZS
        destinationOutsideHelsinki = destinationTazs[id] not in rt.REDUCED_AREA_TAZS
        if originInHelsinki and destinationOutsideHelsinki:
            return True
        return False

    def vehicleIsOutOutVehicle(self, id, originTazs, destinationTazs):
        originOutsideHelsinki = originTazs[id] not in rt.REDUCED_AREA_TAZS
        destinationOutsideHelsinki = destinationTazs[id] not in rt.REDUCED_AREA_TAZS
        if originOutsideHelsinki and destinationOutsideHelsinki:
            return True
        return False

    def vehicleIsInInVehicle(self, id, originTazs, destinationTazs):
        originInHelsinki = originTazs[id] in rt.REDUCED_AREA_TAZS
        destinationInHelsinki = destinationTazs[id] in rt.REDUCED_AREA_TAZS
        if originInHelsinki and destinationInHelsinki:
            return True
        return False

    def vehicleIsInReducedArea(self, vehicle):
        lon = self.getVehicleLon(vehicle)
        lat = self.getVehicleLat(vehicle)
        vehicleIsWithinLon = lon > REDUCED_AREA_MIN_LON and lon < REDUCED_AREA_MAX_LON
        vehicleIsWithinLat = lat > REDUCED_AREA_MIN_LAT and lat < REDUCED_AREA_MAX_LAT
        return vehicleIsWithinLon and vehicleIsWithinLat

    def vehicleHasEnteredHelsinki(self, edge):
        return edge in REDUCED_AREA_EDGES

    def vehicleHasExitedReducedArea(self, edge):
        return edge not in REDUCED_AREA_EDGES

    def originInHelsinki(self, origin):
        return origin in rt.REDUCED_AREA_TAZS

    def destinationInReducedArea(self, destination):
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

    def addOneToTimeStep(self, timeStep):
        timeStep = int(re.findall(r"(\d+).\d+", timeStep)[0])
        timeStep += 1
        return str(timeStep) + ".00"

    def addVehicleToVehicleSet(self, id, vehicleSet):
        vehicleSet[id] = True

    def removeVehicleFromVehicleSet(self, id, vehicleSet):
        vehicleSet[id] = False

    def vehicleInVehicleSet(self, id, vehicleSet):
        return vehicleSet[id] == True

    def createVehicleCoordinates(self, vehicle):
        return " ".join([str(self.getVehicleLon(vehicle)), str(self.getVehicleLat(vehicle))])

    def calculateDistance(self, x1, y1, x2, y2):
        return np.sqrt(np.square(x2 - x1) + np.square(y2 - y1))

    def getTimeFromElement(self, timeStep):
        return timeStep.attrib["time"]

    def getVehicleLon(self, vehicle):
        return float(vehicle.attrib["x"])

    def getVehicleLat(self, vehicle):
        return float(vehicle.attrib["y"])

    def getVehicleEdge(self, vehicle):
        return re.findall(r"(.*)_\d", vehicle.attrib["lane"])[0]

    def getVehicleId(self, vehicle):
        return int(vehicle.attrib["id"])


if __name__ == '__main__':
    sys.exit(main())
