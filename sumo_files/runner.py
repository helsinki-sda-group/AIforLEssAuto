from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import optparse
import pandas as pd
import numpy as np


SIMULATION_END = 3600
STATISTICS_FILE = "data/statistics.ods"
OUTPUT_DIR = "simulation_output"


if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
import traci
from sumolib import checkBinary
import randomTrips


def run():
    teleports = 0
    teleportedVehicles = set()
    # traci.simulationStep()
    # traci.vehicle.add(vehID="test", routeID="testRoute", fromTaz="po_1101", toTaz="po_1001")
    while traci.simulation.getTime() < SIMULATION_END:
        traci.simulationStep()
        # print("Teleported vehicles: " + str(traci.simulation.getStartingTeleportNumber()))
        # print("Teleported vehicles: " + str(traci.simulation.getStartingTeleportIDList()))
        teleports += traci.simulation.getStartingTeleportNumber()
        teleportedVehiclesTuple = traci.simulation.getStartingTeleportIDList()
        if len(teleportedVehiclesTuple) > 0:
            for vehicle in teleportedVehiclesTuple:
                teleportedVehicles.add(vehicle)
        
        # co2Module()
    

    sys.stdout.flush()
    traci.close()

    try:
        df = pd.read_excel(STATISTICS_FILE, index_col=[0])
    except:
        df = pd.DataFrame(columns=["TELEPORTS", "UNIQUE_VEH_TELEPORTS"])
    df = df.append({"TELEPORTS": teleports, "UNIQUE_VEH_TELEPORTS": len(teleportedVehicles)}, ignore_index=True)
    # df["TELEPORTS"][len(df)-1] = teleports
    # df["UNIQUE_VEH_TELEPORTS"][len(df)-1] = len(teleportedVehicles)
    df.to_excel(STATISTICS_FILE)


def co2Module():
    for vehicleId in traci.simulation.getLoadedIDList():
        vehicleParameters = getVehicleParameters(vehicleId)
        # perform CO2 module actions


def getVehicleParameters(vehicleId):
    speed = traci.vehicle.getSpeed(vehicleId)
    accel = traci.vehicle.getAccel(vehicleId)
    time = traci.simulation.getTime()
    type = traci.vehicle.getTypeID(vehicleId)
    emissionClass = traci.vehicle.getEmissionClass(vehicleId)
    position = traci.vehicle.getPosition(vehicleId)
    laneLabel = traci.vehicle.getLaneID(vehicleId)
    # laneLabel = traci.vehicle.getLaneIndex(vehicleId)
    edgeLabel = traci.vehicle.getRoadID(vehicleId)
    return np.array([vehicleId, speed, accel, time, type, emissionClass, position, laneLabel, edgeLabel])




def get_options():
    """define options for this script and interpret the command line"""
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


if __name__ == "__main__":
    options = get_options()
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')
    traci.start(["sumo", '-c', 'sumo_files/1_hour_whole_area.sumocfg'])
    # traci.start([sumoBinary, '-c', 'sumo_files/1_hour_whole_area.sumocfg'])

    # With output prefix
    # traci.start(["sumo", '-c', 'sumo_files/1_hour.sumocfg', '--output-prefix', OUTPUT_DIR])

    run()
