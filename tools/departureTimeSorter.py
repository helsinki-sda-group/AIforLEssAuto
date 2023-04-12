# ----------------------------------------------------------------------
# Copyright (c) 2023 University of Helsinki SDA group
# @file    departureTimeSorter.py
# @author  Anton Taleiko
# @date    Wed Feb 15 2023
# ----------------------------------------------------------------------
import sys
import xml.etree.ElementTree as ET
import re

try:
    INPUT_FILE = sys.argv[1]
    print("Route file set to {}.".format(INPUT_FILE))
    OUTPUT_FILE = sys.argv[2]
    print("Output file set to {}.".format(OUTPUT_FILE))
except:
    INPUT_FILE = "sumo_files/verified_trips.rou.xml"
    print("Input file defaulted to {}, add a file path as argument to change.".format(INPUT_FILE))
    OUTPUT_FILE = INPUT_FILE
    print("Output file defaulted to {}, add a file path as argument to change.".format(OUTPUT_FILE))

def main():
    mainTree = ET.parse(INPUT_FILE)
    mainRoot = mainTree.getroot()
    mainRoot[:] = sorted(mainRoot, key=lambda child: int(re.findall(r"([0-9]+).*", child.get("depart"))[0]))
    mainTree.write(OUTPUT_FILE)


if __name__ == '__main__':
    sys.exit(main())