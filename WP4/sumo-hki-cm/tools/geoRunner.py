# ----------------------------------------------------------------------
# Copyright (c) 2023 University of Helsinki SDA group
# @file    geoRunnerV2.py
# @author  Anton Taleiko
# @date    Wed Feb 15 2023
# ----------------------------------------------------------------------
from __future__ import absolute_import
from __future__ import print_function


import os
import sys
import optparse
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
import traci

CONFIG_FILE = 'demo2/fringe_lanes_length.sumocfg.xml'

ADD_FILE = 'sumo_files/data/helsinki_all_detectors.add.xml'

OUTPUT_DETECTORS_VISITING_VEHICLES_FILE = 'sumo_files/output/simulation/geo_runner/detector_vehicles.xml'

def run():
    # get list of all detectors 
    # (read the reduced_cut.add.xml file and filter all detectors that don't start with HEL)
    addRoot = ET.parse(ADD_FILE).getroot()
    detectorIDs = []
    for detectorElem in addRoot:
        detectorID = detectorElem.get('id')
        if (detectorID[:3] != 'HEL'): # not HKI detector, then digitraffic (change if adding new detectors)
            detectorIDs.append(detectorID)

    if traci.simulation.getEndTime() == -1:  # end time wasn't set
        # run until all vehicles arrived
        while traci.simulation.getMinExpectedNumber() > 0:
            traciStep()
    else:
        while traci.simulation.getTime() < traci.simulation.getEndTime():
            traciStep()
            
    
    # get all ids for the previous interval that passed through the detectors
    detectorVehicles = dict.fromkeys(detectorIDs)
    for detectorID in detectorIDs:
        detectorVehicles[detectorID] = traci.inductionloop.getLastIntervalVehicleIDs(detectorID)
    # co2Module()
    writeDetectorVehicles(detectorVehicles)
    sys.stdout.flush()
    traci.close()

    # try:
    #     df = pd.read_excel(STATISTICS_FILE, index_col=[0])
    # except:
    #     df = pd.DataFrame(columns=["TELEPORTS", "UNIQUE_VEH_TELEPORTS"])
    # df = df.append({"TELEPORTS": teleports, "UNIQUE_VEH_TELEPORTS": len(teleportedVehicles)}, ignore_index=True)
    # df.to_excel(STATISTICS_FILE)


def traciStep():
    traci.simulationStep()
    if (traci.simulation.getTime() % 100 == 0):
        print(traci.simulation.getTime())

def writeDetectorVehicles(detectorVehicles: dict[str, list[str]], outputFile=OUTPUT_DETECTORS_VISITING_VEHICLES_FILE):
    outputRoot = ET.Element('interval')
    for detectorID in detectorVehicles:
        inductionLoopElem = ET.SubElement(outputRoot, 'inductionLoop')
        inductionLoopElem.set('id', detectorID)
        vehicleIDs = detectorVehicles[detectorID]
        inductionLoopElem.set('passed', str(len(vehicleIDs)))
        for vehicleID in vehicleIDs:
            vehicleElem = ET.SubElement(inductionLoopElem, 'vehicle')
            vehicleElem.set('id', vehicleID)

    tree = ET.ElementTree(outputRoot)
    with open(outputFile, "wb") as f:
        tree.write(f)
        


if __name__ == "__main__":
    traci.start(["sumo", '-c', CONFIG_FILE])
    # traci.start([sumoBinary, '-c', 'sumo_files/1_hour_reduced_area_geo_V2.sumocfg'])

    # With output prefix
    # traci.start(["sumo", '-c', 'sumo_files/1_hour_reduced_area_geo_V2.sumocfg', '--output-prefix', OUTPUT_DIR])
    run()