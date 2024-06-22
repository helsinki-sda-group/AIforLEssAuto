import argparse
from bs4 import BeautifulSoup
import random

parser = argparse.ArgumentParser(description="Generating trip file for a given percentage of passenger requests and percentage of taxis",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-t", "--tripfile", help="*.trips.xml file")
parser.add_argument("-pp", "--percpass", choices=range(0,101), type=int, help="percentage of trips to be served by taxis", metavar="PERCPASS")
parser.add_argument("-pt", "--perctaxi", choices=range(0,101), type=int, help="percentage of taxis for taxi passengers", metavar="PERCTAXI")
parser.add_argument("-te", "--taxiend", type=int, help="device.taxi.end", metavar="TAXIEND")
parser.add_argument("-pc", "--capacity", type=int, help="vType person capacity", metavar="CAPACITY")

args = parser.parse_args()
config = vars(args)
filename = config["tripfile"]
percpass = config["percpass"]
perctaxi = config["perctaxi"]
taxiend = config["taxiend"]
capacity = config["capacity"]

summaryFile = open("output/stats/summary.txt", "w")
summaryFile.write("EXPERIMENT PARAMETERS\n")
summaryFile.write("---------------------------------------------------------------------\n")

with open(filename, "r") as f:
    data = f.read()
f.close()

soup = BeautifulSoup(data, "xml")

# definition of taxi vehicle type
# 1300 is an end point of circular behavior,
# was chosen so that taxis can finish passenger trips before the end of the simulation
# otherwise they are not written in tripinfo file, 
# although option tripinfo-output.write-unfinished was set to True in cfg file \_O_/

taxitype = "<vType id=\"taxi\" vClass=\"taxi\" color=\"green\" personCapacity=\"" + str(capacity) + "\">\n\t" + \
        "<param key=\"has.taxi.device\" value=\"true\"/>\n\t" + \
        "<param key=\"device.taxi.pickUpDuration\" value=\"0\"/>\n\t" + \
        "<param key=\"device.taxi.dropOffDuration\" value=\"10\"/>\n\t" + \
        "<param key=\"device.taxi.parking\" value=\"true\"/>\n\t" + \
        "</vType>"
        #<param key=\"device.taxi.end\" value=\" " + str(taxiend) +"\"/>\n" + \
        

# insert before all trips
soup.trip.insert_before(BeautifulSoup(taxitype,'xml'))

passengerCount = 0
tripsCount = 0
edges = set()
firstTrip = True
firstTaxi = False

for trip in soup.find_all("trip"):
    # for percpass% of trips replace them with taxi rides
    # other trips constitute background traffic
    if random.random() * 100 <= percpass:
        orig = str(trip["from"])
        dest = str(trip["to"])

        persontrip = "<person id=\"p" + str(passengerCount) + "\" depart=\"" + str(trip["depart"]) + "\">\n\t" + \
            "<ride from=\"" + orig + "\" to=\""+ dest +"\" lines=\"taxi\" " + "parkingArea=\"pa" + dest + "\"/></person>"
        # print(persontrip)
        personSoup = BeautifulSoup(persontrip,'xml')
        # print(personSoup.person.prettify())
        trip.replace_with(personSoup)
        # print(trip)
        passengerCount += 1
        if firstTrip:
            firstTaxi = True

    # saving edges in a set
    fromEdge = trip["from"]
    toEdge = trip["to"]
    edges.add(fromEdge)
    edges.add(toEdge)
    firstTrip = False
    tripsCount += 1



print("Passengers added: ", passengerCount)


# adding taxis
# each taxi is a separate trip with random origin and destination edge
# origin determines spawning point in the simulation
# then taxis will pick up the passengers, so the actual routes will be calculated dynamically
# but SUMO needs trip or route definition for every vehicle
# all taxis are spawned in the beginning of the simulation

taxiCount = int(passengerCount * perctaxi/100.0)

print("Taxis added: ", taxiCount)

summaryFile.write("Number of trips: " + str(tripsCount) + "\n")
summaryFile.write("Percentage of taxi passengers: " + str(percpass) + "\n")
summaryFile.write("Number of taxi passengers: " + str(passengerCount) + "\n")
summaryFile.write("Percentage of taxis: " + str(perctaxi) + "\n")
summaryFile.write("Number of taxis: " + str(taxiCount) + "\n")

for i in range(0, taxiCount):
    origin = str(random.choice(tuple(edges)))
    dest = str(random.choice(tuple(edges)))
    # departLane = origin + "_0"
    taxi = \
    "<trip id=\"t" + str(i) + "\" depart=\"0\" type=\"taxi\" from=\"" + origin + \
        "\" to=\"" + dest + "\"/>" 
        # departLane=\"" + departLane + "\"/>" 
    if firstTaxi:
        soup.person.insert_before(BeautifulSoup(taxi,'xml'))
    else:
        soup.trip.insert_before(BeautifulSoup(taxi,'xml'))

summaryFile.write("Taxi finishing time: " + str(taxiend) + "\n")

# get other parameters from sumocfg
with open("randgrid.sumocfg", "r") as f:
    data = f.read()

f.close()

cfgSoup = BeautifulSoup(data, "xml")
timeTag = cfgSoup.find("time")
endTag = timeTag.find("end")
simulationTime = int(float(endTag["value"]))

taxiTag = cfgSoup.find("taxi_device")
dispatchTag = taxiTag.find("device.taxi.dispatch-algorithm")
routingAlgorithm = dispatchTag["value"]

summaryFile.write("Simulation time: " + str(simulationTime) + "\n")
summaryFile.write("Routing algorithm: " + str(routingAlgorithm) + "\n")
summaryFile.write("Taxi capacity: " + str(capacity) + "\n")
summaryFile.write("---------------------------------------------------------------------" + "\n")

f = open("randgridmixed.rou.xml", "w")
f.write(soup.prettify())
f.close()
summaryFile.close()


