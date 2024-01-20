# check if all the necessary files are present (for those that were not in github repo)
REQUIRED_FILES=(
    "sumo_files/reduced_cut_area.net.xml" 
    "sumo_files/verified_reduced_geo_trips_V2.rou.xml"
    )

for i in ${REQUIRED_FILES[@]}; do
    if [ ! -f $i ]; then
        echo "File $i does not exist"
        exit 1
    fi
done

echo -e "\nFile check done. Starting the reduced area pipeline:"

echo -e "\nRunning sumo router runner..."
python3 sumo_files/geoRouterRunner.py 2> sumo_files/simulation_output/geo_router_runner/stderr.txt

echo -e "\nRunning routesampler..."
$SUMO_HOME/tools/routeSampler.py -r sumo_files/simulation_output/geo_router_runner/routes.rou.xml --edgedata-files sumo_files/reduced_edgedata.xml -o sumo_files/reduced_routesampler_routes.rou.xml

echo -e "\nSetting depart attributes to routes..."
python3 tools/setDepartAttributesToRoutes.py

echo -e "\nRunning sumo geoRunner..."
python3 sumo_files/geoRunnerV2.py 2> sumo_files/simulation_output/geo_runner/stderr.txt

echo -e "\nCollecting statistics..."
python3 calibration/tools/statistics.py 1 sumo_files/simulation_output/reduced_detector_outputs