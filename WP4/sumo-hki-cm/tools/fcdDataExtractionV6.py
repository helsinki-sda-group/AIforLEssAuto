# ----------------------------------------------------------------------
# Copyright (c) 2023 University of Helsinki SDA group
# @file    fcdDataExtractionV6.py
# @author  Anton Taleiko
# @date    Wed May 3 2023
# ----------------------------------------------------------------------
# For creating a reduced simulation with randomness for edges in Helsinki from
# fcd output from an instance of the large simulation.
# Version 6 uses iterative parsing instead of reading the whole trajectory file at once.

# NOTE: It has not been checked how well the results of this version correspond to those
# produced by version 5 since version 6 was only an intermediate step towards version 8.

import sys
import xml.etree.ElementTree as ET
import numpy as np
import re
import helsinkiTazs as rt
import sumolib
import pandas as pd

# NOTE This variable should be set to false when the file is run normally,
# otherwise things will not work as they should
TESTING = False

FCD_FILE = "sumo_files/simulation_output/fcdresults.xml"
HELSINKI_ZONES_FILE = "data/sijoittelualueet2019.dbf"
HELSINKI_BEG_INDEX = 1013
HELSINKI_END_INDEX = 1394
REDUCED_AREA_TAZ_FILE = "sumo_files/helsinki_edges.taz.xml"
ROU_FILE = "sumo_files/verified_trips.rou.xml"
NET_FILE = "sumo_files/whole_area.net.xml"
try:
    DEPARTURE_OUTPUT_FILE = sys.argv[1]
except:
    DEPARTURE_OUTPUT_FILE = "data/fcd_analysis/departure_times_V6.xlsx"
OUTPUT_COLUMNS = ["fromX", "fromY", "toX", "toY", "depart"]
MOCK_ROU_FILE = "tests/test_files/mock_trips.rou.xml"
REDUCED_AREA_MIN_LAT = 60.130824
REDUCED_AREA_MAX_LAT = 60.303178
REDUCED_AREA_MIN_LON = 24.774271
REDUCED_AREA_MAX_LON = 25.427476
SECOND_LAST_TIME_STEP = "7198.00"

print("Reading the network (whole Helmet area)")
NET = sumolib.net.readNet(NET_FILE)

# def readHelsinkiTazs():
#     table = Dbf5(HELSINKI_ZONES_FILE).to_dataframe()
#     tazs = set(np.array(["po_" + str(int(zone)) for zone in table["SIJ2019"].iloc[HELSINKI_BEG_INDEX:HELSINKI_END_INDEX]]))
#     return tazs

# HELSINKI_TAZS = readHelsinkiTazs()

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
        self.reducedAreaVehicles = set()
        self.outVehicles = set()
        self.inVehicles = set()
        self.originMemory = {}
        self.processedVehicles = set()
        self.departureMemory = {}
        self.extVehicleGeoDepartures = pd.DataFrame(np.nan, index=range(len(ORIGINS)), columns=OUTPUT_COLUMNS)
        self.addedDepartures = 0
        self.destinationMemory = {}
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

    def outputResults(self, departureOutputFile=DEPARTURE_OUTPUT_FILE):
        print("Saving vehicle information...")
        self.extVehicleGeoDepartures.to_excel(departureOutputFile)

    def regularVehicleProcedure(self, vehicle, timeStep, originTazs=VEH_TO_ORIGIN_TAZ, destinationTazs=VEH_TO_DESTINATION_TAZ):
        id = self.getVehicleId(vehicle)
        edge = self.getVehicleEdge(vehicle)
        if self.vehicleIsInReducedArea(vehicle):
            if not self.vehicleInVehicleSet(id, self.processedVehicles):
                if not self.vehicleInVehicleSet(id, self.reducedAreaVehicles):
                    self.newVehicleProcedure(id, edge, timeStep, originTazs, destinationTazs)
                elif self.vehicleInVehicleSet(id, self.outVehicles):
                    self.outVehicleProcedure(id, edge, vehicle, timeStep, destinationTazs)
                elif self.vehicleInVehicleSet(id, self.inVehicles):
                    self.inVehicleProcedure(id, edge, vehicle, originTazs, destinationTazs)

    def finalTimeStepProcedure(self, vehicle, destinationTazs=VEH_TO_DESTINATION_TAZ):
        id = self.getVehicleId(vehicle)
        if self.vehicleInVehicleSet(id, self.reducedAreaVehicles):
            if not self.vehicleInVehicleSet(id, self.processedVehicles):
                if self.vehicleInVehicleSet(id, self.inVehicles):
                    if not self.destinationInHelsinki(destinationTazs[id]):# in-out vehicle
                        self.destinationMemory[id] = self.createVehicleCoordinates(vehicle)

    def newVehicleProcedure(self, id, edge, timeStep, originTazs, destinationTazs):
        self.addVehicleToVehicleSet(id, self.reducedAreaVehicles)
        if edge in REDUCED_AREA_EDGES:
            if self.vehicleIsInInVehicle(id, originTazs, destinationTazs):
                self.addVehicleToVehicleSet(id, self.processedVehicles)
            else:
                self.addVehicleToVehicleSet(id, self.inVehicles)
                self.departureMemory[id] = timeStep
        else:
            self.addVehicleToVehicleSet(id, self.outVehicles)

    def outVehicleProcedure(self, id, edge, vehicle, timeStep, destinationTazs):
        if self.vehicleHasEnteredHelsinki(edge):
            destination = destinationTazs[id]
            time = timeStep
            if self.destinationInHelsinki(destination):# out-in vehicle
                currentPosition = self.createVehicleCoordinates(vehicle)
                self.addGeoDeparture(currentPosition, VEH_TO_DESTINATION_TAZ[id], time)
                self.removeVehicleFromVehicleSet(id, self.outVehicles)
                self.addVehicleToVehicleSet(id, self.processedVehicles)
            else:# out-out vehicle
                if not self.vehicleAlreadyInMemory(id, self.originMemory):
                    # Has already entered Helsinki once, but exited again
                    self.originMemory[id] = self.createVehicleCoordinates(vehicle)
                    self.departureMemory[id] = time
                self.removeVehicleFromVehicleSet(id, self.outVehicles)
                self.addVehicleToVehicleSet(id, self.inVehicles)

    def inVehicleProcedure(self, id, edge, vehicle, originTazs, destinationTazs):
        if self.vehicleHasExitedReducedArea(edge):
            if self.vehicleIsOutOutVehicle(id, originTazs, destinationTazs):# out-out vehicle
                self.destinationMemory[id] = self.createVehicleCoordinates(vehicle)
                self.removeVehicleFromVehicleSet(id, self.inVehicles)
                self.addVehicleToVehicleSet(id, self.outVehicles)
            else:
                originTaz = originTazs[id]
                if self.originInHelsinki(originTaz):# in-out vehicle
                    self.originMemory[id] = VEH_TO_ORIGIN_TAZ[id]
                    self.destinationMemory[id] = self.createVehicleCoordinates(vehicle)
                    self.removeVehicleFromVehicleSet(id, self.inVehicles)
                    self.addVehicleToVehicleSet(id, self.outVehicles)
                # The other case would be that the vehicle actually started outside Helsinki,
                # but was classified as having started indside, because it was on an edge
                # that stretches within the area

    def postProcess(self):
        self.saveOutOutVehicles()
        self.wipeMemoryDetails()

    def saveOutOutVehicles(self):
        for id in self.destinationMemory.keys():
            try:
                self.addGeoDeparture(self.originMemory[id], self.destinationMemory[id], self.departureMemory[id])
            except:
                self.vehicleMemoryMisses += 1
                if id not in self.originMemory.keys():
                    print("ID {} not found in origin memory".format(id))
                if id not in self.destinationMemory.keys():
                    print("ID {} not found in destination memory".format(id))
                if id not in self.departureMemory.keys():
                    print("ID {} not found in departure memory".format(id))
        if not TESTING:
            print("Out out vehicle save fail rate:", self.vehicleMemoryMisses / len(self.destinationMemory))

    def wipeMemoryDetails(self):
        self.originMemory.clear()
        self.destinationMemory.clear()
        self.departureMemory.clear()
        self.processedVehicles.clear()

    def vehicleAlreadyInMemory(self, id, memory):
        return id in memory.keys()

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

    # def addRandomDeparture(self, origin, destination, time):
    #     originCoords = origin.split(" ")
    #     if len(originCoords) == 2:
    #         newEntry = {"fromX": float(originCoords[0]), "fromY": float(originCoords[1]), "toX": destination, "toY": np.nan, "depart": time}
    #     else:
    #         newEntry = {"fromX": float(originCoords[0]), "fromY": np.nan, "toX": destination, "toY": np.nan, "depart": time}

    def addOneToTimeStep(self, timeStep):
        timeStep = int(re.findall(r"(\d+).\d+", timeStep)[0])
        timeStep += 1
        return str(timeStep) + ".00"

    def addVehicleToVehicleSet(self, id, vehicleSet):
        vehicleSet.add(id)

    def removeVehicleFromVehicleSet(self, id, vehicleSet):
        return vehicleSet.remove(id)

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

    def vehicleInVehicleSet(self, id, vehicleSet):
        return id in vehicleSet


if __name__ == '__main__':
    sys.exit(main())
