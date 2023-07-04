# check if all the necessary files are present (for those that were not in github repo)
REQUIRED_FILES=(
    "sumo_files/whole_area.net.xml" 
    "sumo_files/reduced_cut_area.net.xml" 
    "data/sijoittelualueet2019.dbf" 
    "data/demand_aht.omx" 
    "sumo_files/verified_trips.rou.xml"
    "sumo_files/simulation_output/fcdresults.xml"
    )

for i in ${REQUIRED_FILES[@]}; do
    if [ ! -f $i ]; then
        echo "File $i does not exist"
        exit 1
    fi
done

echo -e "\nFile check done. Starting the reduction pipeline:"

echo -e "\nExtracting fcd data..."
python3 tools/fcdDataExtractionV8.py

echo -e "\nConverting extracted OD to trips..."
python3 tools/coordinateODToTripsV2.py

echo -e "\nExecuting duarouter..."
# If multithreading is enabled
duarouter -c sumo_files/geo_duarcfg_file.trips2routes_V2.duarcfg --routing-threads 4 --write-trips true --ignore-errors true
# Otherwise
# duarouter -c sumo_files/geo_duarcfg_file.trips2routes_V2.duarcfg --write-trips true --ignore-errors true

echo -e "\nSorting duarouter output routes..."
python3 tools/departureTimeSorter.py sumo_files/verified_reduced_geo_trips_V2.rou.xml sumo_files/verified_reduced_geo_trips_V2.rou.xml
python3 tools/indexZeroToN.py sumo_files/verified_reduced_geo_trips_V2.rou.xml

echo -e "\nRunning sumo router runner..."
python3 sumo_files/geoRouterRunner.py 2> sumo_files/simulation_output/geo_router_runner/stderr.txt

echo -e "\nRunning routesampler..."
$SUMO_HOME/tools/routeSampler.py -r sumo_files/simulation_output/geo_router_runner/routes.rou.xml --edgedata-files sumo_files/reduced_edgedata.xml -o sumo_files/reduced_routesampler_routes.rou.xml

echo -e "\nSetting depart attributes to routes..."
python3 tools/setDepartAttributesToRoutes.py