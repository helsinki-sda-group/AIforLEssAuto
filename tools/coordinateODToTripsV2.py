import sys
import pandas as pd
import sumolib
import xml.etree.ElementTree as ET
import openmatrix as omx
import math
import random
from simpledbf import Dbf5
from datetime import datetime
import re

INPUT_FILE = "data/fcd_analysis/departure_times_V5.xlsx"
OUTPUT_FILE = "sumo_files/reduced_geo_trips_V2.rou.xml"
NET_FILE = "sumo_files/reduced_area.net.xml"
OD_MATRIX_FILE = "data/demand_aht.omx"
DBF_FILE = "data/sijoittelualueet2019.dbf"
HELSINKI_TAZ_FILE = "sumo_files/reduced_districts.taz.xml"

ORIGIN_X_COLUMN = "fromX"
ORIGIN_Y_COLUMN = "fromY"
DESTINATION_X_COLUMN = "toX"
DESTINATION_Y_COLUMN = "toY"
DEPART_COLUMN = "depart"
MATRICES = ["car_work", "car_leisure", "van"]
HELSINKI_BEG_INDEX = 1013
HELSINKI_END_INDEX = 1394
IGNORED_ZONES = set([231, 291, 368, 381, 1246, 1247, 1313, 1331, 1531, 1532, 1351, 1570])
SIMULATION_END = 3600

NET = sumolib.net.readNet(NET_FILE)

def main():
    random.seed(int(datetime.now().strftime("%Y%m%d%H%M%S")))
    writeFileBeginning()
    id = 0
    global tazEdges
    tazEdges = readTazs()
    id += createInInTrips(id)
    writeExtTrips(id)
    writeFileEnd()
    # Messes up duarouter's process for some reason
    # sortTrips()
    # orderIds()


# Code from visumRouteGenerationV2.py
def createInInTrips(existingIds):
    zoneIdMap, zoneIndexes = createHelsinkiZoneIdMap()
    helsinkiTripTriple = createHelsinkiTrips(zoneIdMap, zoneIndexes)
    return createTrips(helsinkiTripTriple[0], helsinkiTripTriple[1], helsinkiTripTriple[2], existingIds, OUTPUT_FILE)


def createTrips(origins, destinations, nCars, existingIds, outputFile):
    id = existingIds
    global tazEdges
    with open(outputFile, "a") as f:
        for i in range(len(origins)):
            if origins[i] not in IGNORED_ZONES and destinations[i] not in IGNORED_ZONES:
                # print(i)
                # TODO CONTINUE FROM HERE
                for j in range(nCars[i]):
                    depart = random.randint(0, SIMULATION_END)
                    originTazInt = origins[i]
                    randomOriginEdgeIndex = random.randint(0, len(tazEdges[originTazInt])-1)
                    originEdges = tazEdges[originTazInt]
                    # print("origins", originEdges)
                    originEdge = originEdges[randomOriginEdgeIndex]
                    destinationTazInt = destinations[i]
                    randomDestinationEdgeIndex = random.randint(0, len(tazEdges[destinationTazInt])-1)
                    destinationEdges = tazEdges[destinationTazInt]
                    # print("destinations", destinationEdges)
                    destinationEdge = destinationEdges[randomDestinationEdgeIndex]
                    f.write("    <trip id=\"{}\" depart=\"{}.00\" from=\"{}\" to=\"{}\" departLane=\"free\" departSpeed=\"max\"/>\n".format(str(id), str(depart), originEdge, destinationEdge))
                    id += 1
    return id

def readTazs():
    intTazs = {}
    tree = ET.parse(HELSINKI_TAZ_FILE)
    root = tree.getroot()
    for taz in root:
        id = taz.attrib["id"]
        intId = int(re.findall(r"po_(\d+)", id)[0])
        intTazs[intId] = taz.attrib["edges"].split(" ")
    return intTazs

# def readStringTazs():
#     tazs = {}
#     tree = ET.parse(HELSINKI_TAZ_FILE)
#     root = tree.getroot()
#     for taz in root:
#         id = taz.attrib["id"]
#         id = re.findall(r"(po_\d+)", id)[0]
#         tazs[id] = taz.attrib["edges"].split(" ")
#     return tazs

def createHelsinkiZoneIdMap():
    zoneIds, zoneIndexes = readHelsinkiZonesAndIndexes()
    zoneIdMap = {}
    for i in range(len(zoneIds)):
        zoneIdMap[zoneIndexes[i]] = zoneIds[i]
    return zoneIdMap, zoneIndexes

def readHelsinkiZonesAndIndexes():
    table = Dbf5(DBF_FILE).to_dataframe()
    ids = []
    indexes = []
    for i in range(HELSINKI_BEG_INDEX, HELSINKI_END_INDEX):
        ids.append(int(table["SIJ2019"][i]))
        indexes.append(table["FID_1"][i])
    return (ids, indexes)

def createHelsinkiTrips(zoneIdMap, zoneIndexes):
    origins = []
    destinations = []
    nCars = []
    matrices = getWantedMatrices()

    for origin in zoneIndexes:
        for destination in zoneIndexes:
            tripCars = 0.0
            for matrix in matrices:
                tripCars += matrix[origin,destination]
            wholeCars = getWholeCars(tripCars)
            if wholeCars > 0:
                nCars.append(wholeCars)
                origins.append(zoneIdMap[origin])
                destinations.append(zoneIdMap[destination])
    return (origins, destinations, nCars)

def getWantedMatrices():
    od = readOdMatrixFile(OD_MATRIX_FILE)
    return [od[matrix] for matrix in MATRICES]

def readOdMatrixFile(file):
    return omx.open_file(file, "r")

def getWholeCars(tripCars):
    wholeCars = math.floor(tripCars)
    probabilityForExtraCar = tripCars % 1
    if random.random() < probabilityForExtraCar:
        wholeCars += 1
    return wholeCars

def sortTrips():
    tree = ET.parse(OUTPUT_FILE)
    root = tree.getroot()
    root[:] = sorted(root, key=lambda child: float(child.get("depart")))
    tree.write(OUTPUT_FILE)

def orderIds():
    tree = ET.parse(OUTPUT_FILE)
    root = tree.getroot()
    for i in range(len(root)):
        root[i].attrib["id"] = str(i)
    # root[:] = sorted(root, key=lambda child: float(child.get("depart")))
    tree.write(OUTPUT_FILE)

def writeFileBeginning(outputFile=OUTPUT_FILE):
    with open(outputFile, "w") as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n""")

def createTripRow(id, originEdge, destinationEdge, depart):
    return "    <trip id=\"{}\" depart=\"{}\" from=\"{}\" to=\"{}\" departLane=\"free\" departSpeed=\"max\"/>\n".format(id, depart, originEdge, destinationEdge)

def appendToOutputFile(output):
    with open(OUTPUT_FILE, "a") as f:
        f.write(output)

def writeFileEnd(outputFile=OUTPUT_FILE):
    with open(outputFile, "a") as f:
        f.write("</routes>")


def writeExtTrips(existingIds):
    table = readGeoTable()
    output = ""
    id = existingIds
    global outOfBoundsErrors
    outOfBoundsErrors = 0
    # tripClassTables = extTripsByClass(table)
    # tripCreationFunctions = [createInOutTrips, createOutInTrips, createOutInTrips]
    inOutTrips, outInTrips, outOutTrips = extTripsByClass(table)

    # for tripClassTable, tripCreationFunction in tripClassTables, tripCreationFunctions:
    #     outputExtension, id = tripCreationFunction(tripClassTable, id)
    #     output += outputExtension
    outputExtension, id = createInOutTrips(inOutTrips, id)
    output += outputExtension
    outputExtension, id = createOutInTrips(outInTrips, id)
    output += outputExtension
    outputExtension, id = createOutOutTrips(outOutTrips, id)
    output += outputExtension
    print("Out of bounds errors:", outOfBoundsErrors)

    appendToOutputFile(output)

def extTripsByClass(table):
    originIsTazFilter = table[ORIGIN_Y_COLUMN].isnull()
    destinationIsTazFilter = table[DESTINATION_Y_COLUMN].isnull()

    inOutFilter = [originIsTaz and (not destinationIsTaz) for originIsTaz, destinationIsTaz in zip(originIsTazFilter, destinationIsTazFilter)]
    outInFilter = [(not originIsTaz) and destinationIsTaz for originIsTaz, destinationIsTaz in zip(originIsTazFilter, destinationIsTazFilter)]
    outOutFilter = [(not originIsTaz) and (not destinationIsTaz) for originIsTaz, destinationIsTaz in zip(originIsTazFilter, destinationIsTazFilter)]
    
    inOutTrips = table[inOutFilter]
    outInTrips = table[outInFilter]
    outOutTrips = table[outOutFilter]
    return inOutTrips, outInTrips, outOutTrips

def createInOutTrips(inOutTrips, id):
    outputExtension = ""
    global outOfBoundsErrors
    global tazEdges
    for row in inOutTrips.iloc:
        try:
            originEdge = pickRandomEdgeFromTaz(tazEdges, row[ORIGIN_X_COLUMN])
            destinationEdge = findClosestEdge(row[DESTINATION_X_COLUMN], row[DESTINATION_Y_COLUMN])
            depart = row[DEPART_COLUMN]
            outputExtension += createTripRow(str(id), originEdge, destinationEdge, depart)
            id += 1
        except:
            outOfBoundsErrors += 1
    return outputExtension, id

def createOutInTrips(outInTrips, id):
    outputExtension = ""
    global outOfBoundsErrors
    global tazEdges
    for row in outInTrips.iloc:
        try:
            originEdge = findClosestEdge(row[ORIGIN_X_COLUMN], row[ORIGIN_Y_COLUMN])
            destinationEdge = pickRandomEdgeFromTaz(tazEdges, row[DESTINATION_X_COLUMN])
            depart = row[DEPART_COLUMN]
            outputExtension += createTripRow(str(id), originEdge, destinationEdge, depart)
            id += 1
        except:
            outOfBoundsErrors += 1
    return outputExtension, id

def createOutOutTrips(outOutTrips, id):
    outputExtension = ""
    global outOfBoundsErrors
    global tazEdges
    for row in outOutTrips.iloc:
        try:
            originEdge = findClosestEdge(row[ORIGIN_X_COLUMN], row[ORIGIN_Y_COLUMN])
            destinationEdge = findClosestEdge(row[DESTINATION_X_COLUMN], row[DESTINATION_Y_COLUMN])
            depart = row[DEPART_COLUMN]
            outputExtension += createTripRow(str(id), originEdge, destinationEdge, depart)
            id += 1
        except:
            outOfBoundsErrors += 1
    return outputExtension, id

def findClosestEdge(lon, lat, radius=40):
    # print(lon, lat)
    x, y = NET.convertLonLat2XY(lon, lat)
    edges = NET.getNeighboringEdges(x, y, radius)
    # print(x, y)
    # print(edges)
    # if len(edges) == 0:
    #     print("No edges found")
    # Example from SUMO's documentation, causes errors when there are two edges with the same distance
    # distancesAndEdges = sorted([(edge) for edge, dist in edges])
    distancesAndEdges = sorted(edges, key=lambda x: x[1])
    # print(distancesAndEdges)
    closestEdge, dist = distancesAndEdges[0]
    return closestEdge.getID()# edges[0][0].getID()

def pickRandomEdgeFromTaz(tazEdges, taz):
    edges = tazEdges[int(taz[3:len(taz)])]
    return edges[random.randint(0, len(edges)-1)]


def readGeoTable():
    table = pd.read_excel(INPUT_FILE, index_col=0)
    table = table[table[DEPART_COLUMN].notnull()]
    return table


if __name__ == '__main__':
    sys.exit(main())