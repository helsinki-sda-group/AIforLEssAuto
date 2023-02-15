import sys
from random import seed, randint
from datetime import datetime
import xml.etree.ElementTree as ET

try:
    ROU_FILE = sys.argv[1]
except:
    ROU_FILE = "sumo_files/verified_trips.rou.xml"
SIMULATION_END = 3600

def main():
    seed(int(datetime.now().strftime("%Y%m%d%H%M%S")))
    tree = ET.parse(ROU_FILE)
    trips = tree.getroot()
    for trip in trips:
        trip.set("depart", str(randint(0, SIMULATION_END-1)))
    tree.write(ROU_FILE)


if __name__ == '__main__':
    sys.exit(main())