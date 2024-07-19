import libsumo as traci
import os
import sys
import matplotlib.pyplot as plt
import csv


def traciStep():
    traci.simulationStep()
    if (traci.simulation.getTime() % 200 == 0):
        print(traci.simulation.getTime())

def launch_sumo(config_path, sumo_output_path, prefix, percpass, perctaxi):
    # Determine the directory containing the config file
    config_dir = os.path.dirname(os.path.abspath(config_path))

    # Start SUMO with traci
    sumoBinary = "sumo"  # Use sumo-gui or sumo for graphical or non-graphical version
    #os.system(f'sumo-gui -c "{config_path}"')
    traci.start([sumoBinary, "-c", config_path])

    idle_taxis_timeline = []
    en_route_taxis_timeline = [] # en-route to pickup someone
    occupied_taxis_timeline = [] # has a customer and is going to drop-off
    pickup_occupied_taxis_timeline = [] # has a customer but will pickup more

    while traci.simulation.getTime() < 3600:
        traciStep()
        # get current sumo time
        curr_time = traci.simulation.getTime()

        # taxis that 
        idle_taxis = traci.vehicle.getTaxiFleet(0)
        
        # taxis that are en-route to pick up a customer
        # (either currently empty or have a customer on board already)
        # taxi states 1 and 3
        en_route_with_pickup_taxis = traci.vehicle.getTaxiFleet(1)

        # taxis that have a customer on board and driving to drop off
        # or to pickup a new customer
        # taxi states 2 and 3
        occupied_with_pickup_taxis = traci.vehicle.getTaxiFleet(2)

        # taxi has customer on board but will pick up more customers
        # taxis state 3
        pickup_occupied_taxis = traci.vehicle.getTaxiFleet(3)

        # taxis only in state 1 (only en route)
        en_route_taxis = len(en_route_with_pickup_taxis) - len(pickup_occupied_taxis)

        # taxis only in state 2
        occupied_taxis = len(occupied_with_pickup_taxis) - len(pickup_occupied_taxis)


        # sanity check to make sure we cover all taxis
        if (len(idle_taxis) + en_route_taxis + occupied_taxis + len(pickup_occupied_taxis) != len(traci.vehicle.getTaxiFleet(-1))):
            print('Warning: taxis are not split correctly')

        idle_taxis_timeline.append(len(idle_taxis))
        en_route_taxis_timeline.append(en_route_taxis)
        occupied_taxis_timeline.append(occupied_taxis)
        pickup_occupied_taxis_timeline.append(len(pickup_occupied_taxis))

        # # get all reservations (including dispatched ones)
        # all_reservations = traci.person.getTaxiReservations(0)

        # # get all reservations that have not been assigned to taxi
        # reservations = tuple(filter(lambda x: x.state!=4 and x.state!=8 and x.reservationTime != curr_time, all_reservations))

    # Save the data into a separate folder in output
    taxis_data_dir = os.path.join(sumo_output_path, 'taxis')
    os.mkdir(taxis_data_dir)

    # Function to save data to CSV
    def save_to_csv(data, filename, path):
        filepath = os.path.join(path, filename)
        with open(filepath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Second', 'Count'])  # Header
            for second, count in enumerate(data):
                writer.writerow([second, count])

    # Save each dataset as a CSV file
    save_to_csv(idle_taxis_timeline, 'idle_taxis.csv', taxis_data_dir)
    save_to_csv(en_route_taxis_timeline, 'en_route_taxis.csv', taxis_data_dir)
    save_to_csv(occupied_taxis_timeline, 'occupied_taxis.csv', taxis_data_dir)
    save_to_csv(pickup_occupied_taxis_timeline, 'pickup_occupied_taxis.csv', taxis_data_dir)


    seconds = list(range(3600))

    # Plotting the line graph
    plt.figure(figsize=(10, 5))  # Set the figure size for better readability

    # Plot datasets
    plt.plot(seconds, idle_taxis_timeline, label='Number of idle taxis')
    plt.plot(seconds, en_route_taxis_timeline, label='Number of taxis en-route to pick up customers')
    plt.plot(seconds, occupied_taxis_timeline, label='Number of taxis driving to drop-off' )
    plt.plot(seconds, pickup_occupied_taxis_timeline, label='Number of taxis having customers on board but picking up more' )

    plt.title(f'Taxi State Over Time (Greedy Closest algorithm). Config prefix: {prefix}. pp={percpass} pt={perctaxi}')  # Title of the plot
    plt.xlabel('Time (seconds)')  # Label for the x-axis
    plt.ylabel('Idle Taxis')  # Label for the y-axis
    plt.legend()  # Add a legend to identify the plot
    plt.grid(True)  # Enable grid for easier reading of the plot

    plt.savefig(os.path.join(sumo_output_path, 'idle_taxis_plot.png'))
    plt.show()

    return config_dir

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python launch_sumo.py <config_file_path> <sumo_output_path> <cfg_prefix> <percpass> <perctaxi>")
        sys.exit()
    

    config_path = sys.argv[1]
    sumo_output_path = sys.argv[2]
    cfg_prefix = sys.argv[3]
    percpass = sys.argv[4]
    perctaxi = sys.argv[5]
    directory = launch_sumo(config_path, sumo_output_path, cfg_prefix, percpass, perctaxi)

        
