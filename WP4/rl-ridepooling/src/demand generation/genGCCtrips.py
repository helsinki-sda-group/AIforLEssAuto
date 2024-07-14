from bs4 import BeautifulSoup
import argparse
import os
import random

# the main logic of the script may be described as follows:
# trips with departure time after deadline are removed
# for the valid trips we find corresponding route in a route file
# for each route we find subroute which consists of edges in GCC 
# origin and destination of a subroute define new trip 
# departure time of new trip is calculated as # of starting edge/# of route edges (rough approximation, may be improved)
# we include only subroutes with number of edge > minEdges (to avoid extremely short routes)
# and departure time > deadline
# sampling ratio is about which percentage of trips to include in the resulting trip file

parser = argparse.ArgumentParser(description="Generating trip file only for strongly connected component",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-cn", "--connectednet", help="*.net.xml file (connected network)", default="area1_gcc_plain.net.xml")
parser.add_argument("-dt", "--disconnectedtrips", help="*.trips.xml file (trips for disconnected network)", default="area1_disconnected_trips.rou.xml")
parser.add_argument("-dr", "--disconnectedroutes", help="*.routes.xml file (routes for disconnected network)", default="area1_disconnected_routes.rou.xml")
parser.add_argument("-ld", "--lastdeparture", help="trips after last departure time will not be included", default=3600)
parser.add_argument("-mine", "--minimumedges", help="route should contain at least mine edges", default=5)
parser.add_argument("-sr", "--samplingratio", help="the fraction of trips randomly sampled from the overall demand", default=1)
parser.add_argument("-o", "--output", help="*.trips.xml file (trips for connected network)", default="area1_connected_sampled_1.trips.xml")


args = parser.parse_args()
config = vars(args)
cnet = config["connectednet"]
dtrips = config["disconnectedtrips"]
droutes = config["disconnectedroutes"]
lastdeptime = config["lastdeparture"]
mine = config["minimumedges"]
samplingRate = config["samplingratio"]
output = config["output"]

here = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(here, cnet)

# opening file with connected network
with open(filename, "r") as f:
    data = f.read()
f.close()

print("File with connected network ", filename, "opened")

soup = BeautifulSoup(data, "xml")

# creating set with all edge ids
edges = set()

for edge in soup.find_all("edge"):
    id = str(edge["id"])
    edges.add(id)

print("Number of edges (connected network): ", len(edges))

# cut the routes from disconnected network to contain only the edges from GCC
filename = os.path.join(here, droutes)
# opening file with routes from disconnected network
with open(filename, "r") as f:
    data = f.read()
f.close()

print("File with routes from disconnected network ", filename, "opened")

routes = {}
initialRoutes = 0
cutRoutes = 0
fullRoutes = 0
deletedRoutes = 0


soup = BeautifulSoup(data, "xml")
for vehicle in soup.findAll("vehicle"):
    id = vehicle["id"]
    depart = float(vehicle["depart"])
    arrival = float(lastdeptime)
    #arrival = float(vehicle["arrival"])
    # print("vehicle id: ", id)
    vehRoute = vehicle.findChildren("route", recursive=False)
    # we assume that the vehicle contains one and only one route
    route = vehRoute[0]
    edgesList = route["edges"].split(" ")
    subroute = []
    foundFirst = False
    foundLast = False
    # find subroute consisting of the edges from GCC
    for edge in edgesList:
        if foundFirst == False and edge not in edges:
            continue
        foundFirst = True
        if edge in edges:
            subroute.append(edge)
        else: 
            # print("Edge not in gcc: ", edge)
            foundLast = True
            break
    if len(subroute) >= int(mine):
        subrouteStr = " ".join(str(x) for x in subroute)
        # find new departure time
        subrouteOrigin = subroute[0]
        indexSubroutOrigin = edgesList.index(subrouteOrigin)
        newDepTime = round(depart + (arrival-depart)*(indexSubroutOrigin/len(edgesList)),2)
        routes[id] = (str(newDepTime), subrouteStr)
        #print("id: ", id , ", old departure time: ", depart, ", old arrival time: ", arrival,  ", new departure time: ", str(newDepTime), ", subroute: ", subrouteStr)
        #input("")
        # print((id, subroute))
        if len(subroute) == len(edgesList):
            fullRoutes += 1
        else:
            cutRoutes +=1
    else:
        deletedRoutes += 1
    initialRoutes += 1

print("Initial routes: ", initialRoutes)
print("Full routes: ", fullRoutes)
print("Cut routes: ", cutRoutes)
print("Deleted routes: ", deletedRoutes)

#input("")
            


filename = os.path.join(here, dtrips)

# opening file with trips from disconnected network
with open(filename, "r") as f:
    data = f.read()
f.close()

print("File with trips from disconnected network ", filename, "opened")

soup = BeautifulSoup(data, "xml")

print("Trips in disconnected network: ", len(soup.find_all("trip")))

print("Subroutes found: ", len(routes.keys()))

latetrips = 0
removedAfterSampling = 0
subrouteNotFound = 0

# select the trips corresponding to the subroutes found
# cut all the trips that depart later then last departure time
for trip in soup.find_all("trip"):
    id = trip["id"]
    del trip["type"]
    deptime = int(float(trip["depart"]))
    if deptime >= lastdeptime:
        latetrips += 1
        trip.decompose()
    # if subroute was found for this trip
    elif id in routes.keys():
        # print("Old trip: ", trip)
        subroute = routes[id]
        newDepTime = subroute[0]
        subrouteList = subroute[1].split(" ")
        newOrigin = subrouteList[0]
        newDestination = subrouteList[1]
        trip["depart"] = newDepTime
        trip["from"] = newOrigin
        trip["to"] = newDestination
        trip["departLane"] = "best"
        trip["departSpeed"] = "max"
        #print("New trip: ", trip)
        #input("")
        if random.random() > samplingRate:
            trip.decompose()
            removedAfterSampling += 1
    else:
        trip.decompose()
        subrouteNotFound += 1

print("Trips in connected network after sampling: ", len(soup.find_all("trip")))
print("Trips starting after last departure time: ", latetrips)
print("Trips removed after sampling: ", removedAfterSampling)
print("Trips removed because subroute was not found: ", subrouteNotFound)

# sorting the trips by departure time (SUMO requirement)
sortedSoupTags = list(sorted(soup.find_all('trip'), key=lambda x:float(x['depart'])))
#print(sortedSoupTags)
#input("")
sortedSoupStrs = [str(x) for x in sortedSoupTags]

sortedSoupList = ["<routes>"]
sortedSoupList.extend(sortedSoupStrs)
sortedSoupList.append("</routes>")
# print(sortedSoup)

#print(sortedSoupList)
#input("")
#print(''.join(sortedSoupList))

sortedSoup = BeautifulSoup(''.join(sortedSoupList), "xml")

filename = os.path.join(here, output)
f = open(filename, "w")
f.write(sortedSoup.prettify())

print("Output file ", filename, "is written")

f.close()




