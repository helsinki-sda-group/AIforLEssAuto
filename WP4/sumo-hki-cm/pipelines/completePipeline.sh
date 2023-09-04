# Setting up the basic stuff such as districts (zones)
# edgesInDistricts.py

# Needed directories:
# calibration
# calibration/data
# calibration/tools
# data
# data/fcd_analysis
# sumo_files
# sumo_files/simulation_output
# sumo_files/simulation_output/detector_outputs
# sumo_files/simulation_output/reduced_detector_outputs
# tools

# Files needed for the process:
# tools/visumRouteGeneration.py
# data/demand_aht.omx (or whatever demand file is used)
# data/sijoittelualueet2019.dbf

# sumo_files/od2trips.config.xml
# sumo_files/whole_area_districts.taz.xml

# sumo_files/duarcfg_file.trips2routes.duarcfg
# sumo_files/whole_area.net.xml

# tools/randomDepartureTimes.py
# tools/departureTimeSorter.py
# tools/indexZeroToN.py

# sumo_files/runner.py
# 1_hour_whole_area.sumocfg
# whole_area_zones.poly.xml
# 1_hour.add.xml

# tools/fcdDataExtractionV5.py
# sumo_files/helsinki_edges.taz.xml

# tools/coordinateODToTripsV2.py
# sumo_files/reduced_area.net.xml
# sumo_files/reduced_districts.taz.xml

# sumo_files/geo_duarcfg_file.trips2routes_V2.duarcfg
# tools/departureTimeSorter.py
# sumo_files/geoRunnerV2.py
# sumo_files/1_hour_whole_area_geo_V2.sumocfg
# calibration/tools/statistics.py


# Needed preparation
# Check that the demand file is correct in both visumRouteGeneration.py and coordinateODToTripsV2.py
# Change the .net and .taz files
# Change or remove the polygon files from the .sumocfg files


# Setting up needed empty directories (not included in the GitHub repo)

echo -e "\nSETTING UP DIRECTORIES..."

/bin/bash ./pipelines/setupFolders.sh

echo -e "\nSETTING UP DIRECTORIES COMPLETE"


# The pipeline

# Data preprocessing
echo -e "\nDATA PREPROCESSING..."

/bin/bash ./pipelines/dataPreprocessing.sh

echo -e "\nDATA PREPROCESSING COMPLETE"


# Whole area simulation
echo -e "\nWHOLE AREA SIMULATION..."

/bin/bash ./pipelines/wholeAreaSimulation.sh

echo -e "\nWHOLE AREA SIMULATION COMPLETE"


# Reduction
echo -e "\nREDUCTION..."

/bin/bash ./pipelines/reduction.sh

echo -e "\nREDUCTION COMPLETE"


# Reduced area simulation
echo -e "\REDUCED AREA SIMULATION..."

/bin/bash ./pipelines/reducedAreaSimulation.sh

echo -e "\REDUCED AREA SIMULATION COMPLETE"


# # Randomness testing
# for number in 6 7 8 9 10
# do
#     python3 tools/coordinateODToTripsV2.py
#     duarouter -c sumo_files/geo_duarcfg_file.trips2routes_V2.duarcfg --routing-threads 4 --write-trips true --ignore-errors true
#     python3 tools/departureTimeSorter.py sumo_files/verified_reduced_geo_trips_V2.rou.xml sumo_files/verified_reduced_geo_trips_V2.rou.xml
#     python3 sumo_files/geoRunnerV2.py
#     python3 calibration/tools/statistics.py 1 sumo_files/simulation_output/reduced_detector_outputs
#     mv calibration/data/real_world_comparison_sc_1_2021.xlsx calibration/data/Randomness\ 2023-02-23/real_world_comparison_sc_1_2021\ ${number}.xlsx
# done

# # EXPERIMENTS, SUMO's tool calibrator should be used
# # Calibration
# duarouter -c sumo_files/calibration_routes.duarcfg --routing-threads 4 --ignore-errors true
# python3 tools/tripCalibrator.py sumo_files/calibration_routes.rou.xml calibration/data/real_world_comparison_sc_1_2021_V8.xlsx sumo_files/verified_reduced_geo_trips_V2.rou.xml
# python3 tools/departureTimeSorter.py tests/test_output/tripCalibrator/calibrated_trips.rou.xml tests/test_output/tripCalibrator/calibrated_trips.rou.xml
# python3 tools/indexZeroToN.py tests/test_output/tripCalibrator/calibrated_trips.rou.xml