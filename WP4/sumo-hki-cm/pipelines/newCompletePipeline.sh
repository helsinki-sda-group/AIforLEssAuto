# check if all the necessary files are present (for those that were not in github repo)
REQUIRED_FILES=(
    "sumo_files/whole_area.net.xml" 
    "data/sijoittelualueet2019.dbf" 
    "data/demand_aht.omx" 
    "sumo_files/reduction_cutRoutes.config.xml"
    "sumo_files/duarcfg_file.trips2routes.duarcfg"
    "sumo_files/reduced_area_random_trips.config.xml"
    )

for i in ${REQUIRED_FILES[@]}; do
    if [ ! -f $i ]; then
        echo "File $i does not exist"
        exit 1
    fi
done

echo -e "\nFile check done. Starting the pipeline:"


echo -e "\nSetting up directories..."
/bin/bash ./pipelines/setupFolders.sh

echo -e "\nVisum route generation..."
python3 tools/visumRouteGeneration.py

echo -e "\nOD2trips..."
od2trips -c sumo_files/od2trips.config.xml

echo -e "\nDuarouter..."
# If multithreading is enabled
duarouter -c sumo_files/duarcfg_file.trips2routes.duarcfg --routing-threads 8
# Otherwise
# duarouter -c sumo_files/duarcfg_file.trips2routes.duarcfg

echo -e "\nCutRoutes..."
python3 $SUMO_HOME/tools/route/cutRoutes.py -c sumo_files/reduction_cutRoutes.config.xml

# Random trips
echo -e "\nRandom trips..."
python3 $SUMO_HOME/tools/randomTrips.py -c sumo_files/reduced_area_random_trips.config.xml --duarouter-routing-threads 8 --duarouter-weights.priority-factor 20 2>&1 1>sumo_files/output/tools/reduced_area_random_trips/std.log

# Iterative routesampler
echo -e "\nIterative routesampler..."
python3 tools/iterativeRoutesampler.py

# SUMO
echo -e "\nRunning geoRunner (SUMO simulation)..."
python3 tools/geoRunner.py

# statistics
echo -e "\nCollecting statistics..."
python3 calibration/tools/statistics.py 1 sumo_files/simulation_output/reduced_detector_outputs