# ----------------------------------------------------------------------
# Copyright (c) 2023 University of Helsinki SDA group
# @file    indexZeroToN.py
# @author  Anton Taleiko
# @date    Wed Feb 15 2023
# ----------------------------------------------------------------------
import sys
import xml.etree.ElementTree as ET

try:
    ROU_FILE = sys.argv[1]
except:
    ROU_FILE = "sumo_files/verified_trips.rou.xml"

def main():
    tree = ET.parse(ROU_FILE)
    trips = tree.getroot()
    id = 0
    for trip in trips:
        trip.set("id", str(id))
        id += 1
    tree.write(ROU_FILE)


if __name__ == '__main__':
    sys.exit(main())