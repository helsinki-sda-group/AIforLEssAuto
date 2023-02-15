import sys
import openmatrix as omx
import math
from simpledbf import Dbf5
import random
from datetime import datetime

DB_FILE = "data/sijoittelualueet2019.dbf"
DBF_INDICES_COLUMN = "FID_1"
DBF_NAME_COLUMN = "SIJ2019"
OUTPUT_FILE = "sumo_files/OD_file.od"
OD_MATRIX_FILE = "data/demand_aht.omx"
MATRICES = ["car_work", "car_leisure", "van"]
IGNORED_ZONES = set([231, 291, 368, 381, 12030, 1246, 1247, 1313, 1331, 1531, 1532, 1351, 1570, 9203, 9220, 14381, 17504, 17507, 12000, 12030, 20000, 27060, 27070])
# Potential working zones with higher map accuracy:
# 14381, 20000 forest (some other small zones nearby too in the original data, not included, check osmToPolyConverterv3.py)
try:
    SCALING_FACTOR = float(sys.argv[1])
    print("Scaling factor set to {}.".format(SCALING_FACTOR))
except:
    SCALING_FACTOR = 1
    print("Scaling factor set to {}, add a numerical value as argument to change.".format(SCALING_FACTOR))

def main():
    random.seed(int(datetime.now().strftime("%Y%m%d%H%M%S")))
    zoneIdMap, zoneIndexes = createZoneIdMap()
    tripTriple = createOdTrips(zoneIdMap, zoneIndexes)
    writeFileBeginning()
    writeOdPart(tripTriple[0], tripTriple[1], tripTriple[2], OUTPUT_FILE)



def createOdTrips(zoneIdMap, zoneIndexes):
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

def getWholeCars(tripCars):
    scaledTripCars = SCALING_FACTOR * tripCars
    wholeCars = math.floor(scaledTripCars)
    probabilityForExtraCar = scaledTripCars % 1
    if random.random() < probabilityForExtraCar:
        wholeCars += 1
    return wholeCars


def writeOdPart(origins, destinations, nCars, outputFile):
    with open(outputFile, "a") as f:
        for i in range(len(origins)):
            if origins[i] not in IGNORED_ZONES and destinations[i] not in IGNORED_ZONES:
                f.write("         po_{}          po_{}       {}.00\n".format(str(origins[i]), str(destinations[i]), str(nCars[i])))

def createZoneIdMap():
    zoneIds, zoneIndexes = readZonesAndIndexes()
    zoneIdMap = {}
    for i in range(len(zoneIds)):
        zoneIdMap[zoneIndexes[i]] = zoneIds[i]
    return zoneIdMap, zoneIndexes

def readZonesAndIndexes():
    table = Dbf5(DB_FILE).to_dataframe()
    ids = []
    indexes = []
    for i in range(len(table[DBF_INDICES_COLUMN])):
        ids.append(int(table[DBF_NAME_COLUMN][i]))
        indexes.append(table[DBF_INDICES_COLUMN][i])
    return (ids, indexes)


def getWantedMatrices():
    od = readOdMatrixFile(OD_MATRIX_FILE)
    return [od[matrix] for matrix in MATRICES]

def readOdMatrixFile(file):
    return omx.open_file(file, "r")


def writeFileBeginning():
    with open(OUTPUT_FILE, "w") as f:
        f.write("""$OR;D2
* From-Time  To-Time
0.00 0.01
* Factor
1.00
* some
* additional
* comments\n""")


if __name__ == '__main__':
    sys.exit(main())