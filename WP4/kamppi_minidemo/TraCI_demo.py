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

def run(args):
    teleports = []
    while traci.simulation.getTime() < SIMULATION_END:
        traci.simulationStep()
        teleports.append(traci.simulation.getStartingTeleportNumber())

    with open(f"simulation_output/teleports_{args[0]}.txt","w") as f:
        for item in teleports:
            f.write(f"{item}\n")
    sys.stdout.flush()
    traci.close()


def get_options():
    """define options for this script and interpret the command line"""
    optParser = optparse.OptionParser()
    optParser.add_option("--gui", action="store_true",
                         default=False, help="run the GUI version of sumo")
    options, args = optParser.parse_args()
    return options,args


if __name__ == "__main__":
    options,args = get_options()
    # Run in GUI
    if options.gui:
        sumoBinary = checkBinary('sumo-gui')
        traci.start([sumoBinary, '-c', 'TraCI_demo.sumocfg'])
    # Run in CLI
    else:
        traci.start(["sumo", '-c', 'TraCI_demo.sumocfg'])
    run(args)
