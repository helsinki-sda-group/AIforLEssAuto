# Setting up the basic stuff such as districts (zones)
# edgesInDistrict.py

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
mkdir calibration/data/randomness
mkdir data
mkdir data/fcd_analysis
mkdir sumo_files/simulation_output
mkdir sumo_files/simulation_output/detector_outputs
mkdir sumo_files/simulation_output/reduced_detector_outputs

# The pipeline
# Whole area
python3 tools/visumRouteGeneration.py
od2trips -c sumo_files/od2trips.config.xml
# If multithreading is enabled
# duarouter -c sumo_files/duarcfg_file.trips2routes.duarcfg --routing-threads 4 --write-trips true --ignore-errors true
# Otherwise
duarouter -c sumo_files/duarcfg_file.trips2routes.duarcfg --write-trips true --ignore-errors true
python3 tools/randomDepartureTimes.py sumo_files/verified_trips.rou.xml
python3 tools/departureTimeSorter.py
python3 tools/indexZeroToN.py
python3 sumo_files/runner.py

# Reduction
python3 tools/fcdDataExtractionV5.py
python3 tools/coordinateODToTripsV2.py
# If multithreading is enabled
# duarouter -c sumo_files/geo_duarcfg_file.trips2routes_V2.duarcfg --routing-threads 4 --write-trips true --ignore-errors true
# Otherwise
duarouter -c sumo_files/geo_duarcfg_file.trips2routes_V2.duarcfg --write-trips true --ignore-errors true
python3 tools/departureTimeSorter.py sumo_files/verified_reduced_geo_trips_V2.rou.xml sumo_files/verified_reduced_geo_trips_V2.rou.xml
python3 sumo_files/geoRunnerV2.py
python3 calibration/tools/statistics.py 1 sumo_files/simulation_output/reduced_detector_outputs


# # Randomness testing
# for number in 1 2 3 4 5 6 7 8 9 10
# do
#     python3 tools/coordinateODToTripsV2.py
#     duarouter -c sumo_files/geo_duarcfg_file.trips2routes_V2.duarcfg --routing-threads 4 --write-trips true --ignore-errors true
#     python3 tools/departureTimeSorter.py sumo_files/verified_reduced_geo_trips_V2.rou.xml sumo_files/verified_reduced_geo_trips_V2.rou.xml
#     python3 sumo_files/geoRunnerV2.py
#     python3 calibration/tools/statistics.py 1 sumo_files/simulation_output/reduced_detector_outputs
#     mv calibration/data/real_world_comparison_sc_1_2021.xlsx calibration/data/randomness/real_world_comparison_sc_1_2021\ ${number}.xlsx
# done