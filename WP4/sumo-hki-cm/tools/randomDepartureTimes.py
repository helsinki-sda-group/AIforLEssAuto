# ----------------------------------------------------------------------
# Copyright (c) 2023 University of Helsinki SDA group
# @file    randomDepartureTimes.py
# @author  Anton Taleiko
# @date    Wed Feb 15 2023
# ----------------------------------------------------------------------
import sys
from random import seed, randint
from datetime import datetime
import xml.etree.ElementTree as ET

SIMULATION_END = 3600
try:
    ROU_FILE = sys.argv[1]
    OUTPUT_FILE = sys.argv[2]
    DEPART_START = int(sys.argv[3])
    DEPART_END = int(sys.argv[4])-1
except:
    ROU_FILE = "sumo_files/verified_trips.rou.xml"
    OUTPUT_FILE = ROU_FILE
    DEPART_START = 0
    DEPART_END = SIMULATION_END-1

def main():    
    seed(int(datetime.now().strftime("%Y%m%d%H%M%S")))
    tree = ET.parse(ROU_FILE)
    trips = tree.getroot()
    for trip in trips:
        trip.set("depart", str(randint(DEPART_START, DEPART_END)) + ".00")
    tree.write(OUTPUT_FILE)


if __name__ == '__main__':
    sys.exit(main())