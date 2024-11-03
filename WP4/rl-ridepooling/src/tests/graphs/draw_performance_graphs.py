from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.colors as mcolors

FILE_PATH = 'src/tests/graphs/data_points.java'

def parse_file(file_path=FILE_PATH):
    data = {}
    with open(file_path, 'r') as file:
        label = None
        core_counts = [8, 16, 32, 64, 128]
        for line in file:
            line = line.strip()
            if line.startswith("R#"):
                # If it's a reversed comment, set reversed label
                label = line[2:].strip()
                data[label] = []
                reverse_order = True
            elif line.startswith("#"):
                # If it's a regular comment, set regular label
                label = line[1:].strip()
                data[label] = []
                reverse_order = False
            elif line.startswith("//"):
                continue
            elif line and label:
                # If it's a data line and we have a current label
                try:
                    # Convert the line to a float and append to the current dataset
                    data[label].append(float(line))
                except ValueError:
                    print(f"Warning: Skipping invalid data line: {line}")

                # After collecting 5 data points, handle order if needed and reset label
                if len(data[label]) == 5:
                    if reverse_order:
                        # Reverse the list if the label was prefixed with 'R#'
                        data[label].reverse()
                    label = None  # Reset label for the next dataset
    return core_counts, data

def time_model(n, a, b, c):
    return a / (n - b) + c

core_counts, data = parse_file(FILE_PATH)


df = pd.DataFrame(data, index=core_counts)

# Identify missing data points in the original dataframe (df)
missing_data_points = {}
for label, times in df.items():
    missing_data_points[label] = df[label].isna()

linear_interp_df = df.apply(lambda col: col.replace(0, np.nan).interpolate(method='linear', limit_direction='both'))

blue_shades = [mcolors.to_rgba(c) for c in plt.cm.Blues(np.linspace(0.4, 1, 5))]
green_shades = [mcolors.to_rgba(c) for c in plt.cm.Greens(np.linspace(0.4, 1, 5))]
red_shades = [mcolors.to_rgba(c) for c in plt.cm.Reds(np.linspace(0.4, 1, 5))]

# Plotting Area 1
plt.figure(figsize=(8, 6))
area1_count = 0
missing_data_x_area1 = []
missing_data_y_area1 = []

for label, times in linear_interp_df.items():
    if "Area 1" in label:
        color = blue_shades[area1_count % len(blue_shades)]
        area1_count += 1
        plt.plot(df.index, times, marker='o', label=label, color=color)
        # Collect missing data points
        for core in core_counts:
            if df[label][core] == 0:
                missing_data_x_area1.append(core)
                missing_data_y_area1.append(linear_interp_df[label][core])

plt.plot(missing_data_x_area1, missing_data_y_area1, 'rx', markersize=10, markeredgewidth=2, label="Missing Data")
plt.xlabel("Number of Cores (log scale)")
plt.ylabel("Average Running Time per Core per Iteration (seconds)")
plt.title("Area 1: Average Running Time per Core vs. Number of Cores")
plt.xscale("log")
plt.grid(True, which="major", linestyle="--")
plt.xticks(df.index, labels=df.index)
plt.legend()

plt.savefig("area1_runtime_vs_cores.png", dpi=300)
plt.show()

# Plotting Area 2
plt.figure(figsize=(8, 6))
area2_count = 0
missing_data_x_area2 = []
missing_data_y_area2 = []

for label, times in linear_interp_df.items():
    if "Area 2" in label:
        color = green_shades[area2_count % len(green_shades)]
        area2_count += 1
        plt.plot(df.index, times, marker='o', label=label, color=color)
        # Collect missing data points
        for core in core_counts:
            if df[label][core] == 0:
                missing_data_x_area2.append(core)
                missing_data_y_area2.append(linear_interp_df[label][core])

plt.plot(missing_data_x_area2, missing_data_y_area2, 'rx', markersize=10, markeredgewidth=2, label="Missing Data")
plt.xlabel("Number of Cores (log scale)")
plt.ylabel("Average Running Time per Core per Iteration (seconds)")
plt.title("Area 2: Average Running Time per Core vs. Number of Cores")
plt.xscale("log")
plt.grid(True, which="major", linestyle="--")
plt.xticks(df.index, labels=df.index)
plt.legend()

plt.savefig("area2_runtime_vs_cores.png", dpi=300)
plt.show()

# Plotting Area 3
plt.figure(figsize=(8, 6))
area3_count = 0
missing_data_x_area3 = []
missing_data_y_area3 = []

for label, times in linear_interp_df.items():
    if "Area 3" in label:
        color = red_shades[area3_count % len(red_shades)]
        area3_count += 1
        plt.plot(df.index, times, marker='o', label=label, color=color)
        # Collect missing data points
        for core in core_counts:
            if df[label][core] == 0:
                missing_data_x_area3.append(core)
                missing_data_y_area3.append(linear_interp_df[label][core])

plt.plot(missing_data_x_area3, missing_data_y_area3, 'rx', markersize=10, markeredgewidth=2, label="Missing Data")
plt.xlabel("Number of Cores (log scale)")
plt.ylabel("Average Running Time per Iteration (seconds)")
plt.title("Area 3: Average Running Time per Core vs. Number of Cores")
plt.xscale("log")
plt.grid(True, which="major", linestyle="--")
plt.xticks(df.index, labels=df.index)
plt.legend()

plt.savefig("area3_runtime_vs_cores.png", dpi=300)
plt.show()
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.colors as mcolors

# Define sampling percentages and colors
sampling_percentages = [0.2, 0.4, 0.6, 0.8, 1.0]
core_counts = [8, 16, 32, 64, 128]

# Load and parse data
core_counts, data = parse_file(FILE_PATH)
df = pd.DataFrame(data, index=core_counts)

# Identify missing data points in the original dataframe (df) before interpolation
missing_data_points = {}
for label, times in df.items():
    if "Area 1" in label:
        missing_data_points[label] = df[label].isna()

# Interpolate missing values in df to create linear_interp_df
linear_interp_df = df.apply(lambda col: col.replace(0, np.nan).interpolate(method='linear', limit_direction='both'))

# Extract "Area 1" data and add sampling percentage column
area1_data = {label: times for label, times in linear_interp_df.items() if "Area 1" in label}
area1_data_df = pd.DataFrame(area1_data, index=core_counts).T
area1_data_df['Sampling Percentage'] = sampling_percentages

# Define color palette for each core count
blue_shades = [mcolors.to_rgba(c) for c in plt.cm.Blues(np.linspace(0.4, 1, len(core_counts)))]

# Plot all cores on the same graph
plt.figure(figsize=(10, 7))
missing_data_x = []
missing_data_y = []

for i, core in enumerate(core_counts):
    # Plot time vs. sampling percentage for each core
    plt.plot(area1_data_df['Sampling Percentage'], area1_data_df[core], marker='o', color=blue_shades[i], label=f"{core} Cores")
    
    # Collect interpolated (missing) data points based on original missing indices
    for label, is_missing in missing_data_points.items():
        if "Area 1" in label:
            # Use missing indices to get sampling percentages and interpolated values
            missing_x = area1_data_df['Sampling Percentage'][is_missing.values]
            missing_y = area1_data_df[core][is_missing.values]
            missing_data_x.extend(missing_x)
            missing_data_y.extend(missing_y)

# Plot all missing data points as red 'x' markers after the loop
plt.plot(missing_data_x, missing_data_y, 'rx', markersize=10, markeredgewidth=2, label="Missing Data")

plt.xlabel("Percentage Sampled")
plt.ylabel("Average Running Time per Core per Iteration (seconds)")
plt.title(f"Area 1: Average Running Time for {core} Cores vs. Percentage Sampled")
plt.grid(True, which="major", linestyle="--")
plt.xticks(sampling_percentages)
plt.legend()

plt.savefig("area1_running_time_vs_percentage_sampled.png", dpi=300)
plt.show()