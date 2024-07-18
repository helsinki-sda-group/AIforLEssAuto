import traci
import os
import sys


def launch_sumo(config_path):
    # Determine the directory containing the config file
    config_dir = os.path.dirname(os.path.abspath(config_path))

    # Start SUMO with traci
    sumoBinary = "sumo-gui"  # Use sumo-gui or sumo for graphical or non-graphical version
    #os.system(f'sumo-gui -c "{config_path}"')
    traci.start([sumoBinary, "-c", config_path])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python launch_sumo.py <config_file_path>")
        sys.exit()
    

    config_path = sys.argv[1]
    directory = launch_sumo(config_path)

        
