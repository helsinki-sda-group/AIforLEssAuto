import sys
import sumolib
import random
import time
import xml.etree.ElementTree as ET
import re

NET_FILE = "kamppi.net.xml"
try:
    NUMBER_OF_CARS = int(sys.argv[1])
except:
    NUMBER_OF_CARS = 200
ROU_FILE = "TraCI_demo.rou.xml"

NET = sumolib.net.readNet(NET_FILE)

def main():
    random.seed(time.time())
    edges = NET.getEdges()
    numberOfEdges = len(edges)
    with open(ROU_FILE, "w") as f:
        writeTripFileBeginning(f)
        depart = 0.00
        addition = 100 / NUMBER_OF_CARS
        for i in range(NUMBER_OF_CARS):
            writeRandomTrip(f, edges, numberOfEdges, i, depart)
            # writeRandomRoute(f, edges, numberOfEdges, i)
            depart += addition
        writeTripFileEnd(f)
    
    # sortVehiclesByDeparture()

def writeTripFileBeginning(f):
    f.write("""<?xml version="1.0" encoding="UTF-8"?>\n<routes>\n""")
    f.write("""\t<vType id="type1" accel="0.8" decel="4.5" sigma="0.5" length="5" maxSpeed="40"/>\n\n""")

def writeRandomTrip(f, edges, numberOfEdges, i, depart):
    path = None
    while path == None:
        originEdgeStruct = edges[random.randint(0, numberOfEdges-1)]
        destinationEdgeStruct = edges[random.randint(0, numberOfEdges-1)]
        path = NET.getShortestPath(originEdgeStruct, destinationEdgeStruct)[0]
    originEdge = originEdgeStruct._id
    destinationEdge = destinationEdgeStruct._id
    strIndex = str(i)
    f.write("""\t<trip id="test_trip_{}" type="type1" depart="{}" from="{}" to="{}"/>\n""".format(strIndex, str(depart), originEdge, destinationEdge))

def writeRandomRoute(f, edges, numberOfEdges, i):
    path = None
    while path == None:
        originEdgeStruct = edges[random.randint(0, numberOfEdges-1)]
        destinationEdgeStruct = edges[random.randint(0, numberOfEdges-1)]
        path = NET.getShortestPath(originEdgeStruct, destinationEdgeStruct)[0]
    strIndex = str(i)
    f.write("""\t<vehicle id="test_trip_{}" type="type1" depart="{}.00">\n""".format(strIndex, strIndex))
    f.write("""\t\t<route edges="{}"/>\n""".format(" ".join([e.getID() for e in path])))
    f.write("""\t</vehicle>\n""")

def writeTripFileEnd(f):
    f.write("""</routes>""")

def sortVehiclesByDeparture():
    mainTree = ET.parse(ROU_FILE)
    mainRoot = mainTree.getroot()
    mainRoot[:] = sorted(mainRoot, key=lambda child: int(re.findall(r"([0-9]+).*", child.get("depart"))[0]))
    mainTree.write(ROU_FILE)

if __name__ == "__main__":
    sys.exit(main())