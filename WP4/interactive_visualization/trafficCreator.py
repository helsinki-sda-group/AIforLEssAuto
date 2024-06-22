import sys
import sumolib
import random
import time
import xml.etree.ElementTree as ET
import re
import numpy as np

NET_FILE = "kamppi.net.xml"
try:
    NUMBER_OF_CARS = int(sys.argv[1])
    SIMULATION_END = int(sys.argv[2])
except:
    SIMULATION_END = 600
    NUMBER_OF_CARS = 400
ROU_FILE = "TraCI_demo.rou.xml"

NET = sumolib.net.readNet(NET_FILE)

def main():
    random.seed(time.time())
    edges = NET.getEdges()
    numberOfEdges = len(edges)
    with open(ROU_FILE, "w") as f:
        writeTripFileBeginning(f)
        departures = []
        for i in range(0, NUMBER_OF_CARS):
            departures.append(random.randint(0, round(SIMULATION_END*0.99)))
        departures = np.sort(departures)
        electrics = random.sample(range(0, NUMBER_OF_CARS), round(NUMBER_OF_CARS*0.2))
        for i in range(NUMBER_OF_CARS):
            depart = departures[i]
            electric = False
            if i in electrics:
                electric = True
            writeRandomTrip(f, edges, numberOfEdges, i, depart, electric)
        writeTripFileEnd(f)

def writeTripFileBeginning(f):
    f.write("""<?xml version="1.0" encoding="UTF-8"?>\n<routes>\n""")
    f.write("""\t<vType id="fuel" accel="0.8" decel="4.5" sigma="0.5" length="5" maxSpeed="40" emissionClass="HBEFA4/PC_petrol_ltECE"/>\n""")
    f.write("""\t<vType id="electric" accel="0.8" decel="4.5" sigma="0.5" length="5" maxSpeed="40" emissionClass="HBEFA4/PC_BEV"/>\n\n""")

def writeRandomTrip(f, edges, numberOfEdges, i, depart, electric):
    path = None
    while path == None:
        originEdgeStruct = edges[random.randint(0, numberOfEdges-1)]
        destinationEdgeStruct = edges[random.randint(0, numberOfEdges-1)]
        path = NET.getShortestPath(originEdgeStruct, destinationEdgeStruct)[0]
    originEdge = originEdgeStruct._id
    destinationEdge = destinationEdgeStruct._id
    strIndex = str(i)
    if electric:
        f.write("""\t<trip id="test_trip_{}" type="electric" depart="{}" from="{}" to="{}"/>\n""".format(strIndex, str(depart), originEdge, destinationEdge))
    else:
        f.write("""\t<trip id="test_trip_{}" type="fuel" depart="{}" from="{}" to="{}"/>\n""".format(strIndex, str(depart), originEdge, destinationEdge))

def writeTripFileEnd(f):
    f.write("""</routes>""")

if __name__ == "__main__":
    sys.exit(main())