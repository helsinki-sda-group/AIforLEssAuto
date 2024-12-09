import os
import re
import pandas as pd

def find_directories(base_dir, job_id):
    # Create a pattern to match the folder names
    pattern = re.compile(rf"^{job_id}_(\d+)_(\d+)_e(\d+)_area(\d+)_(\d+\.\d+)_tf(\d+)_dlt(\d+)")
    matched_directories = []
    
    # Iterate over all items in the base directory
    for item in os.listdir(base_dir):
        # Check if item is a directory and matches the pattern
        if os.path.isdir(os.path.join(base_dir, item)) and pattern.match(item):
            matched_directories.append(item)
    
    return matched_directories

def parse_directory_name(dir_name):
    # Extract details using regex
    pattern = re.compile(r"^(\d+)_(\d+)_(\d+)_e(\d+)_area(\d+)_(\d+\.\d+)_tf(\d+)_dlt(\d+)")
    match = pattern.match(dir_name)
    if match:
        return {
            "job_id": int(match.group(1)),
            "job_index": int(match.group(2)),
            "task_index": int(match.group(3)),
            "cores": int(match.group(4)),
            "environments": int(match.group(4)),
            "area": int(match.group(5)),
            "sample_percentage": float(match.group(6)),
            "train_frequency": int(match.group(7)),
            "delta": int(match.group(8))
        }
    return None

def process_monitor_file(file_path):
    # Load CSV file and skip the first line (header) with metadata
    df = pd.read_csv(file_path, skiprows=1)
    
    # Check if the DataFrame has any rows
    if df.empty:
        print(f"No data in file: {file_path}")
        return {
            "first_iter_timestamp": 0,
            "last_iter_timestamp": 0,
            "total_iters": 0
        }  # Return None to indicate the file has no valid data
    
    # Extract the first and last runtime, and the total number of lines
    first_iter_timestamp = df['t'].iloc[0]
    last_iter_timestamp = df['t'].iloc[-1]
    total_iters = len(df)
    
    return {
        "first_iter_timestamp": first_iter_timestamp,
        "last_iter_timestamp": last_iter_timestamp,
        "total_iters": total_iters
    }

def main(base_dir, job_id, output_csv):
    # Prepare a list to collect all data rows
    all_data = []
    
    # Step 1: Find matching directories
    directories = find_directories(base_dir, job_id)
    if not directories:
        print("No directories found for the given job ID.")
        return
    
    # Step 2: Process each directory
    for directory in directories:
        # Parse directory name to extract parameters
        parsed_info = parse_directory_name(directory)
        if not parsed_info:
            print(f"Failed to parse directory name: {directory}")
            continue
        
        # Step 3: Find and process monitor.csv file
        monitor_file_path = os.path.join(base_dir, directory, "train", "monitor.csv")
        if os.path.exists(monitor_file_path):
            monitor_data = process_monitor_file(monitor_file_path)
            # Combine parsed info and monitor data into a single dictionary
            data_row = {**parsed_info, **monitor_data}

            # Calculate avg_runtime_per_core as first_iter_timestamp divided by environments
            if data_row["environments"] != 0:
                data_row["avg_runtime_per_core"] = data_row["first_iter_timestamp"] / data_row["environments"]
            else:
                data_row["avg_runtime_per_core"] = None

            all_data.append(data_row)
        else:
            print(f"Monitor file not found in {directory}")

    # Step 4: Write all data to a CSV file
    if all_data:
        df = pd.DataFrame(all_data)
        df = df.sort_values(by=["job_index", "task_index"]).reset_index(drop=True)
        df.to_csv(output_csv, index=False)
        print(f"Data written to {output_csv}")
    else:
        print("No data to write.")

# Example usage
base_dir = "src/tests/output"  # Replace with your actual output folder path
job_id = 8463963     # Replace with your actual job ID
output_csv = "area3_128_summary.csv"  # Output CSV file name
main(base_dir, job_id, output_csv)
