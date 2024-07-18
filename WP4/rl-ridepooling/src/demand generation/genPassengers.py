import argparse
from bs4 import BeautifulSoup
import random
import xml.etree.ElementTree as ET
import os
import shutil
import sys
from xml.dom import minidom
import subprocess

sys.path.append('./src')
from utils.config import Config

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
parser.add_argument("-nt", "--netfile", help="Input network file (for creating simulation test folder)")
parser.add_argument("-sv", "--sumoviewfile", help="Input sumoview file (for creating simulation test folder)")

# Instantiate the config
cfg = Config(parser)

# Access variables
tripFile = cfg.opt.get('tripfile')
percpass = cfg.opt.get('percpass')
perctaxi = cfg.opt.get('perctaxi')
taxiend = cfg.opt.get('taxiend')
capacity = cfg.opt.get('capacity')
parkingFile = cfg.opt.get('parkingfile')
netFile = cfg.opt.get('netfile')
sumoviewFile = cfg.opt.get('sumoviewfile')

# Create output folder
outputPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                          'output', 
                          cfg.output_dir_name)

# create the outputPath folder
os.makedirs(outputPath, exist_ok=True)

# copy the config file to the outputPath folder if it was specified
if cfg.opt.get('config'):
    shutil.copy(cfg.opt.get('config'), outputPath)

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


summaryFile = open(os.path.join(outputPath, 'summary.txt'), "w")
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

if cfg.prefix != None:
    outputTaxisFilename = f'{cfg.prefix}_taxis.rou.xml'
else:
    outputTaxisFilename = 'taxis.rou.xml'
outputTaxisPath = os.path.join(outputPath, outputTaxisFilename)
f = open(outputTaxisPath, "w")
f.write(soup.prettify())
f.close()
summaryFile.close()


def createSimulationFolder(net_file, route_file, parking_file, sumoview_file, path_to_folder, sumocfg_file_name):
    """
    Creates the simulation folder for quickly testing the simulation.
    Copies the network, route, parking areas files, and creates the config file.
    Also creates the sumoview.xml file
    """
    def createSimulationConfig(net_file, route_files, additional_files, sumoview_file, output_path):
        """
        Creates the simulation config file and places it inside the output_path
        """
        # Create the root element
        configuration = ET.Element("configuration")
        
        # Input section
        input_section = ET.SubElement(configuration, "input")
        ET.SubElement(input_section, "net-file", value=net_file)
        ET.SubElement(input_section, "route-files", value=route_files)
        ET.SubElement(input_section, "additional-files", value=additional_files)
        
        # Time section
        time_section = ET.SubElement(configuration, "time")
        ET.SubElement(time_section, "begin", value="0")
        ET.SubElement(time_section, "end", value="3600")
        
        # Taxi device section
        taxi_device = ET.SubElement(configuration, "taxi_device")
        ET.SubElement(taxi_device, "device.taxi.dispatch-algorithm", value="greedyClosest")
        ET.SubElement(taxi_device, "device.taxi.idle-algorithm", value="stop")
        ET.SubElement(taxi_device, "device.taxi.dispatch-period", value="1")
        ET.SubElement(taxi_device, "device.taxi.dispatch-algorithm", params="relLossThreshold:0.2")
        
        # GUI only section
        gui_only = ET.SubElement(configuration, "gui_only")
        ET.SubElement(gui_only, "gui-settings-file", value=sumoview_file)
        
        # Output section
        output_section = ET.SubElement(configuration, "output")
        ET.SubElement(output_section, "tripinfo-output", value="output/tripinfo.xml")
        ET.SubElement(output_section, "tripinfo-output.write-unfinished", value="True")
        ET.SubElement(output_section, "emission-output", value="output/emissions.xml")
        ET.SubElement(output_section, "tripinfo-output.write-undeparted", value="True")
        
        # Report section
        report_section = ET.SubElement(configuration, "report")
        ET.SubElement(report_section, "verbose", value="True")
        ET.SubElement(report_section, "message-log", value="message.xml")
        ET.SubElement(report_section, "error-log", value="error.xml")
        ET.SubElement(report_section, "duration-log.statistics", value="True")
        
        # Convert the tree to a byte stream
        rough_string = ET.tostring(configuration, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml_as_string = reparsed.toprettyxml()

        with open(output_path, 'w') as f:
            f.write(pretty_xml_as_string)


    def copy_safe(input, dest):
        """
        Copy file only if it's specified. if not, pass
        Returns the path to the newly created file
        """
        if input:
            return shutil.copy(input, dest)


    # create output folder
    os.makedirs(path_to_folder, exist_ok=True)

    # copy input files
    local_net_file = copy_safe(net_file, path_to_folder)
    local_route_file = copy_safe(route_file, path_to_folder)
    local_parking_file = copy_safe(parking_file, path_to_folder)
    local_sumoview_file = copy_safe(sumoview_file, path_to_folder)

    # create sumo config
    local_cfg_file = os.path.join(path_to_folder, sumocfg_file_name)
    createSimulationConfig(local_net_file, local_route_file, local_parking_file, local_sumoview_file, local_cfg_file)

    # create output folder so sumo doesn't crash
    os.makedirs(os.path.join(path_to_folder, 'output'))


# create simulation folder for quick testing
simulationFolderPath = os.path.join(outputPath, 'simulation')
launchFilename = 'sumo_launch.sumocfg.xml'
createSimulationFolder(netFile, outputTaxisPath, parkingFile, sumoviewFile, simulationFolderPath, launchFilename)

# launch sumo
launchFilePath = os.path.join('src', 'demand generation', 'simulationTestLaunch.py')
launchFileConfigPath = os.path.join(simulationFolderPath, launchFilename)
sumoLaunchCmd = ["python", launchFilePath, launchFileConfigPath]
print('launching the command:', sumoLaunchCmd)
subprocess.run(sumoLaunchCmd)