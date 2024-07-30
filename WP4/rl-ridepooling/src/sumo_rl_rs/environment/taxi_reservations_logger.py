import os
import csv
import matplotlib.pyplot as plt

class TaxiReservationsLogger:
    def __init__(self, log_taxis: bool, log_reservations: bool, show_graph: bool = False, output_path: str = None) -> None:
        self.log_taxis = log_taxis
        self.show_graph = show_graph

        self._output_path = None  # Private variable to store the output path
        self.output_path = output_path  # Use the setter to initialize

        self._reset_fields()

    @property
    def output_path(self):
        return self._output_path

    @output_path.setter
    def output_path(self, path):
        if path:
            os.makedirs(path, exist_ok=True)  # Create directory if it doesn't exist
        self._output_path = path

    def add_idle_count(self, idle_taxi_count):
        self.idle_taxis_timeline.append(idle_taxi_count)

    def add_en_route_count(self, en_route_taxi_count):
        self.en_route_taxis_timeline.append(en_route_taxi_count)

    def add_occupied_count(self, occupied_taxi_count):
        self.occupied_taxis_timeline.append(occupied_taxi_count)

    def add_pickup_occupied_count(self, pickup_occupied_taxi_count):
        self.pickup_occupied_taxis_timeline.append(pickup_occupied_taxi_count)

    def log(self, sim_time: int):
        if sim_time == 0:
            # don't log empty simulation
            return
        
        if self.log_taxis and self.output_path != None:
            self._save_taxi_logs()
        
        self._make_graph(sim_time)

    def _sanity_check(self):
        """
        Makes sure that the number of entires in all the arrays is the same
        """
        num_entries = len(self.idle_taxis_timeline)
        assert len(self.en_route_taxis_timeline) == num_entries, "Mismatch in en_route_taxis_timeline"
        assert len(self.occupied_taxis_timeline) == num_entries, "Mismatch in occupied_taxis_timeline"
        assert len(self.pickup_occupied_taxis_timeline) == num_entries, "Mismatch in pickup_occupied_taxis_timeline"

    def _save_taxi_logs(self):
        # Function to save data to CSV
        def _save_to_csv(data, filename, path):
            filepath = os.path.join(path, filename)
            with open(filepath, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Second', 'Count'])  # Header
                for second, count in enumerate(data):
                    writer.writerow([second, count])

        _save_to_csv(self.idle_taxis_timeline, 'idle_taxis.csv', self.output_path)
        _save_to_csv(self.en_route_taxis_timeline, 'en_route_taxis.csv', self.output_path)
        _save_to_csv(self.occupied_taxis_timeline, 'occupied_taxis.csv', self.output_path)
        _save_to_csv(self.pickup_occupied_taxis_timeline, 'pickup_occupied_taxis.csv', self.output_path)

    def _make_graph(self, sim_time: int):
        """
        calls plt.show() if show bool is provided. Saves the file if output_path is provided
        """
        seconds = list(range(int(sim_time)))

        # Plotting the line graph
        plt.figure(figsize=(10, 5))  # Set the figure size for better readability

        # Plot datasets
        plt.plot(seconds, self.idle_taxis_timeline, label='Number of idle taxis')
        plt.plot(seconds, self.en_route_taxis_timeline, label='Number of taxis en-route to pick up customers')
        plt.plot(seconds, self.occupied_taxis_timeline, label='Number of taxis driving to drop-off' )
        plt.plot(seconds, self.pickup_occupied_taxis_timeline, label='Number of taxis having customers on board but picking up more' )

        plt.title(f'Taxi State Over Time (Custom algorithm)')  # Title of the plot
        plt.xlabel('Time (seconds)')  # Label for the x-axis
        plt.ylabel('Idle Taxis')  # Label for the y-axis
        plt.legend()  # Add a legend to identify the plot
        plt.grid(True)  # Enable grid for easier reading of the plot

        if self.output_path != None:
            plt.savefig(os.path.join(self.output_path, 'taxis_plot.png'))
        
        if self.show_graph:
            plt.show()

    def _reset_fields(self):
        self.idle_taxis_timeline = []
        self.en_route_taxis_timeline = []
        self.occupied_taxis_timeline = []
        self.pickup_occupied_taxis_timeline = []

    def reset(self):
        self._reset_fields()
