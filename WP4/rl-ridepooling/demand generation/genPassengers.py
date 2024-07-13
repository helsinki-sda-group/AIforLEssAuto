import argparse
from bs4 import BeautifulSoup
import random
import xml.etree.ElementTree as ET
import os
from omegaconf import OmegaConf
from datetime import datetime
import shutil

from pathlib import Path

# Setup the argparse
parser = argparse.ArgumentParser(description="Generating trip file for a given percentage of passenger requests and percentage of taxis",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("-c", "--config", type=str, help="Read arguments from config file. If both config and command line args are specified, command line args will overwrite config arguments")
parser.add_argument("-t", "--tripfile", help="*.trips.xml file")
parser.add_argument("-pp", "--percpass", choices=range(0, 101), type=int, help="Percentage of trips to be served by taxis", metavar="PERCPASS")
parser.add_argument("-pt", "--perctaxi", choices=range(0, 101), type=int, help="Percentage of taxis for taxi passengers", metavar="PERCTAXI")
parser.add_argument("-te", "--taxiend", type=int, help="device.taxi.end", metavar="TAXIEND")
parser.add_argument("-pc", "--capacity", type=int, help="vType person capacity", metavar="CAPACITY")
parser.add_argument("-pa", "--parkingfile", help="Parking areas file")

# Parse default values
defaults = {action.dest: action.default for action in parser._actions}

# Parse arguments from command line
cmd_args = parser.parse_args()

# Determine which arguments were explicitly set by the user
specified_args = {arg: value for arg, value in vars(cmd_args).items() if arg != 'config' and value != defaults[arg]}

# Read config from YAML file if specified
if cmd_args.config:
    config = OmegaConf.load(cmd_args.config)
    # Convert specified command-line arguments into an OmegaConf dictionary
    specified_args_conf = OmegaConf.create(specified_args)
    # Merge config with the command line arguments (command line arguments take precedence)
    all_args = OmegaConf.merge(config, specified_args_conf)
else:
    # If no config file, use command line arguments directly
    all_args = OmegaConf.create(vars(cmd_args))

# Access variables
tripFile = all_args.get('tripfile')
percpass = all_args.get('percpass')
perctaxi = all_args.get('perctaxi')
taxiend = all_args.get('taxiend')
capacity = all_args.get('capacity')
parkingFile = all_args.get('parkingfile')

# Create output folder
now = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
if cmd_args.config: 
    prefix = Path(cmd_args.config).stem
    output_dir_name = f'{now}_{prefix}'
else:
    prefix = None
    output_dir_name = f'{now}'
output_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'output', output_dir_name)

os.makedirs(output_path, exist_ok=True)
if cmd_args.config:
    shutil.copy(cmd_args.config, output_path)

parkingSet = set()

tree = ET.parse(parkingFile)
root = tree.getroot()

for pArea in root.findall('parkingArea'):
    pId = pArea.get("id")
    pId = pId[2:]
    parkingSet.add(pId)

validOrigDestNum = len(parkingSet)
print("Origins/destinations with parking slots: ", validOrigDestNum)

tree = ET.parse(tripFile)
root = tree.getroot()

validTripNum = 0

for trip in root.findall("trip"):
    orig = trip.get("from")
    dest = trip.get("to")
    if orig in parkingSet and dest in parkingSet:
        validTripNum += 1

tripNum = len(root.findall("trip"))
print("Number of trips: ", tripNum)
print("Trips which start and end at parking slots: ", validTripNum)

newPercPass = int( (tripNum * percpass) / float(validTripNum) )
print("New perc pass: ", newPercPass)


summaryFile = open(os.path.join(output_path, 'summary.txt'), "w")
summaryFile.write("EXPERIMENT PARAMETERS\n")
summaryFile.write("---------------------------------------------------------------------\n")

with open(tripFile, "r") as f:
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
    
    orig = str(trip["from"])
    dest = str(trip["to"])


    if orig not in parkingSet or dest not in parkingSet:
        continue

    # for percpass% of trips replace them with taxi rides
    # other trips constitute background traffic
    if random.random() * 100 <= newPercPass:

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
with open(os.path.join('nets', 'ridepooling', 'older_networks', "randgrid.sumocfg"), "r") as f:
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

if prefix != None:
    output_taxis_filename = f'{prefix}_taxis.rou.xml'
else:
    output_taxis_filename = 'taxis.rou.xml'
f = open(os.path.join(output_path, output_taxis_filename), "w")
f.write(soup.prettify())
f.close()
summaryFile.close()


