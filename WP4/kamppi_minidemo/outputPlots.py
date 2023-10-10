import sys
import matplotlib.pyplot as plt
import numpy as np
import xml.etree.ElementTree as ET


def main():
    # Scenarios' amount
    scenarios = 4
    EMISSION_FILES = ['simulation_output/emissions_%d.xml' % i for i in range(1,scenarios+1)]
    TELEPORT_FILES = ["simulation_output/teleports_%d.txt" % i for i in range(1,scenarios+1)]
    # Results
    timestepArray, emissions, vehicles, teleports = parse(EMISSION_FILES, TELEPORT_FILES)
    co2_means, co2_vars, co2_stds, veh_means, veh_vars, veh_stds = plot(scenarios, timestepArray, emissions, vehicles, teleports)

def parse(EMISSION_FILES, TELEPORT_FILES):
    emissions = []
    teleports = []
    vehicles = []
    # Parse the result files
    for EMISSION_FILE in EMISSION_FILES:
        # Scenario
        scenario_emission = []
        scenario_vehicles = []
        scenario_teleports = 0
        timesteps = 0
        co2Sum = 0.0
        n_vehicles = 0

        for e in ET.iterparse(EMISSION_FILE):
            xmlElement = e[1]
            if xmlElement.tag == "vehicle":
                co2Sum += float(xmlElement.attrib["CO2"])
                n_vehicles += 1
            elif xmlElement.tag == "timestep":
                scenario_emission.append(co2Sum)
                scenario_vehicles.append(n_vehicles)
                co2Sum = 0.0
                timesteps += 1
                n_vehicles=0

        for teleport_file in TELEPORT_FILES:
            with open(teleport_file,"r") as f:
                for line in f:
                    try:
                        scenario_teleports += int(line)
                    except ValueError:
                        print('{} is not a number!'.format(line))

        # Conversion to grams from milligrams for emissions
        # The scenario is appended to all results
        emissions.append(np.divide(scenario_emission,10**4))
        vehicles.append(scenario_vehicles)
        teleports.append(scenario_teleports)

        # If no timesteps were found in the scenario
        if timesteps == 0:
                sys.exit()

    # Timesteps
    timestepArray = np.linspace(0, timesteps, timesteps, dtype=int)
    # Results
    return timestepArray, emissions, vehicles, teleports

def plot(scenarios, timestepArray, emissions, vehicles, teleports):
    co2_means = np.mean(emissions,axis=1)
    co2_vars = np.var(emissions,axis=1)
    co2_stds = np.std(emissions,axis=1)
    veh_means = np.mean(vehicles,axis=1)
    veh_vars = np.var(vehicles,axis=1)
    veh_stds = np.std(vehicles,axis=1)
    # Colors
    colors = plt.cm.tab10(np.linspace(0,1,scenarios))
    # Plotting
    fig, axs = plt.subplots(2,2,figsize=(13,9), gridspec_kw={'height_ratios': [3,1]})
    co2_cells = []
    vehicle_cells = []
    for i in range(scenarios):
        axs[0,0].plot(timestepArray, emissions[i], label=f"Scenario {i+1}", color=colors[i])
        axs[0,1].plot(timestepArray, vehicles[i], label=f"Scenario {i+1}", color=colors[i])
        co2_cells.append([f"{co2_means[i]:.2f}",
                        f"{co2_vars[i]:.2f}",
                        f"{co2_stds[i]:.2f}"])
        vehicle_cells.append([f"{veh_means[i]:.0f}",
                        f"{veh_vars[i]:.0f}",
                        f"{veh_stds[i]:.0f}",
                        teleports[i]])
        
    axs[0,0].set_xlabel("time step (s)")
    axs[0,0].set_ylabel("CO2 emission (g/s)")
    axs[0,1].set_xlabel("time step (s)")
    axs[0,1].set_ylabel("# of vehicles")
    axs[1,0].axis('off')
    axs[1,1].axis('off')
    axs[0,0].legend()
    axs[0,1].legend()
    rows = ["Scenario 1", "Scenario 2", "Scenario 3", "Scenario 4"]
    co2_cols = ("Mean CO2", "Var CO2", "Std CO2")
    vehicle_cols = ("Mean of vehicles", "Var of vehicles", "Std of vehicles", "# of teleports")
    co2_table = axs[1,0].table(rowLabels=rows, colLabels=co2_cols, cellText=co2_cells, loc='bottom', rowColours=colors, cellLoc='center')
    vehicle_table = axs[1,1].table(rowLabels=rows, colLabels=vehicle_cols, cellText=vehicle_cells, loc='bottom', rowColours=colors, cellLoc='center')
    co2_table.set_fontsize(8)
    vehicle_table.set_fontsize(8)
    plt.subplots_adjust(left=0.3, bottom=0.2)
    plt.show()
    return co2_means, co2_vars, co2_stds, veh_means, veh_vars, veh_stds

if __name__ == '__main__':
    sys.exit(main())