from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import optparse

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
import traci
from sumolib import checkBinary
import randomTrips

SIMULATION_END = 600

try:
    N_ITER = int(sys.argv[1])
except:
    N_ITER = 0

def run():
    teleports = []
    while traci.simulation.getTime() < SIMULATION_END:
        traci.simulationStep()
        teleports.append(traci.simulation.getStartingTeleportNumber())

    with open(f"simulation_output/teleports_{N_ITER}.txt","w") as f:
        for item in teleports:
            f.write(f"{item}\n")
    sys.stdout.flush()
    traci.close()


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
    traci.start(["sumo", '-c', 'TraCI_demo.sumocfg'])
    # traci.start([sumoBinary, '-c', 'TraCI_demo.sumocfg'])
    run()
